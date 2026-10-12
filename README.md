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
- [Speaker build](docs/AUDIO_SPEAKER_BUILD.md) — exact-match private tuning conversion.
- [Latency build](docs/AUDIO_LATENCY_BUILD.md) — inspection, measurements and candidates.
- [Atmos build](docs/AUDIO_ATMOS_BUILD.md) — offline object rendering and format limits.
- [Development](docs/DEVELOPMENT.md) — review, CI and selective test policy.
- [Operations](docs/OPERATIONS.md) — baseline, result interpretation and physical tests.
- [Provenance](docs/PROVENANCE.md) — migration, source ownership and evidence classes.
- [Review](docs/REVIEW.md) — findings, fixes and final validation.
- [Visual status](docs/STATUS.html) — current workboard.

## Layout

- `scripts/` — offline tooling and repository validation.
- `probes/atmos/` — isolated spatial-audio build and CLI.
- `tests/` — generated, redistributable regression cases.
- `evidence/` — sanitized source and build receipts.
- `docs/` — maintained contracts and acceptance ledger.

## Progress

- [x] Inspect hardware and recover matching OEM tuning privately.
- [ ] Merge reviewed speaker, latency and offline Atmos tools.
- [ ] Measure built-in speaker quality and latency against the Macs.
- [ ] Qualify Sonos Arc/eARC last.
