# rog_audio — Linux speaker quality, latency and spatial audio

Linux audio engineering for the ASUS ROG Zephyrus G16 GU605MZ, with reusable
diagnostics and offline tooling. Built-in speakers and everyday media come
first, measured latency against the M4 Air/M3 Max follows, and Sonos Arc/eARC
Atmos is last.

Read [status](docs/STATUS.md) for progress and evidence boundaries.
The first batch builds offline tools and records the remaining physical
acceptance work. No live audio settings have changed, and macOS-equivalent
performance or Atmos fidelity has not been measured.

Display work remains in [rog_hdr_dv](https://github.com/pjunod/rog_hdr_dv).

## Documentation

- [Audio quality](docs/AUDIO_QUALITY.md) — goals, source research and comparison methods.
- [Hardware](docs/AUDIO_HARDWARE.md) — actual codec, amps and OEM findings.
- [Implementation](docs/AUDIO_IMPLEMENTATION.md) — build order and deliverables.
- [Speaker build](docs/AUDIO_SPEAKER_BUILD.md) — exact-match tuning conversion.
- [Latency build](docs/AUDIO_LATENCY_BUILD.md) — inspection, measurements and candidates.
- [Atmos build](docs/AUDIO_ATMOS_BUILD.md) — offline object rendering and format limits.
- [Development](docs/DEVELOPMENT.md) — review, CI and selective test policy.
- [Operations](docs/OPERATIONS.md) — baseline, result interpretation and physical tests.
- [Provenance](docs/PROVENANCE.md) — migration, source ownership and evidence classes.
- [Review](docs/REVIEW.md) — findings, fixes and final validation.
- [Visual status](docs/STATUS.html) — current workboard.

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
- `probes/atmos/` — isolated spatial-audio build and CLI.
- `tests/` — generated, redistributable regression cases.
- `profiles/` — recovered ASUS tuning and matching hardware mapping.
- `evidence/` — sanitized source and build receipts.
- `docs/` — maintained contracts and acceptance ledger.

## Progress

- [x] Inspect ASUS hardware and publish matching OEM tuning.
- [ ] Merge reviewed speaker, latency and offline Atmos tools.
- [ ] Measure built-in speaker quality and latency against the Macs.
- [ ] Qualify Sonos Arc/eARC last.
