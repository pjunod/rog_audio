# Contributor workflow

Read README.md, docs/STATUS.md and the relevant topical document first.
This repository owns Linux speaker quality, diagnostics, latency and spatial
audio. Display work belongs in pjunod/rog_hdr_dv.

Use your own clone outside ~/code and codex/ implementation branches. Never
work in the owner's checkout. Batch meaningful commits into substantial PRs.
When ready to merge, obtain an independent adversarial agent review, address
its findings, then run each required unit test once on the code being merged.
Repeat only failed tests or tests invalidated by subsequent code changes.
Do not use push-triggered duplicate test runs. Record exact test coverage,
failures and fixes. Compile while building to establish the toolchain.

Update docs/STATUS.md and docs/STATUS.html with progress and acceptance.
Document new topics in README.md. Run python3 scripts/check_repository.py
in the final validation phase. Preserve authorship and dependency licences.
Do not claim certification, measured sound quality, physical latency or
object-metadata rendering from source inspection or synthetic tests alone.

Keep private captures, OEM profiles/binaries, recordings, addresses, device
serials and access keys out of Git. Public summaries use allowlisted fields.
Use neutral host/operator names in committed material. Preserve rollback
assets, stock amplifier firmware and protection. Inspection has no playback,
recording, config activation or service-restart side effects. Coordinate live
changes and audible measurements separately from offline builds.

Do not add artificial feature flags or qualification gates. Report unmet
capabilities and measurement limits truthfully. Input validation, format
support errors and explicit operator actions are ordinary API contracts.
Keep implementation environments isolated and clean up owned temporary
clones/containers after their results are safely retained.
