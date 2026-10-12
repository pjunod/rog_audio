# Lenovo speaker profile — exact first-generation ThinkPad preparation

**Status:** original source published in the candidate branch; three inactive
Linux bundles built; integration review/unit tests and physical acceptance
pending · **Updated:** 2026-10-12.

Companion to [ThinkPad inventory](THINKPAD_AUDIO.md) (what this unit runs) and
[speaker preparation](AUDIO_SPEAKER_BUILD.md) (the shared offline API). This is
the Lenovo-specific source/identity contract. It does not change routing,
services, amplifiers, boot state or playback. No ASUS coefficients are used.

## Exact codec and PCI identity choose the Lenovo source

The supported unit is Lenovo `20MF000DUS`, ThinkPad X1 Extreme Gen 1, with
Realtek ALC285 `10ec0285` and codec subsystem `17aa2276`. The Intel HDA
controller is `8086:a348`, PCI subsystem `17aa:2267`. Those observations are
in [the public inventory](../evidence/thinkpad-audio-inventory-2026-10-12.json).
The importer checks that semantic identity, including first generation and
machine type `20MF`; it records the exact receipt hash actually supplied.

The source XML filename encodes codec subsystem `17AA2276` and PCI subsystem
`226717AA`. These are different subsystem values; swapping the codec ID into
the PCI field would select the wrong contract. The original Dolby INF matches
both HDAUDIO and INTELAUDIO codec/subsystem IDs and explicitly copies the XML.
The observed Linux HDA route selects the HDAUDIO XML. An alternate Intel-audio
XML was found but is not selected merely because the processor is Intel.

The amplifier/protection implementation is unknown in the bounded inventory.
The bundle records that uncertainty. It does not substitute the ASUS CS35L56
identity, firmware, calibration or safety claims. The shared ASUS contract and
its existing bundle hardware fields are preserved.

## The source came from a Lenovo download

[Original files](../profiles/lenovo/x1-extreme-gen1/README.md) comprise the
complete HDA speaker XML, matching Dolby INF and official Lenovo README.
[Source manifest](../profiles/lenovo/x1-extreme-gen1/manifest.json) and
[download/extraction receipt](../evidence/lenovo-audio-package-2026-10-12.json)
record hashes, notices, model support, package versions and cleanup.

Lenovo DS504906 supplies `n2ea118w.exe`, advertised Realtek 6.0.9354.1 for
20MF/20MG. Download SHA256 matched the vendor-published checksum. Innoextract
unpacked it in a disposable Linux container; no Windows installer ran.
The included Dolby extension has its own version, 5.914.455.29, dated
2020-09-13. These versions describe the downloaded package, not installed Linux
software or this laptop's WinRE contents.

The [recovery receipt](../evidence/thinkpad-recovery-status-2026-10-12.json)
records a separate, bounded read-only inspection after the owner fixed sudo
policy. Its 1.1 GiB NTFS partition contains a single WinRE image. The image's
25,538 indexed path entries had no exact `17aa2276` or known speaker XML/INF
filename match. Six Dolby-named Intel DSP firmware paths were not extracted
and do not establish speaker tuning or protection. The reader reported an
incorrect-reference-count warning; integrity/authenticity remain unverified.
No full image copy or payload extraction was made; the partition was verified
unmounted and the temporary reader removed. Filename findings do not cover
every payload's contents or other partitions. No corresponding recovery
source was found for a byte comparison with the downloaded XML/INF.

## Run the unchanged explicit preparation interface

Use this repository's published inventory and source paths. Generate into a
new ignored output directory; existing output is refused. The source manifest
binds the original XML/INF hashes independently of hardware inventory.

