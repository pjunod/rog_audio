/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 rog_audio contributors
 * Independent harness observer; not used by production playback.
 */
#ifndef ROG_CAPTURE_CORE_H
#define ROG_CAPTURE_CORE_H
#include <stdatomic.h>
#include <stdbool.h>
#include <stdint.h>
#define CAP_PROTOCOL "rog-atmos-capture-v1"
#define CAP_RING_FRAMES 4096u
#define CAP_MAX_BYTES (256u * 1024u * 1024u)
enum cap_error { CAP_OK, CAP_OVERFLOW, CAP_LIMIT, CAP_CHUNK, CAP_WRITE,
    CAP_CONTROL, CAP_PIPEWIRE, CAP_CANCELLED, CAP_TIMELINE, CAP_CORRUPTED };
/* Diagnostic association data only; never changes clock validity/failure. */
struct cap_clock_info {
    bool available;
    uint64_t buffer_time, size;
    int64_t now;
    uint32_t rate_num, rate_denom;
};
struct cap_stamp {
    bool clock_valid, header_present, pts_valid;
    uint64_t ticks, sequence;
    int64_t pts;
    uint32_t header_flags;
    struct cap_clock_info clock_info;
};
struct cap_core {
    _Alignas(64) atomic_uint captured;
    _Alignas(64) atomic_uint taken;
    atomic_uint bytes_written, error, maximum_ring, rejected_frames;
    atomic_uint callbacks, clock_observations, unavailable_clock, header_observations;
    atomic_uint overflow_events, writer_io_errors;
    atomic_uint unavailable_pts, sequence_regressions, pts_regressions, clock_gaps, header_discontinuities;
    uint32_t stride;
    /* Callback-owned continuity state, read only after stream destruction. */
    bool have_clock, seen_clock, have_header, have_pts;
    uint64_t last_ticks, first_ticks, last_sequence, first_sequence, largest_sequence_step;
    int64_t last_pts, first_pts;
    uint32_t last_frames;
    bool first_clock_gap;
    uint64_t gap_expected_ticks, gap_actual_ticks;
    uint32_t gap_previous_frames, gap_current_frames;
    struct cap_clock_info last_clock_info, gap_previous_info, gap_current_info;
    unsigned char pcm[CAP_RING_FRAMES * 48];
};
bool cap_init(struct cap_core *, unsigned channels);
void cap_fail(struct cap_core *, enum cap_error);
const char *cap_error_name(unsigned);
/* Callback-only producer; never blocks or grows storage. */
bool cap_push(struct cap_core *, const void *, uint32_t frames, const struct cap_stamp *);
/* Ordinary writer consumer. Returned bytes are copied to private scratch. */
uint32_t cap_take(struct cap_core *, void *, uint32_t maximum_frames);
bool cap_write_bytes(struct cap_core *, int fd, const void *, uint32_t bytes);
#endif
