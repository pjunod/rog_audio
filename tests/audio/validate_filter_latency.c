/* SPDX-License-Identifier: MIT
 * Inactive synthetic filter: properties only, no ports/audio/process callback.
 */
#define _GNU_SOURCE
#include <pipewire/pipewire.h>
#include <pipewire/filter.h>
#include <stdio.h>
#include <string.h>

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    const char *app = "org.rog_audio.SpeakerEffects";
    const char *node = "rog_audio_soe_output_level";
    const char *group = "rog_audio_speaker_sink_group";
    const char *role = "DSP";
    if (strcmp(argv[1], "other-app") == 0) app = "com.github.wwmm.easyeffects";
    else if (strcmp(argv[1], "other-node") == 0) node = "rog_audio_soe_limiter";
    else if (strcmp(argv[1], "other-group") == 0) group = "rog_audio_speaker_source_group";
    else if (strcmp(argv[1], "other-role") == 0) role = "Music";
    else if (strcmp(argv[1], "match") != 0) return 2;
    pw_init(&argc, &argv);
    struct pw_main_loop *loop = pw_main_loop_new(NULL);
    if (!loop) return 3;
    struct pw_context *context = pw_context_new(pw_main_loop_get_loop(loop), NULL, 0);
    if (!context) return 3;
    struct pw_core *core = pw_context_connect(context, NULL, 0);
    if (!core) return 3;
    struct pw_properties *props = pw_properties_new(
        PW_KEY_APP_ID, app, PW_KEY_NODE_NAME, node, PW_KEY_NODE_GROUP, group,
        PW_KEY_MEDIA_ROLE, role, NULL);
    struct pw_filter *filter = pw_filter_new(core, "synthetic-inactive-filter", props);
    if (!filter) return 3;
    if (pw_filter_connect(filter, PW_FILTER_FLAG_INACTIVE|PW_FILTER_FLAG_RT_PROCESS, NULL, 0) < 0)
        return 3;
    const struct pw_properties *observed = pw_filter_get_properties(filter, NULL);
    const char *latency = pw_properties_get(observed, PW_KEY_NODE_LATENCY);
    const char *quantum = pw_properties_get(observed, PW_KEY_NODE_FORCE_QUANTUM);
    const char *rate = pw_properties_get(observed, PW_KEY_NODE_FORCE_RATE);
    printf("latency=%s\nforce_quantum=%s\nforce_rate=%s\n",
           latency ? latency : "absent", quantum ? quantum : "absent", rate ? rate : "absent");
    pw_filter_destroy(filter);
    pw_core_disconnect(core);
    pw_context_destroy(context);
    pw_main_loop_destroy(loop);
    pw_deinit();
    return 0;
}
