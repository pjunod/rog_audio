# ThinkPad audio — first-generation X1 Extreme evidence and build contract

**Inspected:** 2026-10-12 · **State:** read-only inventory and bounded WinRE
index complete; model-specific v0.2.0 tuning active with login startup enabled.

Companion to [ASUS hardware](AUDIO_HARDWARE.md),
[implementation](AUDIO_IMPLEMENTATION.md) and [status](STATUS.md). The
[ThinkPad receipt](../evidence/thinkpad-audio-inventory-2026-10-12.json)
records observed hardware and separates vendor specifications from Linux
observations. `lab6` is a neutral evidence label, not an SSH alias.

## Hardware requires a separate speaker profile

| Item | Observed state |
|---|---|
| Model | Lenovo `20MF000DUS`, ThinkPad X1 Extreme |
| Generation | First generation, from Lenovo's type `20MF` mapping |
| Kernel | `7.3.0-9-generic` |
| Linux codec | Realtek ALC285, vendor `10ec0285`, subsystem `17aa2276` |
| Intel audio PCI | `8086:a348`, subsystem `17aa:2267` |
| HDMI audio | NVIDIA `10de:0fb9`; separate from the speaker path |
| Amplifiers | No matching CS35/TAS/MAX98 driver identified in bounded logs/bus inspection; physical design unknown |
| Mixer | Speaker switches on, headphone switches off, Auto-Mute Disabled |
| Route | ACP analog stereo with internal microphone; `analog-output-speaker` |

[Lenovo's product page](https://pcsupport.lenovo.com/us/en/products/laptops-and-netbooks/thinkpad-x-series-laptops/thinkpad-x1-extreme/20mf/downloads)
identifies the generation. Its
[specification](https://psref.lenovo.com/syspool/Sys/PDF/ThinkPad/ThinkPad_X1_Extreme/ThinkPad_X1_Extreme_Spec.PDF)
names ALC3286, two 2 W speakers, Dolby Audio Premium and Dolby Atmos headphone.
Those are manufacturer claims. The Linux codec name is an observation;
ALC3286 and ALC285 are not asserted equivalent without matching driver evidence.
Headphone Atmos branding does not establish Linux object rendering or tuned
internal-speaker playback.

The ASUS and Lenovo codec vendor IDs match, but subsystem and acoustic design
differ. Do not reuse ASUS EQ, amplifier assumptions or speaker protection claims.
An absent driver name in a bounded capture does not prove absent hardware.

## The idle graph matches the ASUS software baseline

PipeWire is `1.6.8-1ubuntu4` and WirePlumber `0.5.17-1ubuntu1`. The default
rate is 48 kHz and quantum 1024 frames, with limits 32–2048 and no forced
rate/quantum. Four data loops report SCHED_RR priority 20. The 21.333 ms graph
period is not measured physical latency.

The sink and source were suspended, with no active stream or Audio/Filter
nodes. No user or `/etc` PipeWire/WirePlumber overrides were found in the
inspected scope. `pactl` was unavailable; `pw-dump`, `wpctl` and ALSA supplied
the observations. The ACP property is true; an explicit UCM enable property
was absent. No packages, mixer controls, routing or services changed.

Preserve Auto-Mute Disabled as the observed baseline. Headphone bypass needs
separate validation during the coordinated activation window; silently
changing this control would erase useful baseline evidence.

## Recovery access and official-driver fallback

The [recovery receipt](../evidence/thinkpad-recovery-status-2026-10-12.json)
records an unmounted 1.1 GiB NTFS partition with the
Microsoft recovery partition type. Earlier sudo/UDisks authorization failures
are retained as historical evidence. After the owner fixed sudo policy, the
existing NTFS helper mounted the partition with verified
`ro,nodev,nosuid,noexec` options. The partition was unmounted after inspection;
the Windows OS partition was not unlocked or mounted.

The partition contains `Winre.wim`, `boot.sdi` and `ReAgent.xml`, with byte
hashes in the receipt. A temporary copy of an existing 7-Zip reader indexed
one Windows Recovery Environment image (WindowsPE, build 22621) with 25,538
path entries. No exact `17aa2276` or known Lenovo/Dolby speaker XML/INF path
matched the bounded filename search. Six Dolby-named Intel DSP firmware paths
were listed but not extracted; their names do not establish speaker tuning,
Atmos object rendering or amplifier protection. The reader reported an
incorrect-reference-count warning; image integrity and catalogue authenticity
were not verified.

No full WIM copy or recovery payload extraction was made. The temporary reader
and mount directories were removed. No larger dedicated factory-image
partition was identified in the layout, but this search does not establish
the absence of OEM assets elsewhere or in unsearched payload contents.

The
[official Lenovo audio package](https://pcsupport.lenovo.com/us/en/products/laptops-and-netbooks/thinkpad-x-series-laptops/thinkpad-x1-extreme/downloads/ds504906)
supplies the separately inspected speaker source. No matching recovery file
was available for a byte comparison. Downloaded package evidence stays
distinct from recovery observations; no Windows installer ran for extraction.

## Model-specific implementation and acceptance

1. Locate an INF binding `VEN_10EC&DEV_0285&SUBSYS_17AA2276` to the actual
   speaker APO/profile. Preserve original bytes, notices and package hashes;
   distinguish speaker endpoints from headphone processing.
2. Trace the selected profile's units and enabled stages. Extend the importer
   only if the Lenovo format and hardware contract are supported; a shared
   codec name does not satisfy that contract.
3. Build an inactive candidate with exact model binding and documented
   unsupported fields. Review the completed changes adversarially, fix them,
   then run each relevant test once; retry only failed/invalidated tests.
4. Validate the isolated runtime and install/remove behavior, including
   headphone/HDMI bypass and preservation of the prior routing/mixer state.
5. Coordinate live activation and compare sound/latency separately from ASUS.
   Keep stock protection intact; measure response, distortion, latency,
   power, hotplug and resume before claiming improvement.

The ThinkPad kit is installed and active after the authorized deployment.
Its actual preset, IR, plugins and physical output passed live checks, and
login startup is enabled with durable private rollback. See the
[deployment receipt](../evidence/thinkpad-speaker-deployment-2026-10-12.json)
and [installation](SPEAKER_INSTALL.md). The shared units and isolated graph
case remain inherited acceptance. Owner listening and actual post-reboot
startup are pending observation. Live hotplug/resume, acoustic quality,
protection behaviour and latency still need
physical qualification.
