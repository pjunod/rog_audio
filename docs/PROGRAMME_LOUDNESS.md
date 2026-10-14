# Programme loudness — adjustable makeup with original speaker voicing

**Status:** corrected native source/artifacts reviewed; 28 affected units and
both isolated model graphs passed; both current +rog3 deployments/short checks passed, both final software hours passed without added errors and both current generated demos accepted · **Updated:** 2026-10-14.

[The current live settings](../evidence/programme-service-autoload-and-current-settings-v2-2026-10-13.json)
are ROG −20 LUFS/cap 2.6475 dB and ThinkPad −16 LUFS/cap 14.1375 dB,
with original voicing/limiter preserved and separate reviewed helper/unit
backports. Both short checks and native save/autoload passed; both [final software hours](STATUS.md#final-kept-settings-software-hours--2026-10-14)
passed without added errors. Physical recording is deferred to another
coordinated window. [ROG](../evidence/rog-programme-owner-listening-2026-10-13.json)
and [ThinkPad](../evidence/thinkpad-target16-programme-owner-listening-2026-10-13.json)
current demos are accepted; that is not acoustic/all-media qualification.
The public preparer defaults/release assets are
unchanged. ROG's cap equals its 2.6475 dB inverse-FIR source budget;
ThinkPad's cap adds 4 dB above its 10.1375 dB budget, retaining the ordinary
above-source-budget advisory. These are not measured speaker or amplifier
headroom limits.

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

The published programme package is `8.2.8+rog3`; the packaging-only service
follow-up emits `8.2.8+rog4` with the same native ELF/source and an added
[stop helper](SPEAKER_SERVICE.md). Its independent review/acceptance remains
separate. The programme runtime manifest declares
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
candidate had not been installed at preparation. A fresh full-hour software
check may run on the reviewed provisional -20 LUFS/model-cap defaults before
owner listening feedback. Its receipt binds that exact installed condition;
passing software stability does not accept everyday loudness, and listening
acceptance does not transfer across changed settings. Sonos remains last, after both
laptops have accepted everyday loudness and sound quality.

## Provisional ThinkPad adjustment after the first programme demo

The [first +rog3 programme demo](../evidence/thinkpad-programme-owner-listening-2026-10-13.json)
used −20 LUFS and the original 10.1375 dB cap. Owner feedback was “Clear but
still too quiet.” This does not accept everyday loudness.

[Three isolated digital comparisons](../evidence/thinkpad-programme-target-comparison-2026-10-13.json)
then ran the accepted native binary on the same 45-second generated clip and
original ThinkPad IR, with two seconds of capture-alignment padding at each
end. Both ordered channels, all non-AutoGain stages and the final −1 dB
limiter were unchanged; no laptop devices or live settings were accessed.

| Target LUFS | Makeup cap dB | Measured integrated LUFS | Measured digital peak dBFS |
|---|---:|---:|---:|
| −20 | 10.1375 | −21.8 | −9.9 |
| −16 | 10.1375 | −19.8 | −5.9 |
| −16 | 14.1375 | −17.9 | −5.9 |

The last case added 3.9 LU overall relative to the first without raising
this clip's loudest peak above the middle case. It was selected for a
provisional ThinkPad listening trial, with live adjustment and owner
acceptance still pending at the diagnostic receipt. It does not change the
public preparer's defaults or the v0.2.2 release assets. Any new software hour
must bind the actually installed settings.

The initial cap compensates common FIR normalization attenuation; it is not
an OEM loudness ceiling or measured speaker headroom. These digital results
do not establish acoustic loudness, speaker safety, calibration or ordinary
media quality. No audition or gain/limiter usage-counter capture occurred in
the isolated comparison, and no unit suites or native builds were repeated.

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
