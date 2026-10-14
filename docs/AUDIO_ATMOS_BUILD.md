# Host Atmos build — prove decoding and rendering before live integration

**Status:** Linux libraries/CLI built; synthetic renderer exercised; complete official JOC vectors exercised in
development diagnostics; independent fidelity and physical qualification pending ·
**Written:** 2026-10-12 · **Executes:** host Atmos lane in
[implementation](AUDIO_IMPLEMENTATION.md).

Read [audio quality](AUDIO_QUALITY.md), [hardware](AUDIO_HARDWARE.md) and
[development](DEVELOPMENT.md). This lane builds host-side file processing
for laptop/headphone use. Sonos Arc passthrough is explicitly last; do not
spend this batch implementing or testing Sonos routing.

## Implemented offline artifact (2026-10-12)

The [Atmos probe](../probes/atmos/README.md) now contains pinned Linux build
automation, an offline inspect/render CLI, synthetic scenes/regressions and a
[hosted CI recipe](../probes/atmos/ci.sh). The
[source-bound receipt](../evidence/audio-atmos-build-2026-10-12.json) separates
compilation, retained tests and the final default 5.1 E-AC-3 bed-render check.
The bed result is labelled explicitly; no opt-in permission is required.
Independent source review found PCM/metadata boundary and JOC timeslot defects;
three attributed patches now apply to a disposable verified source copy.
The [patch manifest](../probes/atmos/source_manifest.json) preserves the original
pin and declares the modified dependency. The [review-fix compiler receipt](../evidence/audio-atmos-review-fixes-2026-10-12.json)
is separate from the [final acceptance receipt](../evidence/audio-atmos-acceptance-2026-10-12.json):
all fifteen reviewed-source methods passed once. The CI output-ownership
cleanup failure was corrected and its focused path passed without rerunning
those tests. Initial OAMD is required; later
reuse is reported accurately, and incompatible array configurations or sparse
workarounds are rejected. Publication errors preserve public paths because a
conditional inode check followed by unlink would still race with a replacement.
Stereo E-AC-3 is rejected upstream, and the generated mono fixture fails.
JOC, TrueHD, binaural, realtime integration and physical acceptance remain
separate capabilities with documented limits.

The owner moved integration to `pjunod/rog_audio` and requested one substantive
batch. Final adversarial review and the affected tests/integrity/privacy checks
belong to the parent integration; they have not been claimed here. Retry
selected test IDs after that run. Import only the lane files, not this clone's
inherited display history. The remaining numbered sections retain the build
contract and later qualification requirements.

## Official-vector development diagnostics (2026-10-14)

[Atmos references](ATMOS_REFERENCE.md) records two complete official testing
vectors, lossless elementary-stream extraction and actual JOC file rendering.
The original 60-second input bound excluded their full duration; the 90-second
bound retains the format/resource contracts. A 64-descriptor serialization
abort was reproduced, and the 128 allowance supported a sampled native count
of 66. Source/patch pins are unchanged. Observed height energy and repeated
channel order are not independently verified metadata or PCM fidelity.
Four source-review findings were fixed, then the three affected probe methods
and five analyzer/selector methods passed once without failures, errors or
skips. [The acceptance receipt](../evidence/audio-atmos-official-vectors-acceptance-2026-10-14.json)
binds the reviewed source; the earlier complete-vector diagnostics are retained
on their original hashes and are not a fresh post-review vector render.

## 1. Establish the exact candidate and compiler loop

Fetch Cavern at the revision in [implementation](AUDIO_IMPLEMENTATION.md).
Inspect its solution/project target frameworks, supported Linux entry points,
licence and dependency versions before writing an adapter. Record actual
`dotnet --info`, SDK pin, architecture and Linux container image digest.
Build the relevant libraries first. Do not equate a Windows GUI project build
with a usable Linux library or require a system-wide .NET installation.

The README distinguishes E-AC-3 JOC support from TrueHD Atmos through
Cavernize plus Truehdd. Start with E-AC-3 JOC. Determine whether the TrueHD
path and needed entry points are available and buildable on Linux before
promising support. Pin all added dependencies and preserve attribution.
A missing dependency is an explicit capability result, not a cue to silently
fall back to bed-only PCM while reporting Atmos.

