/* SPDX-License-Identifier: MIT
 * Copyright (c) 2026 rog_audio contributors
 * Harness-only observer. RT stream/event pattern follows audio-src-ring.c,
 * Copyright (c) 2024 Wim Taymans, MIT (notice retained).
 */
#define _GNU_SOURCE
#include "capture_core.h"
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
#include <sys/stat.h>
#include <unistd.h>
#include <spa/param/audio/format-utils.h>
#include <spa/buffer/meta.h>
#include <spa/param/buffers.h>
#include <pipewire/pipewire.h>
_Static_assert(SPA_META_HEADER_FLAG_DISCONT == 1 && SPA_META_HEADER_FLAG_CORRUPTED == 2, "capture header flag ABI");
struct capture {
    struct cap_core core;
    struct pw_main_loop *main_loop;
    struct pw_loop *loop;
    struct pw_stream *stream;
    struct spa_source *event, *control_source;
    struct spa_audio_info_raw format;
    int control, output, wake;
    pthread_t writer;
    atomic_bool armed, writer_stop;
    atomic_uint received, ignored;
    bool writer_started, stopping, connected, armed_once, metadata_requested;
    unsigned char callback_scratch[CAP_RING_FRAMES * 48];
};
static void cap_notify(struct capture *p) { pw_loop_signal_event(p->loop, p->event); }
static void capture_fail(struct capture *p, enum cap_error error) { cap_fail(&p->core, error); cap_notify(p); }
static void *write_output(void *opaque)
{
    struct capture *p = opaque;
    unsigned char scratch[4096];
    sigset_t mask; sigemptyset(&mask); sigaddset(&mask, SIGINT); sigaddset(&mask, SIGTERM); sigaddset(&mask, SIGHUP);
    pthread_sigmask(SIG_BLOCK, &mask, NULL);
    for (;;) {
        uint32_t frames = cap_take(&p->core, scratch, sizeof(scratch) / p->core.stride);
        if (frames) {
            if (!cap_write_bytes(&p->core, p->output, scratch, frames * p->core.stride)) { cap_notify(p); break; }
            continue;
        }
        if (atomic_load(&p->writer_stop)) break;
        struct pollfd fd = { .fd = p->wake, .events = POLLIN };
        int n = poll(&fd, 1, 20);
        if (n < 0 && errno != EINTR) { capture_fail(p, CAP_WRITE); break; }
        if (fd.revents & POLLIN) { uint64_t value; while (read(p->wake, &value, sizeof(value)) > 0) {} }
    }
    return NULL;
}
static void capture_event(void *opaque, uint64_t count)
{
    struct capture *p = opaque;
    (void)count;
    uint64_t value = 1;
    if (write(p->wake, &value, sizeof(value)) < 0 && errno != EAGAIN) cap_fail(&p->core, CAP_WRITE);
    if (atomic_load(&p->core.error)) pw_main_loop_quit(p->main_loop);
}
static void capture_process(void *opaque)
{
    struct capture *p = opaque;
    struct pw_buffer *b = pw_stream_dequeue_buffer(p->stream);
    if (!b) return;
    struct spa_buffer *buffer = b->buffer;
    if (buffer->n_datas != 1 || !buffer->datas[0].chunk) {
        cap_fail(&p->core, CAP_CHUNK);
    } else {
        struct spa_data *data = &buffer->datas[0];
        struct spa_chunk *chunk = data->chunk;
        uint32_t stride = p->core.stride;
        if (chunk->flags & SPA_CHUNK_FLAG_CORRUPTED) {
            cap_fail(&p->core, CAP_CORRUPTED);
        } else if (chunk->size > data->maxsize || chunk->size > CAP_RING_FRAMES * stride ||
                chunk->size % stride || (chunk->stride && chunk->stride != (int32_t)stride) ||
                (chunk->size && (!data->maxsize || (!data->data && !(chunk->flags & SPA_CHUNK_FLAG_EMPTY))))) {
            cap_fail(&p->core, CAP_CHUNK);
        } else if (chunk->size) {
            uint32_t frames = chunk->size / stride;
            if (!atomic_load_explicit(&p->armed, memory_order_acquire)) atomic_fetch_add(&p->ignored, frames);
            else {
                atomic_fetch_add(&p->received, frames);
                struct cap_stamp stamp = {0};
                struct pw_time time = {0};
                stamp.clock_info.available = pw_stream_get_time_n(p->stream, &time, sizeof(time)) == 0;
                stamp.clock_valid = stamp.clock_info.available &&
                    time.rate.num == 1 && time.rate.denom == 48000 && time.size == frames;
                stamp.ticks = time.ticks;
                stamp.clock_info.buffer_time = b->time; stamp.clock_info.now = time.now;
                stamp.clock_info.rate_num = time.rate.num; stamp.clock_info.rate_denom = time.rate.denom;
                stamp.clock_info.size = time.size;
                struct spa_meta_header *header = spa_buffer_find_meta_data(buffer, SPA_META_Header, sizeof(*header));
                if (header) {
                    stamp.header_present = true; stamp.sequence = header->seq;
                    stamp.header_flags = header->flags; stamp.pts = header->pts;
                    stamp.pts_valid = header->pts != SPA_TIME_INVALID;
                }
                /* SPA offsets are modulo maxsize; wrapped bytes and neutral
                 * chunks use fixed scratch without touching upstream memory. */
                uint32_t offset = chunk->offset % data->maxsize;
                const unsigned char *source;
                if (chunk->flags & SPA_CHUNK_FLAG_EMPTY) {
                    memset(p->callback_scratch, 0, chunk->size); source = p->callback_scratch;
                } else if (chunk->size > data->maxsize - offset) {
                    uint32_t first = data->maxsize - offset;
                    memcpy(p->callback_scratch, (unsigned char *)data->data + offset, first);
                    memcpy(p->callback_scratch + first, data->data, chunk->size - first);
                    source = p->callback_scratch;
                } else source = (unsigned char *)data->data + offset;
                cap_push(&p->core, source, frames, &stamp);
            }
        }
    }
    if (pw_stream_queue_buffer(p->stream, b) < 0) cap_fail(&p->core, CAP_PIPEWIRE);
    cap_notify(p);
}
static void capture_format(void *opaque, uint32_t id, const struct spa_pod *param)
{
    struct capture *p = opaque;
    struct spa_audio_info_raw actual = {0};
    if (id != SPA_PARAM_Format || !param) return;
    if (spa_format_audio_raw_parse(param, &actual) < 0 || actual.format != SPA_AUDIO_FORMAT_F32_LE ||
            actual.rate != 48000 || actual.channels != p->format.channels ||
            memcmp(actual.position, p->format.position, actual.channels * sizeof(uint32_t))) {
        capture_fail(p, CAP_PIPEWIRE); return;
    }
    unsigned char storage[256];
    struct spa_pod_builder builder = SPA_POD_BUILDER_INIT(storage, sizeof(storage));
    const struct spa_pod *meta = spa_pod_builder_add_object(&builder, SPA_TYPE_OBJECT_ParamMeta, SPA_PARAM_Meta,
        SPA_PARAM_META_type, SPA_POD_Id(SPA_META_Header), SPA_PARAM_META_size, SPA_POD_Int(sizeof(struct spa_meta_header)));
    /* Optional metadata request. Missing support is visible, never a gate. */
    p->metadata_requested = pw_stream_update_params(p->stream, &meta, 1) >= 0;
}
static void capture_state(void *opaque, enum pw_stream_state old, enum pw_stream_state state, const char *error)
{
    struct capture *p = opaque;
    (void)old; (void)error;
    if (state == PW_STREAM_STATE_PAUSED || state == PW_STREAM_STATE_STREAMING) p->connected = true;
    if (state == PW_STREAM_STATE_ERROR || (state == PW_STREAM_STATE_UNCONNECTED && p->connected && !p->stopping))
        capture_fail(p, CAP_PIPEWIRE);
}
static void capture_signal(void *opaque, int number)
{
    struct capture *p = opaque;
    (void)number; cap_fail(&p->core, CAP_CANCELLED); pw_main_loop_quit(p->main_loop);
}
static void capture_control(void *opaque, int fd, uint32_t mask)
{
    struct capture *p = opaque;
    char command[32];
    struct iovec io = { .iov_base = command, .iov_len = sizeof(command) };
    struct msghdr message = { .msg_iov = &io, .msg_iovlen = 1 };
    if (!(mask & SPA_IO_IN)) { capture_fail(p, CAP_CONTROL); return; }
    ssize_t n = recvmsg(fd, &message, MSG_DONTWAIT);
    if (n < 0 && (errno == EAGAIN || errno == EINTR)) return;
    const char *reply = NULL;
    if (!(message.msg_flags & (MSG_TRUNC | MSG_CTRUNC))) {
        if (n == 6 && !memcmp(command, "ARM 1\n", 6) && !p->armed_once && !p->stopping) {
            p->armed_once = true;
            atomic_store_explicit(&p->armed, true, memory_order_release); reply = "ACK 1\n";
        } else if (n == 7 && !memcmp(command, "STOP 2\n", 7) && p->armed_once && !p->stopping) {
            p->stopping = true;
            atomic_store_explicit(&p->armed, false, memory_order_release); reply = "ACK 2\n";
        }
    }
    if (!reply || send(fd, reply, 6, MSG_DONTWAIT | MSG_NOSIGNAL) != 6) { capture_fail(p, CAP_CONTROL); return; }
    if (p->stopping) pw_main_loop_quit(p->main_loop);
}
static const struct pw_stream_events capture_events = {
    PW_VERSION_STREAM_EVENTS, .state_changed = capture_state,
    .param_changed = capture_format, .process = capture_process
};
static void capture_final(struct capture *p)
{
    uint32_t accepted = atomic_load(&p->core.captured), written = atomic_load(&p->core.bytes_written);
    bool complete = p->stopping && !atomic_load(&p->core.error) &&
        accepted == atomic_load(&p->core.taken) && written == accepted * p->core.stride;
    if (!complete && !atomic_load(&p->core.error)) cap_fail(&p->core, CAP_WRITE);
    char packet[2048], first_ticks[32], last_ticks[32], first_seq[32], last_seq[32], first_pts[32], last_pts[32];
    snprintf(first_ticks, sizeof(first_ticks), "%llu", (unsigned long long)p->core.first_ticks);
    snprintf(last_ticks, sizeof(last_ticks), "%llu", (unsigned long long)p->core.last_ticks);
    snprintf(first_seq, sizeof(first_seq), "%llu", (unsigned long long)p->core.first_sequence);
    snprintf(last_seq, sizeof(last_seq), "%llu", (unsigned long long)p->core.last_sequence);
    snprintf(first_pts, sizeof(first_pts), "%lld", (long long)p->core.first_pts);
    snprintf(last_pts, sizeof(last_pts), "%lld", (long long)p->core.last_pts);
    char gap[768] = "null";
    if (p->core.first_clock_gap) {
        const struct cap_clock_info *before = &p->core.gap_previous_info, *after = &p->core.gap_current_info;
        int size = snprintf(gap, sizeof(gap),
            "{\"expected_ticks\":%llu,\"actual_ticks\":%llu,"
            "\"previous\":{\"time_available\":%s,\"buffer_queued_ns\":%llu,\"snapshot_now_ns\":%lld,"
            "\"rate_num\":%u,\"rate_denom\":%u,\"cycle_frames\":%llu,\"chunk_frames\":%u},"
            "\"current\":{\"time_available\":%s,\"buffer_queued_ns\":%llu,\"snapshot_now_ns\":%lld,"
            "\"rate_num\":%u,\"rate_denom\":%u,\"cycle_frames\":%llu,\"chunk_frames\":%u}}",
            (unsigned long long)p->core.gap_expected_ticks, (unsigned long long)p->core.gap_actual_ticks,
            before->available ? "true" : "false", (unsigned long long)before->buffer_time, (long long)before->now,
            before->rate_num, before->rate_denom, (unsigned long long)before->size, p->core.gap_previous_frames,
            after->available ? "true" : "false", (unsigned long long)after->buffer_time, (long long)after->now,
            after->rate_num, after->rate_denom, (unsigned long long)after->size, p->core.gap_current_frames);
        if (size < 0 || (size_t)size >= sizeof(gap)) return;
    }
    int n = snprintf(packet, sizeof(packet),
        "FINAL {\"protocol\":\"%s\",\"status\":\"%s\",\"complete\":%s,"
        "\"callback_received_frames\":%u,\"ring_accepted_frames\":%u,\"writer_taken_frames\":%u,"
        "\"written_bytes\":%u,\"written_complete_frames\":%u,\"ring_capacity_frames\":%u,"
        "\"maximum_ring_frames\":%u,\"rejected_frames\":%u,\"ignored_before_arm_frames\":%u,"
        "\"overflow_events\":%u,\"writer_io_errors\":%u,"
        "\"metadata_request_accepted\":%s,\"clock_observations\":%u,\"unavailable_clock_observations\":%u,\"clock_gap_events\":%u,"
        "\"header_observations\":%u,\"unavailable_pts_observations\":%u,"
        "\"sequence_regressions\":%u,\"pts_regressions\":%u,\"header_discontinuities\":%u,"
        "\"largest_sequence_step\":%llu,\"first_ticks\":%s,\"last_ticks\":%s,"
        "\"first_sequence\":%s,\"last_sequence\":%s,\"first_pts\":%s,\"last_pts\":%s,\"first_clock_gap\":%s}\n",
        CAP_PROTOCOL, cap_error_name(atomic_load(&p->core.error)), complete ? "true" : "false",
        atomic_load(&p->received), accepted, atomic_load(&p->core.taken), written, written / p->core.stride,
        CAP_RING_FRAMES, atomic_load(&p->core.maximum_ring), atomic_load(&p->core.rejected_frames), atomic_load(&p->ignored),
        atomic_load(&p->core.overflow_events), atomic_load(&p->core.writer_io_errors),
        p->metadata_requested ? "true" : "false", atomic_load(&p->core.clock_observations), atomic_load(&p->core.unavailable_clock), atomic_load(&p->core.clock_gaps),
        atomic_load(&p->core.header_observations), atomic_load(&p->core.unavailable_pts),
        atomic_load(&p->core.sequence_regressions), atomic_load(&p->core.pts_regressions), atomic_load(&p->core.header_discontinuities),
        (unsigned long long)p->core.largest_sequence_step,
        p->core.seen_clock ? first_ticks : "null", p->core.seen_clock ? last_ticks : "null",
        p->core.have_header ? first_seq : "null", p->core.have_header ? last_seq : "null",
        p->core.have_pts ? first_pts : "null", p->core.have_pts ? last_pts : "null", gap);
    if (n > 0 && (size_t)n < sizeof(packet)) (void)send(p->control, packet, n, MSG_DONTWAIT | MSG_NOSIGNAL);
}
static void capture_shutdown(struct capture *p)
{
    atomic_store_explicit(&p->armed, false, memory_order_release);
    /* Stream destruction waits for a callback that already observed ARM.
     * No writer-stop/drain decision can precede that final producer. */
    if (p->stream) { pw_stream_destroy(p->stream); p->stream = NULL; }
    atomic_store(&p->writer_stop, true);
    if (p->wake >= 0) {
        uint64_t value = 1;
        if (write(p->wake, &value, sizeof(value)) < 0 && errno != EAGAIN) cap_fail(&p->core, CAP_WRITE);
    }
    if (p->writer_started) { pthread_join(p->writer, NULL); p->writer_started = false; }
}
static int descriptor(const char *s)
{
    if (!*s || strlen(s) > 3) return -1;
    for (const char *p = s; *p; p++) if (*p < '0' || *p > '9') return -1;
    int fd = atoi(s); return fd > 2 && fd < 128 ? fd : -1;
}
int main(int argc, char **argv)
{
    if (argc == 2 && !strcmp(argv[1], "--describe")) {
        printf("{\"protocol\":\"%s\",\"ring_frames\":%u,\"maximum_file_bytes\":%u,\"rate\":48000,\"channels\":[2,12]}\n", CAP_PROTOCOL, CAP_RING_FRAMES, CAP_MAX_BYTES);
        return 0;
    }
    if (argc != 7 || strcmp(argv[1], "--channels") || (strcmp(argv[2], "2") && strcmp(argv[2], "12")) ||
            strcmp(argv[3], "--output-fd") || strcmp(argv[5], "--control-fd")) return 2;
    int output = descriptor(argv[4]), control = descriptor(argv[6]), type;
    struct stat file; socklen_t length = sizeof(type);
    if (output < 0 || control < 0 || output == control || fstat(output, &file) < 0 || !S_ISREG(file.st_mode) ||
            file.st_size || file.st_nlink != 1 || file.st_uid != geteuid() || (file.st_mode & 0777) != 0600 ||
            (fcntl(output, F_GETFL) & (O_ACCMODE | O_APPEND)) != O_WRONLY ||
            getsockopt(control, SOL_SOCKET, SO_TYPE, &type, &length) < 0 || type != SOCK_SEQPACKET) return 2;
    struct capture *p = aligned_alloc(_Alignof(struct capture), sizeof(struct capture));
    if (!p) return 2;
    memset(p, 0, sizeof(*p));
    if (!cap_init(&p->core, atoi(argv[2]))) { free(p); return 2; }
    p->control = control; p->output = output; p->wake = -1;
    atomic_init(&p->armed, false); atomic_init(&p->writer_stop, false);
    atomic_init(&p->received, 0); atomic_init(&p->ignored, 0);
    pw_init(NULL, NULL);
    p->main_loop = pw_main_loop_new(NULL); if (!p->main_loop) goto done;
    p->loop = pw_main_loop_get_loop(p->main_loop);
    p->wake = eventfd(0, EFD_CLOEXEC | EFD_NONBLOCK); if (p->wake < 0) goto done;
    p->event = pw_loop_add_event(p->loop, capture_event, p);
    p->control_source = pw_loop_add_io(p->loop, control, SPA_IO_IN | SPA_IO_HUP | SPA_IO_ERR, false, capture_control, p);
    if (!p->event || !p->control_source) goto done;
    pw_loop_add_signal(p->loop, SIGINT, capture_signal, p); pw_loop_add_signal(p->loop, SIGTERM, capture_signal, p);
    pw_loop_add_signal(p->loop, SIGHUP, capture_signal, p);
    struct pw_properties *props = pw_properties_new(PW_KEY_NODE_NAME, "integration-capture",
        PW_KEY_MEDIA_TYPE, "Audio", PW_KEY_MEDIA_CATEGORY, "Capture", PW_KEY_MEDIA_ROLE, "Test",
        "node.autoconnect", "false", "node.dont-fallback", "true", "node.dont-reconnect", "true",
        "node.dont-move", "true", "stream.dont-remix", "true", "channelmix.disable", "true",
        "stream.capture.sink", "true", NULL);
    if (!props) goto done;
    p->stream = pw_stream_new_simple(p->loop, "ROG isolated capture observer", props, &capture_events, p);
    if (!p->stream) goto done;
    p->format.format = SPA_AUDIO_FORMAT_F32_LE; p->format.rate = 48000; p->format.channels = atoi(argv[2]);
    const uint32_t positions[] = { SPA_AUDIO_CHANNEL_FL, SPA_AUDIO_CHANNEL_FR, SPA_AUDIO_CHANNEL_FC,
        SPA_AUDIO_CHANNEL_LFE, SPA_AUDIO_CHANNEL_RL, SPA_AUDIO_CHANNEL_RR, SPA_AUDIO_CHANNEL_SL,
        SPA_AUDIO_CHANNEL_SR, SPA_AUDIO_CHANNEL_TFL, SPA_AUDIO_CHANNEL_TFR, SPA_AUDIO_CHANNEL_TRL, SPA_AUDIO_CHANNEL_TRR };
    memcpy(p->format.position, positions, p->format.channels * sizeof(uint32_t));
    unsigned char storage[1024]; struct spa_pod_builder builder = SPA_POD_BUILDER_INIT(storage, sizeof(storage));
    const struct spa_pod *format = spa_format_audio_raw_build(&builder, SPA_PARAM_EnumFormat, &p->format);
    if (pw_stream_connect(p->stream, PW_DIRECTION_INPUT, PW_ID_ANY,
            PW_STREAM_FLAG_MAP_BUFFERS | PW_STREAM_FLAG_RT_PROCESS | PW_STREAM_FLAG_DONT_RECONNECT, &format, 1) < 0) goto done;
    if (pthread_create(&p->writer, NULL, write_output, p)) goto done;
    p->writer_started = true;
    pw_main_loop_run(p->main_loop);
done:
    capture_shutdown(p);
    capture_final(p);
    if (p->event) pw_loop_destroy_source(p->loop, p->event);
    if (p->control_source) pw_loop_destroy_source(p->loop, p->control_source);
    if (p->main_loop) pw_main_loop_destroy(p->main_loop);
    if (p->wake >= 0) close(p->wake);
    close(output); close(control);
    bool success = p->stopping && !atomic_load(&p->core.error);
    free(p); pw_deinit(); return success ? 0 : 2;
}
