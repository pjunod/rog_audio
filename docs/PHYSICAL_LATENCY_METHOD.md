# Physical latency method — record key click and speaker response on one phone

**Status:** proposed operator procedure; emitter and pilot not implemented;
no physical measurements collected · **Written:** 2026-10-13 · **Executes:**
physical comparison in [latency comparison](LATENCY_COMPARISON.md).

Companion to [latency tooling](AUDIO_LATENCY_BUILD.md) (trial schema and
statistics), [CoreAudio timing](COREAUDIO_LATENCY.md) (Mac API terms) and
[operations](OPERATIONS.md) (preservation). Follow the steps in order. If a
step requires replacing tuning, changing a system audio service or silently
opening a microphone, stop and flag it rather than changing the experiment.

The available equipment is laptops, phones and tablets. Start with an
external phone recording both a mechanical key click and the laptop's
response on one audio track. A common external keyboard improves control
if one is already available. An electrical trigger and calibrated external
capture remain the later route to an isolated output-latency measurement.

## 1. Name the measured interval before collecting it

The primary result is **audible key click to audible speaker chirp**, a
physical interaction-to-sound interval. It includes the keyboard mechanism
and input delivery, application scheduling/queues, OS audio, speaker DSP,
converters, speakers and the differential sound path to the phone. The
click may occur before or after switch actuation. Its uncalibrated offset
must remain part of the scope; it is not a timestamp for sample submission.

```text
key press ──▶ switch/input event ──▶ application ──▶ tuned speaker chirp
    │                                                        │
    └── mechanical click ──▶ one phone audio track ◀──────────┘
                              t_click          t_chirp
```

Both detected events use sample positions in the same recording, so their
difference does not require synchronized laptop and phone clocks. A common
sample clock removes cross-device clock offset, not detector error, recorder
processing, sample-rate calibration error or keyboard bias.

**Non-goals:** this method does not isolate pure audio-output latency, infer
one-way latency from a round trip, calibrate sound quality, prove Mac parity
from a graph period or measure display timing. Do not use a screen flash as
the reference: display delay and camera audio/video alignment add another
path. Do not substitute Bluetooth, headphones or USB speakers for the
internal speaker route under test.

**Acceptance:** a pilot receipt names both physical endpoints, the recorder
track and the included path. A graph quantum or HAL buffer is metadata only.

## 2. Establish the emitter before calling the plan runnable

The repository has [offline trial analysis](../scripts/analyse_audio_latency.py),
[Linux inspection](../scripts/inspect_audio_path.py) and
[Mac output inspection](../probes/coreaudio/output_inventory.c). It has no
public key-event chirp emitter or automatic phone-waveform detector. The
inactive native validation probes and synthetic player are not substitutes.
This document adds no runtime and starts no playback or recording.

The missing emitter must have the following contract, to be implemented and
reviewed separately before formal capture:

| Behaviour | Required observation and reason |
|---|---|
| Physical key down | One press emits one chirp; ignore key repeat, because a held key would create an ambiguous trial. |
| Preloaded signal | Propose a 20 ms chirp with short tapered edges; choose its frequency band and level in the pilot, then freeze exact waveform bytes/hash. Do not load or decode a file on each press. |
| Warm audio path | Keep the owned output path active between presses. Report initial startup separately; otherwise idle wake-up and steady-state results become mixed. |
| One application path | Use the same implementation/build and comparable settings on all three laptops. A browser version is part of the method, not an interchangeable player. |
| Existing internal output | Verify the full ASUS/Lenovo chain and both hardware channels. Do not route directly to hardware in a way that bypasses speaker correction. |
| Negotiation evidence | Record actual rate and Linux driver quantum while the emitter runs. If it changes from 256/48000, report a different condition; do not force global timing to make it fit. |
| Timing and application metadata | Log key-event sequence and available callback/request timing privately for diagnosis. Do not compare laptop timestamps directly with phone timestamps. |
| Explicit start/stop | Playback requires an operator action. Stop only the owned emitter; never stop other media or restart audio services. |

