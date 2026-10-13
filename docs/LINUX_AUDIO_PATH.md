# Linux audio path — inspect tuned playback and trial one latency request

**Updated:** 2026-10-13 · **State:** reviewed; 30 Linux path/trial unit cases
and native filter/config acceptance passed for PR 5; native environment and
quit-save compatibility fixes passed review and 29 affected methods in PR 6.
Retaining unchanged preset-use list entries passed independent review and
eight affected/new methods in PR 7. Larger 1024/2048-frame request support
cleared independent review and four unique focused methods; only three
macOS platform errors were retried on Linux, where they passed. No larger-period live pass is claimed.

Companion to [latency comparison](LATENCY_COMPARISON.md) (the experiment and
Mac reference), [installation](SPEAKER_INSTALL.md) (the existing runtime), and
[latency tooling](AUDIO_LATENCY_BUILD.md) (the earlier physical-trial analyser
and native playback-client rules). This topic owns the installed processor's
filter path. A playback client's `stream.rules` does not configure `pw_filter`.

## Inspect the active path without starting playback

The [collector](../scripts/inspect_audio_path.py) reuses the bounded inventory
runner and adds before/after speaker fingerprints, candidate/restart environment
inspection, `pw-top` samples and PulseAudio client queue reports. It performs
no playback, microphone capture, service restart or configuration activation.
A separate authorized player must already be running to observe active timing.

```bash
export ROG_AUDIO_STATE_DIR="$HOME/.local/state/rog-audio/easyeffects"
python3 scripts/inspect_audio_path.py \
  --kit PRIVATE_KIT --runtime /opt/rog-audio/easyeffects/bin/easyeffects \
  --samples 6 --output PRIVATE_CAPTURE.json
python3 scripts/inspect_audio_path.py \
  --from-capture PRIVATE_CAPTURE.json --public-summary PRIVATE_SUMMARY.json
```

`--runtime` names the raw installed ELF whose hash is in the kit; the
`/usr/bin/rog-speaker-effects` launcher is a wrapper and is not that artifact.
Use the owning user's existing session bus and runtime directory. Do not invent
a UID, node number or device target. The exact kit binds the model, codec,
subsystem, physical sink and speaker route. Outputs must be new private files;
existing files are preserved. Samples are bounded to 2–30. Full collection also
performs inventories before/after the monitor, so a ten-second player is not
necessarily long enough to cover it. Record actual playback and capture duration.

The private `audio-path-capture` schema version 1 retains raw inventory,
monitor/Pulse output, before/after managed file bytes and hashes, exact route,
configuration preimage and environment evidence. Keep it out of Git. The public
`audio-path-summary` is reconstructed from numeric/enumerated fields and hashes;
it omits arbitrary client names, IDs, addresses, home paths and raw logs.
Synthetic fixtures are explicitly labeled synthetic.
New captures also retain the UTF-8 main settings file (`db/easyeffectsrc`),
bound to its raw hash. Plugin settings remain exact hash records. These private
preimages support the narrowly scoped controlled-quit comparison below; public
summaries include neither settings text nor arbitrary environment values.

**How to read it:** running driver quantum/rate gives the observed graph period.
Follower values are requests, even when they appear beside the driver in
`pw-top`. Suspended or incomplete observations do not prove a running period.
Before/after graph cookies and object serials help reject graph restarts and
reused IDs. Reported DSP ProcessLatency and Pulse queue values retain their
units; they are not added into an acoustic or end-to-end number. Both physical
and end-to-end latency fields remain null. Missing probes are unknown.

Error deltas require a continuous observed active interval and nondecreasing
counters. Otherwise they are marked incomplete/reset; zero late in playback
cannot erase an activation error or qualify a long stress run. Preserve raw
first observations and node lifecycle evidence alongside the summary.

## Prepare an inactive filter request

[The trial tool](../scripts/audio_path_trial.py) writes a new private bundle:

