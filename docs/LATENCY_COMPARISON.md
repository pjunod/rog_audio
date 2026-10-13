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
