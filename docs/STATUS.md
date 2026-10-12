# Status — implementation and physical acceptance

**Updated:** 2026-10-12 · **State:** first batch merged; both inactive installation kits built; all review findings cleared; selective acceptance running.

| Work | State | Next evidence |
|---|---|---|
| Hardware inventory | Read-only inspection complete | Sanitized receipt and build contracts imported |
| ASUS speaker tuning | Original XML and matching INF published | 48 tests and three OEM conversions passed; runtime/acoustics pending |
| Diagnostics and latency | Reviewed; 42 tests and native rule checks passed | Physical comparison and coordinated activation |
| Host Atmos | 15 tests passed; focused CI cleanup fix passed | Actual JOC reference media and physical qualification |
| Laptop installation runtime | Patched EasyEffects compiled and packaged; both inactive kits prepared | All source fixes re-reviewed; selective unit and per-device runtime acceptance running |
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

ASUS: not yet ready for live installation. The patched runtime package and
inactive installation kit are built. Independent review, focused tests and
isolated runtime acceptance remain before delivery. A fresh read-only baseline
and private rollback records are retained. Acoustic quality and physical
latency remain later measurements.

ThinkPad: first-generation model and codec are identified. An exact-match
Lenovo package is published in the candidate branch and its model-specific
importer has built three inactive bundles and an installation kit. Final review,
focused tests and runtime routing acceptance remain before installation
readiness. The recovery WIM index did not reveal matching speaker-profile
paths; the downloaded Lenovo source remains distinct.
The recovery search is read-only; ASUS coefficients are not a ThinkPad profile.

Both laptops have 34 missing prerequisite groups out of the runtime package’s
47 declared groups. Read-only reports are retained; package installation and
runtime activation have not been performed on either laptop. Read-only APT
simulations resolved the exact candidate package using each host’s current
cache: 135 new packages on ASUS and 136 on ThinkPad, with zero upgrades or
removals. Installed-package inventories were unchanged after simulation.

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


## Second-batch review findings

The Lenovo importer/source-provenance review found no actionable defects.
Native review requires route-index filtering for automatic preset selection,
restoration when a still-live stream becomes ignored, and an exact typed-target
restoration assertion in the real graph test. Installer review identified
backup durability, settings preimage consistency, architecture-aware package
inspection and lifecycle-state validation issues. All seven findings are fixed and have cleared focused source re-review at
`155d003`. Selective unit and runtime acceptance is authorized on those source
bytes. The dependency-inspector lane adds nine regression cases; installation
adds four cases and native routing adds three. Final results are pending.

The current APT simulations bind the pre-fix package. Native fixes require a
new package and a focused repeat of its dependency simulation. Earlier results
remain historical receipts and will not be presented as acceptance of new bytes.


## Acceptance progress

The shared speaker/importer suite passed 55 cases and dependency inspection
passed nine cases, each once with zero failures/skips. Source staging passed
one case and reversible installation passed 12. The first native routing run
hit 20 execution errors because its isolated Docker temporary mount was
`noexec`; compilation succeeded. Only those 20 failed cases are being retried
with an executable temporary mount. Source and installation passes are retained.
Real runtime acceptance for each laptop remains pending.
