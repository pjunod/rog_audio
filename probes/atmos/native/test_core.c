/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 rog_audio contributors
 * Separate test executable. The playback helper has no test mode.
 */
#include "playback_core.h"
#include <assert.h>
#include <pthread.h>
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
static struct rog_core core;
static void input(const void *data, size_t bytes)
{
    const unsigned char *p = data;
    while (bytes) {
        size_t take = bytes < 4096 ? bytes : 4096;
        assert(rog_input(&core, p, take));
        p += take; bytes -= take;
    }
}
static void boundary(uint32_t priming, uint32_t media)
{
    char command[128];
    int bytes = snprintf(command, sizeof(command), "BEGIN 1 %u %u\n", priming, media);
    assert(rog_begin(&core, command, bytes));
}
static void fill(float *out, unsigned first, unsigned frames, unsigned channels)
{
    for (unsigned n = 0; n < frames; n++)
        for (unsigned ch = 0; ch < channels; ch++) out[n * channels + ch] = (float)(first + n + ch * 1000000);
}
static void *writer(void *arg)
{
    (void)arg;
    float data[85 * 12];
    for (unsigned at = 0; at < 100000;) {
        unsigned n = 100000 - at; if (n > 85) n = 85;
        while (rog_space(&core) < n) sched_yield();
        fill(data, at, n, 12);
        input(data, n * 48);
        at += n;
    }
    assert(rog_input_eof(&core));
    return NULL;
}
static void concurrent(void)
{
    assert(rog_init(&core, 12)); boundary(0, 100000);
    pthread_t thread; assert(pthread_create(&thread, NULL, writer, NULL) == 0);
    float got[256 * 12], expected[256 * 12];
    unsigned at = 0;
    while (at < 100000) {
        unsigned n = 100000 - at; if (n > 256) n = 256;
        /* This tests the ring's ordering, not synthetic scheduler starvation. */
        if (rog_available(&core) < (at ? n : ROG_RING_FRAMES)) { sched_yield(); continue; }
        assert(rog_render(&core, got, n) == n);
        fill(expected, at, n, 12);
        assert(!memcmp(got, expected, n * 48));
        at += n;
    }
    assert(pthread_join(thread, NULL) == 0);
    assert(rog_consumed_all(&core)); assert(atomic_load(&core.eof));
    assert(!atomic_load(&core.error)); assert(atomic_load(&core.maximum_ring) <= ROG_RING_FRAMES);
}
static void partial_tail(void)
{
    assert(rog_init(&core, 2));
    float media[777 * 2], output[256 * 2], priming[5 * 2] = {0};
    fill(media, 1, 777, 2);
    input(priming, sizeof(priming));
    boundary(5, 777);
    /* The handoff may split priming, but may never consume a media frame. */
    assert(rog_render(&core, output, 256) == 256);
    assert(atomic_load(&core.media_frames) == 0);
    input(media, 7);  /* Deliberately split a frame across I/O reads. */
    input((unsigned char *)media + 7, sizeof(media) - 7);
    assert(rog_input_eof(&core));
    for (unsigned at = 0; at < 777;) {
        unsigned n = 777 - at; if (n > 256) n = 256;
        assert(rog_render(&core, output, 256) == n);
        assert(!memcmp(output, media + at * 2, n * 8)); at += n;
    }
    assert(rog_render(&core, output, 256) == 0);
    assert(atomic_load(&core.priming_frames) == 5);
    assert(atomic_load(&core.startup_silence) == 251);
    assert(rog_consumed_all(&core)); assert(!atomic_load(&core.underflows));
}
static void starvation(void)
{
    float data[4096 * 2] = {0}, output[4096 * 2];
    assert(rog_init(&core, 2)); boundary(0, 5000);
    input(data, 1000 * 8);
    assert(rog_render(&core, output, 256) == 256);
    assert(atomic_load(&core.media_frames) == 0 && atomic_load(&core.prefill_silence) == 256);
    input(data, (4096 - 1000) * 8);
    assert(rog_render(&core, output, 4096) == 4096);
    assert(rog_render(&core, output, 256) == 0);
    assert(atomic_load(&core.error) == ROG_UNDERRUN);
    assert(atomic_load(&core.underflows) == 1 && atomic_load(&core.missing) == 256);
    assert(!rog_consumed_all(&core));
    for (unsigned count = 0; count < 4; count++) {
        assert(rog_init(&core, 2)); boundary(0, 1);
        if (count == 0) { input(data, 7); assert(!rog_input_eof(&core)); }
        if (count == 1) assert(!rog_input_eof(&core));
        if (count == 2) { input(data, 8); assert(!rog_input(&core, (unsigned char *)data, 1)); }
        if (count == 3) assert(!rog_input(&core, (unsigned char *)data, 16));
        assert(atomic_load(&core.error) == (count < 2 ? ROG_TRUNCATED : ROG_EXTRA));
    }
    assert(rog_init(&core, 2)); boundary(0, 1);
    assert(!rog_render(&core, output, ROG_RING_FRAMES + 1));
    assert(atomic_load(&core.error) == ROG_QUANTUM);
}
static void protocol(void)
{
    const char *bad[] = { "BEGIN 2 0 1\n", "BEGIN 1 0 0\n", "BEGIN 1 -1 1\n",
        "BEGIN 1 0 4320001\n", "BEGIN 1 2160001 1\n", "BEGIN 1 0 1\nextra",
        "BEGIN 1 42949672960 1\n", "BEGIN 1 0 1", "BEGIN 1 0 1\n\0extra" };
    for (unsigned n = 0; n < sizeof(bad) / sizeof(bad[0]); n++) {
        assert(rog_init(&core, 2));
        assert(!rog_begin(&core, bad[n], n == 8 ? 19 : strlen(bad[n])));
        assert(!atomic_load(&core.begun));
    }
    assert(rog_init(&core, 2)); boundary(0, 1);
    assert(!rog_begin(&core, "BEGIN 1 0 1\n", 12));
    assert(atomic_load(&core.error) == ROG_CONTROL);
    assert(rog_init(&core, 2));
    char oversized[129]; memset(oversized, 'x', sizeof(oversized));
    assert(!rog_begin(&core, oversized, sizeof(oversized)));
    assert(rog_init(&core, 2)); float priming[4] = {0}; input(priming, sizeof(priming));
    assert(!rog_begin(&core, "BEGIN 1 1 1\n", 12));
}
int main(int argc, char **argv)
{
    if (argc != 2) return 2;
    if (!strcmp(argv[1], "concurrent")) concurrent();
    else if (!strcmp(argv[1], "partial-tail")) partial_tail();
    else if (!strcmp(argv[1], "starvation")) starvation();
    else if (!strcmp(argv[1], "protocol")) protocol();
    else return 2;
    puts("passed"); return 0;
}
