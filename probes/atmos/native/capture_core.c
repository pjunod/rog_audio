/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 rog_audio contributors
 */
#include "capture_core.h"
#include <errno.h>
#include <string.h>
#include <unistd.h>

bool cap_init(struct cap_core *c, unsigned channels)
{
    memset(c, 0, sizeof(*c));
    if (channels != 2 && channels != 12) return false;
    c->stride = channels * 4;
#define INIT(field) atomic_init(&c->field, 0)
    INIT(captured); INIT(taken); INIT(bytes_written); INIT(error); INIT(maximum_ring);
    INIT(overflow_events); INIT(writer_io_errors);
    INIT(rejected_frames); INIT(callbacks); INIT(clock_observations); INIT(unavailable_clock);
    INIT(header_observations); INIT(unavailable_pts); INIT(sequence_regressions);
    INIT(pts_regressions); INIT(clock_gaps); INIT(header_discontinuities);
#undef INIT
    return atomic_is_lock_free(&c->captured) && atomic_is_lock_free(&c->error);
}
void cap_fail(struct cap_core *c, enum cap_error error)
{
    if (error == CAP_OVERFLOW) atomic_fetch_add(&c->overflow_events, 1);
    if (error == CAP_WRITE) atomic_fetch_add(&c->writer_io_errors, 1);
    unsigned expected = CAP_OK;
    atomic_compare_exchange_strong(&c->error, &expected, error);
}
const char *cap_error_name(unsigned error)
{
    const char *const names[] = {"completed", "capture-ring-overflow", "capture-file-limit",
        "capture-chunk-invalid", "capture-write-failure", "capture-control-invalid",
        "capture-pipewire-failure", "capture-cancelled", "capture-timeline-discontinuity", "capture-corrupted"};
    return error < sizeof(names) / sizeof(names[0]) ? names[error] : "capture-internal-failure";
}
static bool stamp(struct cap_core *c, uint32_t frames, const struct cap_stamp *s)
{
    atomic_fetch_add(&c->callbacks, 1);
    if (s->clock_valid) {
        atomic_fetch_add(&c->clock_observations, 1);
        /* Only used when pw_time has the same fixed 48-kHz frame domain and its
         * reported cycle size equals this chunk. No sequence-frequency guess. */
        if (c->have_clock && (s->ticks < c->last_ticks || s->ticks - c->last_ticks != c->last_frames)) {
            if (!c->first_clock_gap) {
                c->first_clock_gap = true;
                c->gap_expected_ticks = c->last_ticks + c->last_frames;
                c->gap_actual_ticks = s->ticks;
                c->gap_previous_frames = c->last_frames; c->gap_current_frames = frames;
                c->gap_previous_info = c->last_clock_info; c->gap_current_info = s->clock_info;
            }
            atomic_fetch_add(&c->clock_gaps, 1); cap_fail(c, CAP_TIMELINE); return false;
        }
        if (!c->seen_clock) c->first_ticks = s->ticks;
        c->seen_clock = true;
        c->have_clock = true; c->last_ticks = s->ticks; c->last_frames = frames;
        c->last_clock_info = s->clock_info;
    } else {
        atomic_fetch_add(&c->unavailable_clock, 1);
        c->have_clock = false;
    }
    if (s->header_present) {
        atomic_fetch_add(&c->header_observations, 1);
        /* SPA meta seq increments at a media-specific frequency, not always 1. */
        uint64_t step = s->sequence - c->last_sequence;
        /* uint64 wrap is forward below half-range; larger jumps are regressions
         * for this bounded capture interval. No fixed increment is assumed. */
        if (c->have_header && step > UINT64_MAX / 2) {
            atomic_fetch_add(&c->sequence_regressions, 1); cap_fail(c, CAP_TIMELINE); return false;
        }
        if (!c->have_header) c->first_sequence = s->sequence;
        else if (step > c->largest_sequence_step)
            c->largest_sequence_step = step;
        /* DISCONT on the first armed header is a startup boundary. */
        if ((s->header_flags & 1u) && c->have_header) {
            atomic_fetch_add(&c->header_discontinuities, 1); cap_fail(c, CAP_TIMELINE); return false;
        }
        if (s->header_flags & 2u) { cap_fail(c, CAP_CORRUPTED); return false; }
        c->have_header = true; c->last_sequence = s->sequence;
    }
    if (s->pts_valid) {
        if (c->have_pts && s->pts < c->last_pts) {
            atomic_fetch_add(&c->pts_regressions, 1); cap_fail(c, CAP_TIMELINE); return false;
        }
        if (!c->have_pts) c->first_pts = s->pts;
        c->have_pts = true; c->last_pts = s->pts;
    } else atomic_fetch_add(&c->unavailable_pts, 1);
    return true;
}
bool cap_push(struct cap_core *c, const void *input, uint32_t frames, const struct cap_stamp *s)
{
    if (atomic_load(&c->error)) { atomic_fetch_add(&c->rejected_frames, frames); return false; }
    if (!frames || frames > CAP_RING_FRAMES || !input || !s) { cap_fail(c, CAP_CHUNK); return false; }
    uint32_t write = atomic_load_explicit(&c->captured, memory_order_relaxed);
    uint32_t used = write - atomic_load_explicit(&c->taken, memory_order_acquire);
    if (write > CAP_MAX_BYTES / c->stride || frames > CAP_MAX_BYTES / c->stride - write) {
        atomic_fetch_add(&c->rejected_frames, frames); cap_fail(c, CAP_LIMIT); return false;
    }
    if (frames > CAP_RING_FRAMES - used) {
        atomic_fetch_add(&c->rejected_frames, frames); cap_fail(c, CAP_OVERFLOW); return false;
    }
    if (!stamp(c, frames, s)) { atomic_fetch_add(&c->rejected_frames, frames); return false; }
    uint32_t first = CAP_RING_FRAMES - write % CAP_RING_FRAMES;
    if (first > frames) first = frames;
    memcpy(c->pcm + (write % CAP_RING_FRAMES) * c->stride, input, first * c->stride);
    memcpy(c->pcm, (const unsigned char *)input + first * c->stride, (frames - first) * c->stride);
    atomic_store_explicit(&c->captured, write + frames, memory_order_release);
    if (used + frames > atomic_load(&c->maximum_ring)) atomic_store(&c->maximum_ring, used + frames);
    return true;
}
uint32_t cap_take(struct cap_core *c, void *output, uint32_t maximum_frames)
{
    uint32_t read = atomic_load_explicit(&c->taken, memory_order_relaxed);
    uint32_t count = atomic_load_explicit(&c->captured, memory_order_acquire) - read;
    if (count > maximum_frames) count = maximum_frames;
    uint32_t first = CAP_RING_FRAMES - read % CAP_RING_FRAMES;
    if (first > count) first = count;
    memcpy(output, c->pcm + (read % CAP_RING_FRAMES) * c->stride, first * c->stride);
    memcpy((unsigned char *)output + first * c->stride, c->pcm, (count - first) * c->stride);
    atomic_store_explicit(&c->taken, read + count, memory_order_release);
    return count;
}
bool cap_write_bytes(struct cap_core *c, int fd, const void *data, uint32_t bytes)
{
    const unsigned char *p = data;
    while (bytes) {
        uint32_t written = atomic_load(&c->bytes_written);
        if (written > CAP_MAX_BYTES || bytes > CAP_MAX_BYTES - written) { cap_fail(c, CAP_LIMIT); return false; }
        ssize_t n = write(fd, p, bytes);
        if (n < 0 && errno == EINTR) continue;
        if (n <= 0) { cap_fail(c, CAP_WRITE); return false; }
        atomic_fetch_add(&c->bytes_written, n); p += n; bytes -= n;
    }
    return true;
}
