# Physical latency method — record key click and speaker response on one phone

**Status:** local emitter source-reviewed; ten synthetic methods passed once;
unarmed Chrome smoke passed on local M3; Firefox/emitter staged on actual M4; manual pilot deferred; no physical measurements collected · **Written:** 2026-10-13 · **Executes:**
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

## 2. Use the local emitter in an explicit playback window

The [local browser page](../tools/physical-latency/index.html),
[signal/lifecycle code](../tools/physical-latency/emitter.js) and
[browser bindings](../tools/physical-latency/emitter-ui.js) need no server,
downloaded libraries, network connection or microphone. Copy the entire
`tools/physical-latency` folder to each laptop and open `index.html` locally.
Loading the page creates no AudioContext. Two source-review findings were
fixed and cleared; ten synthetic methods passed once. The current batch has
emitted no laptop test sound.

Matched Firefox 157.0.1 and the three pinned emitter files were subsequently
staged on the actual remote MacBook Air with Apple M4. A host-bound private
receipt records model identity, exact emitter hashes and browser package
signature/notarization/quarantine checks. This was staging only: the browser
was not launched, no AudioContext or playback started, and no new tests or
physical samples were collected. An earlier private handoff had labelled local
M3 preparation as M4 readiness; that label was corrected and retained in the
handoff history. The separately collected M4 HAL observations remain valid.
The earlier unarmed Chrome smoke is local M3 evidence, not a remote M4 browser
or acoustic pass. Manual launch, armed output/route checks and the capture
pilot remain pending. The ThinkPad's three accepted emitter files were also
copied to its intended Documents location with source/hashes verified; it was
unarmed and unlaunched, with no audio or microphone access. All file preparation
is complete. The private handoff's current M4/ThinkPad instructions are maintained
by its owner; earlier staging/mislabel receipts remain separate history.
Raw remote receipts and host paths stay private.

The repository also has [offline trial analysis](../scripts/analyse_audio_latency.py),
[Linux inspection](../scripts/inspect_audio_path.py) and
[Mac output inspection](../probes/coreaudio/output_inventory.c). Automatic
phone-waveform detection is not implemented; use manual annotations in the
pilot. The inactive native validation probes are not measurement emitters.

In the agreed window, choose the neutral system alias, verify the existing
internal route and start at -60 dBFS. Press **Arm silent warm stream**, then
Space on the focused test pad. Arming is silent; only an eligible Space
keydown requests a chirp. Choose a comfortable, detectable level in the pilot
and keep it fixed within the condition. Changes require disarming first.
The route checkbox records an operator statement; it does not verify routing.

The implemented contract is:

| Behaviour | Required observation and reason |
|---|---|
| Browser-trusted Space key down | One eligible non-repeat press emits one chirp. Modifier/composition events and keys outside the focused pad emit none. Browser trust rejects script-dispatched DOM events; it cannot authenticate a physical keyboard. The external click supplies that reference. |
| Preloaded signal | 20 ms, 750–3000 Hz stereo chirp, identical source channels, 2 ms raised-cosine edge ramps, generated at actual AudioContext rate. Source peak choices are -60 to -30 dBFS. It is generated once per arm, not loaded/decoded per press. |
| Warm audio path | A continuous zero-valued source requests an active owned output between presses. Verify actual Linux graph activity independently. Report initial startup separately; warm processing is not an idle-power baseline. |
| One application path | Use the same implementation/build and comparable settings on all three laptops. A browser version is part of the method, not an interchangeable player. |
| Existing internal output | Verify the full ASUS/Lenovo chain and both hardware channels. Do not route directly to hardware in a way that bypasses speaker correction. |
| Negotiation evidence | The context requests a 0.1-second application latency hint without forcing sample rate or global graph timing. The browser can interpret the hint differently. Record actual context rate and Linux driver quantum while it runs; a departure from the accepted per-host period is a different condition. |
| Timing and application metadata | The local JSON log retains session alias, browser user agent, actual context rate, level, the operator route statement, requested latency hint and finite/null API timing estimates. Events retain sequence, page monotonic time, key event timestamp and context start time as diagnostics only; `physical_latency_ms` stays null. |
| Input/event bounds | Leave 2–4 seconds between trials. Presses less than 750 ms apart emit none and are logged. At 2000 logged events the owned stream stops; export and reload for a new set. |
| Explicit start/stop | Arm creates the owned context; Disarm stops/disconnects owned sources and closes that context. Hiding/leaving the page, switching windows or loss of running context also disarms it. Other media and audio services are untouched. |

