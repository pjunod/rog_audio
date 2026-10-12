# Status — implementation and physical acceptance

**Updated:** 2026-10-12 · **State:** speaker and latency acceptance passed; Atmos fixes reviewed, final tests running.

| Work | State | Next evidence |
|---|---|---|
| Hardware inventory | Read-only inspection complete | Sanitized receipt and build contracts imported |
| ASUS speaker tuning | Original XML and matching INF published | 48 tests and three OEM conversions passed; runtime/acoustics pending |
| Diagnostics and latency | Reviewed; 42 tests and native rule checks passed | Physical comparison and coordinated activation |
| Host Atmos | Review fixes source-checked | Final isolated Linux acceptance running |
| ASUS installation kit | Implementation started | EasyEffects runtime, scoped routing and reversible install/remove |
| ThinkPad X1 Extreme | First-generation inventory complete; recovery mount needs admin access | Official Lenovo driver search and exact-match tuning |
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

ThinkPad: first-generation model and codec are identified. Recovery access
and exact-match OEM tuning remain pending before a model-specific candidate.
The recovery search is read-only; ASUS coefficients are not a ThinkPad profile.
