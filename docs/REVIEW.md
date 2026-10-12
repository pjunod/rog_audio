# Review — findings and validation receipts

Companion to [development](DEVELOPMENT.md) and [status](STATUS.md).

## First implementation batch — pre-merge review

Three independent GPT-6.1 Sol agents reviewed the completed batch at
`b3c92bfdc1be252def1f4b66301f11d7cf8519d2` without running tests. Speaker and latency findings are fixed and source-checked with no remaining
issues in those changes. Atmos fixes at `42642b2` were independently
source-checked with all six findings resolved; final Linux acceptance follows.

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
source, dependency, command and cleanup evidence. Atmos fixes have cleared source re-review; all 15 tests passed once, with zero failures or skips. The surrounding CI
command initially failed removing root-owned build outputs. The reviewed
caller-UID/GID correction passed only a focused compile, ownership, report-copy
and cleanup retry; zero unit tests repeated. The
[Atmos receipt](../evidence/audio-atmos-acceptance-2026-10-12.json) records the
original exit status and separate successful cleanup acceptance.

## Final integration checks

The independently reviewed ThinkPad documentation matches the read-only raw
captures and official model mapping, with recovery-access denial separated
from unknown image contents. No model-specific tuning is activated.

Repository documentation/JSON and recovered ASUS byte checks passed. Gitleaks
found no leaks in the initial candidate tree or all 16 then-reachable commits.
The whitespace check initially flagged required blank context markers in
unified patches; a narrowly scoped Git attribute preserves those bytes and
the focused retry passed. The final documentation/evidence delta receives
its own integrity/privacy check; passing audio suites are retained by source
hash and are not repeated.

## Second implementation batch — acceptance preparation

PR 2 combines model-specific Lenovo preparation, original source publication,
bounded recovery findings and the speaker runtime/installation work. The
completed batch must receive independent adversarial review before its tests.
The runtime builder has compiled and packaged the candidate and prepared an
inactive kit for each laptop. Review and test results are not yet recorded.

The required coverage includes shared ASUS/Lenovo preparation regressions,
file installation and removal, pinned source staging, native target ownership
and route transitions, and a real isolated EasyEffects graph for each emitted
speaker preset. Those graph tests use generated audio and private session
services, without sound devices or the owner's desktop sockets. Source hashes
will bind inherited receipts and new results to the merge candidate. Unchanged
latency and Atmos suites retain their first-batch acceptance and are not rerun.

The package and both kits remain inactive. Physical headphone transitions,
resume, listening, power and latency measurements require the coordinated
laptop window after delivery.


Three independent agents reviewed the completed PR 2 source at `661dafb`
without executing tests. The Lenovo/source-provenance lane found no actionable
defects. The other two lanes requested these fixes before acceptance:

| Area | Finding | State |
|---|---|---|
| Native routing | Delayed autoload ignores the route profile-device index on multi-output ALSA devices | Fix in progress; add automatic preset-selection regression |
| Native routing | Ignoring a still-live stream drops target ownership without restoring metadata | Fix in progress; distinguish from actual removal/ID reuse |
| Runtime acceptance | Relinking after quit does not prove exact typed metadata restoration | Add pre-interception metadata and exact post-quit comparison |
| File recovery | Backup files/directories are not durable before the journal allows replacement | Flush complete snapshot and archive before mutations |
| File installation | Settings payload can precede a newer snapshot preimage | Derive settings from verified backup bytes |
| Dependency inspection | Package names collapse architecture and multiple providers | Fixed in `dbb1dba`; source re-review passed, nine regression cases pending execution |
| Public status | Snapshot lifecycle state is returned without enum validation | Reject unknown state before public output |

Native fixes require a replacement binary/package. The earlier compiler and
APT receipts describe their recorded hashes and are retained as historical
evidence; acceptance will bind the final source and artifact bytes. No PR 2
unit/runtime tests have run as of this review entry.
