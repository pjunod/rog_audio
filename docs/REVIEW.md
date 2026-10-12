# Review — findings and validation receipts

Companion to [development](DEVELOPMENT.md) and [status](STATUS.md).

## First implementation batch — pre-merge review

Three independent GPT-6.1 Sol agents reviewed the completed batch at
`b3c92bfdc1be252def1f4b66301f11d7cf8519d2` without running tests. Findings are
being addressed before the final Linux acceptance pass.

| Lane | Finding | Disposition |
|---|---|---|
| Speaker | Missing-channel HP/LP padding applied active filters | Fix neutral padding and asymmetric-channel regressions |
| Speaker | Field report claimed bypassed dynamics stages that were absent | Reconcile mappings with emitted stages |
| Latency | Equivalent integer/float calibration models split trial groups | Canonicalize numeric group identity, preserve input declarations |
| Latency | Interrupted validation could leave its named container | Always clean owned container and retain interruption receipt |
| Atmos | Eager frame fetch advances metadata before final PCM block renders | Explicit attributed patch of pinned upstream dependency |
| Atmos | JOC matrix timeslot wraps at channel count instead of frame length | Patch to frame-size/subband count and add dependency regression |
| Atmos | Sparse-decoder flag observed before matrix expansion updates it | Validate after rendering before publishing a successful result |
| Atmos | Output rollback unlinks a path without confirming file identity | Preserve unrelated replacements during failure cleanup |
| Documentation | Old display provenance still called published OEM files private | Update migration note and stale README label |

No physical acoustic or latency measurement, actual JOC reference comparison,
EasyEffects runtime loading or Dolby certification is claimed by these checks.
Final results and exact source identities will be recorded after fixes.
