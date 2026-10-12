# Operations — inspect, prepare and measure audio

Read [status](STATUS.md) for what is implemented and
[hardware](AUDIO_HARDWARE.md) for the observed baseline. The build contracts
are [speaker](AUDIO_SPEAKER_BUILD.md), [latency](AUDIO_LATENCY_BUILD.md) and
[Atmos](AUDIO_ATMOS_BUILD.md).

## Keep the observed baseline recoverable

The initial laptop inspection used read-only commands. It did not play or
record sound, alter mixer controls, restart services or install profiles.
Private raw captures and recovered files are operator inputs, outside Git.
The stock CS35L56 firmware and protection remain installed. Preserve exact
current routing and config snapshots before any later activation.

## Interpret generated output by its evidence class

A successful OEM conversion means the selected input was parsed and a bundle
was built. It does not prove the tuning sounds better or protects the drivers.
An inactive latency candidate is a proposed client policy. Graph period is
not physical delay. Synthetic Atmos rendering proves an exercised API;
actual object metadata and codec support require separate media evidence.
Commands, output fields, dependencies and failure meanings are recorded in
the corresponding lane documents alongside the implementation.

## Run physical comparison as a coordinated experiment

Use the M4 Air as primary reference and M3 Max as secondary. Record actual
models, OS versions, route, sample rate, power state, workload, levels,
measurement method and uncertainty. Compare the same measurement kind and
route; do not halve round-trip delay to claim one-way latency.

Speaker playback begins at a conservative level with an immediate bypass
and verified restoration procedure. Headphones and HDMI do not inherit
speaker correction. Check calling, hotplug, volume behaviour, A/V sync,
power and resume alongside response/distortion and latency.

Sonos Arc/eARC is the last route. Record the actual TV model, source-to-TV
connection, passthrough setting and soundbar-reported received format. The
owner confirmed Arc/eARC, but the full chain remains unverified. Do not
report decoded PCM or a codec badge as evidence of Atmos arriving at the Arc.
