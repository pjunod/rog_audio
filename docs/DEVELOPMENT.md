# Development — build, review and validate a complete batch

Read [implementation](AUDIO_IMPLEMENTATION.md) for lane contracts and
[status](STATUS.md) for acceptance. The owner requested GPT-6.1 Sol builders.

## Clone outside the owner’s source directory

```bash
git clone https://github.com/pjunod/rog_audio.git /tmp/rog-audio-work
cd /tmp/rog-audio-work
git switch -c codex/audio-change
```

Use a unique path if that directory exists. Keep dependencies and private
inputs outside the tracked tree. Do not install build dependencies into a
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
`python3 scripts/validate_speaker_install.py --stage all`. Select `install`,
`source` or `routing`, optionally with repeated `--test-id` arguments, to retry
only failed cases. Missing compiler/source prerequisites and skipped tests
fail the lane. The manually dispatched job stages only pinned public source.
Real EasyEffects graph acceptance has two separate selectors and uses the
retained compiled image and source-built kits; see
[speaker installation](SPEAKER_INSTALL.md). It is deliberately separate from
the unit lane so a unit retry does not rebuild or rerun both runtime cases.
