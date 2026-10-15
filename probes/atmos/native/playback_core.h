/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 rog_audio contributors
 * Fixed single-producer/single-consumer PCM transport. No PipeWire dependency.
 */
#ifndef ROG_PLAYBACK_CORE_H
#define ROG_PLAYBACK_CORE_H
#include <stdatomic.h>
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#define ROG_RING_FRAMES 4096u
#define ROG_MAX_CHANNELS 12u
#define ROG_MAX_PRIMING 2160000u
#define ROG_MAX_MEDIA 4320000u
#define ROG_CONTROL_BYTES 128u
#define ROG_PROTOCOL "rog-atmos-pw-v1"
enum rog_error { ROG_OK, ROG_CONTROL, ROG_INPUT, ROG_TRUNCATED, ROG_EXTRA,
    ROG_UNDERRUN, ROG_QUANTUM, ROG_PIPEWIRE, ROG_CANCELLED, ROG_IO };
struct rog_core {
    _Alignas(64) atomic_uint written;
    _Alignas(64) atomic_uint consumed;
    atomic_uint maximum_ring, maximum_callback, error;
    atomic_bool begun, eof, media_started;
    uint32_t channels, stride;
    /* Published once, by release store to begun, before any media stdin bytes. */
    uint32_t boundary, expected;
    atomic_uint media_frames, priming_frames, startup_silence, prefill_silence;
    atomic_uint underflows, missing;
    unsigned char pcm[ROG_RING_FRAMES * ROG_MAX_CHANNELS * sizeof(float)];
    /* I/O-thread owned, never touched by the callback. */
    unsigned char partial[ROG_MAX_CHANNELS * sizeof(float)];
    size_t partial_bytes;
};
bool rog_init(struct rog_core *, uint32_t channels);
void rog_fail(struct rog_core *, enum rog_error);
const char *rog_error_name(unsigned error);
uint32_t rog_available(const struct rog_core *);
uint32_t rog_space(const struct rog_core *);
/* Input is only called by the I/O thread, with <=4096 bytes and enough space. */
bool rog_input(struct rog_core *, const unsigned char *, size_t bytes);
bool rog_input_eof(struct rog_core *);
bool rog_begin(struct rog_core *, const char *, size_t bytes);
/* Callback-only consumer: returns chunk frames, including startup silence.
 * A declared final partial media chunk returns only its actual frame count. */
uint32_t rog_render(struct rog_core *, void *, uint32_t requested);
bool rog_consumed_all(const struct rog_core *);
#endif
