# Status — implementation and physical acceptance

**Updated:** 2026-10-12 · **State:** first batch merged; Lenovo candidates built; installation/routing batch in progress.

| Work | State | Next evidence |
|---|---|---|
| Hardware inventory | Read-only inspection complete | Sanitized receipt and build contracts imported |
| ASUS speaker tuning | Original XML and matching INF published | 48 tests and three OEM conversions passed; runtime/acoustics pending |
| Diagnostics and latency | Reviewed; 42 tests and native rule checks passed | Physical comparison and coordinated activation |
| Host Atmos | 15 tests passed; focused CI cleanup fix passed | Actual JOC reference media and physical qualification |
| ASUS installation kit | Implementation underway; stock EasyEffects route transition issue identified | Target-aware routing, prompt headphone bypass and reversible install/remove |
| ThinkPad X1 Extreme | Downloaded exact-match sources and three inactive bundles built; WinRE index inspected | Combined batch review/tests and installation runtime |
| macOS comparison | Pending physical measurements | M4 Air primary, M3 Max secondary |
| Sonos Arc/eARC | Deferred until internal audio work | TV route and actual received formats |

The first batch combines all three implementation lanes and documentation.
Independent adversarial review happens once the batch is ready to merge;
findings are addressed before the required tests run. Failed or invalidated
tests alone are repeated. Source capability, synthetic results, installation
and measured performance remain separate claims.

## Decisions made during implementation

The repository is public, matching the display project. Original tool code
uses MIT; vendor and third-party terms remain separate. The owner explicitly
requested the recovered ASUS XML/INF be committed, overriding earlier private
storage instructions. Raw observations and access credentials remain excluded.

The first implementation PR combines the three lanes. Tests are explicitly
selected after adversarial review; hosted CI is manual to avoid duplicate
push-triggered runs. All agent workspaces are outside the owner's ~/code tree.
No live audio deployment or physical measurement is implied by this batch.

## Installation readiness

ASUS: not yet ready for live installation. The offline tuning importer and
latency tooling have passed their reviewed checks, but the EasyEffects
runtime, internal-speaker routing and reversible install/remove kit still
need implementation and acceptance. Acoustic quality and physical latency
remain later measurements.

ThinkPad: first-generation model and codec are identified. An exact-match
Lenovo package is published in the candidate branch and its model-specific
importer has built three inactive bundles. Final review/unit tests and runtime routing remain open before installation
readiness. The recovery WIM index did not reveal matching speaker-profile
paths; the downloaded Lenovo source remains distinct.
The recovery search is read-only; ASUS coefficients are not a ThinkPad profile.

## Second implementation batch

The first audio batch merged as PR 1. The next batch combines the Lenovo
importer and original source files with the reversible EasyEffects install kit
and routing corrections. Lenovo conversion/build evidence exists; unit tests
are deferred until the combined batch is complete and adversarially reviewed.

The corrected ThinkPad sudo policy allowed read-only recovery inspection.
One Windows Recovery Environment image was indexed (25,538 path entries).
No exact subsystem or known speaker XML/INF path matched the bounded search.
Dolby-named DSP firmware paths are present but were not extracted. The reader
reported an incorrect-reference-count warning, so this is a filename-index
observation, not image-integrity verification. Recovery was unmounted and
the temporary reader removed. Earlier access failures are historical.
