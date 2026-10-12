# Audio latency build — inspect, measure and generate reversible candidates

**Status:** tools implemented; native config parse passed, final integration checks
pending, physical data absent ·
**Written:** 2026-10-12 · **Executes:** diagnostics/latency lane in
[implementation](AUDIO_IMPLEMENTATION.md).

Read [hardware](AUDIO_HARDWARE.md) and [audio quality](AUDIO_QUALITY.md).
The ROG already has realtime data-loop scheduling. Build diagnostics and
measurement tools first; do not solve a presumed scheduler problem or lower
buffers on the live desktop. Sonos work is last and outside this lane.

## 1. Build a reusable read-only inspector

Implemented interface, following the existing display inspector's privacy model:

```bash
python3 scripts/inspect_audio.py --output PRIVATE_JSON
python3 scripts/inspect_audio.py --from-capture PRIVATE_JSON --public-summary SUMMARY_JSON
```

Native Linux collection uses bounded subprocess calls with an allowlist:
ALSA card/codec metadata, package versions, read-only PipeWire graph/settings,
current profiles/routes, relevant driver/firmware diagnostics, config hashes
and scheduler state. Never record microphone audio, play a probe, install a
package, invoke setters, restart a service or elevate itself. A caller may
supply a privately captured kernel log if permission is unavailable.

Every probe returns `ok`, `unavailable`, `permission-denied`, `timeout` or
`parse-error`; missing data is not a negative hardware finding. Handle no
session bus, absent tools, suspended nodes, hotplug during collection and
multiple cards. Resolve the real session environment; do not hard-code UID
1000, card 1 or PipeWire node 61. The first inspected route is evidence, not
a global constant. macOS invocation should report unsupported collection or
use explicitly scoped native inventory, never execute Linux setters.

Public summaries use an allowlisted schema, not regex-only redaction of full
logs. Omit user/client/app names, node serials, USB serials, hostnames, addresses,
absolute home paths, session cookies and arbitrary configuration content.
Include source-hash provenance and explicit limits. Construct privacy tests
with hostile nested graph properties and diagnostic errors containing secrets.

## 2. Analyse physical latency without relabelling graph timing

Offline interfaces (candidate requires explicit target arguments; see §6):

```bash
python3 scripts/analyse_audio_latency.py --input TRIALS_JSON --output RESULT_JSON
python3 scripts/prepare_audio_latency.py --inventory PRIVATE_JSON --quantum 256 --output PRIVATE_CANDIDATE
```

Define and document `TRIALS_JSON` schema before implementation. Each trial
must specify measurement kind (`round-trip`, `event-to-output`, `idle-onset`
or `av-offset`), measured delay and unit, sample rate if sample-based, method,
route, reference/capture clock relationship, uncertainty, power/load state,
DSP state and validity/rejection reason. Preserve raw and corrected values;
never subtract converter or propagation delay without an explicit model and
recorded parameter. Unsynchronised cross-device timestamps are not a valid
latency measurement. Reject NaN, infinity and invalid rates/counts.

Report count, exclusions, median, explicitly defined p95 estimator, min/max
and uncertainty. Keep each route/measurement kind/state separate. Never pool
ASUS speakers, a USB interface, Bluetooth and HDMI into one latency number.
One-way latency cannot be inferred by halving round-trip unconditionally.
Keep PipeWire `quantum_frames / rate_hz` in a separate `graph_period_ms` field.
A fixture-generated result must be labelled synthetic.

Comparison gates in [audio quality](AUDIO_QUALITY.md) are provisional: 100
onset trials per state, zero new xruns/audible gaps in a 60-minute bounded
load run, and a same-path Mac comparison. No physical data exists yet. Build
an import/analysis pipeline and an exact capture procedure; do not fabricate
trials to satisfy the acceptance threshold. The M4 Air is primary and M3 Max
secondary; exact OS/models/interface must be recorded when tested.

## 3. Generate candidates without applying them

