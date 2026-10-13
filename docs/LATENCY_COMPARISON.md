# Latency comparison — tuned Linux laptops and the M4 Air

**Status:** baseline collection and scoped implementation in progress ·
**Written:** 2026-10-13 · **Executes:** latency phase in
[implementation](AUDIO_IMPLEMENTATION.md).

Companion to [latency tooling](AUDIO_LATENCY_BUILD.md) and [status](STATUS.md).
This document compares the actual installed speaker paths. Preserve the sound
already accepted on the ROG and the separate Lenovo tuning on the ThinkPad.
Sonos Atmos remains outside this phase.

## 1. Compare the same kind of evidence

| Evidence | Linux observation | Mac observation | What it establishes |
|---|---|---|---|
| Processing period | Running driver QUANT / RATE | CoreAudio buffer frames / sample rate | Configured or observed software scheduling; not acoustic delay |
| Requested period | Follower node latency request | HAL buffer request/range where reported | A request or available range, not proof of actual physical performance |
| Reported processing delay | Node/port latency and DSP ProcessLatency | Device, stream latency and safety offset | API-reported components; do not combine incomparable totals |
| Runtime stability | Active-path error-counter deltas and load | Available HAL running state and later callback evidence | Scope and duration of observation, not a long-term reliability guarantee |
| Physical delay | Documented trigger/capture experiment | Same measurement method and conditions | Actual measured path, including the declared input/output components |

Record exact source/runtime/preset hashes and the active route for each result.
A suspended Linux endpoint supplies no running-period evidence. Missing APIs,
idle paths or unavailable counters remain unknown. A CoreAudio property value
and PipeWire graph period do not constitute a macOS-parity measurement.

## 2. Preserve speaker processing while changing one request

The first candidate requests 256 frames at 48 kHz on the candidate processor's
exact output filter through its private PipeWire client configuration. That
request corresponds to 5.333 ms per processing cycle if negotiated. It does
not guarantee a particular physical delay. A later 128-frame candidate must
be justified by observed behaviour; 64 frames is not the default objective.

Use an exact filter rule and retain its prior state. Do not set a global forced
quantum, alter amplifier controls, disable the limiter, shorten or replace the
IR, bypass tuning, change physical defaults or restart PipeWire/WirePlumber.
The configuration affects negotiation in the linked graph; record other active
clients because a shared driver is not isolated to one application.

The source-backed mechanism requires a controlled restart of only the speaker
processor. Build and review the complete change first, then validate its
configuration and rollback before the coordinated live trial. Record environment
overrides that could supersede the rule. An unchanged requested property is not
proof of the negotiated driver period.

## 3. Observe each candidate and retain a usable rollback

1. Capture the active device/route, graph settings, client requests, actual
   driver timing, reported DSP delays, error counters and preservation hashes.
2. Retain a durable preimage of the exact private configuration file and existing
   startup state. Prepare controlled quit, restoration and restart commands.
3. Apply only the reviewed request in the coordinated window, restart only the
   candidate processor, and confirm the exact preset, IR and physical output.
4. Compare actual driver timing and fresh error-counter deltas with the baseline.
   Note load, power state and whether real media was active. Do not reset error
   counters to conceal pre-existing or new failures.
5. Restore the previous request if the candidate causes errors, broken routing,
   missing processing or audible trouble. Preserve the failed receipt and retry
   only the failed or invalidated acceptance cases.

Keep short operational checks separate from the later 60-minute representative
load run and physical hotplug/resume qualification. Do not silently change the
owner's volume or stop their media to manufacture an idle baseline.

## 4. Measure physical response with an explicit capture path

The preferred output-latency comparison uses a common trigger and external
capture clock, with the same calibrated setup on all three laptops. An
interface loopback measures the declared round-trip path, not speaker onset.
A built-in speaker-to-microphone experiment, if supported with trustworthy
reference/capture timing, includes the microphone path and propagation; it
cannot be relabelled pure output latency or an isolated operating-system cost.