```bash
python3 scripts/audio_path_trial.py prepare \
  --capture PRIVATE_CAPTURE.json --quantum 256 --output PRIVATE_TRIAL
```

The default request remains 256/48000, or 5.333 ms per cycle if negotiated.
The supported 48 kHz requests are 128, 256, 512, 1024 and 2048 frames. One
shared integer set drives rule construction and CLI choices; bundle and
snapshot validation reconstruct that same rule. The default remains 256.
The additive 1024/2048 support passed final review and focused acceptance.
Use the accepted post-v0.2.2 tool source after PR 11 merges; the unchanged
v0.2.2 tag still has only 128/256/512 requests. Existing file/settings/environment/conflict guards are
unchanged; these remain private requests, never forced global graph periods.

| Requested frames | Nominal period at 48 kHz | Evidence boundary |
|---|---|---|
| 128 | 2.667 ms | Existing preparer capability, not a laptop stability pass |
| 256 | 5.333 ms | Historical paired observations; ROG later failed, ThinkPad old-runtime hour passed |
| 512 | 10.667 ms | ROG short +rog2 check passed, but a later six-second baseline grew driver ERR 3→4→4 |
| 1024 | 21.333 ms | Source review/tests passed; shared 1024 observed on +rog2, explicit guarded trial pending |
| 2048 | 42.667 ms | Recoverable prior default; explicit request support is new, not a new hour result |

The latest 512 failure preceded any +rog3 package or gain-preset change. Keep
it separate from the earlier 20.065-second short pass and the 256 failure.
Removing the private 512 request restored the original tuning, but the shared
graph negotiated 1024 with a browser requesting it; historical 2048 was not
reproduced. This does not qualify an explicit 1024 request. Try that guarded
request after this accepted follow-up merges; use recoverable 2048 if needed. Preserve
every failed interval. Observe the running driver quantum/rate; neither the
request nor its nominal period establishes physical delay or Mac parity.

```bash
python3 scripts/audio_path_trial.py prepare \
  --capture PRIVATE_FRESH_BASELINE.json --quantum 1024 --output PRIVATE_NEW_TRIAL
```

This creates an inactive bundle only. Remove any prior owned fragment using
its retained snapshot before collecting the fresh baseline; preparation and
installation still reject an occupied trial filename. Do not overwrite the
existing fragment in place or reuse its snapshot to remove another request.
Use a new bundle and snapshot for each candidate. The preset, IR, settings,
physical route and startup unit retain the same preservation contract.

The fragment uses `filter.rules` and matches all four exact properties:

| Property | Required value |
|---|---|
| `application.id` | `org.rog_audio.SpeakerEffects` |
| `node.name` | `rog_audio_soe_output_level` |
| `node.group` | `rog_audio_speaker_sink_group` |
| `media.role` | `DSP` |

