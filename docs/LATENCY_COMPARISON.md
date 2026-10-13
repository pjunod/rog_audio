# Latency comparison — tuned Linux laptops and the M4 Air

**Status:** both tuned 256-frame trials active; physical comparison pending ·
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
The owner has laptops, phones and tablets. The
[phone-recorded interaction method](PHYSICAL_LATENCY_METHOD.md) proposes a
same-track key-click/chirp comparison with those devices. Its local browser
emitter is implemented with source review and synthetic acceptance pending;
the manual capture pilot has not run. This interaction metric cannot isolate
pure output latency from keyboard/application delay.
Physical capture needs a concrete method, uncertainty budget and coordinated
playback/recording window. Retain rejected trials and raw captures privately;
use the existing analyser for appropriately declared physical trial sets.

## 5. Review and acceptance ledger

Finish the batch before independent adversarial review. Fix its findings, then
run the affected new tests once against the final source; retain prior speaker,
latency and Atmos passes when their sources are unchanged. Compiler execution
while building establishes the native toolchain and is distinct from unit tests.
Record every acceptance outcome, retry and limitation in [review](REVIEW.md).

Software period reductions are recorded below from source-bound operational
receipts. Physical improvement and Mac parity remain unmeasured.

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

## 7. Paired 256-frame trials — both tuned paths preserved

The [paired trial receipt](../evidence/linux-speaker-latency-trials-2026-10-13.json)
records the final operational results. Both Linux pairs used the same explicit
`pw-play` request of 4800/48000 (100 ms), all-zero PCM, the full model-specific
DSP chain and the persistent user service. The four bounded observations lasted
4.67–5.88 seconds; exact durations and startup sequences are in the
receipt. The 256-frame output-filter request was observed on the actual linked
driver, and remains active on both laptops.

| Host | Paired baseline | Final software period | Processing and error observations |
|---|---|---|---|
| ROG | Driver 2048/48000 = 42.667 ms | Driver 256/48000 = 5.333 ms | Full ASUS chain and both hardware channels; all sampled driver/DSP error counters zero |
| ThinkPad | Driver 2048/48000 = 42.667 ms | Driver 256/48000 = 5.333 ms | Full Lenovo chain and both hardware channels; startup reached driver count 1 in both runs, later five running samples stayed at 1 |
| M4 Air | Separate getter reference, not a Linux-style paired trial | HAL buffer 512/48000 = 10.667 ms | Device-running false/true/false; no equivalent error counter collected |

The Linux scheduling period is one eighth of its paired baseline. That ratio
does not describe acoustic delay. The Mac used `afplay` and reports a different
API quantity; its separate device-plus-stream accounting remains 27.917 ms
and its safety offset 1 ms. No endpoint has a physical delay measurement.
The short ThinkPad observation shows no counter increase over its baseline,
but does not qualify zero-error startup. Neither laptop has completed the
60-minute representative-load check, hotplug/resume qualification or power
comparison. No microphone or audible probe was used.

**Preservation:** runtime and kit bytes, preset/IR payloads, plugin settings,
physical defaults and stock PipeWire/WirePlumber processes were unchanged
within each pair. Only the private output-filter request was installed. The
ROG's native shutdown incremented its selected preset-use counter while
preserving the bypass entry; both raw preimages are retained. The final owner
volumes were preserved at 86% on ROG and 20% on ThinkPad. Both persistent user
services are active and enabled; actual post-reboot startup is still unobserved.

**Rollback:** each host retains its exact accepted tools, bundle, snapshot and
`ROLLBACK.json` beneath the private audio state directory. ROG uses deployment
`latency-256-aff7fdb` and snapshot `latency256-lab5-aff7fdb`; ThinkPad uses
`latency-256-90fea80` and snapshot `latency256-lab6-90fea80`. The recorded
commands stop only `rog-audio-speaker.service`, remove the owned fragment
through the guarded tool into a new retained archive, and restart that same
service. The original package/tuning rollback remains available. Live fragment
removal was not needed or exercised; synthetic lifecycle/race acceptance
covers that implementation. See [file-level recovery](LINUX_AUDIO_PATH.md).

The refused ROG attempt is retained separately: the earlier singleton counter
check refused before any fragment or snapshot was created and the tuned
baseline was resumed. The reviewed list correction passed all eight affected
methods once before the successful retry. No failed evidence was discarded.
Sonos Arc/eARC remains deferred until the internal-speaker work is qualified.

## 8. Sustained checks and session-start correction — in progress

The [progress receipt](../evidence/speaker-startup-stability-progress-2026-10-13.json)
is an operator-reported snapshot, not a completed measurement. ROG's initial
attempt stopped before timing on a startup counter increase. ThinkPad's first
attempt stopped when volume changed from 20% to 74%; its elapsed time of
581.040 seconds includes cleanup, not exact uninterrupted active coverage;
its sampled driver count stayed at 1 and DSP/source counts stayed zero.
The revised normal-use method logs volume adjustments without writing volume,
while retaining strict processing, routing, service, counter and continuity
checks. Earlier incomplete attempts are not accumulated into a later hour.

ThinkPad's fresh interval remains active from 10:02:02 to an expected
11:02:02 Eastern on 2026-10-13. ROG started at 10:09:39 after exact tuned-preset
restoration, with sampled errors zero. It then stopped after 67.982 seconds
of owned playback: sampled driver errors rose 0→1 and the owned zero-PCM
client and convolver each rose 0→2. The 256/48000 graph, 94% physical volume
and service identities/restart counts were preserved; owned test processes
were removed and the failure archive retained. No counter reset or retry was
automatically performed. The startup correction was not installed, and the
cause of this later error growth remains unestablished.

The operator diagnosed a separate session-start ordering race; its permanent
runtime fix remains offline work. A successful timed run after manual
restoration would not establish reliable automatic preset loading.

Only completed continuous coverage, endpoint checks, observed counter deltas
and final preservation can qualify the declared software stability workload.
The owned all-zero stream and separate listening/recording overlaps do not
substitute for a physical response-time distribution or absence of audible
gaps. [Current status](STATUS.md#startup-and-sustained-check-progress--2026-10-13)
will record actual outcomes when the receipts arrive.
