/* Synthetic inactive stream: no sound input or output. */
#include <pipewire/pipewire.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

static struct pw_main_loop *loop;
static struct pw_stream *stream;
static int result = 1;
static const char *expected;
static void state_changed(void *data, enum pw_stream_state old,
                          enum pw_stream_state state, const char *error)
{
    (void)data; (void)old; (void)error;
    if (state == PW_STREAM_STATE_PAUSED) {
        const struct pw_properties *props = pw_stream_get_properties(stream);
        const char *latency = pw_properties_get(props, PW_KEY_NODE_LATENCY);
        result = expected ? !(latency && !strcmp(latency, expected)) : latency != NULL;
        printf("rule_assertion=%s\n", result ? "FAIL" : "PASS");
        pw_main_loop_quit(loop);
    } else if (state == PW_STREAM_STATE_ERROR) {
        pw_main_loop_quit(loop);
    }
}
static const struct pw_stream_events events = {
    PW_VERSION_STREAM_EVENTS, .state_changed = state_changed
};
int main(int argc, char **argv)
{
    if (argc != 4) return 2;
    expected = strcmp(argv[3], "absent") ? argv[3] : NULL;
    pw_init(&argc, &argv);
    loop = pw_main_loop_new(NULL);
    if (!loop) return 3;
    stream = pw_stream_new_simple(pw_main_loop_get_loop(loop), "synthetic-latency-test",
        pw_properties_new(PW_KEY_MEDIA_TYPE, "Audio", PW_KEY_MEDIA_CATEGORY, "Playback",
                          PW_KEY_MEDIA_CLASS, "Stream/Output/Audio",
                          PW_KEY_APP_PROCESS_BINARY, argv[1], PW_KEY_TARGET_OBJECT, argv[2], NULL),
        &events, NULL);
    if (!loop || !stream) return 3;
    if (pw_stream_connect(stream, PW_DIRECTION_OUTPUT, PW_ID_ANY,
                          PW_STREAM_FLAG_INACTIVE, NULL, 0) < 0) return 4;
    pw_main_loop_run(loop);
    pw_stream_destroy(stream);
    pw_main_loop_destroy(loop);
    pw_deinit();
    return result;
}
