# rog_audio — Linux speaker quality, latency and spatial audio

Linux audio engineering for the ASUS ROG Zephyrus G16 GU605MZ, with reusable
diagnostics and offline tooling, extended to the first-generation ThinkPad X1
Extreme. Built-in speakers and everyday media come
first, measured latency against the M4 Air/M3 Max follows, and Sonos Arc/eARC
Atmos is last.

[The October 13 deployment receipt](evidence/programme-service-autoload-and-current-settings-v2-2026-10-13.json)
and completed hours record both laptops on `8.2.8+rog3` with the reviewed
synchronous-stop helper backported separately. Original IRs, non-AutoGain
voicing, final limiters and stock protection were preserved; both generated
demos and settings-bound software hours passed. Those are exact historical
conditions, not fresh observations of an active audio path.

[The earlier October 15 read-only refresh](evidence/speaker-live-preparation-observation-2026-10-15.json)
finds the ROG service and all twelve protected files unchanged from the
earlier postboot observation. Physical and tuned stereo sink nodes are
present; the idle graph has zero links, so active full routing and fresh IR
loading remain unverified. ThinkPad timed out once and its current state is
unknown. The [latest bounded connectivity check](evidence/speaker-connectivity-refresh-2026-10-15.json)
timed out on both laptops before its read-only script ran, so both current
states are unknown. No service change, playback or recording occurred.
Physical measurement remains deferred.

| System | Last qualified software | Accepted software timing at 48 kHz | Programme settings | October 15 / remaining evidence |
|---|---|---|---|---|
| ROG G16 | +rog3 and PR 12 helper/unit backport | 1024-frame graph cycle: 21.333 ms | −20 LUFS; cap 2.6475 dB | Prior hour/demo and unchanged-file observation retained; latest connection timed out, current state unknown |
| ThinkPad X1 Extreme | +rog3 and PR 12 helper/unit backport | 256-frame graph cycle: 5.333 ms | −16 LUFS; cap 14.1375 dB | Prior hour/demo passed; unreachable in new check, current state unknown |
| M4 Air | Stock output; matched browser/emitter files previously staged | 512-frame HAL buffer: 10.667 ms | Unchanged in prior observation | Route/armed pilot and physical comparison pending |
| Sonos Arc/eARC | Deferred | Unmeasured | Unassessed | Follows internal-speaker acceptance |

These graph/HAL terms do not measure speaker delay or prove Mac parity. The
historical matching Linux before/after numbers describe both drivers selecting
the same integer periods for the same request; their real stability results
differ. See [comparison and retained trials](docs/LATENCY_COMPARISON.md) and
the [phone-recorded method](docs/PHYSICAL_LATENCY_METHOD.md). No physical latency
or calibrated sound-quality result has been collected.

The [bounded Atmos pull API](probes/atmos/README.md) implements caller-owned
PCM reads, sample timestamps, seek/flush and exact EOS. [PR 16 acceptance](evidence/audio-playback-and-annotations-acceptance-2026-10-15.json)
records sixteen affected Atmos methods and eleven signed-annotation methods
passed once after independent review and fixes. A fresh full official JOC
render and four separate continuity groups passed; the original combined seek
sequence hit a process limit and remains a recorded limitation. These are
same-engine checks, not independent Dolby fidelity or realtime qualification.

[Signed manual annotation analysis](docs/MANUAL_LATENCY_ANNOTATIONS.md) preserves
negative click-to-chirp intervals, rejected attempts and declared onset bounds
without recording or inferring physical validity. The [accepted-filter audit](evidence/speaker-chain-algorithmic-delay-audit-2026-10-15.json)
found no justified removable fixed delay; original filters/limiter stay intact.
The [live player prototype](docs/LIVE_ATMOS.md) streams rendered PCM into
an explicit PipeWire sink. Its [software acceptance](evidence/live-atmos-acceptance-2026-10-15.json)
records 63 distinct live methods and a bit-exact full JOC media capture under
the explicit 48-kHz/1024-frame, two-CPU/6-GiB isolated condition. Ordinary
256-frame media receipts remain inherited; full JOC failures at 256 are retained.
This does not qualify ThinkPad 256-frame playback or either laptop's live path.
The [native playback helper contract](docs/LIVE_ATMOS_NATIVE.md) covers its
callback, buffering, control and build boundaries.
Independent fidelity, binaural/realtime support and physical qualification
remain open. Sonos Arc/eARC remains last.

