# rog_audio — Linux speaker quality, latency and spatial audio

Linux audio engineering for the ASUS ROG Zephyrus G16 GU605MZ, with reusable
diagnostics and offline tooling, extended to the first-generation ThinkPad X1
Extreme. Built-in speakers and everyday media come
first, measured latency against the M4 Air/M3 Max follows, and Sonos Arc/eARC
Atmos is last.

Read [status](docs/STATUS.md) for progress and evidence boundaries.
The speaker runtime and separate ASUS/ThinkPad kits have passed review, unit
tests and isolated runtime acceptance. The ROG now runs the corrected `8.2.8+rog2` runtime with its original preset,
IR, plugins and hardware output checked;
the ThinkPad now runs its separate Lenovo candidate with the same live checks.
Both have automatic startup enabled at user login after reboot. The owner reports
substantial audible improvement in clarity, but everyday movies/shows remain
too quiet on both laptops at maximum output. Loudness acceptance, physical
hotplug and measurements remain pending. macOS-equivalent performance or
Atmos fidelity has not been measured.

Historical paired zero-PCM observations reduced both tuned Linux driver
periods from 2048 frames (42.667 ms) to 256 frames (5.333 ms) at 48 kHz with
the same client request. The ROG now runs at 512 frames (10.667 ms) after its 256-frame stability
failure and a separate successful short trial; ThinkPad remains at 256. The M4 Air reports
a 512-frame HAL buffer (10.667 ms). These are software timing terms, not
measured speaker delay or proof of Mac parity.
The [comparison and rollback](docs/LATENCY_COMPARISON.md#7-paired-256-frame-trials--both-tuned-paths-preserved)
record the results and limits.

The ThinkPad completed 3600.177 seconds of the declared normal-use software
check on the existing v0.2.0 runtime: sampled driver count remained at its
startup value of 1, followers stayed zero and protected state matched at
start, midpoint and end. The ROG's 256-frame attempt failed after 67.982
seconds; reviewed rollback preserved its full tuning at 2048 frames. Neither
result measures physical latency or qualifies the startup-fixed runtime.
The corrected native runtime and final artifact bindings cleared re-review,
PR 9 merged, and the ROG upgrade automatically loaded the unchanged tuning. All 29 affected unit methods and six isolated graph selectors passed once,
with zero failures or skips. The [acceptance receipt](evidence/speaker-autoload-acceptance-2026-10-13.json)
binds the reviewed source, runtime and retained logs. [Current results](docs/STATUS.md#startup-and-sustained-check-progress--2026-10-13)
keep those evidence classes distinct. The [published v0.2.1 release](https://github.com/pjunod/rog_audio/releases/tag/v0.2.1)
contains package `8.2.8+rog2`, corresponding source/notices, both newly bound
kits and checksums. Its tag and remote asset hashes were verified; existing
v0.2.0 assets remain unchanged.
A later [ROG listening observation](evidence/rog-owner-listening-2026-10-13.json)
records “Sounded good” with matching protected state; driver timing was not
sampled during that demo, so it is separate from latency/stability results.
The [ThinkPad listening receipt](evidence/thinkpad-owner-listening-2026-10-13.json)
also records “sounded good” for the demo, while explicitly leaving everyday
loudness unaccepted after the subsequent movies/shows report. A separate gain
investigation will address that issue without changing this frozen batch.
The ThinkPad runtime update remains held for capacity after pilot staging
reported `ENOSPC`. Authorized cleanup completed with verified private backup,
but actual available space is only 45,326,336 bytes (43.23 MiB). Recovery
assets, installed packages and audio settings remain preserved.
A later [paired digital gain capture](evidence/both-laptop-digital-gain-transfer-2026-10-13.json)
found speech attenuation consistent with the retained FIR filters (-0.343 dB
ROG, -3.903/-3.783 dB ThinkPad), with no additional runtime gain loss for that
low-level clip. Ordinary movie/show loudness remains unresolved.

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
- [Speaker autoload](docs/SPEAKER_AUTOLOAD.md) — native device-return fix, bounded build and unchanged-tuning runtime upgrade.
- [Programme loudness](docs/PROGRAMME_LOUDNESS.md) — adjustable bounded makeup, preserved voicing and the unresolved everyday-volume evidence.
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
- [x] Trial lower tuned Linux graph periods and collect the M4 Air software reference; ROG now 512, ThinkPad 256.
- [ ] Qualify physical headphone/HDMI routing and resume.
- [ ] Measure built-in speaker quality and latency against the Macs.
- [ ] Qualify Sonos Arc/eARC last.
