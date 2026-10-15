/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 rog_audio contributors
 * Exercise the actual helper I/O functions without connecting a PipeWire server.
 * A separate translation unit gives its test driver access to private functions;
 * the production executable itself has no test mode.
 */
#define main rog_playback_main
#include "playback.c"
#undef main
#include <assert.h>
#include <time.h>
static struct pw_buffer *test_buffer;
static int queue_result;
static unsigned queued_calls, drain_calls;
struct pw_buffer *__wrap_pw_stream_dequeue_buffer(struct pw_stream *stream)
{
    (void)stream;
    return test_buffer;
}
int __wrap_pw_stream_queue_buffer(struct pw_stream *stream, struct pw_buffer *buffer)
{
    (void)stream;
    assert(buffer == test_buffer);
    queued_calls++;
    return queue_result;
}
int __wrap_pw_stream_flush(struct pw_stream *stream, bool drain)
{
    (void)stream;
    assert(drain);
    drain_calls++;
    return 0;
}
int main(void)
{
    int input_pipe[2], control[2];
    assert(pipe2(input_pipe, O_CLOEXEC | O_NONBLOCK) == 0);
    assert(fcntl(input_pipe[1], F_SETPIPE_SZ, 4096) == 4096);
    assert(dup2(input_pipe[0], STDIN_FILENO) == STDIN_FILENO);
    close(input_pipe[0]);
    assert(socketpair(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0, control) == 0);
    struct playback *p = aligned_alloc(_Alignof(struct playback), sizeof(struct playback));
    assert(p && (uintptr_t)p % _Alignof(struct playback) == 0);
    memset(p, 0, sizeof(*p));
    assert(rog_init(&p->core, 12));
    atomic_init(&p->stop, false);
    atomic_init(&p->queued_all, false);
    atomic_init(&p->demand_after_final, false);
    p->control = control[1];
    pw_init(NULL, NULL);
    p->main_loop = pw_main_loop_new(NULL); assert(p->main_loop);
    p->loop = pw_main_loop_get_loop(p->main_loop);
    p->event = pw_loop_add_event(p->loop, on_event, p); assert(p->event);
    p->wake = eventfd(0, EFD_CLOEXEC | EFD_NONBLOCK); assert(p->wake >= 0);
    /* A previous/EOF event must not flush while the final callback has consumed
     * its last partial frame but has not yet queued its output buffer. */
    const unsigned char frame[48] = {0};
    unsigned char output[256 * 48];
    assert(rog_begin(&p->core, "BEGIN 1 0 1\n", 12));
    assert(rog_input(&p->core, frame, sizeof(frame)) && rog_input_eof(&p->core));
    assert(rog_render(&p->core, output, 256) == 1 && rog_consumed_all(&p->core));
    on_event(p, 1);
    assert(!p->draining && !atomic_load(&p->core.error));
    struct spa_chunk chunk = {0};
    struct spa_data data = { .data = output, .maxsize = sizeof(output), .chunk = &chunk };
    struct spa_buffer buffer = { .n_datas = 1, .datas = &data };
    struct pw_buffer pw_buffer = { .buffer = &buffer, .requested = 256 };
    test_buffer = &pw_buffer;
    /* Failed final queueing must never publish either drain prerequisite. */
    assert(rog_init(&p->core, 12));
    assert(rog_begin(&p->core, "BEGIN 1 0 1\n", 12));
    assert(rog_input(&p->core, frame, sizeof(frame)) && rog_input_eof(&p->core));
    queue_result = -EIO;
    on_process(p);
    assert(atomic_load(&p->core.error) == ROG_PIPEWIRE);
    assert(!atomic_load(&p->queued_all) && !atomic_load(&p->demand_after_final));
    /* Exercise actual partial and aligned callbacks, and late transport EOF.
     * Successful queue_buffer alone is insufficient: a later process request
     * must publish demand, without queueing any zero-size EOF buffer. */
    unsigned char media[256 * 48];
    for (size_t i = 0; i < sizeof(media); i++) media[i] = (unsigned char)(i % 251 + 1);
    for (unsigned attempt = 0; attempt < 2; attempt++) {
        unsigned frames = attempt == 0 ? 247 : 256;
        assert(rog_init(&p->core, 12));
        atomic_store(&p->queued_all, false); atomic_store(&p->demand_after_final, false);
        p->draining = p->drained = false;
        queue_result = 0; queued_calls = drain_calls = 0;
        char command[64];
        int count = snprintf(command, sizeof(command), "BEGIN 1 0 %u\n", frames);
        assert(count > 0 && rog_begin(&p->core, command, (size_t)count));
        for (size_t offset = 0; offset < frames * 48; ) {
            size_t bytes = frames * 48 - offset;
            if (bytes > 4096) bytes = 4096;
            assert(rog_input(&p->core, media + offset, bytes)); offset += bytes;
        }
        if (attempt == 0) assert(rog_input_eof(&p->core));
        on_process(p);
        assert(queued_calls == 1 && atomic_load(&p->queued_all));
        assert(!atomic_load(&p->demand_after_final));
        assert(chunk.size == frames * 48 && pw_buffer.size == frames);
        assert(!memcmp(output, media, frames * 48));
        on_event(p, 1);
        assert(!p->draining && drain_calls == 0);
        on_process(p);
        assert(queued_calls == 1 && atomic_load(&p->demand_after_final));
        on_event(p, 1);
        if (attempt == 1) {
            assert(!p->draining && drain_calls == 0);
            assert(rog_input_eof(&p->core));
            on_event(p, 1);
        }
        assert(p->draining && drain_calls == 1);
        on_process(p); on_event(p, 1);
        assert(queued_calls == 1 && drain_calls == 1);
        on_drained(p);
        assert(p->drained && !atomic_load(&p->core.error));
    }
    assert(rog_init(&p->core, 12)); atomic_store(&p->queued_all, false);
    atomic_store(&p->demand_after_final, false);
    p->draining = p->drained = false;
    assert(pthread_create(&p->reader, NULL, read_input, p) == 0);
    unsigned char zeros[4096] = {0};
    size_t remaining = ROG_RING_FRAMES * 48;
    for (unsigned tries = 0; remaining && tries < 10000; tries++) {
        size_t count = remaining < sizeof(zeros) ? remaining : sizeof(zeros);
        ssize_t written = write(input_pipe[1], zeros, count);
        if (written > 0) remaining -= written;
        else { assert(errno == EAGAIN); usleep(1000); }
    }
    assert(!remaining);
    for (unsigned tries = 0; rog_available(&p->core) != ROG_RING_FRAMES && tries < 10000; tries++) usleep(1000);
    assert(rog_available(&p->core) == ROG_RING_FRAMES);
    assert(write(input_pipe[1], zeros, 4080) == 4080);
    /* This ACK must not depend on draining stdin or the full PCM ring. */
    const char command[] = "BEGIN 1 4181 1\n";
    assert(send(control[0], command, sizeof(command) - 1, 0) == sizeof(command) - 1);
    on_control(p, control[1], SPA_IO_IN);
    char reply[128];
    ssize_t size = recv(control[0], reply, sizeof(reply), MSG_DONTWAIT);
    assert(size == 13 && !memcmp(reply, "ACK 1 4181 1\n", 13));
    /* Cancellation wakes and joins the real I/O thread while both queues are full. */
    on_signal(p, SIGTERM);
    atomic_store(&p->stop, true);
    uint64_t wake = 1; assert(write(p->wake, &wake, sizeof(wake)) == sizeof(wake));
    struct timespec deadline; assert(clock_gettime(CLOCK_REALTIME, &deadline) == 0); deadline.tv_sec += 2;
    assert(pthread_timedjoin_np(p->reader, NULL, &deadline) == 0);
    assert(atomic_load(&p->core.error) == ROG_CANCELLED);
    final_status(p);
    char terminal[2048];
    size = recv(control[0], terminal, sizeof(terminal) - 1, MSG_DONTWAIT);
    assert(size > 0); terminal[size] = 0;
    assert(strstr(terminal, "native-cancelled") && strstr(terminal, "\"drained\":false"));
    close(input_pipe[1]); close(control[0]); close(control[1]); close(p->wake);
    pw_loop_destroy_source(p->loop, p->event); pw_main_loop_destroy(p->main_loop);
    pw_deinit(); free(p); puts("passed"); return 0;
}