[The Linux live Atmos preview is published](https://github.com/pjunod/rog_audio/releases/tag/v0.3.0-atmos-preview.1)
from merged PR 17, with exact runtime/source archives, checksums and packaging
inspection. [Publication verification](evidence/live-atmos-preview-publication-2026-10-15.json)
binds all four asset digests and the tag to `cc5bf674`; v0.2.3 remains the stable
latest release. See [download and use](docs/LIVE_ATMOS.md#download-the-published-preview)
for dependencies and checksum verification. Publication adds no laptop,
256-frame full-JOC, physical or Sonos qualification.
[Owned NUC build cleanup](evidence/live-atmos-owned-cleanup-2026-10-15.json)
removed the archived workspace, 46 stopped containers and three unshared
images after verified offhost retention; a shared parent image was retained.

[v0.2.3 is published](https://github.com/pjunod/rog_audio/releases/tag/v0.2.3)
with the [verified packaging-only +rog4 runtime](evidence/speaker-stop-packaging-only-rog4-2026-10-13.json),
corresponding source/notices, both [kept-settings-bound model kits](evidence/speaker-stop-provisional-rog4-kit-manifest-2026-10-13.json),
the required standalone service companion, release notes and checksums.
[Publication verification](evidence/speaker-runtime-v023-publication-2026-10-14.json)
binds the tag and five exact assets; v0.2.2 assets remain unchanged.
The +rog4 native payload matches the accepted +rog3 engine. The last qualified laptop conditions
use +rog3 with the separate helper/unit backport; no +rog4 package rewrite
occurred in this work. The earlier ROG inspection confirmed +rog3; the latest connection attempts
could not refresh either laptop. The sealed kit metadata remains its preparation-era snapshot;
outer release notes record the later scoped demos and completed software hours.

[Current status and dated receipts](docs/STATUS.md) preserve the earlier
startup fixes, ROG 256/512 failures and 1024 pass, ThinkPad old-runtime hour,
partial −20 run, shutdown diagnosis/recovery and listening feedback. Historical
passes do not qualify the current settings. The [service fix](docs/SPEAKER_SERVICE.md)
passed independent review, eleven focused Linux methods and one actual native
IPC/save/exit integration; unchanged native/audio suites were retained.

Display work remains in [rog_hdr_dv](https://github.com/pjunod/rog_hdr_dv).

## Documentation

- [Audio quality](docs/AUDIO_QUALITY.md) — goals, source research and comparison methods.
- [Hardware](docs/AUDIO_HARDWARE.md) — actual codec, amps and OEM findings.
- [ThinkPad](docs/THINKPAD_AUDIO.md) — independent inventory, recovery status and tuning contract.
- [Implementation](docs/AUDIO_IMPLEMENTATION.md) — build order and deliverables.
- [Speaker build](docs/AUDIO_SPEAKER_BUILD.md) — exact-match tuning conversion.
- [Lenovo speaker preparation](docs/LENOVO_SPEAKER_PROFILE.md) — exact first-generation X1 Extreme source, identity and offline candidates.
- [ASUS four-channel mapping](docs/ASUS_FOUR_CHANNEL.md) — why the investigated profile needs explicit rear-pair routing and stereo remains the working fallback.
- [Speaker installation](docs/SPEAKER_INSTALL.md) — scoped runtime and reversible file kit.
- [Speaker service shutdown](docs/SPEAKER_SERVICE.md) — authenticated quit, bounded exit wait and reversible unit backport.
- [Speaker autoload](docs/SPEAKER_AUTOLOAD.md) — native device-return fix, bounded build and unchanged-tuning runtime upgrade.
- [Programme loudness](docs/PROGRAMME_LOUDNESS.md) — adjustable makeup, preserved voicing and selective acceptance.
- [Latency build](docs/AUDIO_LATENCY_BUILD.md) — inspection, measurements and candidates.
- [Linux tuned-path timing](docs/LINUX_AUDIO_PATH.md) — inspect the active processor and apply or remove one private latency request.
- [CoreAudio timing](docs/COREAUDIO_LATENCY.md) — read-only Mac output terms, M4 Air observations and physical measurement limits.
- [Latency comparison](docs/LATENCY_COMPARISON.md) — tuned laptop baselines, M4 Air reference and reversible experiments.
- [Physical latency method](docs/PHYSICAL_LATENCY_METHOD.md) — local key-to-chirp emitter and proposed phone-recorded comparison, with repeat counts and measurement limits.
- [Manual latency annotations](docs/MANUAL_LATENCY_ANNOTATIONS.md) — signed sample intervals, exclusions, private byte verification and declared uncertainty.
- [Atmos build](docs/AUDIO_ATMOS_BUILD.md) — offline object rendering and format limits.
- [Live Atmos](docs/LIVE_ATMOS.md) — bounded PCM streaming to one explicit matching PipeWire sink, with initial seek, attenuation and private delivery reports.
- [Native capture observer](docs/LIVE_ATMOS_CAPTURE.md) — isolated sink-monitor recording, bounded callback/writer accounting and evidence limits.
- [Atmos references](docs/ATMOS_REFERENCE.md) — official JOC test inputs, bounded file rendering and observed channel energy.
- [Development](docs/DEVELOPMENT.md) — review, CI and selective test policy.
- [Operations](docs/OPERATIONS.md) — baseline, result interpretation and physical tests.
- [Provenance](docs/PROVENANCE.md) — migration, source ownership and evidence classes.
- [Review](docs/REVIEW.md) — findings, fixes and final validation.
- [Visual status](docs/STATUS.html) — current workboard.

## Install the speaker candidate

Download the runtime (including corresponding source), per-device kits and
checksums from the [latest release](https://github.com/pjunod/rog_audio/releases/latest).
Follow [speaker installation](docs/SPEAKER_INSTALL.md) for checksum verification,
package dependencies, the ASUS or ThinkPad kit, a private rollback snapshot
and explicit start/stop commands. The package does not activate itself.
Use a coordinated listening window for the first activation; physical hotplug,
resume, acoustic quality and latency still need measurement.

The [ROG deployment receipt](evidence/rog-speaker-deployment-2026-10-12.json)
records the authorized installation and live operational checks. Its initial
volume is 20%, with the original volume and private rollback snapshot retained.
Both laptops now have [automatic startup after login](docs/SPEAKER_INSTALL.md#automatic-startup-after-login),
with the startup unit and disable/remove procedure retained alongside rollback.
Initial startup enablement preserved the listening processes. Both subsequently
moved to the persistent service during the latency trials; an actual post-reboot
run was observed once on the ThinkPad with its original v0.2.0 runtime;
[that bounded receipt](evidence/thinkpad-postboot-observation-v1-2026-10-13.json)
does not qualify repeated startup or the corrected runtime. ROG post-reboot
acceptance remains pending.
The [ThinkPad deployment receipt](evidence/thinkpad-speaker-deployment-2026-10-12.json)
records its separate model binding, 20% initial volume and retained rollback.

## Install and use the diagnostics

The diagnostics and latency tools use Python 3 with its standard library.
Linux collection requires the relevant ALSA/PipeWire commands; absent probes
are reported explicitly. Speaker and Atmos builds have separate pinned
container dependencies in their build documents.

```bash
audio_work_root="$HOME/.local/state/rog-audio/work"  # Durable owned storage.
mkdir -p "$audio_work_root"
git clone https://github.com/pjunod/rog_audio.git "$audio_work_root/diagnostics-example"
cd "$audio_work_root/diagnostics-example"
mkdir -p -m 700 private  # Retain raw inventory and analysis outside Git.
python3 scripts/inspect_audio.py --output private/audio-inventory.json
python3 scripts/analyse_audio_latency.py \
  --input tests/audio/synthetic-trials.json --output private/audio-analysis.json
python3 scripts/analyse_manual_annotations.py \
  --input tests/audio/synthetic-manual-annotations.json \
  --output private/synthetic-annotation-result.json
```

Use a new clone name if that directory exists. Keep work and private outputs
in durable owned storage; project storage in `/tmp` is not permitted. Existing
output files are not overwritten. The example analysis
uses synthetic trials, not a measurement of your machine. Collection is
read-only and never starts playback or recording. See the lane documents
for speaker conversion, client latency requests and the offline Atmos CLI.

## Recovered ASUS files

The [original tuning XML and matching INF](profiles/asus/gu605mz/README.md)
are included with hashes and vendor notices, as requested by the laptop owner.

[Licensing and attribution](LICENSES.md) distinguishes original tools from
recovered vendor files and separately fetched dependencies.

## Layout

- `scripts/` — offline tooling and repository validation.
- `systemd/` — optional user-login startup for the installed speaker runtime.
- `probes/atmos/` — isolated spatial-audio build and CLI.
- `tests/` — generated, redistributable regression cases.
- `profiles/` — original ASUS and Lenovo tuning with matching hardware maps.
- `evidence/` — sanitized source and build receipts.
- `docs/` — maintained contracts and acceptance ledger.

## Progress

- [x] Inspect ASUS hardware and publish matching OEM tuning.
- [x] Build and validate reviewed speaker, latency and offline Atmos tools.
- [x] Build reversible installation and pass both isolated runtime/routing cases.
- [x] Install both model-specific candidates and enable automatic login startup.
- [x] Trial lower tuned Linux graph periods and collect the M4 Air software reference; retain distinct bounded passes and later ROG 256/512 failures.
- [x] Merge guarded 1024/2048 requests and pass the explicit ROG 1024 short trial.
- [x] Review/test/deploy synchronous service stop and both current programme settings; retain both accepted demo listening results.
- [x] Finish both settings-bound software hours without added errors; verify intact logs, preserved state and owned cleanup.
- [x] Review and accept signed manual annotations and the bounded offline Atmos API; retain the documented long-sequence resource limit.
- [ ] Verify the post-login ROG route and refresh the reachable ThinkPad state.
- [ ] Qualify physical headphone/HDMI routing and resume.
- [ ] Measure built-in speaker quality and latency against the Macs.
- [ ] Qualify Sonos Arc/eARC last.
