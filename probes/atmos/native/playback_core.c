/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 rog_audio contributors
 */
#include "playback_core.h"
#include <string.h>
#include <limits.h>

bool rog_init(struct rog_core *c, uint32_t channels)
{
    memset(c, 0, sizeof(*c));
    if (channels != 2 && channels != 12) return false;
    c->channels = channels;
    c->stride = channels * sizeof(float);
    atomic_init(&c->written, 0); atomic_init(&c->consumed, 0);
    atomic_init(&c->maximum_ring, 0); atomic_init(&c->maximum_callback, 0);
    atomic_init(&c->error, ROG_OK); atomic_init(&c->begun, false);
    atomic_init(&c->eof, false); atomic_init(&c->media_started, false);
    atomic_init(&c->media_frames, 0); atomic_init(&c->priming_frames, 0);
    atomic_init(&c->startup_silence, 0); atomic_init(&c->prefill_silence, 0);
    atomic_init(&c->underflows, 0); atomic_init(&c->missing, 0);
    return sizeof(float) == 4 && atomic_is_lock_free(&c->written) &&
        atomic_is_lock_free(&c->begun) && atomic_is_lock_free(&c->error);
}
void rog_fail(struct rog_core *c, enum rog_error error)
{
    unsigned expected = ROG_OK;
    atomic_compare_exchange_strong(&c->error, &expected, error);
}
const char *rog_error_name(unsigned error)
{
    static const char *const names[] = { "completed", "native-control-invalid",
        "native-input-invalid", "native-input-truncated", "native-input-extra",
        "native-media-underrun", "native-callback-quantum-unsupported",
        "native-pipewire-failure", "native-cancelled", "native-io-failure" };
    return error < sizeof(names) / sizeof(names[0]) ? names[error] : "native-internal-failure";
}
uint32_t rog_available(const struct rog_core *c)
{
    return atomic_load_explicit(&c->written, memory_order_acquire) -
           atomic_load_explicit(&c->consumed, memory_order_acquire);
}
uint32_t rog_space(const struct rog_core *c) { return ROG_RING_FRAMES - rog_available(c); }
static bool push(struct rog_core *c, const unsigned char *data, uint32_t frames)
{
    uint32_t written = atomic_load_explicit(&c->written, memory_order_relaxed);
    uint32_t used = written - atomic_load_explicit(&c->consumed, memory_order_acquire);
    bool begun = atomic_load_explicit(&c->begun, memory_order_acquire);
    uint32_t limit = begun ? c->boundary + c->expected : ROG_MAX_PRIMING;
    if (frames > ROG_RING_FRAMES - used) { rog_fail(c, ROG_INPUT); return false; }
    if (written > limit || frames > limit - written) { rog_fail(c, ROG_EXTRA); return false; }
    uint32_t first = ROG_RING_FRAMES - written % ROG_RING_FRAMES;
    if (first > frames) first = frames;
    memcpy(c->pcm + (written % ROG_RING_FRAMES) * c->stride, data, first * c->stride);
    memcpy(c->pcm, data + first * c->stride, (frames - first) * c->stride);
    atomic_store_explicit(&c->written, written + frames, memory_order_release);
    if (used + frames > atomic_load(&c->maximum_ring)) atomic_store(&c->maximum_ring, used + frames);
    return true;
}
bool rog_input(struct rog_core *c, const unsigned char *data, size_t bytes)
{
    if (bytes > 4096 || atomic_load(&c->eof)) { rog_fail(c, ROG_INPUT); return false; }
    bool begun = atomic_load_explicit(&c->begun, memory_order_acquire);
    uint32_t limit = begun ? c->boundary + c->expected : ROG_MAX_PRIMING;
    uint32_t written = atomic_load(&c->written);
    if (written > limit || c->partial_bytes + bytes > (size_t)(limit - written) * c->stride) {
        rog_fail(c, ROG_EXTRA); return false;
    }
    if (c->partial_bytes) {
        size_t take = c->stride - c->partial_bytes;
        if (take > bytes) take = bytes;
        memcpy(c->partial + c->partial_bytes, data, take);
        c->partial_bytes += take; data += take; bytes -= take;
        if (c->partial_bytes == c->stride) {
            if (!push(c, c->partial, 1)) return false;
            c->partial_bytes = 0;
        }
    }
    uint32_t frames = bytes / c->stride;
    if (frames && !push(c, data, frames)) return false;
    data += frames * c->stride; bytes -= frames * c->stride;
    if (bytes) { memcpy(c->partial, data, bytes); c->partial_bytes = bytes; }
    return true;
}
bool rog_input_eof(struct rog_core *c)
{
    if (c->partial_bytes || !atomic_load_explicit(&c->begun, memory_order_acquire) ||
            atomic_load(&c->written) != c->boundary + c->expected) {
        rog_fail(c, ROG_TRUNCATED); return false;
    }
    atomic_store_explicit(&c->eof, true, memory_order_release);
    return true;
}
/* Exact unsigned decimal fields; no signs, trailing tokens or embedded NUL. */
static bool number(const char **cursor, const char *end, uint32_t *value, char terminator)
{
    const char *p = *cursor;
    uint32_t result = 0;
    if (p == end || *p < '0' || *p > '9') return false;
    while (p < end && *p >= '0' && *p <= '9') {
        unsigned digit = (unsigned)(*p++ - '0');
        if (result > (UINT32_MAX - digit) / 10) return false;
        result = result * 10 + digit;
    }
    if (p == end || *p++ != terminator) return false;
    *cursor = p; *value = result;
    return true;
}
bool rog_begin(struct rog_core *c, const char *packet, size_t bytes)
{
    const char *p = packet, *end = packet + bytes;
    uint32_t sequence, boundary, expected;
    if (bytes < 7 || bytes > ROG_CONTROL_BYTES || memcmp(p, "BEGIN ", 6)) goto invalid;
    p += 6;
    if (!number(&p, end, &sequence, ' ') || !number(&p, end, &boundary, ' ') ||
            !number(&p, end, &expected, '\n') || p != end || sequence != 1 ||
            atomic_load(&c->begun) || boundary > ROG_MAX_PRIMING ||
            !expected || expected > ROG_MAX_MEDIA ||
            boundary < atomic_load(&c->written) || boundary < atomic_load(&c->consumed)) goto invalid;
    c->boundary = boundary; c->expected = expected;
    atomic_store_explicit(&c->begun, true, memory_order_release);
    return true;
invalid:
    rog_fail(c, ROG_CONTROL);
    return false;
}
static void pull(struct rog_core *c, unsigned char *out, uint32_t read, uint32_t frames)
{
    uint32_t first = ROG_RING_FRAMES - read % ROG_RING_FRAMES;
    if (first > frames) first = frames;
    memcpy(out, c->pcm + (read % ROG_RING_FRAMES) * c->stride, first * c->stride);
    memcpy(out + first * c->stride, c->pcm, (frames - first) * c->stride);
    atomic_store_explicit(&c->consumed, read + frames, memory_order_release);
}
uint32_t rog_render(struct rog_core *c, void *output, uint32_t requested)
{
    if (!requested || requested > ROG_RING_FRAMES) { rog_fail(c, ROG_QUANTUM); return 0; }
    if (requested > atomic_load(&c->maximum_callback)) atomic_store(&c->maximum_callback, requested);
    if (atomic_load(&c->error)) return 0;
    uint32_t read = atomic_load_explicit(&c->consumed, memory_order_relaxed);
    uint32_t available = atomic_load_explicit(&c->written, memory_order_acquire) - read;
    bool begun = atomic_load_explicit(&c->begun, memory_order_acquire);
    if (!begun || read < c->boundary) {
        uint32_t frames = available < requested ? available : requested;
        if (begun && frames > c->boundary - read) frames = c->boundary - read;
        pull(c, output, read, frames);
        memset((unsigned char *)output + frames * c->stride, 0, (requested - frames) * c->stride);
        atomic_fetch_add(&c->priming_frames, frames);
        atomic_fetch_add(&c->startup_silence, requested - frames);
        return requested;
    }
    uint32_t media = atomic_load(&c->media_frames), remaining = c->expected - media;
    if (!remaining) return 0;
    if (!atomic_load(&c->media_started)) {
        uint32_t prefill = remaining < ROG_RING_FRAMES ? remaining : ROG_RING_FRAMES;
        if (available < prefill) {
            memset(output, 0, requested * c->stride);
            atomic_fetch_add(&c->prefill_silence, requested);
            return requested;
        }
        atomic_store(&c->media_started, true);
    }
    uint32_t frames = remaining < requested ? remaining : requested;
    if (available < frames) {
        atomic_fetch_add(&c->underflows, 1);
        atomic_fetch_add(&c->missing, frames - available);
        rog_fail(c, ROG_UNDERRUN);
        return 0;
    }
    pull(c, output, read, frames);
    atomic_fetch_add(&c->media_frames, frames);
    return frames;
}
bool rog_consumed_all(const struct rog_core *c)
{
    return atomic_load_explicit(&c->begun, memory_order_acquire) &&
        atomic_load(&c->consumed) == c->boundary + c->expected &&
        atomic_load(&c->media_frames) == c->expected;
}
