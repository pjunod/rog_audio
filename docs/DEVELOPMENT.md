# Development — build, review and validate a complete batch

Read [implementation](AUDIO_IMPLEMENTATION.md) for lane contracts and
[status](STATUS.md) for acceptance. The owner requested GPT-6.1 Sol builders.

## Clone outside the owner’s source directory

```bash
audio_work_root="$HOME/.local/state/rog-audio/work"  # Durable owned storage.
mkdir -p "$audio_work_root"
git clone https://github.com/pjunod/rog_audio.git "$audio_work_root/change-example"
cd "$audio_work_root/change-example"
git switch -c codex/audio-change
```

Use a unique path if that directory exists. Keep clones, build work and
private receipts in durable owned storage; `/tmp`, `/private/tmp` and `/var/tmp`
are not project-storage locations. Keep dependencies and private inputs
outside the tracked tree. Set test scratch and runtime directories beneath
the retained output when running isolated acceptance; retain receipts before
cleaning owned work. Do not install build dependencies into a
live audio session; use disposable Linux build environments. Record compiler
versions, source commits and container identities. Do not expose sound
devices or host runtime sockets to offline builds.

## Commit and review before running the acceptance tests

Make focused commits and combine related work in one substantial PR. Finish
implementation and compilation first. When the PR is ready to merge, obtain
independent adversarial review of its actual code, resolve findings, and run
each required test once. Retry only failed cases and tests invalidated by a
fix. A result on unchanged code remains valid; documentation-only edits do
not require rerunning audio suites.

The [acceptance workflow](../.github/workflows/acceptance.yml) is manually
dispatched after review, with separate lanes. Its definition first becomes
dispatchable when merged to main, so the initial batch uses the same isolated
Linux validation scripts directly. Do not rerun that accepted batch merely
to obtain a hosted badge. Subsequent batches choose the reviewed branch in
the workflow dispatcher. Do not duplicate a full local suite and hosted CI on identical code.
For a failed case, dispatch only its lane and test ID on the corrected
reviewed revision; rerunning the whole job would repeat passing cases. Record revision and results in
[review](REVIEW.md). Merge only after required checks pass; distinguish
unavailable optional hardware qualification from implemented test coverage.

```bash
python3 scripts/check_repository.py  # Final repository integrity check.
```

This check validates documentation/JSON hygiene without network, hardware,
profile activation or dependency installation. Every tracked profile manifest
must name nonduplicate, tracked regular files whose sizes and SHA256 values
match the published originals. This covers both ASUS and Lenovo inputs.
Lane documents give the
actual build and test commands; do not confuse a skipped compiler with a pass.

## Preserve evidence and dependency rights

[Provenance](PROVENANCE.md) records migration and upstream ownership. Keep
third-party code under its own licence. The OEM profile is an operator-owned
input published at the owner’s request under profiles/asus/gu605mz, with
equivalent ThinkPad originals under profiles/lenovo/x1-extreme-gen1. Private
media remains outside Git. Hashes identify an artifact, not authenticity or
acoustic correctness.

No current test demonstrates macOS-level latency, speaker quality, Dolby
certification or complete Atmos format support. Physical comparison needs
explicit recorded methods and measurements in a later coordinated window.

## Select a failing check without repeating the suite

The speaker wrapper accepts `bash scripts/ci_speaker.sh unit TEST_ID`; a
single OEM profile conversion accepts `music`, `dynamic` or `off` as its stage.
Latency accepts `--stage unit --test-id MODULE.CLASS.test_METHOD` or one of
its named config/native stages. Atmos accepts repeated `--test METHOD`.
The full first pass runs each lane once; an unknown ID is an error.

Hosted inputs are passed as quoted data, not interpolated shell code. Jobs
have read-only GitHub permissions, no credentials persisted by checkout, and
no automatic push/PR trigger. Runtime tests do not mount sound devices or
session sockets. Synthetic logs can appear in job output; personal captures
and credentials cannot enter that workflow.

The installation lane runs file, source-staging and native routing tests through
`python3 scripts/validate_speaker_install.py --stage all`. Select `install`, `inspector`,
`source` or `routing`, optionally with repeated `--test-id` arguments, to retry
only failed cases. Missing compiler/source prerequisites and skipped tests
fail the lane. The manually dispatched job stages only pinned public source.
Real EasyEffects graph acceptance has two separate selectors and uses the
retained compiled image and source-built kits; see
[speaker installation](SPEAKER_INSTALL.md). It is deliberately separate from
the unit lane so a unit retry does not rebuild or rerun both runtime cases.