`prepare_audio_latency.py` writes a new bundle containing a candidate
configuration, manifest and restoration instructions. It must never change
live metadata or restart services. Keep observed values and proposed changes
side by side, including explicit previous user configuration and unknowns.
Require an unambiguous target route and supported installed config version.
Refuse globally forcing a guessed quantum when endpoint/application-specific
policy can express the experiment. Do not create a watchdog.

Start with 256 and 128 frames at the observed 48 kHz; 64 remains optional.
Retain the working realtime settings and ALSA batch defaults unless a trace
shows why a device-specific change is needed. Account for PulseAudio clients'
additional buffering and any speaker DSP delay. Do not assume a requested
client latency is what the graph actually negotiated. Existing remembered
USB-output preference is not permission to erase it.

The bundle manifest includes inventory/config hashes, proposed values,
version constraints and `activation_state: "not-installed"`. Configuration
syntax must be checked against an isolated PipeWire/WirePlumber environment
matching the installed versions where practical; no host sockets or sound
hardware. If a matching package environment cannot be built, report that
constraint and retain the candidate as unvalidated rather than install it.

## 4. Focused regression and integration checks

Test probe timeouts, partial failures and absent commands without hanging;
privacy allowlists; supported/unsupported inventory schemas; mixed units and
measurement kinds; percentile calculation on hand-computable fixtures;
invalid clocks/nonfinite values; clipping/exclusion flags; deterministic
configuration generation; path/overwrite handling; and no side effects.
The physical analyser is standard-library Python unless a justified algorithm
requires a pinned numerical dependency. Use synthetic data for public tests.

Prepare the bounded recording/playback workflow as an explicit later operator
step. It must identify loopback wiring, shared clock or trigger, test signal,
levels, sample rate, signal detection/correlation method, ambiguity rejection,
error counters and uncertainty. Capture is separately opt-in and cannot be
hidden in `inspect_audio.py` or repository checks.

## 5. Ship actual tooling with a source-bound receipt

Deliver code, synthetic tests, documented schemas, an example generated
candidate and an analysis example clearly labelled synthetic. Run on the
private read-only snapshot if possible, publishing only a sanitised summary.
Record the Linux tool/config validation separately from macOS unit tests.
Prepare rollback and the remaining physical benchmark procedure, then use
independent adversarial review and the affected fast lane in
[implementation](AUDIO_IMPLEMENTATION.md). Do not claim a latency improvement
until a physical before/after receipt exists.

## 6. Run the implemented tools — private inputs and inactive outputs

The [inspector](../scripts/inspect_audio.py),
[analyser](../scripts/analyse_audio_latency.py) and
[candidate generator](../scripts/prepare_audio_latency.py) use Python's standard
library. None plays, records, sets metadata, changes routing or restarts a
service. Outputs are new files with mode `0600`; existing files and symlinks
are preserved. Candidate directories have mode `0700`. Keep raw inventory,
trial reports and generated real-endpoint candidates in ignored `private/`.

```bash
python3 scripts/inspect_audio.py --output private/audio-inventory.json
python3 scripts/inspect_audio.py --from-capture private/audio-inventory.json \
  --public-summary private/audio-summary.json
python3 scripts/analyse_audio_latency.py --input private/trials.json \
  --output private/analysis.json
python3 scripts/prepare_audio_latency.py --inventory private/audio-inventory.json \
  --quantum 256 --node-name alsa_output.EXACT_NAME \
  --route-name EXACT_ACTIVE_ROUTE --client-binary pw-play \
  --output private/latency-256
```

**How to read it:** `graph_default.graph_period_ms` describes the core default,
not a measured running period. `graph_settings` separately reports observed
metadata, including any forced values. Suspended endpoints are included.
Missing session sockets or tools produce `unavailable`; missing permissions
produce `permission-denied`. Partial probes never prove hardware absent.
Native collection on macOS reports `unsupported-platform` without probing.
`--kernel-log PRIVATE_FILE` imports an already captured kernel log; collection
does not elevate. The optional `--legacy-capture` adapter imports the private
2026-10-12 `captured_at`/`commands` snapshot only for summarisation. That
snapshot lacks prior config/version evidence and cannot generate a candidate.

