/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 rog_audio contributors
 * Separate harness observer tests; no server connection or production test mode.
 */
#define main rog_capture_main
#include "capture.c"
#undef main
#include <assert.h>
#include <sched.h>
static struct cap_core test_core;
static struct pw_buffer *test_buffer;
static struct capture *test_capture;
static int write_fd = -1, write_mode, write_calls, queue_result;
static bool inject_final;
static uint64_t test_ticks;
ssize_t __real_write(int fd, const void *data, size_t size);
ssize_t __wrap_write(int fd, const void *data, size_t size)
{
    if (fd == write_fd) {
        write_calls++;
        if (write_mode == 2 && write_calls > 1) { errno = EIO; return -1; }
        size_t bound = write_mode == 2 ? 3 : 7;
        if (write_mode && size > bound) size = bound;
    }
    return __real_write(fd, data, size);
}
struct pw_buffer *__wrap_pw_stream_dequeue_buffer(struct pw_stream *stream) { (void)stream; return test_buffer; }
int __wrap_pw_stream_queue_buffer(struct pw_stream *stream, struct pw_buffer *buffer)
{ (void)stream; assert(buffer == test_buffer); return queue_result; }
int __wrap_pw_stream_get_time_n(struct pw_stream *stream, struct pw_time *time, size_t size)
{
    (void)stream; assert(size == sizeof(*time)); memset(time, 0, size);
    time->rate.num = 1; time->rate.denom = 48000; time->size = 256; time->ticks = test_ticks; return 0;
}
void __wrap_pw_stream_destroy(struct pw_stream *stream)
{
    assert(stream == (struct pw_stream *)1 && test_capture);
    assert(!atomic_load(&test_capture->armed) && !atomic_load(&test_capture->writer_stop));
    if (inject_final) {
        float frame[12] = {0}; struct cap_stamp stamp = {0};
        atomic_fetch_add(&test_capture->received, 1);
        assert(cap_push(&test_capture->core, frame, 1, &stamp));
    }
}
static void fill(float *out, unsigned first, unsigned frames)
{
    for (unsigned n = 0; n < frames; n++)
        for (unsigned ch = 0; ch < 12; ch++) out[n * 12 + ch] = (float)(first + n + ch * 1000000);
}
static void *produce(void *unused)
{
    (void)unused; float data[257 * 12]; struct cap_stamp stamp = {0};
    for (unsigned at = 0; at < 100000;) {
        unsigned used = atomic_load(&test_core.captured) - atomic_load(&test_core.taken);
        unsigned n = CAP_RING_FRAMES - used;
        if (!n) { sched_yield(); continue; }
        if (n > 257) n = 257;
        if (n > 100000 - at) n = 100000 - at;
        fill(data, at, n); assert(cap_push(&test_core, data, n, &stamp)); at += n;
    }
    return NULL;
}
static void ring_case(void)
{
    assert(cap_init(&test_core, 12));
    pthread_t thread; assert(pthread_create(&thread, NULL, produce, NULL) == 0);
    float out[85 * 12], expected[85 * 12];
    for (unsigned at = 0; at < 100000;) {
        unsigned n = cap_take(&test_core, out, 85);
        if (!n) { sched_yield(); continue; }
        fill(expected, at, n); assert(!memcmp(out, expected, n * 48)); at += n;
    }
    assert(pthread_join(thread, NULL) == 0 && !atomic_load(&test_core.error));
    static float full[CAP_RING_FRAMES * 12]; struct cap_stamp stamp = {0};
    assert(cap_init(&test_core, 12)); assert(cap_push(&test_core, full, CAP_RING_FRAMES, &stamp));
    assert(!cap_push(&test_core, full, 1, &stamp));
    assert(atomic_load(&test_core.error) == CAP_OVERFLOW && atomic_load(&test_core.rejected_frames) == 1);
    assert(atomic_load(&test_core.captured) == CAP_RING_FRAMES);
    assert(cap_init(&test_core, 12)); atomic_store(&test_core.captured, CAP_MAX_BYTES / 48);
    assert(!cap_push(&test_core, full, 1, &stamp) && atomic_load(&test_core.error) == CAP_LIMIT);
}
static void timeline_case(void)
{
    float frame[12] = {0};
    struct cap_stamp stamp = {.clock_valid = true, .header_present = true, .pts_valid = true,
        .ticks = 100, .sequence = UINT64_MAX - 1, .pts = -100};
    assert(cap_init(&test_core, 12)); assert(cap_push(&test_core, frame, 1, &stamp));
    stamp.ticks++; stamp.sequence = 1; stamp.pts++;
    assert(cap_push(&test_core, frame, 1, &stamp));  /* Actual uint64 wrap, not a regression. */
    stamp.ticks += 2;
    assert(!cap_push(&test_core, frame, 1, &stamp));
    assert(atomic_load(&test_core.clock_gaps) == 1);
    for (unsigned mode = 0; mode < 4; mode++) {
        assert(cap_init(&test_core, 12));
        stamp = (struct cap_stamp){.header_present = true, .pts_valid = true, .sequence = 100, .pts = 100};
        assert(cap_push(&test_core, frame, 1, &stamp));
        if (mode == 0) stamp.sequence = 99;
        if (mode == 1) stamp.pts = 99;
        if (mode == 2) stamp.header_flags = SPA_META_HEADER_FLAG_DISCONT;
        if (mode == 3) stamp.header_flags = SPA_META_HEADER_FLAG_CORRUPTED;
        assert(!cap_push(&test_core, frame, 1, &stamp));
    }
    assert(cap_init(&test_core, 12)); stamp = (struct cap_stamp){0};
    assert(cap_push(&test_core, frame, 1, &stamp)); assert(cap_push(&test_core, frame, 1, &stamp));
    assert(atomic_load(&test_core.unavailable_clock) == 2 && atomic_load(&test_core.unavailable_pts) == 2);
    assert(!atomic_load(&test_core.error)); /* Missing metadata is not an invented loss. */
}
static void writer_case(void)
{
    FILE *file = tmpfile(); assert(file); write_fd = fileno(file);
    unsigned char data[48] = {0};
    assert(cap_init(&test_core, 12)); write_mode = 1; write_calls = 0;
    assert(cap_write_bytes(&test_core, write_fd, data, sizeof(data)));
    assert(atomic_load(&test_core.bytes_written) == 48 && write_calls > 1);
    assert(cap_init(&test_core, 12)); write_mode = 2; write_calls = 0;
    assert(!cap_write_bytes(&test_core, write_fd, data, sizeof(data)));
    assert(atomic_load(&test_core.bytes_written) == 3 && atomic_load(&test_core.error) == CAP_WRITE);
    assert(cap_init(&test_core, 12)); atomic_store(&test_core.bytes_written, CAP_MAX_BYTES);
    assert(!cap_write_bytes(&test_core, write_fd, data, 1) && atomic_load(&test_core.error) == CAP_LIMIT);
    write_mode = 0; write_fd = -1; fclose(file);
}
static void lifecycle_case(void)
{
    struct capture *p = aligned_alloc(_Alignof(struct capture), sizeof(struct capture));
    assert(p && (uintptr_t)p % _Alignof(struct capture) == 0); memset(p, 0, sizeof(*p));
    assert(cap_init(&p->core, 12)); atomic_init(&p->armed, false); atomic_init(&p->writer_stop, false);
    atomic_init(&p->received, 0); atomic_init(&p->ignored, 0);
    int controls[2]; assert(socketpair(AF_UNIX, SOCK_SEQPACKET, 0, controls) == 0);
    FILE *file = tmpfile(); assert(file); p->output = fileno(file); p->control = controls[1];
    pw_init(NULL, NULL); p->main_loop = pw_main_loop_new(NULL); assert(p->main_loop);
    p->loop = pw_main_loop_get_loop(p->main_loop); p->event = pw_loop_add_event(p->loop, capture_event, p); assert(p->event);
    p->wake = eventfd(0, EFD_CLOEXEC | EFD_NONBLOCK); assert(p->wake >= 0);
    float samples[257 * 12] = {0}; struct spa_chunk chunk = {.offset = 48, .size = 256 * 48, .stride = 48};
    struct spa_data data = {.data = samples, .maxsize = sizeof(samples), .chunk = &chunk};
    struct spa_buffer buffer = {.n_datas = 1, .datas = &data}; struct pw_buffer pw_buffer = {.buffer = &buffer};
    test_buffer = &pw_buffer; queue_result = 0; test_ticks = 100;
    capture_process(p); assert(atomic_load(&p->ignored) == 256 && !atomic_load(&p->core.captured));
    assert(send(controls[0], "ARM 1\n", 6, 0) == 6); capture_control(p, controls[1], SPA_IO_IN);
    char reply[32]; assert(recv(controls[0], reply, sizeof(reply), MSG_DONTWAIT) == 6 && !memcmp(reply, "ACK 1\n", 6));
    capture_process(p); assert(atomic_load(&p->core.captured) == 256);
    assert(pthread_create(&p->writer, NULL, write_output, p) == 0); p->writer_started = true;
    assert(send(controls[0], "STOP 2\n", 7, 0) == 7); capture_control(p, controls[1], SPA_IO_IN);
    assert(recv(controls[0], reply, sizeof(reply), MSG_DONTWAIT) == 6 && !memcmp(reply, "ACK 2\n", 6));
    p->stream = (struct pw_stream *)1; test_capture = p; inject_final = true;
    capture_shutdown(p); assert(atomic_load(&p->core.bytes_written) == 257 * 48);
    assert(atomic_load(&p->core.captured) == atomic_load(&p->core.taken));
    capture_final(p); char terminal[2048]; ssize_t count = recv(controls[0], terminal, sizeof(terminal) - 1, MSG_DONTWAIT);
    assert(count > 0); terminal[count] = 0; assert(strstr(terminal, "\"complete\":true"));
    /* Actual callback rejects invalid byte extents and a failed requeue. */
    assert(cap_init(&p->core, 12)); chunk.size = 1; capture_process(p);
    assert(atomic_load(&p->core.error) == CAP_CHUNK);
    assert(cap_init(&p->core, 12)); chunk.size = 48; queue_result = -EIO; capture_process(p);
    assert(atomic_load(&p->core.error) == CAP_PIPEWIRE);
    assert(cap_init(&p->core, 12)); p->armed_once = false; p->stopping = false;
    assert(send(controls[0], "STOP 2\n", 7, 0) == 7); capture_control(p, controls[1], SPA_IO_IN);
    assert(atomic_load(&p->core.error) == CAP_CONTROL);
    assert(cap_init(&p->core, 12)); p->armed_once = false; p->stopping = false;
    assert(send(controls[0], "ARM 1\n", 6, 0) == 6); capture_control(p, controls[1], SPA_IO_IN);
    assert(recv(controls[0], reply, sizeof(reply), MSG_DONTWAIT) == 6);
    assert(send(controls[0], "ARM 1\n", 6, 0) == 6); capture_control(p, controls[1], SPA_IO_IN);
    assert(atomic_load(&p->core.error) == CAP_CONTROL);
    assert(cap_init(&p->core, 12)); char oversized[33]; memset(oversized, 'x', sizeof(oversized));
    assert(send(controls[0], oversized, sizeof(oversized), 0) == sizeof(oversized));
    capture_control(p, controls[1], SPA_IO_IN); assert(atomic_load(&p->core.error) == CAP_CONTROL);
    assert(cap_init(&p->core, 12)); atomic_store(&p->armed, true); queue_result = 0;
    for (unsigned i = 0; i < sizeof(samples) / sizeof(float); i++) ((float *)samples)[i] = (float)i;
    chunk.offset = sizeof(samples) - 24; chunk.size = 48; chunk.flags = 0;
    capture_process(p); float observed[12], expected[12];
    memcpy(expected, (unsigned char *)samples + sizeof(samples) - 24, 24); memcpy(expected + 6, samples, 24);
    assert(cap_take(&p->core, observed, 1) == 1 && !memcmp(observed, expected, 48));
    assert(cap_init(&p->core, 12)); data.data = NULL; chunk.flags = SPA_CHUNK_FLAG_EMPTY;
    capture_process(p); assert(cap_take(&p->core, observed, 1) == 1);
    const float silence[12] = {0}; assert(!memcmp(observed, silence, 48));
    assert(cap_init(&p->core, 12)); chunk.flags = SPA_CHUNK_FLAG_CORRUPTED;
    capture_process(p); assert(atomic_load(&p->core.error) == CAP_CORRUPTED);
    assert(cap_init(&p->core, 12)); capture_signal(p, SIGTERM);
    assert(atomic_load(&p->core.error) == CAP_CANCELLED);
    close(p->wake); close(controls[0]); close(controls[1]); fclose(file);
    pw_loop_destroy_source(p->loop, p->event); pw_main_loop_destroy(p->main_loop); pw_deinit(); free(p);
}
static void fd_case(void)
{
    char path[] = "/tmp/rog-capture-fd.XXXXXX";
    int initial = mkstemp(path); assert(initial >= 0); close(initial);
    int output = open(path, O_WRONLY); assert(output > 2);
    int control[2]; assert(socketpair(AF_UNIX, SOCK_SEQPACKET, 0, control) == 0);
    char output_text[16], control_text[16];
    snprintf(output_text, sizeof(output_text), "%d", output); snprintf(control_text, sizeof(control_text), "%d", control[1]);
    char *args[] = {"capture", "--channels", "2", "--output-fd", output_text, "--control-fd", control_text, NULL};
    assert(write(output, "x", 1) == 1); assert(rog_capture_main(7, args) == 2); assert(ftruncate(output, 0) == 0);
    assert(fchmod(output, 0644) == 0); assert(rog_capture_main(7, args) == 2); assert(fchmod(output, 0600) == 0);
    char linked[128]; snprintf(linked, sizeof(linked), "%s.link", path);
    assert(link(path, linked) == 0); assert(rog_capture_main(7, args) == 2); assert(unlink(linked) == 0);
    assert(fcntl(output, F_SETFL, O_APPEND) == 0); assert(rog_capture_main(7, args) == 2); assert(fcntl(output, F_SETFL, 0) == 0);
    snprintf(control_text, sizeof(control_text), "%d", output); assert(rog_capture_main(7, args) == 2);
    int stream[2]; assert(socketpair(AF_UNIX, SOCK_STREAM, 0, stream) == 0);
    snprintf(control_text, sizeof(control_text), "%d", stream[1]); assert(rog_capture_main(7, args) == 2);
    close(stream[0]); close(stream[1]);
    int pipes[2]; assert(pipe(pipes) == 0);
    snprintf(output_text, sizeof(output_text), "%d", pipes[1]); snprintf(control_text, sizeof(control_text), "%d", control[1]);
    assert(rog_capture_main(7, args) == 2);
    close(pipes[0]); close(pipes[1]); close(output); close(control[0]); close(control[1]); assert(unlink(path) == 0);
}
int main(int argc, char **argv)
{
    if (argc != 2) return 2;
    if (!strcmp(argv[1], "ring")) ring_case();
    else if (!strcmp(argv[1], "timeline")) timeline_case();
    else if (!strcmp(argv[1], "writer")) writer_case();
    else if (!strcmp(argv[1], "lifecycle")) lifecycle_case();
    else if (!strcmp(argv[1], "fd-contract")) fd_case();
    else return 2;
    puts("passed"); return 0;
}
