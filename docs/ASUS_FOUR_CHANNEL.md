# ASUS four-channel profile — why stereo preserves the accepted speaker path

**Investigated:** 2026-10-13 · **Decision:** use the authorized stereo fallback
for the latency comparison; four-channel routing requires further implementation.

Companion to [hardware](AUDIO_HARDWARE.md) (codec and OEM sources),
[installation](SPEAKER_INSTALL.md) (the accepted stereo runtime and rollback),
and [latency comparison](LATENCY_COMPARISON.md) (preserving tuning during trials).
This document distinguishes the source contract, read-only live routing evidence
and the limits of those observations.

## The OEM input describes two logical outputs

The unchanged [GU605MZ XML](../profiles/asus/gu605mz/README.md) selects
`internal_speaker`, `normal`, 48 kHz, with `total_count="2"`, `front_count="2"`
and `output-count` 2. Left uses `output_route="0"`; right uses
`output_route="1"`. The converted candidate and its IR remain stereo FL/FR.
Those fields provide no independently tuned RL/RR outputs and no basis for
duplicating the EQ into a four-channel preset.

The pinned [kernel source at
`058f2c4b7533365d99d4868fb29a68a5b62ecf5a`](https://github.com/torvalds/linux/blob/058f2c4b7533365d99d4868fb29a68a5b62ecf5a/sound/hda/codecs/realtek/alc269.c)
matches subsystem `1043:1c63` to
`ALC285_FIXUP_ASUS_GU605_SPI_SPEAKER2_TO_DAC1`. Its
`alc285_fixup_speaker2_to_dac1` forces bass-speaker pin `0x17` to DAC `0x02`
to share the main speaker DAC. This is source evidence about the model fixup;
the active codec observations below establish the inspected route separately.

## The four-channel PCM puts the speaker pair at channels 2/3

The owner selected ACP `analog-surround-40` on lab5. The fresh physical sink
exposed four playback inputs, while the previously installed kit named the
old `analog-stereo` node. That mismatch prevents a claim that the existing
candidate was processing the newly selected sink.

Read-only active graph and codec observations supplied by the deployment
session on 2026-10-13 established this mapping. The
[sanitized baseline receipt](../evidence/linux-audio-latency-baselines-2026-10-13.json)
binds these observations to the retained private captures:

| Observation | Active four-channel value | Meaning |
|---|---|---|
| Playback port map | FL 0 · FR 1 · RL 2 · RR 3 | PipeWire port names and local IDs |
| Speaker DAC `0x02` | Stream 1, channel 2 | Speaker PCM pair begins at channels 2/3 |
| Headphone DAC `0x03` | Stream 1, channel 0 | Headphone PCM pair begins at channels 0/1 |
| Main speaker pin `0x14` | DAC `0x02` | Main speaker path shares that DAC |
| Bass speaker pin `0x17` | Selected DAC `0x02`; overridden connection list contains `0x02` | Bass speaker path shares that DAC |

The earlier private baseline also showed both speaker pins connected to
`0x02`. The active stream/channel values above add the PCM assignment that
the baseline connection list alone could not establish. Raw graphs, codec
captures, host details and rollback state remain private.

FL/FR and RL/RR are logical PCM labels in this profile. They do not establish
four independent acoustic speaker paths. These observations identify a
software routing relationship, not physical audibility, calibrated response,
distortion, protection performance or latency.

## Rebinding the existing kit would feed the wrong PCM pair

The [kit preparer](../scripts/speaker_install.py) already accepts a freshly
observed exact ALSA speaker node and route. An inactive kit can therefore
name `analog-surround-40` without changing the preset, IR or installed runtime.
That proves preparation support only; it does not solve output-channel mapping.

In the delivered v0.2.0 corresponding source, `pw_link_manager.cpp` uses
`find_matching_ports` for the final output-level-to-device links. It recognizes
FL · FR · MONO · PROBE_FL · PROBE_FR. Seeing RL/RR makes ordinary links fall
back to matching local `port_id`. The stereo output-level ports 0/1 therefore
link to the four-channel device inputs 0/1, labeled FL/FR. In the inspected
active codec map, those PCM channels belong to headphone DAC `0x03`, while
the speaker DAC consumes channels 2/3.

The accepted runtime package remains SHA256
`089ae964c8e1b75281d589a6cd52a3a25d358f9443112162fea616b69b5904d7`, with
binary SHA256
`e5061dcc1e0b925933eceeacffb576536d24f609307166b97d0e159c0f1772d1`.
The [v0.2.0 release](https://github.com/pjunod/rog_audio/releases/tag/v0.2.0)
retains corresponding source and notices. Source inspection found no supported
runtime configuration for an explicit final FL/FR-to-RL/RR hardware port map.
A configuration-only node rebind cannot be presented as preserving the
working speaker delivery.

## Stereo fallback keeps the accepted DSP implementation

The owner authorized returning to stereo if the four-channel profile could
not reliably preserve the working tuning. Use that fallback for the current
latency scope, retaining the reviewed binary, model-specific preset, IR, stock
amplifier protection and recoverable configuration. The deployment session
owns any live profile change and verifies the restored speaker route and
runtime output links; this investigation performs no live changes.

Keeping four channels would require explicit mapping of the final stereo DSP
output to the observed speaker pair at RL/RR. The present runtime creates its
own final links, so manually replacing them is not a durable solution across
graph rebuilds. A future implementation needs a supported mapping contract,
independent adversarial review, appropriate native and isolated graph checks,
and a new runtime artifact if its source changes. It must keep the existing
two-channel coefficients and report unused PCM ports explicitly.

No four-channel fixture or new runtime was accepted for this investigation.
The inherited stereo unit and isolated graph receipts remain historical
acceptance of their original inputs. They do not cover this four-channel
profile or prove restored live state. Physical channel audibility needs a
coordinated measurement or listening method; silent unused logical ports
alone would not prove which physical drivers are audible.

The settings UI hung during profile selection and was closed. Neither source
inspection nor these routing observations establishes the cause of that UI
failure.
