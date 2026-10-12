# Status — implementation and physical acceptance

**Updated:** 2026-10-12 · **State:** initial implementation in progress.

| Work | State | Next evidence |
|---|---|---|
| Hardware inventory | Read-only inspection complete | Sanitized receipt migrating with build docs |
| ASUS speaker tuning | Exact matching OEM XML recovered privately | Offline converter and synthetic validation |
| Diagnostics and latency | GPT-6.1 Sol implementation in progress | Reviewed inspector, analyser and candidate generator |
| Host Atmos | GPT-6.1 Sol isolated Linux build in progress | Offline harness, synthetic renderer and capability receipt |
| macOS comparison | Pending physical measurements | M4 Air primary, M3 Max secondary |
| Sonos Arc/eARC | Deferred until internal audio work | TV route and actual received formats |

The first batch combines all three implementation lanes and documentation.
Independent adversarial review happens once the batch is ready to merge;
findings are addressed before the required tests run. Failed or invalidated
tests alone are repeated. Source capability, synthetic results, installation
and measured performance remain separate claims.
