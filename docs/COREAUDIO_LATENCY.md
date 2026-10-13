# CoreAudio latency — compare reported output terms without inventing delay

**Updated:** 2026-10-13 · **State:** M4 Air idle and silent-running snapshots
collected; native compile, source review and 16 offline unit cases passed.

Companion to [latency tooling](AUDIO_LATENCY_BUILD.md) and
[audio quality](AUDIO_QUALITY.md). This document explains the Mac component
inventory and a possible later acoustic method. It does not establish a
physical latency result or macOS parity for either tuned Linux laptop.

## HAL getters inspect output without starting IO

[The native probe](../probes/coreaudio/output_inventory.c) enumerates devices
and their output streams with `AudioObjectHasProperty`,
`AudioObjectGetPropertyDataSize` and `AudioObjectGetPropertyData`. It reads
the default and system output before and after the snapshot. It creates no
IOProc or AudioUnit, starts no playback/capture, writes no HAL property and
changes no audio service, routing, volume or privacy permission.

The fixed inventory includes nominal/actual rate, device buffer size/range,
output device latency/safety offset, running/alive state and each output
stream's latency, active state, terminal type and virtual/physical format.
Device latency and safety offset use output scope. Stream properties use
global scope: an AudioStream has only global scope. Each field retains its
numeric OSStatus and `ok`, `unavailable`, `error` or `invalid-data` state.
Missing latency is not zero latency. Object-list reads are bounded at 128
devices or streams; oversized or changing list data is a property failure.

The native JSON includes ephemeral HAL object IDs to associate the current
defaults with devices. It reads no names, UIDs, serials or owner/client data.
Keep raw JSON private. Getters are sequential, so rate, buffer and topology
can change between reads; unchanged default IDs do not prove an atomic
snapshot. A running flag is activity evidence, not a callback timing trace.

## Build and summarise a new private snapshot

Use a Mac with an existing compiler/SDK. These commands create files only in
a new private directory under durable owned storage; retain its binary,
capture and summary. They install no packages or audio configuration.

```bash
coreaudio_root="$HOME/.local/state/rog-audio/coreaudio"  # Durable private root.
mkdir -p "$coreaudio_root"
coreaudio_work=$(mktemp -d "$coreaudio_root/capture-XXXXXXXX")  # New retained capture.
xcrun clang -std=c11 -Wall -Wextra -Werror -Wpedantic \
  -framework CoreAudio probes/coreaudio/output_inventory.c \
  -o "$coreaudio_work/coreaudio-output-inventory"         # Compile getter-only source.
(umask 077; set -C; "$coreaudio_work/coreaudio-output-inventory" > "$coreaudio_work/capture.json")
python3 scripts/analyse_coreaudio_latency.py \
  --input "$coreaudio_work/capture.json" --output "$coreaudio_work/summary.json"
```

[The offline summariser](../scripts/analyse_coreaudio_latency.py) uses only
Python's standard library and performs no subprocess, network or audio calls.
It reconstructs fixed numeric/enumerated fields, removes HAL IDs and ignores
unrecognised device/owner metadata. It rejects malformed property states,
duplicate JSON keys/objects, nonfinite values, boolean numbers, invalid rates
and unknown schema versions. Final-component input symlinks and nonregular
files are refused; reads are bounded at 8 MiB. Output is exclusive mode 0600;
an existing output or symlink is preserved. CLI errors contain a fixed reason
without supplied paths or payload text.

Exit 0 means a summary was written, including partial inventories. Exit 2
means input/schema/output creation failed. Native exit 0 means device-list
enumeration completed; individual fields can still fail. Native exit 3 means
device-list enumeration failed, 2 means invalid arguments and 1 means stdout
failed. No exit code certifies hardware timing accuracy.

