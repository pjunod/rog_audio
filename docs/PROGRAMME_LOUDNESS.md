# Programme loudness — adjustable makeup with original speaker voicing

**Status:** corrected native source/artifacts reviewed; 28 affected units and
both isolated model graphs passed; coordinated laptop acceptance pending · **Updated:** 2026-10-13.

Companion to [speaker installation](SPEAKER_INSTALL.md) and
[device-return autoload](SPEAKER_AUTOLOAD.md). This document describes the
new gain control and offline bundle preparation. General live acceptance is
recorded in [status](STATUS.md); the published v0.2.1 runtime remains separate.

## What the quieter-output investigation established

The owner reported that ordinary movies and shows became too quiet on both
laptops after tuning, even at maximum volume. Positive speech/music demo
clarity did not accept everyday loudness.

The [paired low-level digital transfer](../evidence/both-laptop-digital-gain-transfer-2026-10-13.json)
measured the following source-aligned speech intervals on the original runtime:

| Signal comparison | ROG | ThinkPad |
|---|---:|---:|
| Source to processor input | 0 dB | 0 dB |
| Original FIR speech attenuation, left/right | -0.343/-0.343 dB | -3.903/-3.783 dB |
| Extra native loss relative to exact FIR prediction | Below 0.000001 dB | Below 0.000001 dB |

Both physical and virtual digital gains were unity. Hardware amplifier
controls were unchanged from the retained pre-tuning inventories. The
ThinkPad's static filtering explains a meaningful loss with its approximation
of programme compensation bypassed. The small ROG loss in this clip does not
explain the larger everyday-media regression. That part remains unresolved.
These are digital observations on one low-level clip, not calibrated acoustic
output, an ordinary-movie capture or physical speaker latency.

Enabling a programme leveler is an improvement under evaluation. The old
AutoGain's uncapped makeup and stale-gain transition behavior were found while
preparing that improvement. AutoGain was bypassed in the installed profiles;
those prospective enablement defects are not established causes of the
current quietness.

## The native contract preserves voicing and limits automatic makeup

The additive [native patch](../patches/easyeffects/0003-Bound-programme-loudness-makeup.patch)
adds `maximumGain` to the AutoGain configuration and `maximum-gain` to JSON
presets, independently of its LUFS target. The UI exposes **Maximum automatic
makeup**, with an ordinary 0–36 dB range. Its default is 0 dB: old profiles do
not acquire automatic positive gain just by upgrading the runtime.

```text
original model FIR / voicing / bypassed dynamics
                     │
                     ▼
 independent EBU programme leveler ── target LUFS, maximum makeup dB
                     │
                     ▼
          original final -1 dB limiter
                     │
                     ▼
               physical speakers
```

One gain value applies to both channels. Requested gain and retained smoothed
state are clamped to the selected automatic limit. A lower limit clamps old
state immediately, before smoothing. Silence, bypass, unavailable/nonfinite
loudness estimates and failed analysis reset retained makeup to unity.
Changing to louder material lowers the requested gain instead of retaining
old high makeup when a sample-peak request would exceed headroom. Ingestion
errors also enter the unity/reset path; history reset invalidates analyser
and makeup state together under synchronization.

The analyser state is borrowed only while its ownership mutex is held.
Worker allocation uses a captured format request; a generation-checked swap
publishes readiness and rejects stale work. History controls share the same
lease, and retired state is destroyed after the swap unlocks. This removes
the reviewed history/reconstruction lifetime race without libebur128 state
allocation on the processing thread.

Ordinary 100 ms reduction and 400 ms increase smoothing are retained. The
sample-peak headroom bound limits the *requested* gain; smoothing can exceed
that request transiently. The final existing limiter handles those transients.
This is not an independent hard true-peak guarantee, PCM-NaN sanitizer, speaker
excursion model or calibrated amplifier safety limit. Manual input/output
controls are separate from automatic makeup; prepared profiles keep both at
0 dB. The original firmware and hardware protection remain required.

## 1. Prepare a derived model bundle offline

Use the verified retained model bundle. The tool copies the exact impulse
bytes, preserves every non-AutoGain stage, inserts the independent leveler
immediately before the original final limiter and records parent manifest,
preset and mapping-report hashes. It does not install, activate, play or record.

```bash
python3 scripts/prepare_programme_loudness.py \
  --bundle ORIGINAL_MODEL_BUNDLE --output NEW_PROGRAMME_BUNDLE
```

