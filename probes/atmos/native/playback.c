/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 rog_audio contributors
 * Process callback/stream setup adapted from PipeWire audio-src-ring.c:
 * Copyright (c) 2024 Wim Taymans, MIT. See PIPEWIRE-EXAMPLE-LICENSE.
 * PCM/control I/O is confined to ordinary threads. The callback never waits.
 */
#define _GNU_SOURCE
#include "playback_core.h"
#include <errno.h>
#include <fcntl.h>
#include <poll.h>
#include <pthread.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/eventfd.h>
#include <sys/socket.h>
#include <unistd.h>
#include <spa/param/audio/format-utils.h>
#include <pipewire/pipewire.h>

struct playback {
    struct rog_core core;
    struct pw_main_loop *main_loop;
    struct pw_loop *loop;
    struct pw_stream *stream;
    struct spa_source *event, *control_source;
    int control, wake;
    pthread_t reader;
    bool reader_started, draining, drained, connected;
    atomic_bool stop, queued_all;
    struct spa_audio_info_raw format;
};
static void notify(struct playback *p) { pw_loop_signal_event(p->loop, p->event); }
static void fail(struct playback *p, enum rog_error error)
{
    rog_fail(&p->core, error);
    notify(p);
}
static void *read_input(void *opaque)
{
    struct playback *p = opaque;
    unsigned char bytes[4096];
    sigset_t mask;
    sigemptyset(&mask); sigaddset(&mask, SIGINT); sigaddset(&mask, SIGTERM); sigaddset(&mask, SIGHUP);
    pthread_sigmask(SIG_BLOCK, &mask, NULL);
    while (!atomic_load(&p->stop) && !atomic_load(&p->core.error)) {
        uint32_t space = rog_space(&p->core);
        struct pollfd fds[2] = {{ .fd = space ? STDIN_FILENO : -1, .events = POLLIN },
                               { .fd = p->wake, .events = POLLIN }};
        int result = poll(fds, 2, 50);
        if (result < 0) { if (errno == EINTR) continue; fail(p, ROG_IO); break; }
        if (fds[1].revents & POLLIN) { uint64_t n; while (read(p->wake, &n, sizeof(n)) > 0) {} }
        if (!space || !(fds[0].revents & (POLLIN | POLLHUP | POLLERR))) continue;
        size_t limit = space * p->core.stride - p->core.partial_bytes;
        if (limit > sizeof(bytes)) limit = sizeof(bytes);
        ssize_t count = read(STDIN_FILENO, bytes, limit);
        if (count < 0) {
            if (errno == EAGAIN || errno == EINTR) continue;
            fail(p, ROG_IO); break;
        }
        if (!count) { rog_input_eof(&p->core); notify(p); break; }
        if (!rog_input(&p->core, bytes, (size_t)count)) { notify(p); break; }
    }
    return NULL;
}
/* Called on the mainloop, not from the realtime process callback. */
static void on_event(void *opaque, uint64_t count)
{
    struct playback *p = opaque;
    (void)count;
    uint64_t wake = 1;
    if (write(p->wake, &wake, sizeof(wake)) < 0 && errno != EAGAIN) rog_fail(&p->core, ROG_IO);
    if (atomic_load(&p->core.error)) { pw_main_loop_quit(p->main_loop); return; }
    if (!p->draining && atomic_load_explicit(&p->queued_all, memory_order_acquire) &&
            atomic_load_explicit(&p->core.eof, memory_order_acquire) && rog_consumed_all(&p->core)) {
        p->draining = true;
        if (pw_stream_flush(p->stream, true) < 0) {
            rog_fail(&p->core, ROG_PIPEWIRE); pw_main_loop_quit(p->main_loop);
        }
    }
}
static void on_process(void *opaque)
{
    struct playback *p = opaque;
    struct pw_buffer *b = pw_stream_dequeue_buffer(p->stream);
    if (b == NULL) return;
    struct spa_buffer *buffer = b->buffer;
    uint32_t frames = 0;
    if (buffer->n_datas != 1 || buffer->datas[0].data == NULL || buffer->datas[0].chunk == NULL) {
        rog_fail(&p->core, ROG_PIPEWIRE);
    } else {
        struct spa_data *data = &buffer->datas[0];
        uint32_t requested = data->maxsize / p->core.stride;
        if (b->requested && b->requested < requested) requested = b->requested;
        frames = rog_render(&p->core, data->data, requested);
        data->chunk->offset = 0;
        data->chunk->stride = p->core.stride;
        data->chunk->size = frames * p->core.stride;
    }
    b->size = frames;
    bool final_media = frames > 0 && rog_consumed_all(&p->core);
    int queued = pw_stream_queue_buffer(p->stream, b);
    if (queued < 0) rog_fail(&p->core, ROG_PIPEWIRE);
    /* Counters are visible before queue_buffer. Publish drain eligibility only
     * after the final buffer has actually been queued, including partial tails. */
    if (final_media && queued >= 0 && !atomic_load(&p->core.error))
        atomic_store_explicit(&p->queued_all, true, memory_order_release);
    /* PipeWire's ring example uses this RT-safe event handoff. No file/socket
     * read/write, allocation, logging, mutex or condition wait occurs here. */
    notify(p);
}
static void on_drained(void *opaque)
{
    struct playback *p = opaque;
    if (!p->draining || !atomic_load(&p->queued_all) || !atomic_load(&p->core.eof) || !rog_consumed_all(&p->core)) {
        rog_fail(&p->core, ROG_PIPEWIRE);
    } else p->drained = true;
    pw_main_loop_quit(p->main_loop);
}
static void on_state(void *opaque, enum pw_stream_state old, enum pw_stream_state state, const char *error)
{
    struct playback *p = opaque;
    (void)old; (void)error;
    if (state == PW_STREAM_STATE_PAUSED || state == PW_STREAM_STATE_STREAMING) p->connected = true;
    if (state == PW_STREAM_STATE_ERROR || (state == PW_STREAM_STATE_UNCONNECTED && p->connected && !p->drained))
        fail(p, ROG_PIPEWIRE);
}
static void on_format(void *opaque, uint32_t id, const struct spa_pod *param)
{
    struct playback *p = opaque;
    struct spa_audio_info_raw actual = {0};
    if (id != SPA_PARAM_Format || param == NULL) return;
    if (spa_format_audio_raw_parse(param, &actual) < 0 || actual.format != SPA_AUDIO_FORMAT_F32_LE ||
            actual.rate != 48000 || actual.channels != p->format.channels ||
            memcmp(actual.position, p->format.position, actual.channels * sizeof(uint32_t)))
        fail(p, ROG_PIPEWIRE);
}
static const struct pw_stream_events events = {
    PW_VERSION_STREAM_EVENTS, .state_changed = on_state, .param_changed = on_format,
    .process = on_process, .drained = on_drained
};
static void on_signal(void *opaque, int number)
{
    struct playback *p = opaque;
    (void)number;
    rog_fail(&p->core, ROG_CANCELLED);
    pw_main_loop_quit(p->main_loop);
}
static void on_control(void *opaque, int fd, uint32_t mask)
{
    struct playback *p = opaque;
    char packet[ROG_CONTROL_BYTES], reply[ROG_CONTROL_BYTES];
    struct iovec io = { .iov_base = packet, .iov_len = sizeof(packet) };
    struct msghdr msg = { .msg_iov = &io, .msg_iovlen = 1 };
    if (!(mask & SPA_IO_IN)) { fail(p, ROG_CONTROL); return; }
    ssize_t count = recvmsg(fd, &msg, MSG_DONTWAIT);
    if (count < 0 && (errno == EAGAIN || errno == EINTR)) return;
    if (count <= 0 || (msg.msg_flags & (MSG_TRUNC | MSG_CTRUNC)) ||
            !rog_begin(&p->core, packet, count)) { fail(p, ROG_CONTROL); return; }
    int size = snprintf(reply, sizeof(reply), "ACK 1 %u %u\n", p->core.boundary, p->core.expected);
    if (send(fd, reply, size, MSG_DONTWAIT | MSG_NOSIGNAL) != size) fail(p, ROG_CONTROL);
}
static void final_status(struct playback *p)
{
    char packet[2048];
    unsigned error = atomic_load(&p->core.error);
    if (!error && !p->drained) { rog_fail(&p->core, ROG_PIPEWIRE); error = atomic_load(&p->core.error); }
    int size = snprintf(packet, sizeof(packet),
        "FINAL {\"protocol\":\"%s\",\"status\":\"%s\",\"input_frames\":%u,"
        "\"consumed_frames\":%u,\"media_frames\":%u,\"stdin_priming_frames\":%u,"
        "\"startup_silence_frames\":%u,\"prefill_silence_frames\":%u,"
        "\"underflow_events\":%u,\"missing_media_frames\":%u,\"ring_capacity_frames\":%u,"
        "\"maximum_ring_frames\":%u,\"maximum_callback_frames\":%u,"
        "\"input_eof\":%s,\"ring_consumed\":%s,\"drained\":%s}\n",
        ROG_PROTOCOL, rog_error_name(error), atomic_load(&p->core.written), atomic_load(&p->core.consumed),
        atomic_load(&p->core.media_frames), atomic_load(&p->core.priming_frames),
        atomic_load(&p->core.startup_silence), atomic_load(&p->core.prefill_silence),
        atomic_load(&p->core.underflows), atomic_load(&p->core.missing), ROG_RING_FRAMES,
        atomic_load(&p->core.maximum_ring), atomic_load(&p->core.maximum_callback),
        atomic_load(&p->core.eof) ? "true" : "false", rog_consumed_all(&p->core) ? "true" : "false",
        p->drained ? "true" : "false");
    if (size > 0 && (size_t)size < sizeof(packet)) (void)send(p->control, packet, size, MSG_DONTWAIT | MSG_NOSIGNAL);
}
static bool decimal(const char *s)
{
    if (!*s || strlen(s) > 19) return false;
    for (const char *p = s; *p; p++) if (*p < '0' || *p > '9') return false;
    errno = 0;
    return strtoull(s, NULL, 10) > 0 && errno == 0;
}
int main(int argc, char **argv)
{
    if (argc == 2 && !strcmp(argv[1], "--describe")) {
        printf("{\"protocol\":\"%s\",\"ring_frames\":%u,\"rate\":48000,\"channels\":[2,12],"
               "\"format\":\"f32le\",\"pipewire_library\":\"%s\"}\n", ROG_PROTOCOL, ROG_RING_FRAMES, pw_get_library_version());
        return 0;
    }
    if (argc != 9 || strcmp(argv[1], "--target") || !decimal(argv[2]) ||
            strcmp(argv[3], "--channels") || (strcmp(argv[4], "2") && strcmp(argv[4], "12")) ||
            strcmp(argv[5], "--name") || !*argv[6] || strlen(argv[6]) > 128 ||
            strcmp(argv[7], "--control-fd") || !decimal(argv[8])) return 2;
    for (const char *n = argv[6]; *n; n++)
        if (!((*n >= 'a' && *n <= 'z') || (*n >= '0' && *n <= '9') || *n == '-')) return 2;
    unsigned long long fd = strtoull(argv[8], NULL, 10);
    if (fd <= STDERR_FILENO || fd > 127) return 2;
    int type = 0; socklen_t length = sizeof(type);
    if (getsockopt((int)fd, SOL_SOCKET, SO_TYPE, &type, &length) < 0 || type != SOCK_SEQPACKET) return 2;
    struct playback *p = aligned_alloc(_Alignof(struct playback), sizeof(struct playback));
    if (!p) return 2;
    memset(p, 0, sizeof(*p));
    if (!rog_init(&p->core, (uint32_t)atoi(argv[4]))) { free(p); return 2; }
    p->control = (int)fd; p->wake = -1;
    atomic_init(&p->stop, false);
    atomic_init(&p->queued_all, false);
    if (fcntl(STDIN_FILENO, F_SETFL, fcntl(STDIN_FILENO, F_GETFL) | O_NONBLOCK) < 0) goto done;
    pw_init(NULL, NULL);
    p->main_loop = pw_main_loop_new(NULL);
    if (!p->main_loop) goto done;
    p->loop = pw_main_loop_get_loop(p->main_loop);
    p->wake = eventfd(0, EFD_CLOEXEC | EFD_NONBLOCK);
    if (p->wake < 0) goto done;
    p->event = pw_loop_add_event(p->loop, on_event, p);
    p->control_source = pw_loop_add_io(p->loop, p->control, SPA_IO_IN | SPA_IO_ERR | SPA_IO_HUP, false, on_control, p);
    if (!p->event || !p->control_source) goto done;
    pw_loop_add_signal(p->loop, SIGINT, on_signal, p);
    pw_loop_add_signal(p->loop, SIGTERM, on_signal, p);
    pw_loop_add_signal(p->loop, SIGHUP, on_signal, p);
    struct pw_properties *props = pw_properties_new(
        PW_KEY_MEDIA_TYPE, "Audio", PW_KEY_MEDIA_CATEGORY, "Playback", PW_KEY_MEDIA_ROLE, "Music",
        PW_KEY_NODE_NAME, argv[6], PW_KEY_MEDIA_NAME, "ROG Atmos prototype", PW_KEY_TARGET_OBJECT, argv[2],
        "node.dont-fallback", "true", "node.dont-reconnect", "true", "node.dont-move", "true",
        "stream.dont-remix", "true", "channelmix.disable", "true", "state.restore-props", "false", NULL);
    if (!props) goto done;
    p->stream = pw_stream_new_simple(p->loop, "ROG Atmos prototype", props, &events, p);
    if (!p->stream) goto done;
    p->format.format = SPA_AUDIO_FORMAT_F32_LE;
    p->format.rate = 48000;
    p->format.channels = p->core.channels;
    const uint32_t positions[] = { SPA_AUDIO_CHANNEL_FL, SPA_AUDIO_CHANNEL_FR, SPA_AUDIO_CHANNEL_FC,
        SPA_AUDIO_CHANNEL_LFE, SPA_AUDIO_CHANNEL_RL, SPA_AUDIO_CHANNEL_RR, SPA_AUDIO_CHANNEL_SL,
        SPA_AUDIO_CHANNEL_SR, SPA_AUDIO_CHANNEL_TFL, SPA_AUDIO_CHANNEL_TFR, SPA_AUDIO_CHANNEL_TRL, SPA_AUDIO_CHANNEL_TRR };
    memcpy(p->format.position, positions, p->core.channels * sizeof(uint32_t));
    unsigned char storage[1024];
    struct spa_pod_builder builder = SPA_POD_BUILDER_INIT(storage, sizeof(storage));
    const struct spa_pod *params[] = { spa_format_audio_raw_build(&builder, SPA_PARAM_EnumFormat, &p->format) };
    if (pw_stream_connect(p->stream, PW_DIRECTION_OUTPUT, PW_ID_ANY,
            PW_STREAM_FLAG_AUTOCONNECT | PW_STREAM_FLAG_MAP_BUFFERS | PW_STREAM_FLAG_RT_PROCESS |
            PW_STREAM_FLAG_DONT_RECONNECT, params, 1) < 0) goto done;
    if (pthread_create(&p->reader, NULL, read_input, p)) goto done;
    p->reader_started = true;
    pw_main_loop_run(p->main_loop);
done:
    atomic_store(&p->stop, true);
    if (p->wake >= 0) {
        uint64_t n = 1;
        if (write(p->wake, &n, sizeof(n)) < 0 && errno != EAGAIN) rog_fail(&p->core, ROG_IO);
    }
    if (p->reader_started) pthread_join(p->reader, NULL);
    /* Destroy the stream before reading callback-owned counters or freeing it. */
    if (p->stream) pw_stream_destroy(p->stream);
    final_status(p);
    if (p->event) pw_loop_destroy_source(p->loop, p->event);
    if (p->control_source) pw_loop_destroy_source(p->loop, p->control_source);
    if (p->main_loop) pw_main_loop_destroy(p->main_loop);
    if (p->wake >= 0) close(p->wake);
    close(p->control);
    bool success = p->drained && atomic_load(&p->core.error) == ROG_OK;
    free(p); pw_deinit();
    return success ? 0 : 2;
}
