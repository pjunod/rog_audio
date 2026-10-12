# Status — implementation and physical acceptance

**Updated:** 2026-10-12 · **State:** offline tools assembled; ready for adversarial review; final acceptance tests pending.

| Work | State | Next evidence |
|---|---|---|
| Hardware inventory | Read-only inspection complete | Sanitized receipt and build contracts imported |
| ASUS speaker tuning | Original XML and matching INF published | Converter built; final review/tests pending |
| Diagnostics and latency | Tools implemented; final review/tests pending | Reviewed inspector, analyser and candidate generator |
| Host Atmos | Pinned Linux build and offline CLI implemented | Offline harness, synthetic renderer and capability receipt |
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