Candidate defaults are -20 LUFS, Integrated reference, 15 seconds of maximum
history and a -50 LUFS silence threshold. The default maximum makeup derives
from the model's existing FIR normalization: 2.6475 dB for the retained ROG
music/balanced bundle and 10.1375 dB for the retained ThinkPad music/balanced
bundle, limited to the native 36 dB range. FIR normalization is an engineering
budget, not measured acoustic headroom. The default caps and target are
unqualified experiments and may not reach the target on every programme.

For an ordinary explicit adjustment, supply the target and maximum separately:

```bash
python3 scripts/prepare_programme_loudness.py \
  --bundle ORIGINAL_MODEL_BUNDLE --output NEW_ADJUSTED_BUNDLE \
  --target-lufs -20 --maximum-gain-db 6 \
  --history-seconds 15 --silence-threshold-lufs -50
```

The preparation API accepts finite targets from -100 to 0 LUFS, makeup from
0 to 36 dB, integer history from 6 to 3600 seconds and silence thresholds from
-100 to 0 LUFS. Invalid controls and existing destinations are refused without
replacing owner files. A failure after directory creation retains partial
output for explicit recovery; the tool does not delete a public pathname that
may have been replaced by another writer. Raising the cap above FIR normalization emits
`above_source_budget_advisory: true`; it remains an ordinary supported control,
with no qualification feature flag or hidden source-budget gate.

**How to read the output:** `prepared` and `not-installed` mean only an offline
bundle exists. `maximum_gain_db` is the automatic ceiling, not measured output
loudness. `offline-candidate-unqualified` preserves the existing evidence class.
Mapping entries for the old OEM leveler become `not-emitted`: the new generic
EBU control does not claim to implement Dolby's OEM processing or equivalence.
The original bundle, source reports and IR remain available for rollback.

## 2. Bind the bundle to a capable runtime and retain recovery

The new candidate package is `8.2.8+rog3`. Its runtime manifest declares
`programme_loudness_contract: bounded-programme-makeup-v1`. Kit preparation
and loading refuse a programme bundle against an older runtime because the
older preset loader ignores the cap. This is a format/capability contract;
it does not block ordinary gain adjustments.

```bash
python3 scripts/speaker_install.py prepare \
  --bundle NEW_PROGRAMME_BUNDLE --inventory FRESH_PRIVATE_INVENTORY.json \
  --runtime-manifest NEW_RUNTIME_ARTIFACT/runtime.json --output NEW_MODEL_KIT
```

Use a fresh read-only model/route inventory when preparing an actual laptop
kit. The synthetic graph-kit inventory is exclusively a test fixture. Before
any coordinated activation, retain the existing package, kit, original bundle,
preset/IR/autoload hashes, startup unit and private install/latency snapshots.
A programme kit intentionally changes the preset and autoload identity by
adding or enabling the independent leveler. Compare the impulse and every
non-AutoGain stage against the original bundle; their bytes/settings must
remain unchanged. The no-difference payload check in
[device-return autoload](SPEAKER_AUTOLOAD.md) applies to a runtime-only upgrade
using the same original bundle, rather than this derived programme bundle.

The [installation procedure](SPEAKER_INSTALL.md) remains the owner of file
snapshots and conflict-aware removal. Gain work does not replace stock
PipeWire/WirePlumber, amplifier firmware or existing hardware protection.

At preparation time, the ROG runs the accepted +rog2 runtime at 512 frames;
the ThinkPad's existing condition is recorded separately in status. The +rog3
candidate has not been installed. Final kept gain settings determine the
subsequent full-hour stability condition. Sonos remains last, after both
laptops have accepted everyday loudness and sound quality.

## 3. Review and run only the affected acceptance selection

The [corrected compiler/export receipt](../evidence/programme-loudness-reviewed-build-2026-10-13.json)
binds the reviewed 713-file source, compiled runtime, package and both newly
bound model kits. The [initial build receipt](../evidence/programme-loudness-build-2026-10-13.json)
and artifact remain retained and superseded. Compilation is distinct from
[selective acceptance](../evidence/programme-loudness-acceptance-2026-10-13.json).
All existing attributed/imported patch bytes remain unchanged; SHA256SUMS was
deliberately extended for the new additive patch and native header pin.

