# Atmos references — offline official vectors and channel observations

**Status:** complete-vector development diagnostics passed; review and affected
formal tests pending · **Written:** 2026-10-14 · **Executes:** host Atmos lane in
[audio implementation](AUDIO_IMPLEMENTATION.md).

Companion to [Atmos build](AUDIO_ATMOS_BUILD.md) and the
[probe contract](../probes/atmos/README.md). This document explains the official
inputs, lossless extraction, bounded file rendering and interpretation of
channel-energy reports. It does not activate desktop audio.

## Official inputs are for testing and stay private

Dolby's [automotive test-content article](https://dolby.my.site.com/professionalsupport/s/article/App-Development-for-Automotive-Test-Content)
provides the Channel ID 5.1.4 and 7.1.4 DASH manifests and states that its
vectors may solely be used for testing. The manifests point to clear audio-only
MP4 files, identify 48 kHz `ec-3` representations, and signal JOC complexity 16
at 448 and 768 kbit/s. The selected 768 kbit/s files returned HTTP 200. Keep
original MP4s, extracted streams, WAVs and detailed reports in owned private
storage outside Git; this permission does not grant redistribution.

| Input | Official file | MP4 bytes | MP4 SHA256 | Entire duration |
|---|---|---|---|---|
| Channel ID 5.1.4 | [MP4](https://ott.dolby.com/DISC/assets/54bfa462-f806-4b77-a303-5f8255be9847/channel_ID_voices_514_768.mp4) | 5907021 | `e2ea5a2f33e5e3d0a06abf76e4216f00a3b92bff1cddcb8fc9a423ac0da10fee` | 61.504s |
| Channel ID 7.1.4 | [MP4](https://ott.dolby.com/DISC/assets/ef7d6eeb-1968-4010-82e8-808399604553/channel_ID_voices_714_768.mp4) | 7059393 | `3c7db38e5fe29124c10c660177b6bc377703f2af846a67bf7f452431d3e9bb08` | 73.504s |

The official [5.1.4 manifest](https://ott.dolby.com/DISC/assets/54bfa462-f806-4b77-a303-5f8255be9847/channel_ID_voices_514.mpd)
and [7.1.4 manifest](https://ott.dolby.com/DISC/assets/ef7d6eeb-1968-4010-82e8-808399604553/channel_ID_voices_714.mpd)
are publisher signalling evidence. The actual decoder observations below are
separate evidence; an MP4 profile badge alone is insufficient.

## Extract from frame 0 and render only to new files

Obtain the named official file explicitly, verify its published receipt hash,
and supply its new private path. Never search personal media. Use FFmpeg
stream copy to remove the MP4 container, because the probe accepts elementary
E-AC-3 rather than MP4. Do not decode/re-encode, select AAC, or begin a crop
midstream: a crop can discard initial object metadata. The recorded extraction
used FFmpeg 9.0.2 on macOS; the decoder and renderer ran inside the pinned Linux
container. The full source streams remained intact.

```bash
ffmpeg -nostdin -hide_banner -i PRIVATE/channel_ID_voices_714_768.mp4 \
  -map 0:a:0 -c:a copy -f eac3 -n PRIVATE/channel_ID_voices_714_768.eac3
# Stream-copy the sole audio track; -n refuses an existing output.

PRIVATE_BUILD/atmos-probe inspect \
  --input PRIVATE/channel_ID_voices_714_768.eac3 \
  --report PRIVATE/inspect.json
# Parse the entire explicit input inside the isolated Linux container.

PRIVATE_BUILD/atmos-probe render \
  --input PRIVATE/channel_ID_voices_714_768.eac3 --layout 7.1.4 \
  --output PRIVATE/render.wav --report PRIVATE/render.json
# Render to new private files; no sound device is opened.

python3 scripts/analyse_atmos_render.py \
  --input PRIVATE/render.wav --report PRIVATE/channel-energy.json --window-ms 250
# Observe channel energy; no playback or independent fidelity comparison.
```

Choose distinct output paths for each attempt. Run the build and media commands
with the isolation described in the [probe README](../probes/atmos/README.md):
no network during compilation/processing, no sound devices, desktop sockets or
host configuration mounts. The development container used two CPUs, 1 GiB
memory and 128 processes, with Linux amd64 under local macOS arm64 emulation.
The encoder-independent elementary streams have these identities:

| Stream | Bytes | SHA256 | Complete frames / samples per channel |
|---|---|---|---|
| 5.1.4 | 5904384 | `6ee95693613da2b6daa1a21deb9fd730271f428d2bfd2f4cfd589363365f0240` | 1922 / 2952192 |
| 7.1.4 | 7056384 | `c190089bbb0600b8bcba27dbe07c370252c3c2605fd285b4f596b9c2a9d59432` | 2297 / 3528192 |

## Runtime limits accommodate the actual reference work

The previous 60-second input bound excluded both complete vectors. Encoded
input is now bounded to 90 seconds, retaining 48 kHz, 64 MiB, single independent
substream 0, constant configuration and complete-syncframe validation. Maximum
12-channel output is 207360068 bytes, below 198 MiB. Synthetic JSON scenes retain
their separate ten-second bound. No format restriction is silently relaxed.

The prior 64-descriptor launcher could complete a JOC WAV then abort while
loading `System.Reflection.Primitives` for JSON serialization. A direct bounded
reproduction retained that private exception. The revised allowance is 128,
with CPU 60 seconds, wall 90 seconds, disabled core dumps/diagnostics, 512 MiB
managed heap and container resource limits retained. Both complete-vector
processes reached a sampled 66 open descriptors. Sampling every 10 ms gives a
lower bound on the actual peak; it does not prove a universal maximum.

The exact Cavern pin and three attributed patches are unchanged. No upstream
acceptance, proprietary runtime, binaural HRTF or installed laptop change is
part of this batch. The object-configuration report exposes the validated
initial OAMD/JOC shape: object counts, JOC input channels, bed count and LFE
object index. Later incompatible configurations remain rejected.

## Read channel energy as an observation

The [streaming analyzer](../scripts/analyse_atmos_render.py) accepts only the
probe's contiguous 48kHz WAVE-extensible float32 stereo/7.1.4 contract. It checks
length, format, finite samples, unit peak, duration and unchanged input identity.
It reads bounded windows, records input SHA256, sample count, per-channel RMS
and peak, and each window's dominant channel. Input is opened nonblocking and rejected unless its descriptor is a regular
file, so FIFOs cannot block startup. It creates a new JSON file with mode 0600
and refuses existing files, directories and dangling symlinks. It does not infer
Atmos from PCM or compare with an independent reference.

**How to read it:** each window gives `start_sample` and `samples_per_channel`;
divide by 48000 for time in seconds. `dominant_channel:null` means exactly zero
energy in every channel. A dominant channel alone can describe tiny noise;
apply an explicit energy threshold when summarizing activity. The development
summary used 250 ms windows with maximum channel RMS at least0.001. Its7.1.4
sequence repeated three times:

```text
FL → FR → FC → SL → SR → BL → BR → TFL → TFR → TBL → TBR → LFE
```

These are observed labels derived from the configured WAV channel order. They
are not independently verified spoken labels, expected object trajectories,
aligned PCM, gain accuracy or metadata fidelity. The full 5.1.4 vector had zero
BL/BR RMS and nonzero activity on its ten intended output channels, including
four height channels. Both outputs were finite and below unit peak. Exact
counts, hashes and diagnostics live in the [allowlisted receipt](../evidence/audio-atmos-official-vectors-2026-10-14.json).

## Acceptance keeps inherited and new evidence distinct

The inherited 15-method reviewed synthetic/bed acceptance and separate focused
CI cleanup remain in their [original receipt](../evidence/audio-atmos-acceptance-2026-10-12.json).
They contain no official JOC payload. This batch adds a scanner 90-second
boundary regression, object-shape report coverage and five generated WAV/selector
analyzer methods. Final selection after independent review covers those five
methods plus `test_encoded_duration_bound`,
`test_oamd_freshness_and_stable_configuration` and `test_generated_eac3_bed`.
Unchanged QMF/parser patches, synthetic position rendering and publication-race
methods are retained rather than repeated. Private vector diagnostics precede
review and are labelled accordingly; affected formal acceptance is pending.

JOC file decoding/rendering is now exercised on two official complete vectors.
Independent renderer comparison, moving-object fidelity, delay/tail accounting,
binaural output, TrueHD, stereo/mono decoder support and realtime integration
remain separate work. No acoustic or physical latency result is inferred.
Sonos stays last, and accepted laptop speaker tuning is unchanged.

## Run only the reviewed analyzer methods

The `atmos-energy` choice in the [manual acceptance workflow](../.github/workflows/acceptance.yml)
runs only the offline Python analyzer methods through the
[selective runner](../scripts/validate_atmos_energy.py). It does not rebuild
Cavern or rerun the encoded Atmos suite. Full local acceptance and a single
failed-method retry use new report paths:

```bash
python3 scripts/validate_atmos_energy.py --report PRIVATE/energy-all.json
# Run the five reviewed analyzer/input/privacy/selection methods once.

python3 scripts/validate_atmos_energy.py \
  --test-id test_analyse_atmos_render.AnalyseAtmosTests.test_duration_bound_and_report_collision \
  --report PRIVATE/energy-failed-retry.json
# Retry this failed method alone; unchanged passing methods stay retained.
```

Exact module/class/method IDs are validated before execution. Unknown IDs,
duplicates and cross-module selections fail rather than silently running a
partial or empty suite. Errors, failures, skips and zero-test runs fail
acceptance. Optional reports are exclusively created with mode 0600.
The initial vector receipt binds its pre-review source bytes; the later review
fixes and final affected acceptance have separate source identities. No
successful complete-vector diagnostic is repeated for these input/report/CI
changes.
