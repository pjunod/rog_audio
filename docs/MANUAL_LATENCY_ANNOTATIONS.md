# Manual latency annotations — preserve signed click-to-chirp samples

**Status:** implemented; independent review and focused acceptance pending ·
**Written:** 2026-10-15 · **Executes:** the signed annotation path in
[the physical method](PHYSICAL_LATENCY_METHOD.md#7-preserve-signed-annotations-before-choosing-the-analysis-path).

Companion to [the older trial schema](AUDIO_LATENCY_BUILD.md) and
[current acceptance](STATUS.md). This offline tool summarises manually marked
sample positions. It never captures sound, detects waveforms, starts playback,
opens a microphone, changes tuning or establishes physical validity. The
existing v1 trial analyser is unchanged.

## Run the generated example before using private annotations

The [example JSON](../tests/audio/synthetic-manual-annotations.json) is generated;
its all-zero recording digest is a placeholder and no such recording exists.
Choose a new output path because existing files are never overwritten:

```bash
mkdir -p -m 0700 private  # Durable private reports, outside version control.
python3 scripts/analyse_manual_annotations.py \
  --input tests/audio/synthetic-manual-annotations.json \
  --output private/synthetic-annotation-result.json
```

**How to read it:** four attempted presses contain three included signed
intervals: −5, 0 and 12 ms; one missing chirp is retained and excluded. The
median is 0 ms and nearest-rank p95 is 12 ms. `synthetic-only`,
`physical_validity: not-verified` and `qualification: not-established` remain
explicit. These numbers describe fabricated annotations, not any laptop.
Unknown timebase calibration is `null`; annotation bounds remain available,
while combined annotation/timebase bounds remain `null`.

## Bind each annotation to its declared recording and condition

The strict v1 input has exactly `schema_version`, `evidence_class`,
`recordings`, `conditions` and `trials`. Evidence is an operator declaration:
`synthetic` or `physical-measurement`. A label or plausible digest cannot
prove that a physical recording exists. Use these exact fields; arbitrary
metadata stays in the private method receipt.

| Object | Required fields and limits |
|---|---|
| Recording | `recording_id`; lowercase 64-hex `sha256`; integer `sample_rate_hz` 1–768000; integer `frame_count` 1–2^40; `timebase_scale_bound_ppm` null or finite 0–100000; `preprocessing` alias; up to 16 unique `unquantified_biases` aliases. |
| Condition | `condition_id`, `setup_id`, `route`, `settings_id`, `method_id`, `keyboard_id`, `geometry_id`, `signal_id`, `power_state`, `load_state`, `phase`. All are aliases; phase is `pilot` or `formal`. |
| Trial | Unique `trial_id`; existing `recording_id` and `condition_id`; `block_id`; `click`; `chirp`; boolean `valid`; unique `rejection_reasons` list. |
| Onset | Null for a missing/rejected onset, or exactly integer `sample`, `lower`, `upper`, with `0 ≤ lower ≤ sample ≤ upper < frame_count`. Both onsets use this one recording's frame indices. |

Aliases match `[a-z][a-z0-9_-]{0,63}`. Inventories each contain 1–128 unique
records; there are at most 10000 trials. Missing/extra fields, duplicate JSON
keys, nonfinite numbers, boolean integers, invalid references, out-of-range
samples and duplicate included click or chirp anchors within one
condition/recording fail with fixed reason codes. Two analysts may compare
methods using separate conditions; their annotations are never pooled.

Use a distinct condition when setup, route, runtime/preset/gain, actual graph,
browser, detector, keyboard, geometry, signal, power or load changes. Bind the
aliases to exact hashes/versions and preserved settings in the private method
receipt. The analyser cannot infer these physical conditions from labels.

A valid trial has both onsets and no rejection reasons. A rejected trial has
one or more of `missing-click` · `missing-chirp` · `ambiguous-onset` ·
`clipping` · `xrun` · `overlapping-sound` · `incomplete-capture` ·
`operator-rejected`. Available onsets and computed signed intervals remain in
rejected rows; rejection counts are reported separately. Rejecting a valid
interval solely because it is negative would bias the result.

## Interpret intervals without inventing uncertainty

For one recording at declared rate `f`, the nominal interval is
`1000 * (chirp.sample - click.sample) / f` ms. The conservative annotation
range is `[chirp.lower - click.upper, chirp.upper - click.lower]` samples.
The chosen samples are retained as integers and are never clipped to zero.

`timebase_scale_bound_ppm` declares a bound on **time per sample**, relative
to the nominal `1000/f` ms. It is not an inferred sample-rate tolerance.
When present, all combinations of the two annotation endpoints and the two
positive scale factors `1 ± ppm/1000000` define the combined interval. This
preserves signed and zero-crossing ranges. Null means unknown, not zero.
Unquantified keyboard/recorder/geometry biases remain named; these numerical
bounds do not silently cover them. No graph period or propagation model is
subtracted, and no electrical switch-actuation timestamp is inferred.

Groups never mix different recording IDs or conditions. Each group retains
input row indices and per-block summaries in declared first-seen block order,
plus the aggregate for those blocks within the same recording/condition.
Different recordings are deliberately separate even when nominal rates match.
For included rows, output reports signed min, median, nearest-rank p95 and max.
The p95 index is `ceil(0.95*n)-1`; endpoint order statistics provide conservative
bounds on each statistic. These are measurement-model ranges, not sampling
confidence intervals. Sampling confidence is `not-estimated`.

An all-rejected group has null statistics and retained reasons. An empty trial
list returns no groups and explicitly lists unused condition/recording IDs.
`onset_count_status` is `synthetic-only` for generated data, `pilot` for a
declared physical pilot, or `count-met`/`insufficient-trials` for formal groups
with/without 100 included rows. Count alone never establishes physical validity,
acoustic accuracy or Mac parity.

## Verify explicit file bytes without promoting their meaning

By default the digest, rate, frame count and annotations are declarations.
Optionally supply a local file explicitly; no recording paths are discovered
from JSON, directories or the network:

```bash
# Replace the alias/path with your declared recording and retained original.
python3 scripts/analyse_manual_annotations.py \
  --input private/annotations.json --output private/new-annotation-result.json \
  --verify-recording phone-track=private/original-recording.wav
```

The file is hashed in bounded chunks, up to 2 GiB, and must match the declared
digest. `digest-matched-explicit-file` means only those bytes were checked;
format, frame count, sample rate, sample positions and physical provenance
remain operator declarations. Even a digest-matched manufactured file cannot
make `physical_validity` verified or establish qualification.

Input JSON is bounded at 8 MiB/depth 32. POSIX regular-file checks, no-follow
and nonblocking opens reject symlinks/special files and detect observed
changes during reads. Output is created exclusively at mode 0600 and synced;
an existing file, symlink or FIFO is a collision, never an overwrite. A failed
write can leave a new partial private file for inspection. Exit 0 means the
report was written; 2 means invalid input/binding/arguments; 1 means output
creation/write failed. Error messages omit private paths and input values.

## Run only the reviewed focused methods

After independent review, run the eleven new methods once through the focused
runner. This does not repeat the older analyser or emitter suites:

```bash
mkdir -p private  # Use a new result name for each authorised acceptance run.
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_manual_annotations.py \
  --report private/manual-annotation-acceptance.json
# Only a failed/invalidated method may be selected for a later retry.
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_manual_annotations.py \
  --report private/manual-annotation-retry.json \
  --test-id test_analyse_manual_annotations.AnnotationTests.test_signed_statistics_and_asymmetric_onset_timebase_bounds
```

The manually dispatched `manual-annotations` CI lane uses the same runner and
supports exact failed `test_ids`; it has no push trigger. `source_sha256`
retains hashes of the three source/test files and generated JSON fixture
captured before project-code loading. `source_sha256_after` is compared after
execution; an unreadable or changed file sets `source_unchanged: false` and
fails acceptance even when methods pass. After-only hashes cannot rebind old
in-memory code to untested disk bytes. The provenance regression uses a fake
controlled loader/runner, without recursively running the real suite.

Reports retain test counts and synthetic-only scope. A result-path collision
is refused before tests execute. Public summaries need separate privacy/scope
review; raw recordings and annotation reports remain private.
