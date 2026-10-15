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
int main(void)
{
    int input_pipe[2], control[2];
    assert(pipe2(input_pipe, O_CLOEXEC | O_NONBLOCK) == 0);
    assert(fcntl(input_pipe[1], F_SETPIPE_SZ, 4096) == 4096);
    assert(dup2(input_pipe[0], STDIN_FILENO) == STDIN_FILENO);
    close(input_pipe[0]);
    assert(socketpair(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0, control) == 0);
    struct playback *p = calloc(1, sizeof(*p));
    assert(p && rog_init(&p->core, 12));
    atomic_init(&p->stop, false);
    p->control = control[1];
    pw_init(NULL, NULL);
    p->main_loop = pw_main_loop_new(NULL); assert(p->main_loop);
    p->loop = pw_main_loop_get_loop(p->main_loop);
    p->event = pw_loop_add_event(p->loop, on_event, p); assert(p->event);
    p->wake = eventfd(0, EFD_CLOEXEC | EFD_NONBLOCK); assert(p->wake >= 0);
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