A local Web Audio page is one candidate, not a delivered tool. Its latency
request and reported timing are application/API parameters, not physical
ground truth. The [Web Audio specification](https://www.w3.org/TR/webaudio-1.0/)
defines the application graph and reported timing; the actual browser route
and negotiation still need a pilot. If browsers cannot maintain comparable
conditions, propose a small native emitter before expanding implementation.

**Acceptance:** a short pilot demonstrates one chirp per press, an active
verified tuned path, retained signal/source hashes and explicit stop without
altering other streams. A prospective emitter specification is not a pass.

## 3. Preserve the tuned state and coordinate the capture window

Before the window, retain runtime/kit/preset/IR/plugin settings hashes, the
physical default/profile/route, owner volume, persistent startup state and
the existing [rollback](LATENCY_COMPARISON.md#7-paired-256-frame-trials--both-tuned-paths-preserved).
Record power state, actual client requests and other media. Keep the 256-frame
request, limiter, IR, amplifier protection and stock audio services intact.

Agree who operates the recorder, who presses the key, the quiet capture
interval, the conservative signal level and the start/stop sequence. Do not
overlap this measurement with the separate listening or stability window
unless the coordinator deliberately defines a different load condition.
Signal level is chosen for clear, unclipped detection; percentages on two
volume controls are not proof of matched acoustic level. Preserve the owner
volume and record any explicitly chosen signal-amplitude difference.

Use the phone/tablet as the external recorder; no laptop microphone access is
needed for this procedure. Recording is an explicit action in this window,
not a side effect of an inspector or repository check. Keep the original
audio, waveform annotations, logs and detailed method receipt private. Public
summaries use neutral aliases, hashes, counts, statistics and stated limits.

If a route, preset, service or error counter changes during a trial block,
stop the owned emitter and retain the affected data. Do not repair the
configuration invisibly and continue the same block. Mark the condition
change and coordinate recovery with the live owner.

**Acceptance:** before/after state receipts preserve the tuned path. The
recording window and any other active workload are explicitly retained.

## 4. Choose a recorder and control the keyboard and geometry

Use one phone, one recording app/mode and one physical audio track for all
systems. Prefer unprocessed lossless/PCM audio at a known rate if available.
Record the actual exported format/rate; do not assume 48 kHz from a setting.
Disable optional enhancement/noise suppression where supported and record
what remains unknown. Never denoise, trim, resample or time-stretch the
original; retain a hash and annotate a lossless working copy.

Place the recorder so both the key click and speaker chirp are identifiable.
Mark its position, laptop orientation and key/speaker distances. A rigid stand
or a repeatable marked position is preferable to holding it. Keep the room
and microphone orientation consistent. Differential propagation is
`(speaker_distance - key_distance) / sound_speed`; retain both distances and
the sound-speed assumption if any correction is later justified. It can be
signed. Leave it uncorrected in the first practical comparison; do not invent
a positive correction or silently move an event timestamp.

| Keyboard choice | Interpretation |
|---|---|
| Same wired external keyboard and same key on all three | Preferred when available. Keep the device, key, connection and pressing technique fixed. USB host/input scheduling still belongs to the measured path. |
| Each laptop's built-in keyboard | Available without extra equipment. The click-to-switch offset and keyboard processing differ and can bias cross-laptop results; do not claim an isolated audio difference. |
| Bluetooth keyboard | Keep out of the initial comparison because wireless input timing introduces another variable. |

Equal distances and the same recorder reduce differences; they do not
calibrate recorder processing or key actuation. A common keyboard cannot
turn the acoustic click into an exact electrical trigger.

**Acceptance:** raw audio contains two separable transients per pilot press;
positions, format and keyboard method are reproducible. If suppression or
overlap masks either transient, change the pilot method before collecting
formal trials rather than manufacturing timestamps.

## 5. Pilot the detector, then collect repeated blocks

Collect a small pilot, such as 10 presses per system. This is method discovery,
not the formal comparison. Export the original audio and establish a detector
before inspecting formal results. Manual waveform annotation is a practical
first detector; record the analysis application/version and sample positions.

Define the click as one documented mechanical transient and the chirp as a
documented first reliable acoustic response. Retain waveform crops and
allowed onset intervals, not just a picked maximum. A correlation peak may
indicate waveform alignment rather than first onset; if used, name that
metric separately and keep it out of an onset group. Record the noise-floor,
threshold/window rule and ambiguity criteria in the private method receipt.
Re-annotate the pilot independently or blind to system labels to estimate
annotation variability. Do not select a threshold because it makes one
laptop look faster.

After the method is fixed, target **100 included presses per system and
condition**, consistent with the existing onset-count contract. A practical
sequence is five blocks of 20 valid events, rotating ROG, ThinkPad and M4 Air
between blocks. Allow roughly 2–4 seconds between presses; avoid overlap and
record changes in workload, power or background media. Warm steady-state
and idle-onset are different conditions; do not pool them. Do not restore
the old 2048-frame configuration merely to create another baseline here.

Retain every attempted press. Reject missing/ambiguous clicks or chirps,
clipping, overlapping unrelated sounds, incomplete captures or an observed
xrun affecting that interval. A chirp preceding the chosen click is evidence
of an unsuitable click reference or annotation, not a zero-latency success.
Keep rejected events and their reasons; collect replacements to reach the
included count. If rejection rates or the method change substantially,
report that and begin a new condition rather than hiding the old attempts.

**Acceptance:** each condition has the same declared detector and retained
attempts, at least 100 included events, exclusion counts and verified tuning.
Meeting the count alone establishes neither precision nor Mac parity.

## 6. Quantify uncertainty without erasing systematic differences

For click sample `i_click`, chirp sample `i_chirp` and recorder rate `f_rec`:

```text
raw_samples = i_chirp - i_click
raw_ms      = 1000 * raw_samples / f_rec
```

Retain allowed intervals for both indices. The widest difference consistent
with those intervals supplies the annotation bound; include sample grid,
recorder clock/timebase uncertainty and known preprocessing effects without
double counting. A fine sample grid is not a claim of equally fine accuracy.

| Source | How to carry it |
|---|---|
| Click and chirp annotation | Use the pilot's independently checked onset intervals and document the conservative bound. |
| Recorder sample timebase | Preserve exported rate and known calibration. If calibration is unknown, say so; do not label the clock calibrated. |
| Differential propagation | Keep raw geometry effects, or use a separately documented scoped model with distance and temperature uncertainty. |
| Click relative to switch actuation | Preserve as part of the interaction metric; uncalibrated keyboard bias prevents a pure output-latency interpretation. |
| Recorder enhancement/codec effects | Document mode and remaining unknown bias; lossless export alone does not prove unprocessed capture. |
| Trial-to-trial scheduling | This is part of the response-time distribution, not detector noise to subtract. |

The analyser accepts only finite declared bounds; it cannot encode an
unbounded/unknown bias as a number. Keep any unquantified effect explicit in
the method receipt and final interpretation. If there is no defensible
measurement bound, retain the annotated pilot and descriptive findings but
do not invent zero uncertainty or call the result calibrated. Increasing
the number of presses does not remove a fixed keyboard or recorder bias.

## 7. Import actual annotations into the existing analyser

Re-verify the exact schema against
[the analyser](../scripts/analyse_audio_latency.py) and
[its contract](AUDIO_LATENCY_BUILD.md#clocks-and-corrections-preserve-the-measured-path)
at execution time. Keep raw indices, recordings and method detail in the
private annotation receipt; the strict trial JSON has no arbitrary extra
metadata fields. Use neutral aliases matching `[a-z][a-z0-9_-]{0,63}`.

| Trial field | Value for this method |
|---|---|
| `kind` | `event-to-output`, explicitly scoped to acoustic key click through speaker response. |
| `method` | A neutral detector alias such as `phone-click-chirp-v1`; different detector revisions use different aliases. |
| `delay`, `unit` | The measured nonnegative integer sample difference and `samples`; retain invalid/ambiguous attempts separately if no honest numeric interval can be formed. Never invent a number to satisfy the schema. |
| `sample_rate_hz` | Actual recorder/export timebase; independent of the laptop's graph rate. |
| `clock` | Exactly `{ "relationship": "same-clock" }` only when both indices are from one physical recording track. |
| `uncertainty` | Exactly `{ "bound": <documented bound>, "unit": "ms" }`; numerical angle brackets are placeholders, not executable JSON or a measured value. |
| `corrections` | Start with `[]`. Any later correction requires its own model ID, physical scope, finite delay and uncertainty. The current schema cannot directly express a signed propagation correction. |
| `graph` | Linux: observed `quantum_frames` and `rate_hz`; Mac: `null`, because a HAL buffer is not this Linux graph declaration. |
| Group aliases | Keep system/setup, configuration, route, power, load and DSP state distinct; do not pool three systems or different keyboard methods. |
| Validity | `valid: false` requires an allowlisted reason. Flags such as `clipping`, `ambiguous-detection`, `xrun` or `missing-trigger` exclude the row. |

Only a real capture set uses `evidence_class: "physical-measurement"`.
The existing synthetic fixture remains synthetic; changing its label would
not create a physical result. Full top-level and trial fields are documented
in [the schema](AUDIO_LATENCY_BUILD.md#9-trial-schema-and-statistics--preserve-clocks-and-corrections).

```bash
python3 scripts/analyse_audio_latency.py \
  --input PRIVATE_TRIALS.json --output PRIVATE_NEW_RESULT.json  # Offline only.
```

**How to read it:** report raw min, median, nearest-rank p95 and max, included
and excluded counts, exclusion reasons, conservative measurement bounds and
block order. P95 uses sorted index `ceil(0.95*n)-1`; 100 observations still
provide a limited tail sample. The analyser reports sampling confidence as
`not-estimated`; its statistic bounds cover declared measurement errors,
not population confidence. Repeated block results help reveal drift. Do not
interpret non-overlap as an isolated audio difference when keyboard bias is
unquantified. Report Mac parity only for the exact measured interaction path
and resolved uncertainty; the analyser always leaves qualification unestablished.

**Acceptance:** real input and output are source/hash-bound, every number is
traceable to a private recording/annotation, and limitations remain alongside
the statistics. No physical values have been produced by this documentation.

## 8. Keep sustained software stability separate

The coordinated 60-minute Linux check has its own start/end times, workload,
driver/DSP error deltas, identity continuity and preservation receipts. A
silent processing run can establish sustained reported scheduling behaviour
under its declared load; it cannot demonstrate the absence of audible gaps
or a physical response-time distribution. Listening, silent stability,
physical onset and reboot/hotplug/resume are separate acceptance records.
Sonos remains last.
