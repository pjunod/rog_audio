# Speaker build — prepare and inspect offline candidates

**Status:** importer and three candidates implemented; integration review/tests,
EasyEffects runtime validation and physical qualification pending ·
**Updated:** 2026-10-12 · **Executes:** speaker lane in
[implementation](AUDIO_IMPLEMENTATION.md).

Read [hardware](AUDIO_HARDWARE.md) for identity/recovery evidence and
[audio quality](AUDIO_QUALITY.md) for acoustic acceptance. This document is the
operator contract for [the preparation tool](../scripts/prepare_speaker_profile.py).
The [build receipt](../evidence/audio-speaker-build-2026-10-12.json) separates
previous synthetic checks from the actual isolated Linux conversions. No live
routing, package, service or amplifier control changed.

## 1. Bind inputs before conversion

The implementation accepts the inspected Realtek `10ec0285`, subsystem
`10431c63`, two CS35L56 amps and speaker ID 0. The supplied inventory receipt
is trusted input, not a fresh hardware probe. By default the tool uses
[the public inventory](../evidence/audio-inventory-2026-10-12.json).
`--inventory` can supply another receipt, including synthetic tests; it still
must declare the supported identity. No owner-authorization switch is needed.

The XML/INF names, sizes and SHA256 hashes must match that receipt. The INF
must contain the exact HDAUDIO/INTELAUDIO ID in a DeviceExtensions section,
including the optional `FUNC_01` prefix. Its selected install section must
copy the XML and SourceDisksFiles must list it. Renamed source-file copies are
unsupported. The filename/hashes identify bytes, not signed authenticity.

The endpoint explicitly selects `internal_speaker`, mode `normal`, two front
channels and 48 kHz. Profile choice is required. Invalid numeric fields,
nested/duplicate endpoints/profiles and unknown enabled PEQ shapes fail.
The XML is bounded to 2 MiB, 10,000 nodes, 32 levels and 512 children per
node. DTDs, entities and external references fail. File opens reject symlinks,
nonregular files and FIFOs; no-follow directory descriptors prevent ancestor
symlink races. Only pinned converter Python bytes enter its import snapshot.

Use `--duplicate-xml DUPLICATE` on inspect/build to demand byte identity with
another recovered copy. Disagreement fails. The coordinating lane recorded a
[cross-package comparison](../evidence/asus-tuning-duplicate-2026-10-12.json):
the eSupport package and published DriverStore XML are byte-identical at
86,807 bytes, SHA256
`d6728635859309e0fecf2bdc32844ac15a32f67261e5aae8ae2e91ab01580149`.
This uses the same recovery image and 7-Zip reader; it is neither an
independent-reader check nor authentication. The inherited reference-count
warning remains. The coordinator's read-only mount was unmounted afterward;
this speaker implementation lane did not access the recovery partition.

The owner authorised publication of the recovered ASUS XML/INF in `rog_audio`.
Integration owns `profiles/asus/gu605mz/`, original notices and hash provenance;
these inputs can be used directly from that repository. Raw diagnostics and
connection credentials remain excluded. Generated candidate bundles are kept
in ignored output storage until runtime/physical qualification.

## 2. Prepare a new bundle

Commands below are implemented. Replace uppercase output/source placeholders;
the XML/INF paths refer to the integration-owned source files. Existing output
and report paths are never overwritten. There is no activation command.

```bash
# Read identity and discover profile names; writes a new metadata report.
python3 scripts/prepare_speaker_profile.py inspect \
  --xml profiles/asus/gu605mz/DEV_0285_SUBSYS_10431C63_PCI_SUBSYS_1C631043.xml \
  --inf profiles/asus/gu605mz/dax3_ext_rtk.inf --report REPORT

# Generate the explicit music/balanced candidate from pinned converter source.
python3 scripts/prepare_speaker_profile.py build \
  --xml profiles/asus/gu605mz/DEV_0285_SUBSYS_10431C63_PCI_SUBSYS_1C631043.xml \
  --inf profiles/asus/gu605mz/dax3_ext_rtk.inf \
  --codec 10ec0285 --subsystem 10431c63 \
  --endpoint internal_speaker --mode normal --profile music \
  --voicing balanced --converter PINNED_CONVERTER --output BUNDLE

# Verify hashes, references, stages and the stereo float-WAV format.
python3 scripts/prepare_speaker_profile.py verify --bundle BUNDLE
```

`--voicing` accepts balanced · detailed · warm, default balanced. The profile
`off` uses its XML enable bits; it does not promise an empty preset. The final
sample limiter remains present. Generate music, dynamic and off separately.