**How to read it:** `buffer_period_ms` is frames divided by the reported
nominal rate. `reported_device_latency_ms` and `safety_offset_ms` remain
separate. Each stream's `reported_device_plus_stream_latency_ms` sums the
device and stream frame counts only when both reported format rates equal
the device nominal rate. Missing/mismatched rates leave derived stream terms
null. `physical_latency_ms` is always null. `partial` includes failed
properties, unavailable defaults, a default change or an observed dead device.
A requested stream can be enabled while the device is idle.

## Apple defines device and stream latency as separate terms

The Apple SDK's `CoreAudio.framework/Headers/AudioHardwareBase.h` describes
device latency as frames and explicitly says to add the stream's reported
latency when both report latency. It describes safety offset as the distance
ahead of the hardware position at which output IO is safe. The companion
`AudioHardware.h` describes buffer frame size as IO buffer frames and actual
rate as measured from device timestamps. These are API/driver reports;
neither documentation nor successful queries authenticate acoustic accuracy.

Apple's [presentation-latency reference](https://developer.apple.com/documentation/avfaudio/avaudioionode/presentationlatency)
links the presentation/hardware term to the device and stream properties.
[Buffer frame size](https://developer.apple.com/documentation/coreaudio/kaudiodevicepropertybufferframesize),
[safety offset](https://developer.apple.com/documentation/coreaudio/kaudiodevicepropertysafetyoffset),
[device latency](https://developer.apple.com/documentation/coreaudio/kaudiodevicepropertylatency)
and [stream latency](https://developer.apple.com/documentation/coreaudio/kaudiostreampropertylatency)
identify the collected selectors. SDK header comments are the detailed
property contract used by this implementation; retrieved web declarations
alone do not provide a complete latency formula.

Do not add every displayed term and name the result event-to-sound delay.
Application queues, scheduling, resampling and processing may add delay;
reported values may have uncalibrated bias. The Mac HAL buffer period and
a running PipeWire graph period can be placed beside each other as scheduling
parameters. HAL device/stream terms and Linux DSP/node/ALSA terms require
their own provenance and units. They do not form interchangeable totals.

## M4 Air snapshot — idle and silent running are separate observations

[The source-bound receipt](../evidence/m4-coreaudio-timing-2026-10-13.json)
records model `Mac16,13`, arm64, macOS 27.0.1 build `26A434` and Apple clang
21.0.0. A separate private system-profiler capture identifies the built-in
stereo speaker output. The stream terminal code was unclassified by the SDK
fourcc mapping; the probe does not invent a speaker classification from it.

| Output term | Idle | All-zero PCM running | Meaning |
|---|---|---|---|
| Nominal / actual rate | 48000 / 48000 Hz | 48000 / 48000 Hz | HAL reports, not clock calibration |
| IO buffer | 512 frames / 10.667 ms | 512 frames / 10.667 ms | Current device IO period |
| Buffer range | 15–4096 frames | 15–4096 frames | Advertised range, not a recommendation |
| Output device latency | 60 frames / 1.25 ms | 60 frames / 1.25 ms | Reported device term |
| Output stream latency | 1280 frames / 26.667 ms | 1280 frames / 26.667 ms | Reported stream term |
| Device + stream | 1340 frames / 27.917 ms | 1340 frames / 27.917 ms | Supported reported sum, not total delay |
| Safety offset | 48 frames / 1 ms | 48 frames / 1 ms | IO safety position offset |
| Device running | 0 | 1 | Different operational contexts |
| Stream enabled | 1 | 1 | Does not prove the device was running |

The separately authorized operational sample used `/usr/bin/afplay` with a
10-second, 48 kHz, stereo, 16-bit WAV containing only zero samples. The device
was running during collection and idle before/after. Default and system
output IDs were unchanged throughout. Only the owned player was stopped;
its WAV/source/binary workspace was removed. This sample emits no audible
probe, measures no acoustic event and imposes no representative stress load.
No microphone was opened and no property/configuration/service was changed.
This running sample is not a unit-test or physical acceptance receipt.

## Built-in acoustic round trip is feasible with a narrower claim

**Design only:** a later authorized audible/capture window could use the
internal speaker and microphone without buying an interface. The initial
inventory includes a built-in microphone but does not establish app access,
capture processing or measurement fidelity. Normal microphone permission is
required. Apple documents [the usage-description key](https://developer.apple.com/documentation/bundleresources/information-property-list/nsmicrophoneusagedescription)
and [user authorization](https://developer.apple.com/documentation/bundleresources/requesting-authorization-for-media-capture-on-macos).
No permission reset, privacy-database edit or bypass is part of this method.

Define the primary metric as **software submission to delivery of the input
buffer containing the acoustic onset**. Bracket submission of a known short
PCM pulse/noise burst with the host monotonic clock. Timestamp microphone
buffer delivery on that same host clock; preserve raw samples, buffer sizes
and timestamps privately. Offline correlation identifies the first buffer
containing the onset using a predetermined window, threshold and competing
peak rejection rule. The primary delay is its delivery time minus submission
time. It includes output queuing/DSP, speaker and propagation, microphone
processing, input buffering and callback scheduling. Capture-buffer phase is
part of this endpoint; do not subtract it or halve the result into output
latency. Linux playback must traverse the working tuned speaker route.

Timestamp brackets provide a software timing interval. Correlation ambiguity,
clipping, route changes, dropouts or missing timestamps exclude a trial.
Record clock resolution/timebase, callback bounds, input/output formats and
actual processing routes. External clock accuracy and input/presentation
timestamp bias remain uncalibrated; a finite callback interval is not a
calibrated absolute-accuracy bound. Do not invent a numeric physical bound
to fit the existing analyser. Build the capture/method receipt and review its
uncertainty model before admitting physical trials.

Apple's [IOProc contract](https://developer.apple.com/documentation/coreaudio/audiodeviceioproc)
defines `inInputTime` as the first frame's hardware acquisition time and
`inOutputTime` as the first frame's time of passage to hardware; `inNow` is
the start of the IO cycle including scheduling latency. A separately reported
driver-timestamp-referenced acoustic metric can map the detected sample
offset using [host time](https://developer.apple.com/documentation/coreaudiotypes/audiotimestamp/mhosttime)
and [sample time](https://developer.apple.com/documentation/coreaudiotypes/audiotimestamp/msampletime).
Check [validity flags](https://developer.apple.com/documentation/coreaudiotypes/audiotimestampflags)
and convert host ticks with `AudioConvertHostTimeToNanos`. Different input
and output devices' sample counters are not one clock merely because both
say 48 kHz. Timestamp-referenced acquisition removes input delivery buffering
from its endpoint, so it is a different metric from the full practical loop.
Its driver bias is unverified; it is not calibrated pure speaker-output delay.

Keep stock microphone processing and document it rather than silently
disabling echo cancellation, beamforming or protection. Use a conservative
recorded level, stable laptop/lid placement and power/load/DSP state. Warm
and idle-onset trials must be separate, with at least 100 accepted onset
trials per state for the existing comparison plan. Built-in microphone
differences remain part of the practical loop comparison. A shared external
trigger/recorder is still needed for the stronger output-only comparison.

## Reviewed offline summary acceptance

[Synthetic tests](../tests/test_analyse_coreaudio_latency.py) cover component
arithmetic, missing/zero latency, rate mismatch, route changes, multiple
outputs/streams, privacy, invalid numeric values, failed/duplicate objects,
bounded exclusive file IO and symlink/FIFO handling. They invoke no HAL or
audio IO. The 16 cases passed once after combined source review, as recorded
in [acceptance](../evidence/audio-path-acceptance-2026-10-13.json). The command
below is for a future changed source requiring revalidation:

```bash
python3 -m unittest discover -s tests -p test_analyse_coreaudio_latency.py -v
```

The receipt distinguishes native compilation and getter/silent operational
observations from the later unit acceptance. This lane supplies no audible capture,
latency reduction, per-client Mac tuning, acoustic calibration or Atmos work.
