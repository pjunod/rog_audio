# rog_audio — Linux speaker quality, latency and spatial audio

Linux audio engineering for the ASUS ROG Zephyrus G16 GU605MZ, with reusable
diagnostics and offline tooling, extended to the first-generation ThinkPad X1
Extreme. Built-in speakers and everyday media come
first, measured latency against the M4 Air/M3 Max follows, and Sonos Arc/eARC
Atmos is last.

Read [status](docs/STATUS.md) for progress and evidence boundaries.
The speaker runtime and separate ASUS/ThinkPad kits have passed review, unit
tests and isolated runtime acceptance. The ROG now runs the v0.2.0 internal
speaker candidate with its preset, IR, plugins and hardware output checked;
the ThinkPad now runs its separate Lenovo candidate with the same live checks.
Both have automatic startup enabled at user login after reboot. The owner reports
substantial audible improvement; physical hotplug and measurements remain
pending. macOS-equivalent performance or
Atmos fidelity has not been measured.

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
- [Latency build](docs/AUDIO_LATENCY_BUILD.md) — inspection, measurements and candidates.
- [Linux tuned-path timing](docs/LINUX_AUDIO_PATH.md) — inspect the active processor and apply or remove one private latency request.
- [CoreAudio timing](docs/COREAUDIO_LATENCY.md) — read-only Mac output terms, M4 Air observations and physical measurement limits.
- [Latency comparison](docs/LATENCY_COMPARISON.md) — tuned laptop baselines, M4 Air reference and reversible experiments.
- [Atmos build](docs/AUDIO_ATMOS_BUILD.md) — offline object rendering and format limits.
- [Development](docs/DEVELOPMENT.md) — review, CI and selective test policy.
- [Operations](docs/OPERATIONS.md) — baseline, result interpretation and physical tests.
- [Provenance](docs/PROVENANCE.md) — migration, source ownership and evidence classes.
- [Review](docs/REVIEW.md) — findings, fixes and final validation.
- [Visual status](docs/STATUS.html) — current workboard.

## Install the speaker candidate

Download the runtime (including corresponding source), per-device kits and
checksums from [v0.2.0](https://github.com/pjunod/rog_audio/releases/tag/v0.2.0).
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
The current listening process was preserved while future startup was enabled;
an actual post-reboot run has not yet been observed.
The [ThinkPad deployment receipt](evidence/thinkpad-speaker-deployment-2026-10-12.json)
records its separate model binding, 20% initial volume and retained rollback.

## Install and use the diagnostics

The diagnostics and latency tools use Python 3 with its standard library.
Linux collection requires the relevant ALSA/PipeWire commands; absent probes
are reported explicitly. Speaker and Atmos builds have separate pinned
container dependencies in their build documents.

```bash
git clone https://github.com/pjunod/rog_audio.git /tmp/rog-audio-work
cd /tmp/rog-audio-work
python3 scripts/inspect_audio.py --output /tmp/audio-inventory.json
python3 scripts/analyse_audio_latency.py --input tests/audio/synthetic-trials.json --output /tmp/audio-analysis.json
```

Use new output paths; existing files are not overwritten. The example analysis
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
- [ ] Qualify physical headphone/HDMI routing and resume.
- [ ] Measure built-in speaker quality and latency against the Macs.
- [ ] Qualify Sonos Arc/eARC last.