The page's latency request and reported timing are application/API parameters,
not physical ground truth. The [Web Audio specification](https://www.w3.org/TR/webaudio-1.0/)
defines the application graph and reported timing; the actual browser route
and negotiation still need a pilot. Use the same browser/version when possible
and record differences. If browsers cannot maintain comparable conditions,
report the limitation before proposing a native emitter.

**Download private event log** saves JSON in the browser's normal download
location. It is not a physical-trial input: no microphone samples or acoustic
event positions are present. **Download chirp reference WAV** saves the latest
armed waveform as stereo little-endian IEEE float32 WAV without playback.
Retain that reference and its SHA256 for each level/rate/session before
changing parameters; both downloads are explicit local actions. Download
dialogs may switch focus and disarm, so export a reference before the formal
block and re-arm to establish a new warm interval. Record the tool source
commit/file hashes alongside the external recording and browser metadata.

**Acceptance:** a short pilot demonstrates one chirp per press, an active
verified tuned path, retained signal/source hashes and explicit stop without
altering other streams. Written code or a prospective specification is not
physical measurement acceptance.

## 3. Preserve the tuned state and coordinate the capture window

Complete software qualification before the coordinated recording session.
Both laptops now run +rog3 with the separate reviewed helper/unit backport:
ROG 1024/48000, target −20 LUFS/cap 2.6475 dB; ThinkPad 256/48000, target
−16 LUFS/cap 14.1375 dB. Original IRs/non-AutoGain stages and final limiters
remain intact. Both [final settings-bound hours](STATUS.md#final-kept-settings-software-hours--2026-10-14) passed without added errors; current
generated demos are accepted at the recorded conditions. Physical recording
is deferred to another coordinated window; no page is to be armed or
recording started until that window is agreed. These results do not
qualify acoustic response or every media source. Earlier ROG 256/512 failures, 1024
short pass and recovered shutdown failure, and the old ThinkPad hour/partial
−20 run remain distinct history in [status](STATUS.md).

Preserve each host's actually kept runtime, timing and tuning bindings. Record
the negotiated running driver quantum/rate for each physical capture; the
request alone does not establish that condition. Keep different periods,
runtime versions or gain settings in separate measurement groups. The
historical PR 8 source/test receipt remains unchanged. No browser was armed
or physical result collected by file staging.

Before the window, retain runtime/kit/preset/IR/plugin settings hashes, the
physical default/profile/route, owner volume, persistent startup state and
the existing [rollback](LATENCY_COMPARISON.md#7-paired-256-frame-trials--both-tuned-paths-preserved).
Record power state, actual client requests and other media. Preserve the
per-host latency request actually accepted at session time, alongside the
limiter, IR, amplifier protection and stock audio services.

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
xrun affecting that interval. A confidently detected chirp preceding the
chosen click is a valid signed interval: switch actuation can precede the
mechanical click. Retain it with its original negative value; do not clip it
to zero, reject it or collect a replacement solely because of its sign.
Keep genuinely rejected events and their reasons; collect replacements to
reach the included count. If rejection rates or the method change
substantially, report that and begin a new condition rather than hiding the old attempts.

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

## 7. Preserve signed annotations before choosing the analysis path

Re-verify the exact schema against
[the analyser](../scripts/analyse_audio_latency.py) and
[its contract](AUDIO_LATENCY_BUILD.md#clocks-and-corrections-preserve-the-measured-path)
at execution time. Keep raw indices, recordings and method detail in the
private annotation receipt; the strict trial JSON has no arbitrary extra
metadata fields. Use neutral aliases matching `[a-z][a-z0-9_-]{0,63}`.

The separate [manual annotation analyser](MANUAL_LATENCY_ANNOTATIONS.md)
implements the signed path from raw sample positions, with per-recording and
per-condition groups, per-block summaries, retained rejections and conservative
onset ranges. Its [generated example](../tests/audio/synthetic-manual-annotations.json)
is synthetic and contains a placeholder recording digest. Source implementation
is distinct from pending independent review/focused acceptance; no physical
recording has been collected by adding this tool.

The older analyser below still accepts only nonnegative event-to-output delays.
Use the new signed path for a whole condition containing any valid negative
click-to-chirp interval. Do not feed only a nonnegative subset to the older
analyser, shift values, replace negative presses or relabel valid rows invalid.
The old strict v1 schema and its retained passing tests are unchanged. Its
compatible alternative fields remain documented below; raw annotations use
the new tool's separate schema and never masquerade as v1 trial JSON.

| Trial field | Value for this method |
|---|---|
| `kind` | `event-to-output`, explicitly scoped to acoustic key click through speaker response. |
| `method` | A neutral detector alias such as `phone-click-chirp-v1`; different detector revisions use different aliases. |
| `delay`, `unit` | The measured integer sample difference and `samples`, only if the whole condition is representable as described above. Keep every valid signed interval in the private annotations; never invent, clip or exclude a value to satisfy the nonnegative schema. |
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

**How to read either analysis path:** report raw signed min, median,
nearest-rank p95 and max, included and excluded counts, exclusion reasons, conservative measurement bounds and
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

## 9. Review the new emitter before executing its focused cases

[The new Python test wrapper](../tests/test_physical_emitter.py) selects one
[Node case](../tests/physical_emitter_cases.js) per unit method. The cases use
synthetic AudioContext and DOM objects; they open no browser audio device,
recording, network or microphone. Node.js and Python 3 are required for this
new lane. Missing Node is an execution failure, not a skipped pass.

Ten methods cover no autoplay/invalid arming, actual-rate signal bounds and
taper, trusted-key/repeat/modifier/cooldown handling, warm-stream diagnostic
logs, exact stereo reference WAV bytes, owned-source cleanup, cancellation
and stale state callbacks, failed start cleanup, close/event-limit behaviour,
and browser focus/hidden-page bindings. Complete source review precedes their
first run; only failed or invalidated methods repeat. Existing analyser,
native, speaker and CoreAudio source is unchanged, so retain its acceptance.

```bash
python3 -m unittest discover -s tests -p test_physical_emitter.py -v  # New cases only, after review.
```

Source parsing completed with Node v26.8.1 and Python syntax compilation;
these alone are not unit or browser acceptance. After both reviewers cleared
`66080621`, all ten methods passed once with zero failures or skips under
Python 3.14.7 and Node v26.8.1. The [acceptance receipt](../evidence/physical-emitter-acceptance-2026-10-13.json)
binds exact source hashes, method IDs and retained logs. A separate unarmed
Chrome 155.0.8059.40 smoke check passed for local-file load, CSP, initial
controls and diagnostic JSON download, with zero AudioContext creations,
only the three local page/script requests and no console errors. Its private
receipt, screenshot and smoke script hashes are retained in the same public
acceptance receipt. Real-browser reference WAV download was not exercised
because the page was not armed. Actual chirp playback and hardware routing
require the agreed window. These checks do not qualify physical latency,
chirp level or phone-capture accuracy.