```bash
# Inspect source/identity metadata without conversion or session access.
python3 scripts/prepare_speaker_profile.py inspect \
  --xml profiles/lenovo/x1-extreme-gen1/HDAUDIO_DEV_0285_SUBSYS_17AA2276_PCI_SUBSYS_226717AA.xml \
  --inf profiles/lenovo/x1-extreme-gen1/dax3_ext_dolbyatmos.inf \
  --inventory evidence/thinkpad-audio-inventory-2026-10-12.json \
  --report PRIVATE_REPORT

# Prepare the exact Lenovo music candidate using pinned converter source.
python3 scripts/prepare_speaker_profile.py build \
  --xml profiles/lenovo/x1-extreme-gen1/HDAUDIO_DEV_0285_SUBSYS_17AA2276_PCI_SUBSYS_226717AA.xml \
  --inf profiles/lenovo/x1-extreme-gen1/dax3_ext_dolbyatmos.inf \
  --inventory evidence/thinkpad-audio-inventory-2026-10-12.json \
  --codec 10ec0285 --subsystem 17aa2276 \
  --endpoint internal_speaker --mode normal --profile music \
  --converter PINNED_CONVERTER --output PRIVATE_BUNDLE

# Verify manifest hashes, references, stages and float-WAV layout.
python3 scripts/prepare_speaker_profile.py verify --bundle PRIVATE_BUNDLE
```

**How to read it:** a successful build means an inactive offline bundle was
prepared and verified. The manifest records `activation_state: not-installed`,
`qualification: offline-candidate-unqualified`, hardware inventory hash and
`source_manifest_sha256`. The Lenovo hardware record includes machine type,
PCI subsystem and `amplifier_identification: unknown`. It is an input-evidence
statement, not a fresh probe during conversion. A registry-supported codec
alone cannot relabel input from a different inventory/device.

The default inventory remains ASUS for compatibility; supply the explicit
ThinkPad inventory for Lenovo. Both devices require the exact profile choice,
internal-speaker endpoint and normal mode. No authorization switch or live
configuration exists in the preparation tool.

## Legacy schema differences preserve units and channel balance

| Field/stage | Lenovo source | Interpretation |
|---|---|---|
| Endpoint layout | `ch_count=2` instead of modern front/side/height counts | Stereo only; contradictory extra channel declarations fail |
| Audio optimizer | `gain_l`/`gain_r` instead of `ch_00`/`ch_01` | Retained upstream legacy channel rules; raw values /16 dB |
| IEQ | Same 20-band curve and amount fields | /16 dB curve, amount/100 static weight; enable bit respected |
| FIR | Shared upstream minimum-phase algorithm | 4096 stereo float32 frames, 48 kHz; common nonnegative attenuation |
| Speaker PEQ/MBC | Absent in the selected legacy source | No corresponding preset stages invented |
| Dynamics/media processing | Selected CP fields and other vendor controls | Available approximations bypassed; absent/disabled and unsupported stages reported separately |
| Other vendor/headphone processing | Generic headphone and operator XMLs present in full download | Research references only; not applied to internal speakers |
| Fortemedia | Exact-ID files target capture/microphone endpoints | Excluded from speaker correction |

The complete source file is retained, including unsupported fields. The field
report describes every selected leaf and reconciles output references with
actual preset stages; `complete_equivalence` remains false. An absent PEQ block
is not permission to synthesize bass, and a Windows format label is not host
Atmos rendering. Preserve stock routing and driver protection.

## Linux build receipts are separate from the final test lane

[The build receipt](../evidence/lenovo-speaker-build-2026-10-12.json) binds the
executed wrapper/source hashes and exact public inventory to music, dynamic
and off outcomes. The shared digest-pinned Python container has no sound
hardware, network during conversion, desktop sockets or owner configuration.
Python compilation and real source conversion ran; unit tests did not.

The first three conversions failed because a shared converter checkout had
been cleaned up. A fresh owned checkout at the identical pinned revision
restored the missing dependency; only those failed conversions were retried.
There was no source/DSP workaround or dependency-pin change.

Synthetic Lenovo regressions cover model/codec/PCI matching, source pinning,
legacy channel declarations, gain units, stereo relationship and cross-device
labelling rejection. They are added to the shared focused module but await
independent batch review before execution. Use individual unittest IDs for
failed-case retries; do not repeat unrelated passing first-batch checks.

## Runtime routing and physical results remain open

The shared tool prepares files only. It does not load a profile, configure
headphone/HDMI bypass or implement a system-wide renderer. The next installation
batch must define actual internal-speaker route matching and reversible
installation/removal. Coordinate every service/routing change and audible test.

EasyEffects loader/plugin execution, acoustic response/distortion, subjective
level-matched listening, physical latency, protection behaviour, hotplug,
calls and resume remain unmeasured on this ThinkPad. No Mac comparison or
Sonos acceptance is implied; Sonos Arc/eARC remains last.