Its only update is `node.latency`. The destination is the processor's private
`config/pipewire/client.conf.d/90-rog-audio-latency-trial.conf` beneath
`ROG_AUDIO_STATE_DIR`. The delivered runtime selects this configuration root.
The PipeWire 1.6.8 implementation applies filter rules during `pw_filter_connect`;
`PIPEWIRE_LATENCY` can supersede the request, while `PIPEWIRE_QUANTUM` introduces
forced timing. The tool checks candidate, current, user-manager and service
environments and reports unknown/overridden configuration as a conflict.
The environment reader uses `systemctl --user show --all` for `Environment`
and a read-only `busctl --user get-property` for the owned service's
`EnvironmentFiles`. It accepts only a successful typed `a(sb) 0` response as
proof of no environment files. Missing output, a nonempty array, a different
type or an unavailable probe remains a conflict. The
[systemd 261 formatter](https://github.com/systemd/systemd/blob/v261/src/systemctl/systemctl-show.c)
prints each array entry and omits an empty array even with `--all`; its
[D-Bus declaration](https://github.com/systemd/systemd/blob/v261/src/core/dbus-execute.c)
retains the typed property. The owning user's session bus and `busctl` must be
available; an unknown property or service remains unavailable, with no alias
fallback.

Preparation requires the inspected PipeWire 1.6.8/WirePlumber 0.5.17 versions,
48 kHz graph configuration, unforced timing, consistent route and speaker
fingerprints, and an absent owned trial filename. These checks protect an
exact configuration experiment; they do not establish acoustic qualification.
The preset, IR, limiter, amplifier controls and existing audio policy are not
modified. A rule on this processor still influences negotiation in its shared
graph, so retain the other active client requests during the comparison.

## Install files and explicitly restart only the processor

The command performs file operations only. In the coordinated window, use the
existing service owner to stop the candidate with controlled quit first.
PipeWire and WirePlumber remain running. Preserve current profile, default,
volume, exact runtime/preset/IR hashes and the startup unit before proceeding.

```bash
python3 scripts/audio_path_trial.py install \
  --bundle PRIVATE_TRIAL --kit PRIVATE_KIT \
  --runtime /opt/rog-audio/easyeffects/bin/easyeffects --snapshot PRIVATE_NEW_SNAPSHOT
python3 scripts/audio_path_trial.py status --snapshot PRIVATE_NEW_SNAPSHOT
```

Installation rechecks the stopped candidate, fresh route, versions, graph
forcing, restart environment and unchanged preimage. It stores a durable
snapshot before publishing the complete fragment through an exclusive link.
After snapshotting it queries manager/unit environment and fresh candidate
idle/route/timing state again immediately before publication. A restart or
override introduced during snapshotting rejects the addition.
The journal records incomplete installation if publication or persistence
fails. No command starts playback or a service. Restart only the candidate
through its established user service, then verify its exact tuning and links.

A controlled quit can save the preset-use bookkeeping counter. Native evidence
from 2026-10-13 showed only `[StreamOutputs] usedPresets` changing from the
installed preset's count 1 to 2. Installation therefore permits only an
increasing count for one exact `rog-speaker-<16 hex digits>` kit preset entry
in that key. A second ROG receipt showed that increment beside a retained
`<kit-preset>-bypass:1` entry. A comma-separated list is allowed only when all
other entries retain their exact name, count, bytes and position. Every other
main-settings byte, section/key, permission, plugin
settings record, payload, runtime, route and PipeWire preimage must match.
Names use 1–128 ASCII letters, digits, dots, underscores or hyphens. Each
entry has one canonical integer count from 0 to 2147483647; at most 128 unique
entries are accepted. Exactly one entry names the selected kit preset.
Different names, decreasing/malformed counts, duplicate names, reordered or
added/removed entries, added keys,
`mostUsedPresets` changes and all other differences are conflicts. Earlier
captures without hash-bound raw main-settings text require an exact match.
The baseline capture retains the original raw text and the installation
snapshot retains the stopped raw text and hashes. The tool rewrites no settings.
After snapshotting the stopped state must still match exactly; this exception
does not excuse concurrent changes or a counter change during capture.

For the deployed laptops, transition from the original transient listener to
the already-enabled `rog-audio-speaker.service` before collecting the fresh
baseline. Record that transition explicitly. Baseline and candidate then use
the same service/arguments/environment, differing only by the owned fragment.
Automatic login startup and rollback use that same persistent service.

Use identical zero-PCM client requests and capture duration before/after.
Confirm the actual running driver period, active full DSP path, error counters,
unchanged physical default/volume and unchanged stock audio service PIDs.
A shorter scheduling period with broken tuning is a failed experiment.

## Remove the owned request and retain its evidence

Stop only the candidate with controlled quit. Then archive the current private
configuration and remove the hash-matching owned addition:

```bash
python3 scripts/audio_path_trial.py remove \
  --snapshot PRIVATE_NEW_SNAPSHOT --archive PRIVATE_NEW_ARCHIVE
```

The tool checks snapshot ownership/root, retained backup hashes and the exact
owned rule. It preserves a user-edited fragment as a conflict instead of
silently deleting it. Unrelated configuration and all DSP payloads remain
untouched. Only empty directories introduced by the addition are removed.
Removal requires Linux `renameat2` support and an archive on the configuration's
filesystem. It atomically moves the live inode to
`quarantine/removed-rule.conf` in that archive before verifying inode identity
and content. The inode remains retained even on success, so later writes
through an already-open descriptor are not lost. `removal.json` records the
planned move and its outcome.

If a replaced inode was moved, the tool restores it only when the original
path remains absent. It never overwrites a concurrent replacement. Otherwise
the moved object stays in the archive and exit 2 reports `removal-conflict`
with recovery `restored-original-path` or `retained-in-archive`. The installation
journal remains uncompleted on conflict. A persistence failure after the move
also leaves the inode and planned recovery record available; inspect both
locations before any manual restoration, and preserve a newer destination.
Restart the same persistent candidate service and verify baseline timing and
speaker tuning again. Preserve failed trial receipts; do not reset counters.

## Validate new source without repeating the accepted earlier lane

The isolated [Dockerfile](../tests/audio/latency-path.Dockerfile) pins the Ubuntu
base and matching PipeWire/WirePlumber packages. Build dependencies stay in the
container. No host audio devices, session sockets or user configuration are
mounted. The native probe has no ports, processing callback or audio buffers;
it connects an inactive synthetic filter to a disposable PipeWire daemon and
inspects the resulting properties.

After the complete batch is reviewed, use the manual `audio-path` lane in
[acceptance](../.github/workflows/acceptance.yml), or run the same
[harness](../tests/audio/linux-path-validation.sh) in the retained isolated
build environment. `unit-path` and `unit-trial` cover the new collector and
file lifecycle. Other selectors cover compilation, native config parsing,
the exact four-property match, each single-property mismatch and environment
precedence. A failed unit method can be selected by its full ID. Skips, empty
suites and invalid IDs do not count as acceptance.
PR 6 added positive/missing/nonempty/malformed typed-property
cases and controlled-quit counter acceptance/refusal/preimage cases in these
two unit modules and passed 29 affected methods after source review. The
preset-list follow-up adds selected-counter success with retained bypass,
other-entry/ordering refusal, malformed/duplicate-entry refusal and selected
position cases. These four new cases and four affected prior counter cases
passed once at `aff7fdb`, with zero skips or failures. The
[list-extension receipt](../evidence/audio-path-preset-list-acceptance-2026-10-13.json)
binds the exact accepted source; unrelated passes were retained.

Keep the original 42-test latency receipt and accepted speaker graph receipts
when their inputs remain unchanged. Record each new pass/failure once, retry
only failed or invalidated cases, and retain exact source/image hashes. These
checks prove parser/file/rule behavior; they do not prove negotiated running
latency, audible stability, physical hotplug, power cost or Mac parity.


### 512-frame follow-up — focused file-lifecycle acceptance passed

The expanded rule and CLI allowlists add 512 frames without changing the
256-frame default or the file-only lifecycle. One new synthetic method,
`test_audio_path_trial.TrialTests.test_512_cli_lifecycle_preserves_tuning_and_unrelated_config`,
exercises actual CLI preparation, inactive state, exact 512-frame rule,
install/status/remove, archived rule bytes and full restoration of tuning,
runtime/kit identity and an unrelated config file with its mode. Unsupported
values and types remain refused. No existing test treated 512 as invalid.

The focused method passed once using Linux `renameat2` after independent
adversarial review, within PR 9's 29 affected unit methods and six separate
isolated graph selectors. The [acceptance receipt](../evidence/speaker-autoload-acceptance-2026-10-13.json)
retains exact method and log bindings. Accepted unchanged 128/256 and
native/Mac/speaker evidence remains retained. This synthetic test proves
scoped file behaviour. The later [live status](STATUS.md) records the separate
ROG 512-frame short check; sustained and physical qualification remain open.