The accepted selection passed after independent source/artifact and final
fixture review. All 28 unit methods passed on their first execution, without
skips or repeats. Both graph selectors initially stopped before gain checks
because raw stdin lacked `pw-cat --raw`; those failures are retained. The
independently re-reviewed harness correction added explicit raw mode and
clean stopped-pipe shutdown. Only those two failed selectors repeated, and
both then passed all eight assertions. No production source or package
changed for the harness correction.

The commands below document that completed selection; do not repeat passing
methods or selectors without a change that invalidates their results:

```bash
# Use a durable scratch parent; these cases access no laptop audio.
TMPDIR=DURABLE_TEST_SCRATCH ROG_EASYEFFECTS_SOURCE=NEW_PATCHED_SOURCE \
  python3 scripts/validate_speaker_install.py --stage makeup
TMPDIR=DURABLE_TEST_SCRATCH ROG_EASYEFFECTS_SOURCE=NEW_PATCHED_SOURCE \
  python3 scripts/validate_speaker_install.py --stage analyser
TMPDIR=DURABLE_TEST_SCRATCH \
  python3 scripts/validate_speaker_install.py --stage programme
TMPDIR=DURABLE_TEST_SCRATCH ROG_EASYEFFECTS_GIT=PUBLIC_EASYEFFECTS_GIT \
  python3 scripts/validate_speaker_install.py --stage source
TMPDIR=DURABLE_TEST_SCRATCH \
  python3 scripts/validate_speaker_install.py --stage build \
  --test-id test_easyeffects_build.RuntimeBuildTests.test_podman_native_build_and_export_are_bounded_and_durable \
  --test-id test_easyeffects_build.RuntimeBuildTests.test_exported_programme_contract_mismatch_fails \
  --test-id test_easyeffects_build.RuntimeBuildTests.test_exported_old_package_version_fails
```

Eight actual-header cases cover requested and retained caps, silence reset,
invalid finite controls, louder-source reductions and smoothing. Four
threaded analyser methods exercise history changes during reconstruction,
stale-generation rejection, processing leases versus state replacement and
failed candidates. Twelve
profile methods cover both model defaults, preserved FIR/stage/parent hashes,
ordinary above-budget controls, invalid inputs, output ownership/replacement, tampering,
final-limiter requirements, old-runtime refusal and legacy bypass behavior.
The source-preparation method and selected export methods cover changed patch,
package and capability bindings. Previously passed, unchanged suites remain
inherited rather than repeated.

Prepare both real-model synthetic kits with the new runtime manifest, then
execute each selector once in the retained device-free image:

```bash
python3 scripts/prepare_speaker_graph_kit.py \
  --bundle NEW_PROGRAMME_BUNDLE --runtime-manifest NEW_RUNTIME_ARTIFACT/runtime.json \
  --device asus --output NEW_ASUS_GRAPH_KIT
python3 scripts/check_programme_loudness.py --case asus-programme \
  --kit NEW_ASUS_GRAPH_KIT --output NEW_ASUS_PRIVATE_GRAPH_RECEIPT
python3 scripts/check_programme_loudness.py --case lenovo-programme \
  --kit NEW_LENOVO_GRAPH_KIT --output NEW_LENOVO_PRIVATE_GRAPH_RECEIPT
```

Use `--device thinkpad` for the separate Lenovo graph kit. Each selector keeps
one PCM source and one runtime process alive through model-cap, lower-cap,
silence and louder-source transitions. It checks native cap consumption,
stereo gain, exact ordered active FL/FR links through every distinct plugin
instance, finite output and the final limiter. Controlled test presets use
-12 LUFS so model caps bind; the generated 0.025-amplitude quiet tone remains
above the normal silence gate after both FIRs. A separate 4.0-amplitude float
PCM stress transition forces the final limiter to engage in the device-free
graph. These synthetic levels are not a laptop playback programme. An acceptance-only library
shim injects actual ingestion errors inside the same two selectors and
requires native unity/reset and recovery; that shim is not part of the
production runtime.
All private captures, graphs and failures are retained. Retry only a failed
case or a case invalidated by a subsequent correction. The final repository
check follows the integrated factual documentation and selective acceptance.

## Evidence still required on the laptops

Synthetic output confirms implementation behavior in the isolated runtime.
It cannot establish the cause of the ROG's ordinary-movie report, comfortable
speaker loudness, acoustic safety, distortion or physical delay. A matched
stock/tuned programme observation and owner listening must evaluate the final
settings. Prepare playback first, cue immediately before starting, and do not
interpret absence of owner feedback as acceptance. Preserve speaker voicing,
startup, rollback and the negotiated buffer during the coordinated window.
