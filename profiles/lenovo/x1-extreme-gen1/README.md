# Lenovo X1 Extreme Gen 1 — original speaker-tuning source

These are complete, unmodified selected files from Lenovo's public
[Realtek Audio package DS504906](https://pcsupport.lenovo.com/us/en/products/laptops-and-netbooks/thinkpad-x-series-laptops/thinkpad-x1-extreme/downloads/ds504906),
`n2ea118w.exe`, advertised Realtek version 6.0.9354.1. They were downloaded
and unpacked offline with Innoextract; the Windows installer was never run.
The laptop owner requested equivalent Lenovo support and directly available
OEM inputs. [The manifest](manifest.json) records source URLs, hashes, original
notices and limits; [the source receipt](../../../evidence/lenovo-audio-package-2026-10-12.json)
records extraction and cleanup.

| File | Role |
|---|---|
| `HDAUDIO_DEV_0285_SUBSYS_17AA2276_PCI_SUBSYS_226717AA.xml` | DAX speaker source matching observed codec `10ec0285`/subsystem `17aa2276` and PCI subsystem `17aa2267` |
| `dax3_ext_dolbyatmos.inf` | Original Dolby extension association, driver 5.914.455.29; copyright notice retained |
| `n2ea118w.txt` | Original Lenovo model support, versions, instructions and trademark notices |

The selected XML uses the legacy DAX stereo schema (`ch_count=2`,
`gain_l`/`gain_r`) and contains internal-speaker/normal tuning at 48 kHz,
with dynamic, movie, music, game, voice, three personal profiles and off.
The INF lists exact HDAUDIO and INTELAUDIO matches. Its full copy list refers
to other package files intentionally outside this narrow source set; this is
not a Windows driver installer. The Intel-audio XML and generic headphone and
operator references were retained separately during research, not selected as
this observed HDA speaker's input. Fortemedia files in the package target
microphone/capture endpoints; they are not substituted as speaker correction.

The original vendor terms remain separate from repository-owned code. A
matching file is not a licence grant, Dolby certification, an Atmos renderer,
amplifier protection implementation or acoustic calibration. This source is a
vendor download, not a recovered factory-image receipt. The separate
[WinRE inspection](../../../evidence/thinkpad-recovery-status-2026-10-12.json)
found no exact matching speaker XML/INF path in its bounded filename search;
no recovery/download byte comparison was possible. The recovery partition is
unmounted, and no recovery payloads were extracted.
Use [Lenovo preparation](../../../docs/LENOVO_SPEAKER_PROFILE.md) for the offline
contract and its remaining physical limits.