**How to read it:** exit 0 means the offline operation succeeded; 2 means
invalid input/identity/schema/filesystem operation; 3 means unsupported
capability or missing dependency. Output uses allowlisted status and manifest
hashes, never arbitrary paths/exceptions or coefficients. `activation_state`
is always `not-installed`, qualification `offline-candidate-unqualified`.
Verification checks integrity and the bounded bundle contract; it does not
externally authenticate a self-supplied manifest.

| Bundle file | Purpose |
|---|---|
| `manifest.json` | Schema, converter pin, versions, input hashes, hardware/selection, output hashes and activation state |
| `preset.json` | EasyEffects output preset referencing its IR stem |
| `irs/speaker-HASH.irs` | 4096-frame stereo float32 RIFF/WAV, 48 kHz; stem follows sample-content hash |
| `field-mapping.json` | Selected profile leaves, source attributes, units, output stages, approximations/unsupported fields and FIR-only signal checks |

Unknown/omitted fields are visible; `complete_equivalence` is always false.
Dynamics fields report `disabled` when the source enable bit is off and no
stage is emitted, or `not-emitted` when no corresponding plugin is present.
Only an actual emitted, bypassed plugin is labelled `approximation-bypassed`.
Absent stages have a null output reference. Verification reconciles the field
references and stage inventory with the actual preset.
Verification rejects edited/missing/extra files, escaping references, wrong
kernel names, nonfinite samples, wrong layouts and positive stage input/output
gain. Approximate dynamics must remain bypassed. Input bytes are bound at
preparation time; verify does not reopen XML/INF.

## 3. Understand what the candidate maps

The external converter is MIT licensed by Antoine Cellerier. Its commit and
all imported runtime Python file hashes are in
[speaker source pins](../evidence/audio-speaker-sources.json). The wrapper
snapshots verified code and calls `lib.dax.parse`, `lib.preset.fir`,
`lib.preset.bands` and `lib.preset.plugins` directly. It never calls upstream
CLIs, discovery, autoload, reload, stale-IR cleanup, audio clients or services.

The audit found EasyEffects reload/autoload, hardware/session probes and
stale-file scans/removal in upstream CLI paths. The PipeWire CLI can install
configuration and restart PipeWire by default; dry-run can unpack archives.
These paths are excluded from preparation.

| Stage | Candidate behaviour | Evidence limit |
|---|---|---|
| Audio optimizer | L/R divided by 16 dB; disabled optimizer gives zero correction | Static curve only; no acoustic calibration |
| IEQ | Selected curve /16 dB, weighted by amount/100; disabled IEQ contributes zero | Static approximation, no media steering; absent amount explicitly uses upstream 10% default |
| FIR | Minimum-phase, 4096 frames, shared louder-peak reference | Positive peaks attenuated; all-cut curves never boosted; runtime latency unmeasured |
| Speaker PEQ | Supported filters preserved; asymmetric empty slots receive neutral zero-gain bells; positive gains summed per channel for attenuation | Headroom estimate, not full cascade/sample/protection proof |
| Dialog/leveler/MBC/regulator | Available plugin approximations emitted bypassed | No dynamics equivalence or qualification |
| Final limiter | -1 dB sample threshold, 1 ms lookahead, no gain boost | Not thermal/excursion protection or total physical latency |
| Loudness restoration/virtual bass | Suppressed | No volmax, gain restoration, bass synthesis or widening |
| Other OEM fields | Listed unsupported | Includes vendor coefficients, volume models, CP processing and steering; no host Atmos |

Upstream's independent channel normalization can erase an intended stereo
level difference or boost an all-cut curve. This wrapper uses one nonnegative
attenuation to preserve balance without restoring gain. Synthetic regressions
exercise both cases and the Q4/Q15 compressor units and band-index sentinel.

Impulse/sweep peaks, shape error, samples over full scale, frequency peak and
L1-norm bound describe the **FIR only**. They do not execute the EasyEffects
EQ/limiter or model physical drivers. The runtime loader and plugin availability
have not been validated. Stock amp firmware/calibration/gain remain unchanged.

## 4. Reproduce the isolated Linux build

[The Dockerfile](../scripts/speaker-build.Dockerfile) pins the base-image digest
and dependencies. The completed conversion used Linux x86_64, Python 3.12.15,
NumPy 2.2.6 and SciPy 1.15.3. Dependencies were installed only in the disposable
image. Runtime had no network, a read-only filesystem, all capabilities dropped
and no-new-privileges. Only explicit source/input/output mounts and temporary
storage were present. Never mount `/dev/snd`, desktop sockets or owner config.

