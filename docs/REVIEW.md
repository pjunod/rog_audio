# Review — findings and validation receipts

Companion to [development](DEVELOPMENT.md) and [status](STATUS.md).

## First implementation batch — pre-merge review

Three independent GPT-6.1 Sol agents reviewed the completed batch at
`b3c92bfdc1be252def1f4b66301f11d7cf8519d2` without running tests. Speaker and latency findings are fixed and source-checked with no remaining
issues in those changes. Atmos fixes precede the final Linux acceptance pass.

| Lane | Finding | Disposition |
|---|---|---|
| Speaker | Missing-channel HP/LP padding applied active filters | Fixed; neutral padding and asymmetric-channel regressions |
| Speaker | Field report claimed bypassed dynamics stages that were absent | Fixed; mappings checked against emitted stages |
| Latency | Equivalent integer/float calibration models split trial groups | Fixed; numeric grouping canonicalized, original declarations retained |
| Latency | Interrupted validation could leave its named container | Fixed; bounded owned-container cleanup and interrupt receipt |
| Atmos | Eager frame fetch advances metadata before final PCM block renders | Explicit attributed patch of pinned upstream dependency |
| Atmos | JOC matrix timeslot wraps at channel count instead of frame length | Patch to frame-size/subband count and add dependency regression |
| Atmos | Sparse-decoder flag observed before matrix expansion updates it | Validate after rendering before publishing a successful result |
| Atmos | Persistent metadata and changing object/channel counts were not distinguished | Track payload presence and reject unsupported renderer reconfiguration |
| Atmos | Relative build output resolved in the wrong directory | Resolve from caller before changing directories |
| Atmos | Output rollback unlinks a path without confirming file identity | Preserve unrelated replacements during failure cleanup |
| Documentation | Old display provenance still called published OEM files private | Update migration note and stale README label |

No physical acoustic or latency measurement, actual JOC reference comparison,
EasyEffects runtime loading or Dolby certification is claimed by these checks.
Final results and exact source identities will be recorded after fixes.

## Completed final lanes

Speaker: 48 tests, zero skips, plus music/dynamic/off conversion and verification
passed once on the reviewed source. Latency: 42 tests, zero skips, config merge,
warnings-as-errors compilation and exact/negative native route tests passed
once. Neither lane needed retries or a redundant macOS/hosted run. Source
hashes bind the accepted code despite later documentation commits.

The [speaker receipt](../evidence/audio-speaker-validation-2026-10-12.json) and
[latency receipt](../evidence/audio-latency-validation-2026-10-12.json) record
source, dependency, command and cleanup evidence. Atmos remains in final fixes.
