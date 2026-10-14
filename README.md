# rog_audio — Linux speaker quality, latency and spatial audio

Linux audio engineering for the ASUS ROG Zephyrus G16 GU605MZ, with reusable
diagnostics and offline tooling, extended to the first-generation ThinkPad X1
Extreme. Built-in speakers and everyday media come
first, measured latency against the M4 Air/M3 Max follows, and Sonos Arc/eARC
Atmos is last.

[The current live receipt](evidence/programme-service-autoload-and-current-settings-v2-2026-10-13.json)
records both laptops running `8.2.8+rog3` with the reviewed synchronous-stop helper
backported separately. Original IRs, non-AutoGain settings, final limiters,
owner gains and stock protection are preserved. Login startup is enabled;
two controlled automatic starts and real saved-state checks passed. Both
final software hours passed with no added errors, and both current generated
demos were accepted. Physical recording is deferred to another coordinated
window; measurements and broader media qualification remain open.

| System | Current software | Software timing at 48 kHz | Programme settings | Current acceptance |
|---|---|---|---|---|
| ROG G16 | +rog3 and PR 12 helper/unit backport | 1024-frame graph cycle: 21.333 ms | −20 LUFS; cap 2.6475 dB | Full hour passed without added errors; demo accepted, loudness improved |
| ThinkPad X1 Extreme | +rog3 and PR 12 helper/unit backport | 256-frame graph cycle: 5.333 ms | −16 LUFS; cap 14.1375 dB | Full hour passed without added errors; sound/loudness demo accepted |
| M4 Air | Stock output; matched browser/emitter files staged | 512-frame HAL buffer: 10.667 ms | Unchanged | Route/armed pilot and physical comparison pending |
| Sonos Arc/eARC | Deferred | Unmeasured | Unassessed | Follows internal-speaker acceptance |

These graph/HAL terms do not measure speaker delay or prove Mac parity. The
historical matching Linux before/after numbers describe both drivers selecting
the same integer periods for the same request; their real stability results
differ. See [comparison and retained trials](docs/LATENCY_COMPARISON.md) and
the [phone-recorded method](docs/PHYSICAL_LATENCY_METHOD.md). No physical latency
or calibrated sound-quality result has been collected.

[v0.2.3 is published](https://github.com/pjunod/rog_audio/releases/tag/v0.2.3)
with the [verified packaging-only +rog4 runtime](evidence/speaker-stop-packaging-only-rog4-2026-10-13.json),
corresponding source/notices, both [kept-settings-bound model kits](evidence/speaker-stop-provisional-rog4-kit-manifest-2026-10-13.json),
the required standalone service companion, release notes and checksums.
[Publication verification](evidence/speaker-runtime-v023-publication-2026-10-14.json)
binds the tag and five exact assets; v0.2.2 assets remain unchanged.
The +rog4 native payload matches the accepted +rog3 engine. Actual laptops
retain +rog3 with the separate helper/unit backport; no +rog4 package rewrite
occurred. The sealed kit metadata remains its preparation-era snapshot;
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
- [Atmos build](docs/AUDIO_ATMOS_BUILD.md) — offline object rendering and format limits.
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
- [ ] Qualify physical headphone/HDMI routing and resume.
- [ ] Measure built-in speaker quality and latency against the Macs.
- [ ] Qualify Sonos Arc/eARC last.