[Focused tests](../tests/test_prepare_speaker_profile.py) construct invented
values; no OEM discovery occurs. An explicit converter environment variable
selects the DSP test dependency; without it those tests report skips.

The following recipe works in a local clone or a GitHub Linux runner. It uses
an empty Docker build context so ignored raw/private files are not sent to the
builder. Runtime mounts only this audio repository, the pinned converter and
an explicit output directory. The source snapshot verifies converter file
hashes again at build time. Choose a new empty `build/speaker-validation`
directory for each validation batch because the bundle tool refuses overwrite.

```bash
# Fetch only the pinned public converter; keep its licence in the checkout.
git clone https://github.com/antoinecellerier/speaker-tuning-to-easyeffects \
  build/speaker-converter
git -C build/speaker-converter checkout 430e3a501e21bf8fdb615b133d2e8130b17973c1
mkdir -p build/speaker-validation

# Empty build context; packages are installed inside the disposable image.
docker build --tag rog-audio-speaker:local - < scripts/speaker-build.Dockerfile

# Synthetic tests once, then actual repository ASUS conversion/verification.
docker run --rm --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --user "$(id -u):$(id -g)" \
  --tmpfs /tmp:rw,nosuid,nodev,size=256m \
  --mount "type=bind,src=$(pwd),dst=/repo,readonly" \
  --mount "type=bind,src=$(pwd)/build/speaker-converter,dst=/converter,readonly" \
  --mount "type=bind,src=$(pwd)/build/speaker-validation,dst=/output" \
  --env ROG_SPEAKER_CONVERTER=/converter rog-audio-speaker:local sh -ec '
    python -m unittest discover -s tests -p test_prepare_speaker_profile.py -v
    for profile in music dynamic off; do
      python scripts/prepare_speaker_profile.py build \
        --xml profiles/asus/gu605mz/DEV_0285_SUBSYS_10431C63_PCI_SUBSYS_1C631043.xml \
        --inf profiles/asus/gu605mz/dax3_ext_rtk.inf \
        --codec 10ec0285 --subsystem 10431c63 \
        --endpoint internal_speaker --mode normal --profile "$profile" \
        --converter /converter --output "/output/$profile"
      python scripts/prepare_speaker_profile.py verify --bundle "/output/$profile"
    done
  '
```

For a failed wrapper check, keep the same container mounts and run only its
reported ID, for example `PYTHONPATH=tests python -m unittest -v
test_prepare_speaker_profile.DSPPreparationTest.test_stereo_units_and_headroom`.
Do not rerun unrelated passing tests. A failed conversion leaves no qualified
bundle; correct its input/capability cause and retry that selected profile in
a new directory.

```bash
# Integration unit lane; defer until the single batch review is complete.
ROG_SPEAKER_CONVERTER=PINNED_CONVERTER \
  python3 -m unittest discover -s tests -p test_prepare_speaker_profile.py -v

# Relevant upstream lane in a source-only isolated container.
pytest -n 0 -m "not live_machine" --ignore=tests/corpus -p no:cacheprovider \
  tests/test_fir_math.py tests/test_biquads.py tests/test_decoders.py \
  tests/test_golden_preset.py
```

Earlier revisions passed 39 wrapper tests and 145 upstream synthetic tests.
Those receipts are historical, not a pass on the latest code. Later edits and
new regressions await the parent's single integration review/test lane per the
owner's revised workflow. Music, dynamic and off converted and verified in
Linux; their hashes/stages are in the receipt and generated bytes remain ignored.

## 5. Hand off activation and physical acceptance

This tool does not install/remove config or set routing/autoload. No deployable
routing package is claimed. First validate the loader/plugins in isolated
EasyEffects, retain the recorded cross-package comparison and unresolved
recovery integrity limitation, and prepare exact snapshot,
install and removal commands against the chosen EasyEffects version. Those
commands belong to integration; copying into an unknown live XDG path cannot
establish correct per-device activation.

The later procedure must retain the hardware sink as default, scope correction
to hardware identity and the actual internal analog speaker port, bypass
headphones/HDMI, handle restart/resume, and restore the previous configuration
on removal. Coordinate every restart and audible test. Transient node IDs or
every stereo sink are not suitable selection rules.

Physical acceptance requires calibrated microphone/level-matched response and
distortion captures, listening preference, channel/driver operation, physical
latency, calls/hotplug, CPU/power and resume results. Neither a bundle nor amp
calibration messages supplies those measurements. Sonos Arc/eARC remains last.
