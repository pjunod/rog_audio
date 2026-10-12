# Atmos probe — offline Cavern inspection and rendering

**Status:** patched libraries, CLI and source regressions compiled on Linux
x86_64 on 2026-10-12; post-review tests and JOC/reference qualification pending.

This probe processes explicit files and writes new JSON/WAV outputs. It never
opens a sound device, discovers personal media, registers with a desktop or
changes routing. The [source manifest](source_manifest.json) pins Cavern,
SDK/runtime and the build image. Cavern remains subject to its
[upstream licence](https://github.com/VoidXH/Cavern/blob/7d85d1880666ca5ea323848cff47ce7f50b29f7d/LICENSE.md):
no sale or advertisements; public/commercial use has attribution/permission
conditions. This is not Dolby certification or a qualified playback product.

## Build in an isolated Linux container

Fetch the pinned source explicitly. The build does not fetch dependencies or
install packages on the host. These commands use only disposable storage;
choose unique names when other workers use the same Docker daemon.

```bash
mkdir -p private-atmos
cd private-atmos
git clone https://github.com/VoidXH/Cavern.git Cavern
git -C Cavern checkout 7d85d1880666ca5ea323848cff47ce7f50b29f7d
cd ..
docker build --platform linux/amd64 --target build -t atmos-sdk-local probes/atmos
docker run --rm --name atmos-build-local --network none \
  --memory 1g --pids-limit 128 \
  -v "$PWD:/work" -w /work/probes/atmos atmos-sdk-local \
  sh build.sh --source /work/private-atmos/Cavern \
  --output /work/private-atmos/build
```

Mount a disposable clone containing no recordings, secrets or
configuration. Do not mount `/dev/snd`, a desktop runtime socket or the owner's
home. The image installs pinned Debian Python only in its own filesystem.
The libraries use `netstandard2.1`; the harness uses `net8.0`. Neither library
has a NuGet package dependency. Builds preserve the upstream licence in the
output. Cavern's first clean build produced two CS0649 warnings; the harness
uses warnings as errors. The build refuses a wrong/dirty source revision,
wrong SDK or existing output directory. Relative output paths are resolved
from the caller before changing directory, and final symlinks remain collisions.

The original source pin is unchanged. The build archives that verified pristine
commit into a disposable copy, verifies original file/patch hashes and applies
three local corrections: [PCM metadata boundary](patches/0001-block-buffer-exact-read.patch),
[JOC timeslot wrap](patches/0002-joc-timeslot-frame-boundary.patch) and
[OAMD payload presence](patches/0003-emdf-oamd-presence.patch). It verifies the
patched file hashes before compilation. The original checkout is never edited.
[SHA256SUMS](SHA256SUMS) was created deliberately for these patch bytes;
[source manifest](source_manifest.json) and runtime reports identify a patched
dependency. Original authorship/licence remains Bence Sgánetz (VoidX); the
local changes are attributed to Codex Agent. Neither upstream acceptance nor
JOC fidelity is implied.

## Generate and process a synthetic scene

Run all media commands inside the same no-network, memory-limited container,
using the explicit paths below after substituting your private workspace.

```bash
python3 probes/atmos/generate_scene.py --output private-atmos/moving.json
private-atmos/build/atmos-probe inspect \
  --input private-atmos/moving.json --report private-atmos/inspect.json
private-atmos/build/atmos-probe render \
  --input private-atmos/moving.json --layout 7.1.4 \
  --output private-atmos/moving.wav --report private-atmos/render.json
```

JSON scenes use schema version 1, 48,000 Hz, 256–480,000 samples, 1–8 mono
objects, amplitudes 0–0.25 with summed amplitudes at most 0.5, and frequencies
20–20,000 Hz. Each object has 1–128 strictly ascending keyframes beginning at
sample 0, ending before the scene's sample count. Positions `[x,y,z]` use
Cavern's normalised room: right/up/front are positive; each coordinate is
bounded to `[-1,1]`. Positions interpolate linearly and update at each
256-sample block. The oscillator phase starts at zero. This is synthetic
position rendering, not encoded Dolby metadata.

`stereo-speakers` outputs FL/FR speaker panning without an HRTF, speaker EQ or
virtualisation. `7.1.4` outputs interleaved FL, FR, FC, LFE, BL, BR, SL, SR,
TFL, TFR, TBL, TBR. It writes WAVE extensible IEEE float32 with the explicit
speaker mask. The normaliser is disabled and listener gain is unity.
Nonfinite samples or peaks above 1 fail without publishing a WAV. Output
length matches the input count, including a partial final block; tails are
not flushed or compensated. Delay fields remain unknown until measured.

## Inspect or render elementary E-AC-3

```bash
private-atmos/build/atmos-probe inspect \
  --input private-atmos/reference.eac3 --report private-atmos/codec.json
private-atmos/build/atmos-probe render \
  --input private-atmos/reference.eac3 --layout 7.1.4 \
  --output private-atmos/reference.wav --report private-atmos/reference.json
```

Only raw E-AC-3 is accepted: one independent substream 0, 48 kHz, constant
frame block count/channel mode, complete syncframes, at most 60 seconds and
64 MiB. MP4/MKV demux, dependent substreams, ordinary AC-3 and TrueHD are
explicitly unsupported. The scanner counts actual frames; it does not trust
Cavern's bitrate-derived duration or file extensions for the codec. A `.json`
extension selects the synthetic schema.

The pinned `EnhancedAC3Decoder` parses JOC/EMDF. The adapter observes the exact
internal `Extensions.HasObjects` branch using reflection at this source pin;
changes to those internals fail closed. Object rendering requires initially observed OAMD and current JOC with bounded
object counts. The patched parser tracks actual OAMD payload presence separately
from its persisted instance: later frames may reuse OAMD state, and reports
count `oamd_fresh_object_frames` and `oamd_reused_object_frames`. Object/JOC
counts, JOC channels, bed count and LFE placement must remain compatible with
the initially allocated renderer arrays. Incompatible configuration changes
are rejected before those arrays are consumed. Sparse JOC workarounds are
checked both during frame observation and after rendering, because the flag
can first become true during matrix expansion in the final frame. These checks
do not establish metadata fidelity. Successful
JOC results carry `joc-rendered-unqualified`, never a certification/acceptance
label. Reference comparison is still required, including height and motion.

Without JOC, render uses an explicit conventional-channel PCM adapter and
returns `bed-fallback-rendered`, with
`object_metadata_consumed: false`. The upstream E-AC-3 renderer's bed
Update/Dispose code cannot be used safely at this pin. The adapter sorts
input channels to match the decoder's interleaved order. It preserves
conventional channels, not Atmos objects. A generated 5.1 stream successfully
exercised this path. No opt-in permission is required for supported bed input.
The pinned decoder rejects stereo mode explicitly and
fails on the generated mono fixture; these are recorded capabilities rather
than silently substituted decoders.

## Reports, collisions and limits

Schema 1 records the tool/source version, input SHA-256, container/codec,
parsed JOC signalling (or unknown), actual decoder, metadata consumption,
renderer, layout/rate/channel order, sample count, peak/RMS, delay accounting,
warnings and evidence class. Errors distinguish unsupported capabilities,
invalid input, decoder failures and resource/process failures. Upstream
exception text and private paths are suppressed.

The Linux Python launcher applies a 90-second wall timeout, 60-second CPU
limit, 64-descriptor limit, disabled core dumps/diagnostics and a 512 MiB
managed heap limit. The Docker memory/process limits additionally constrain
native allocations. The launcher alone is not a filesystem/network sandbox;
keep untrusted input in the documented disposable container. A file-size
rlimit prevented .NET startup through its runtime-backed files; output size
is instead bounded by the validated sample/channel counts (under 139 MiB).

JSON and WAV are privately prepared and published with exclusive hard links.
Existing files/directories and broken symlinks collide. A raced destination
fails publication. Failed decoding publishes its error report but no WAV;
a later publication collision may leave an already linked WAV. Publication
returns an error and never unlinks a public target. An inode check followed by
unlink is still racy, so this preserves both partial output and any replacement
made by another writer; it does not promise an atomic two-file transaction. Keep
reports, inputs and generated outputs from personal media private.

## Synthetic regression and qualification boundaries

The [regression runner](test_probe.py) checks channel mapping/height, stereo
panning, motion, repeatable WAV bytes, silence, partial-block output length,
invalid metadata/size limits, collisions/symlinks and malformed bitstreams.
Generate optional codec fixtures locally; do not download film tracks:

```bash
ffmpeg -f lavfi -i sine=frequency=997:sample_rate=48000:duration=0.16 \
  -c:a eac3 -b:a 768k -ac 6 -f eac3 private-atmos/bed.eac3
ffmpeg -f lavfi -i sine=frequency=997:sample_rate=48000:duration=0.16 \
  -c:a eac3 -b:a 192k -ac 2 -f eac3 private-atmos/stereo.eac3
python3 probes/atmos/test_probe.py --probe private-atmos/build/atmos-probe \
  --bed-fixture private-atmos/bed.eac3 \
  --stereo-fixture private-atmos/stereo.eac3 \
  --report private-atmos/regression.json
```

Fixture bytes depend on the encoder version; the retained receipt uses FFmpeg
9.0.1 and records hashes. The final integration suite/review is deferred by
the owner's updated batching policy. Earlier tests exercised eight passing
synthetic cases and discovered the stereo decoder limitation; the subsequent
5.1 CLI check is a separate build/debug receipt, not a final suite pass.

| Capability | Evidence and remaining limit |
|---|---|
| Linux core/format libraries and CLI | Built at exact Cavern/SDK pin, x86_64 |
| Synthetic speaker object rendering | Exercised stereo and 7.1.4; no perceptual or acoustic qualification |
| Conventional 5.1 E-AC-3 | Generated signal decoded/rendered; explicit bed fallback |
| Stereo E-AC-3 | Upstream explicitly rejects this mode |
| Generated mono E-AC-3 | Upstream decoder error 1; broader mono support unqualified |
| E-AC-3 JOC | API compiled; lawful sample/metadata/reference comparison pending |
| TrueHD Atmos | Unsupported here; Cavernize's inspected adapter invokes external `truehdd.exe` and downloads floating releases; no pinned Linux decoder supplied |
| Binaural/headphones | Unsupported; no HRTF source/licence or fidelity qualification |
| Dolby gst-home-audio | Alternate public contract; proprietary native libraries not supplied |
| Realtime/desktop/PipeWire | No integration, install or activation; offline timing includes I/O/startup |
| Sonos Arc/eARC | Deferred to the final audio lane |

The smallest prototype is this player-side file-to-WAV command. Later app
integration must retain encoded audio/metadata before downmixing and render
once. The offline result has no timestamp, seek/flush, gap or live EOS API;
create a new decoder/renderer per input. Establish decoder/JOC and QMF delay,
tail handling, seek state, allocation and block cost before a playback API.
There is no always-running service or physical-device output in this batch.

## Hosted CI and focused retries

The [CI recipe](ci.sh) needs a Linux host with Git and Docker. It fetches only
Cavern's exact commit, builds the pinned `ci` image, generates both codec
fixtures with Debian FFmpeg `7:5.1.9-0+deb12u1`, then compiles/runs without
network, devices or session sockets. The image/fixtures are disposable. The runtime uses the caller UID/GID so
build outputs remain removable by the host; .NET, NuGet and XDG cache/config
paths use container-local `/tmp` directories without overriding `HOME`.
Run the full suite once after the batch's adversarial review, for example
from a manually dispatched GitHub job on `ubuntu-24.04`:

```bash
probes/atmos/ci.sh --report atmos-regression.json
```

A GitHub job can upload `atmos-regression.json` as its test artifact. This
recipe is supplied for parent integration and has not yet been executed;
source compilation/CLI debugging and retained tests are separate receipts.
Do not automatically run it on every push. Retry only a failing or affected
method, using either a retained build or the same isolated CI recipe:

```bash
python3 probes/atmos/test_probe.py --probe private-atmos/build/atmos-probe \
  --bed-fixture private-atmos/bed.eac3 --stereo-fixture private-atmos/stereo.eac3 \
  --test test_generated_eac3_bed --report private-atmos/bed-retry.json
probes/atmos/ci.sh --report stereo-retry.json --test test_unsupported_stereo_eac3
```

Repeat `--test` to select several method IDs. Unknown IDs fail instead of
silently running an empty suite. Four additional source-bound regressions exercise the exact PCM/metadata read
boundary, QMF timeslot wrap across 256/512/768/1536-sample frames, late sparse
flag detection and initial/fresh/reused OAMD with stable renderer configuration.
A publication regression simulates a competing writer replacing the linked
WAV before report collision and checks that its inode/data remains. These
regressions use generated arrays and reflection, with no Dolby payload.

The complete suite has fifteen methods; without
explicit generated codec fixtures, those two methods are recorded as skips.