Use Dolby's pinned `gst-home-audio` as a contract reference and alternative
only if the required proprietary Linux libraries are actually available with
appropriate use rights. The public wrapper does not contain those runtimes.
Do not copy Windows DLLs into Linux paths or claim the OEM recovery package
supplies a native Linux renderer. Any proprietary experiment remains private.

## 2. Build an offline harness with an honest result contract

Proposed deliverable location: `probes/atmos/`, including build script,
source manifest, CLI harness and generated synthetic tests. Example intended
interface (adjust executable name to the proved toolchain and document it):

```bash
./probes/atmos/build.sh --output PRIVATE_BUILD
PRIVATE_BUILD/atmos-probe inspect --input PRIVATE_MEDIA --report PRIVATE_REPORT
PRIVATE_BUILD/atmos-probe render --input PRIVATE_MEDIA --layout stereo-binaural --output PRIVATE_WAV --report PRIVATE_REPORT
```

No hardware output, network fetch, default-sink change or desktop registration
occurs. Input must be explicitly supplied; never search personal media.
Write only to explicit new output paths and fail on collision by default.
Constrain untrusted media parsing by resource/time limits in a disposable
process. Keep decoder failures and unsupported formats distinguishable.

The JSON report must include schema/tool/source versions, input hash,
container/codec, detected Atmos signalling, actual decoder, whether object
metadata was consumed, renderer, output layout/rate/channels, sample count,
delay accounting, warnings and evidence class. Unknown metadata fields are
unknown, not false. Report a conventional-channel fallback explicitly; never
label it a successful Atmos render.

Headphone binaural output needs a documented HRTF source/licence, coordinate
convention, channel mapping and gain normalisation. A stereo speaker output
must have a separate label and contract; headphone HRTFs are not laptop
speaker tuning. A reference multichannel render is useful even if binaural
integration remains unfinished. Output WAVs from private media stay private.

## 3. Separate synthetic renderer checks from codec qualification

First build deterministic synthetic moving-object scenes through the library
API. Check channel ordering, position/orientation, finite samples, output
length, silence, gain bounds and repeatability. Test malformed metadata and
resource limits. This proves the exercised renderer API, not Dolby bitstream
decoding, metadata fidelity, perceptual localisation or certification.

Then use a lawfully available local E-AC-3 JOC sample with a recorded hash.
Record object/bed metadata and rendering behaviour against a documented
reference, including height and motion. If no sample is available, finish
the compiler/harness/synthetic work and mark codec qualification pending.
Do not download random copyrighted movie tracks or commit reference payloads.
TrueHD is a separate row with its own decoder dependency and evidence.

Reference comparison records renderer/version/layout, any gain alignment,
resampling, delay alignment and tolerance with its rationale. Samplewise
identity is not assumed across different renderers/HRTFs. An Atmos string
from ffprobe or a successful plain E-AC-3 decode is insufficient.

## 4. Prepare realtime integration only after offline correctness

Measure processing cost and allocations for bounded blocks without writing to
a physical device. Determine whether decoder framing, seeks and rendering
state can support playback. Record algorithmic delay and buffer requirements;
do not force 64-frame processing merely because PipeWire permits it.

A later integration consumes encoded audio and metadata before information
is discarded, renders once, and sends PCM to PipeWire. Generic PipeWire EQ
cannot recover objects from an already downmixed stream. Specify timestamp,
seek/flush, gap, channel layout, volume and EOS contracts. Keep a stereo/bed
fallback visibly labelled. Plurx-specific negotiation remains in Plurx.

Do not build an always-running system-wide service until the offline path and
required app boundary are proven. Document the smallest runnable player-side
prototype and remaining gaps. Measure laptop-speaker spatial treatment
separately from headphone rendering and OEM tonal correction.

## 5. Deliver a build, not another research-only plan

The minimum completed batch is pinned Linux build automation, working offline
CLI, synthetic renderer tests, source-bound receipts and a format capability
matrix. If a candidate genuinely cannot build, diagnose the failure and try a
bounded supported library target or documented alternative; report the exact
external blocker alongside all completed work. Preserve licence limitations.

Submit the implementation for independent adversarial review, fix findings,
then run the affected fast lane once. Record source compilation, synthetic
results, private sample qualification, runtime readiness and physical
acceptance independently. Sonos remains deferred until the coordinator
finishes the internal-audio work and schedules that final route.