The `coreaudio` lane runs only the offline Mac-summary tests on Linux; it does
not require HAL access or repeat the native Mac compile/observation receipt.
Set `test_ids` to a failed `test_analyse_coreaudio_latency.CLASS.test_METHOD`
for a focused retry. Input is checked before unittest import, and skipped or
empty acceptance is an error. The native probe is compiled on a Mac when its
C source changes; that compiler receipt is distinct from these parser tests.


The `audio-path` lane covers only the new tuned-path inspector, file-only trial
lifecycle and inactive native filter rules. Its `all` selection runs `unit-path`,
`unit-trial`, `compile`, `config`, `filter-match`, the four `filter-other-*`
properties (`app`, `node`, `group`, `role`), `filter-env-latency` and
`filter-env-quantum`. Select one failed stage for retry; unit stages additionally
accept exact failed method IDs. Independent stages continue after a failure,
so their passing results remain usable. This lane does not rerun the previous
42 latency tests or either accepted speaker-runtime graph case.


The `atmos-energy` lane runs only the offline channel-energy methods through
`python3 scripts/validate_atmos_energy.py`, without a Cavern build or codec
suite. Exact failed IDs use repeated `--test-id` arguments in the form
`test_analyse_atmos_render.AnalyseAtmosTests.test_METHOD`. Unknown/duplicate
IDs, skips and empty results fail. A new optional `--report` is mode 0600.
See [reference acceptance commands](ATMOS_REFERENCE.md#run-only-the-reviewed-analyzer-methods).


The `manual-annotations` lane runs only the eleven generated/manual-sample
analysis methods through `python3 scripts/validate_manual_annotations.py`.
It does not capture sound, hash personal recordings in CI, build Cavern or
repeat the older latency/emitter/speaker suites. Choose that lane explicitly;
leave `test_ids` empty for the one reviewed first pass, or supply only exact
failed/invalidated IDs for a retry. The workflow's generic `selection` stage
input does not select methods for this lane.

```bash
# Only after review, and only if this exact method failed or was invalidated.
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_manual_annotations.py \
  --report private/new-manual-annotation-retry.json \
  --test-id test_analyse_manual_annotations.AnnotationTests.test_signed_statistics_and_asymmetric_onset_timebase_bounds
```

Repeat `--test-id` for additional failed methods. Malformed or duplicate IDs
fail before loading tests; an unknown method cannot yield passing acceptance.
The mode-0600 report is reserved exclusively before execution, so an existing
result path does not trigger another test run. Failures, errors, skips and
empty results fail the lane; reports bind source hashes and synthetic-only
scope. See [manual annotation acceptance](MANUAL_LATENCY_ANNOTATIONS.md#run-only-the-reviewed-focused-methods)
for the first-pass command and schema/measurement limits. Do not rerun the
accepted first pass later as a hosted badge.


Manual-annotation acceptance snapshots the analyser, runner, test module and
its dynamically read generated JSON fixture before loading project code.
Reports retain those initial hashes and compare them with a second snapshot
after execution. Any changed/unreadable source fails acceptance even if the
methods themselves passed; no passing result is rebound to after-only hashes.
The provenance regression uses a controlled fake loader/runner and an owned
fake project tree, without recursively executing the real unit suite.

## Live Atmos selection

The manual-only `atmos-live` workflow lane is independent of legacy Atmos and
speaker acceptance. Select `units` for the full IDs exposed by
[`validate_atmos_live.py`](../scripts/validate_atmos_live.py), `integration`
for exact private virtual-sink case IDs, or `all` for this new lane's initial
acceptance. [Live playback](LIVE_ATMOS.md#acceptance--run-selected-methods-only-after-independent-review)
documents commands and evidence limits. Review and fix the complete source
before the first method run; retry only failed or invalidated methods/cases.
No push trigger, host sound device or desktop session socket is added.

Local live-wrapper retries default `--test-id` to units and `--case` or
`--joc-input` to integration. Mixed stage selectors and explicit `all` with
retry selectors/input are rejected before external commands. The pure
[`select_stage`](../probes/atmos/live_ci_options.py) helper is shared by the
wrapper and its focused regression methods.