The inventory envelope is `schema_version: 1`, `kind: "audio-inventory"`,
`evidence_kind: "live-read-only"`, `collection_status`, `probes`, `files`,
`config_root` and `user_config`. Probe values contain a status, and private
stdout/stderr for completed commands. The fixed command allowlist is in
[the inspector](../scripts/inspect_audio.py); no caller supplies a command.
`pw-dump` retains graph profiles/routes privately. ALSA card/codec files and
user config bytes/hashes stay private. Scheduler summaries retain only
recognised data-loop classes/priorities. A public summary is reconstructed
from fixed numeric/enumerated fields and digest strings; arbitrary graph
properties, diagnostic errors and config contents are never copied.

The candidate requires one exact ALSA sink and one matching currently active
output route. Unknown versions, previous config, rates other than 48 kHz,
ambiguous routes/nodes or an existing trial filename are refusal conditions.
The supported interface family is PipeWire `1.4`–`1.6` and WirePlumber `0.5`;
only the exact versions in the validation receipt have been exercised.
Custom native-client config selection must be checked again before activation.

The generated `client.conf.d` fragment matches all three of
`application.process.binary`, `target.object` and output-stream media class.
It sets only `node.latency`, a suggested fraction in seconds. It neither
forces the graph quantum nor edits the ALSA endpoint or WirePlumber policy.
PulseAudio clients require a separately designed buffering experiment. An
endpoint shared by speakers/headphones can change route after inspection;
recheck the active route immediately before a coordinated test.
[PipeWire's property reference](https://docs.pipewire.org/page_man_pipewire-props_7.html)
defines this suggestion and its possible negotiation to a larger period;
[client configuration](https://docs.pipewire.org/page_man_pipewire-client_conf_5.html)
defines `stream.rules`. The bundle's `manifest.json` contains observed and
proposed values, inventory/config hashes and `activation_state: "not-installed"`.
`validation_state: "unvalidated"` is deliberate: an offline source receipt
validates a synthetic rule; it cannot certify a later private bundle or route.

**Recovery:** `previous-user-config.json` retains the inspected config bytes
and hashes. `RESTORE.txt` gives the bounded operator workflow: snapshot again,
check the destination absent, add only this fragment in the agreed window,
restart only the named test client, then remove only the hash-matching trial
fragment and relaunch that client. Verify routing, defaults and graph timing
again. Do not use this bundle to rewrite the owner's existing settings.

## 7. Physical capture remains a separate operator gate

For wired round-trip trials, connect line output to line input on a known
interface with one shared converter clock. Record exact interface/model,
OS/build, wiring and gain in private setup metadata; use neutral aliases in
trial files. Do not connect amplified speaker outputs to line inputs. For
speaker onset, capture an electrical trigger and the microphone response on
the same multichannel recorder. Event-to-output includes the event trigger;
idle-onset includes a recorded, specified idle duration. A/V trials require a
photodiode and microphone on that same clock; define positive delay as audio
late. Unsynchronised computer timestamps are excluded.

In the coordinated window, use a short band-limited pulse or a fixed-seed
noise burst at a conservative, recorded level. Record 48 kHz PCM without
clipping. Preserve the signal and recording privately. Detect the trigger,
then correlate the response against the recorded source in a bounded search
window fixed before capture. Record detection threshold, window and competing
peak criterion in the private method receipt. Reject missing triggers,
clipping, ambiguous peaks and xruns; keep rejected trials with reason codes.
Record sample quantisation, trigger/detection error, clock calibration and
microphone distance uncertainty as conservative bounds. Subtract converter
or propagation delay only with a named, measured model and parameter bounds.
Do not halve round-trip to infer one-way delay.

Collect at least 100 onset trials per route/configuration/power/load/DSP state.
Then collect graph error-counter baselines and deltas over a bounded 60-minute
load test, recording audible gaps separately. Inspect negotiated quantum
while the test client is active. Repeat the same path and method on the M4
Air first, M3 Max second, recording exact OS/models/interface. The analyser
checks counts and exclusions, not listening quality or the 60-minute gate.
No synthetic fixture satisfies these physical gates.

## 8. Reproduce offline validation

```bash
python3 -m unittest discover -s tests -p 'test_*audio*.py'
python3 scripts/check_repository.py
```

[The Linux harness](../tests/audio/linux-validation.sh) is intended only for
a disposable Ubuntu container containing the new lane scripts/tests and a
synthetic candidate at `/case/candidate.conf`. It installs dependencies there,
parses `client.conf` with `pw-config`, compiles an inactive native stream
probe with warnings as errors, and checks matching and nonmatching rules on
an isolated PipeWire daemon. No host runtime/config sockets or `/dev/snd`
are mounted. The probe uses no audio buffers and never activates the stream.
The standalone parser passed on the matching Linux package versions. Full
merge-code validation is pending in the dedicated audio repository; the
subsequent run must include the synthetic evidence fixture as well as tests.

## 9. Trial schema and statistics — preserve clocks and corrections

### Run analysis on a declared trial set

```bash
python3 scripts/analyse_audio_latency.py --input PRIVATE_TRIALS_JSON --output PRIVATE_RESULT_JSON
```

The analyser performs no playback, recording, network access or subprocess
calls. Input must be a nonsymlink regular UTF-8 JSON file, at most 8 MiB,
with at most 32 levels of nesting and 10,000 trials. Duplicate object keys,
unknown/missing schema fields, malformed JSON, nonfinite values, booleans
in numeric fields and invalid rates/counts fail with a fixed reason code.
Output is a newly created private file, mode 0600. Existing destinations,
symlinks and input/output identity cannot be overwritten. Exit 0 means a
report was written; 1 means output creation failed; 2 means input/schema
or argument failure. Errors never include supplied paths or payload text.

The parser cannot establish whether a declared measurement really happened.
The operator is responsible for evidence class and documented uncertainty.
Reports remain private until reviewed; neutral aliases are operator supplied.

### V1 input uses exact fields and explicit units

The root contains exactly `schema_version`, `evidence_class`, `setups` and
`trials`. `schema_version` is integer 1. `evidence_class` is `synthetic` or
`physical-measurement`; classes cannot be mixed in one report. `setups` has
1–128 objects with exactly `setup_id`, `system`, `os`, `interface`. All four
are neutral aliases, with `setup_id` unique. Keep an exact private mapping
from these aliases to OS/version, machine/model and instrument/interface,
clock wiring, detection algorithm parameters and source-capture hashes.
Do not put serials, owner identities or raw filenames in aliases.

All aliases match `[a-z][a-z0-9_-]{0,63}`. Thus paths, spaces, free-form
errors and uppercase identifiers are rejected. This is a schema constraint,
not a guarantee that an otherwise matching alias contains no private data.
Setups and trial IDs are unique; a trial's setup must exist.

Every trial has exactly these fields:

| Field | Contract |
|---|---|
| `trial_id`, `setup_id`, `configuration_id` | Neutral aliases. Separate baseline/candidate IDs; setup identifies the instrument/system/OS path. |
| `kind` | `round-trip` · `event-to-output` · `idle-onset` · `av-offset`. |
| `delay`, `unit` | Finite measured scalar and `ms` · `s` · `samples`. Samples require an integer count; negative values only for `av-offset`. Absolute normalised delay ≤ 1,000,000,000 ms. |
| `sample_rate_hz` | Integer 1–768000 Hz, or null when unavailable and no sample-based field is present. This is the measurement clock rate, independent of graph rate. |
| `method`, `route` | Neutral aliases naming a privately documented detector and the exact physical route. Keep Bluetooth, HDMI, USB and internal speakers separate. |
| `clock` | Exact clock relationship object described below. |
| `uncertainty` | Exactly `bound` and `unit`. Finite nonnegative measurement-error bound in `ms`, `s` or `samples`; sample fractions permitted here for interpolated bounds. This is a conservative absolute bound, not standard deviation or a confidence interval. |
| `power_state`, `load_state`, `dsp_state` | Neutral aliases, e.g. `ac`, `idle`, `stock`. Document load/DSP versions, hashes and trial conditions privately. |
| `valid`, `rejection_reason` | Boolean and null if true; if false, an allowlisted reason is mandatory. |
| `flags` | Unique list drawn from `clipping`, `ambiguous-detection`, `xrun`, `missing-trigger`. Any flag excludes the trial even if `valid` was true. |
| `corrections` | Up to 16 explicit correction objects; an empty list applies no converter/propagation/trigger subtraction. |
| `graph` | Null, or exactly integer `quantum_frames` (1–1048576) and `rate_hz` (1–768000). Graph metadata is never subtracted. |

For an explicitly invalid trial, rejection reasons are `clipping`,
`ambiguous-detection`, `xrun`, `missing-trigger`, `clock-invalid`,
`operator-rejected` or `capture-incomplete`. Rejected trials still require
valid numeric and structural fields, so a corrupt import cannot be silently
treated as usable data.

### Clocks and corrections preserve the measured path

`clock` contains exactly `{ "relationship": "same-clock" }` for a shared
physical reference/capture clock. A shared-clock trigger or same interface
loopback must be documented in the private receipt; clock identity is not
established merely by using the same nominal sample rate.

`{ "relationship": "unsynchronised" }` excludes the trial as
`clock-invalid`, and corrected delay/combined uncertainty are null. Its raw
value is retained solely as excluded evidence. Cross-device timestamps
without a synchronization model cannot qualify latency.

For `synchronised`, supply exactly `relationship`, `model_id`, `offset_ms`,
`uncertainty_ms`. The model ID names the private synchronization calibration.
`offset_ms` is the amount by which the measured capture-minus-reference delay
is inflated by clock offset; corrected delay subtracts it. Offsets may be
signed. The nonnegative uncertainty must include residual calibration error
and drift over the capture interval. A common wall-clock name is insufficient.
Different offsets or uncertainty/calibration IDs form distinct groups; use a
shared measurement clock for repeated-trial comparisons where possible.

A correction object contains exactly `model_id`, `kind`, `delay_ms`,
`uncertainty_ms`. Model IDs are unique within a trial. Kind is `converter`,
`propagation` or `trigger`; delay and uncertainty are finite nonnegative
explicit recorded parameters. The private model receipt must justify the
parameter for this path, level, sample rate and detector. For propagation,
retain distance and sound-speed assumptions; for converter delay, retain the
scoped calibration; for trigger delay, retain trigger calibration. Do not
subtract the same latency twice via clock offset and a correction model.

```text
 corrected_ms = raw_ms - clock_offset_ms - sum(model_delay_ms)
 bound_ms     = measurement_bound_ms + clock_bound_ms + sum(model_bound_ms)
```

The bound is additive, so independence is not assumed. A negative corrected
non-AV latency is excluded as `negative-corrected-delay`, even if its bound
spans zero; retain its raw/corrected values to diagnose an invalid model.
AV offset is audio-minus-video: positive means audio late, negative means
audio early. Round-trip is never halved into inferred one-way latency.

### How to read group statistics and acceptance fields

Grouping uses setup, configuration, kind, method, route, measurement rate,
power/load/DSP states, the full clock model, full correction models and full
graph declaration. Input units may differ within a group because they are
converted to ms. Corrections are sorted by model ID; input order does not
alter a report. Trial order is sorted by ID. Graph period is separate:
`graph_period_ms = quantum_frames * 1000 / rate_hz`, or null when unknown.

Each group reports total, included and excluded counts, per-reason counts,
raw and corrected min/median/p95/max for included trials, and every trial's
raw unit/value, normalised value, corrected value, original validity/reason/
flags, full applied models, combined bound and exclusion reasons. Multiple
reasons may apply to one trial, so reason counts need not sum to exclusions.
All-excluded groups use null statistics; empty input has no groups.

Median is the central order statistic, or arithmetic mean of the two central
values for even n. P95 is nearest-rank: ascending index `ceil(0.95*n)-1`.
For values 1–20 ms, median is 10.5 ms and p95 is 19 ms; small n is explicitly
reported and does not establish a population tail estimate.

For every corrected statistic, compute the same order statistic on each
trial's `value - bound` and `value + bound` to obtain conservative lower/
upper bounds. Do not divide systematic uncertainty by sqrt(n). This bounds
declared measurement errors, not sampling uncertainty: a population/sampling
confidence interval is explicitly `not-estimated`.

The onset trial-count field requires 100 included `idle-onset` or
`event-to-output` trials per group. Physical input can report `count-met`
or `insufficient-trials`; other physical kinds are `not-applicable`.
Synthetic input always reports `synthetic-only`, regardless of count.
`qualification` is always `not-established`: the analyser does not evaluate
the 60-minute load-run/error-counter gate, audible gaps, or same-path Mac
comparison. It cannot certify latency improvement from a count alone.

### The reproducible example is synthetic

[Synthetic trial JSON](../tests/audio/synthetic-trials.json) contains twenty
hand-computable declared delays, 1–20 ms, generated without audio capture.
[Synthetic result](../evidence/audio-latency-synthetic-analysis.json) preserves
its evidence class and input SHA-256. The example passes no physical gate.
Regenerate it only into a new output path, then review and replace the tracked
example deliberately; the CLI refuses overwriting files.

```bash
python3 -m unittest discover -s tests -p test_analyse_audio_latency.py -v
```

Tests cover hand-computable tails, mixed units, clock/calibration separation,
exclusions, signed AV, explicit corrections, heterogeneous uncertainty,
synthetic-vs-physical count gates, schema corruption, NaN/infinity/booleans,
duplicates, deep JSON, special files/symlinks, concurrent input edits,
exclusive mode-0600 output and private argument/error text. Physical capture
and detection still require the separately coordinated operator procedure.

## 10. Integration handoff — dedicated audio repository

On 2026-10-12 the owner moved audio implementation to
[rog_audio](https://github.com/pjunod/rog_audio). Import the lane files
selectively; do not push inherited display history. The parent integration
batch owns common README/status edits, final adversarial review and one final
unit-test run. This lane's later identifier guards and validation packaging
changes have not yet been run under that final workflow.

[The development receipt](../evidence/audio-latency-build-2026-10-12.json)
records exact runtime packages/image and distinguishes earlier working-tree
checks from pending final source validation.
[The privacy-filtered snapshot](../evidence/audio-latency-snapshot-2026-10-12.json)
reports graph defaults and scheduling; its physical latency is null.
No improvement, no live candidate activation and no physical acceptance are
claimed.

[The Linux packaging CLI](../scripts/validate_audio_linux.py) explicitly runs
an isolated container and stores diagnostics in a new private file. It accepts
an optional private SSH alias/key; never put those arguments in a public
receipt. The image must already exist; `--pull=never` prevents an implicit host
pull. Package installation is confined to the disposable container, and exact
PipeWire/WirePlumber package versions are pinned. Include both synthetic input
and result fixtures. The prior container packaging omitted the result fixture;
that failure was corrected in source but not rerun after the workflow change.

```bash
python3 scripts/validate_audio_linux.py --output private/linux-validation.json
```

The parent should run this after the integration review; it includes the
focused unit suite once plus compiler and native-rule checks. For remote
Docker, append the explicitly authorised `--ssh-target` and `--identity-file`
arguments. There are no host sound/config/runtime mounts. An interrupted run
attempts removal of only its own uniquely named container.