Measurement hardware is not yet established. Native probes in this batch are
read-only and never record microphones, play a signal or alter privacy settings.
Physical capture needs a concrete method, uncertainty budget and coordinated
playback/recording window. Retain rejected trials and raw captures privately;
use the existing analyser for appropriately declared physical trial sets.

## 5. Review and acceptance ledger

Finish the batch before independent adversarial review. Fix its findings, then
run the affected new tests once against the final source; retain prior speaker,
latency and Atmos passes when their sources are unchanged. Compiler execution
while building establishes the native toolchain and is distinct from unit tests.
Record every acceptance outcome, retry and limitation in [review](REVIEW.md).

No new physical improvement or Mac parity has been established as of this plan.
The comparison table will be populated only from collected, source-bound
receipts; it will retain separate software and physical evidence labels.

## 6. Initial running observations — 2026-10-13

The [Linux baseline receipt](../evidence/linux-audio-latency-baselines-2026-10-13.json),
[ROG stereo recovery receipt](../evidence/rog-speaker-stereo-recovery-2026-10-13.json)
and [Mac receipt](../evidence/m4-coreaudio-timing-2026-10-13.json) retain
source hashes and bounded software observations.

Linux observations used approximately ten seconds of all-zero PCM. The Mac
snapshot used a ten-second zero-PCM file, with its player stopped after the
running snapshot. No microphone was opened and no audible probe was generated.
Linux used `pw-play` with its 100 ms client request; the Mac used `afplay`. They exercise different application
paths and do not establish equal application buffering.

| Component | ROG, four-channel investigation | ThinkPad, tuned stereo | M4 Air, built-in output |
|---|---|---|---|
| Observed running period | 2048 / 48000 = 42.667 ms | 2048 / 48000 = 42.667 ms | HAL 512 / 48000 = 10.667 ms |
| Speaker DSP during observation | Bypassed because kit binds stereo | Full convolver, autogain, multiband compressor and limiter | System path; no equivalent graph inventory |
| Error observation | Zero in active snapshots | First active counter 1, then unchanged across five rows | No equivalent counter collected |
| ALSA period / buffer | 1024 / 32768 frames | 1024 / 32768 frames | Not an ALSA endpoint |
| API device / stream latency | Retain reported graph components separately | Retain reported graph components separately | 60 / 1280 frames = 1.25 / 26.667 ms |
| API safety offset | Not a comparable collected field | Not a comparable collected field | 48 frames = 1 ms |
| Physical delay | Unmeasured | Unmeasured | Unmeasured |

The Linux client request influences negotiation. The 2048-frame period is not
an intrinsic hardware minimum or an untreated default-only benchmark. Hold the
same client request, signal and running path constant in before/after trials.
The ROG observation is route-diagnosis evidence and cannot be used as a tuned
performance baseline. The ThinkPad observation cannot support a zero-error
startup claim. Neither short run establishes sustained-load reliability.

[On the Mac](COREAUDIO_LATENCY.md), the device-running flag changed from false
to true to false; its
reported timing components stayed constant. Device plus stream latency is
1340 frames (27.917 ms) under the API's accounting. Keep that component separate
from buffer size, safety offset and physical onset; do not compare it directly
with a Linux graph period.

[The four-channel investigation](ASUS_FOUR_CHANNEL.md) found the ROG stream
assigned the speaker DAC to PCM channels 2/3 and
the headphone DAC to channels 0/1. The installed processor would link its
stereo output to ports 0/1. Correct rear-pair routing requires a runtime change;
the owner-authorized fallback to the validated stereo profile is being used
for this latency phase. The OEM two-channel coefficients remain unchanged.


After the authorized fallback, a separate ten-second silent observation on the
ROG confirmed the full ASUS pipeline: convolver, two multiband-compressor
stages, limiter, spectrum and output-level filters, then hardware FL/FR. The
speaker DAC used stream 1, channel 0. With the same 100 ms client request the
driver again ran at 2048/48000; all five running error-counter samples were
zero. Volume was explicitly set to 20% for the restored output. Managed DSP
files, startup configuration and all audio service process IDs were unchanged.
This is the tuned stereo baseline for the forthcoming ROG trial.
