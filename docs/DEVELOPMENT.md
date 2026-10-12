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

CI is manually dispatched after review, with independent jobs so a failed
job can be retried without rerunning passing lanes. Do not duplicate a full
local suite and hosted CI on identical code. Record revision and results in
[review](REVIEW.md). Merge only after required checks pass; distinguish
unavailable optional hardware qualification from implemented test coverage.

```bash
python3 scripts/check_repository.py  # Final repository integrity check.
```

This check validates documentation/JSON hygiene without network, hardware,
profile activation or dependency installation. Lane documents give the
actual build and test commands; do not confuse a skipped compiler with a pass.

## Preserve evidence and dependency rights

[Provenance](PROVENANCE.md) records migration and upstream ownership. Keep
third-party code under its own licence. The OEM profile is an operator-owned
private input; the repository never distributes recovered tuning or rendered
media. Hashes identify an artifact, not authenticity or acoustic correctness.

No current test demonstrates macOS-level latency, speaker quality, Dolby
certification or complete Atmos format support. Physical comparison needs
explicit recorded methods and measurements in a later coordinated window.
