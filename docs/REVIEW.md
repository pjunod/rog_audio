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

## Second implementation batch — final disposition

Three independent agents reviewed the completed PR 2 source at `661dafb`
without executing tests. The Lenovo/source-provenance lane found no actionable
defects. All seven findings below were fixed and cleared focused source
re-review at `155d003` before unit execution.

| Area | Finding | Resolution |
|---|---|---|
| Native routing | Delayed autoload ignored route profile-device index | Filter exact route index; unrelated output cannot select a preset |
| Native routing | A still-live stream becoming ignored lost target ownership | Restore owned metadata before dropping its observation proxy |
| Runtime acceptance | Relinking after quit did not prove typed metadata restoration | Assert original pair, intercepted pair and exact restored types/values |
| File recovery | Backups were not durable before replacement | Sync backup bytes, directories and publication parents before mutations |
| File installation | Settings could precede the snapshot preimage | Derive settings from verified backup bytes |
| Dependency inspection | Names collapsed architectures and providers | Keep architecture-aware real/virtual provider lists |
| Public status | Snapshot lifecycle state lacked validation | Validate the fixed lifecycle enum before public output |

The final package passed read-only APT simulation on both laptops with zero
upgrades/removals and unchanged installed-package inventories. Historical
pre-fix compiler/APT receipts remain explicitly superseded.

## PR 2 acceptance — passing sources retained

The shared importer passed 55 cases and dependency inspection nine, each once.
Source staging passed one case and installation 12. Native routing initially
had 20 execution errors because its private container mount was noexec; only
those 20 failed cases were retried with an executable private mount and passed.
All 97 affected unit cases passed with zero skips. Their source-hash manifests
match the merge candidate. Unchanged latency 42 and Atmos 15 passes from PR 1
were retained without reruns.

Both device graph cases passed ten assertions on `ca0e755`, using the final
package and each delivered kit. They cover automatic preset/IR/plugin loading,
ordinary interception, explicit HDMI/USB targets, default changes, immediate
speaker-route bypass, stock namespace isolation and exact typed restoration.
The ASUS case required four failed attempts before its pass: wrong fixture
export interface, duplicate server module, duplicate client module, then an
observation timeout with no retained precise stage. Each fixture correction
cleared focused review; the final retry added private writable state and stage
diagnostics. The earlier state warning was not proven to cause the timeout.
The ThinkPad case passed on its first attempt. No assertions were relaxed,
no passing cases were repeated, and production bytes remained unchanged.

Receipts: [shared/importer and inspector](../evidence/speaker-importer-inspector-acceptance-2026-10-12.json),
[source/install/native units](../evidence/speaker-installation-unit-validation-2026-10-12.json),
[compiler](../evidence/speaker-runtime-build-2026-10-12.json),
[final package simulation](../evidence/speaker-package-reviewed-simulation-2026-10-12.json)
and [real isolated graphs](../evidence/speaker-runtime-graph-validation-2026-10-12.json).
Raw logs remain private and are bound by hashes.

Repository integrity passed at the reviewed production revision. Whitespace
validation initially flagged required blank context in unified patches; the
reviewed attribute-only correction passed with patch bytes unchanged. Privacy
scans passed for that public tree/history and the staged runtime/source release.
Final documentation and receipt additions receive a final integrity, whitespace
and privacy check before merge; accepted unit/runtime tests are not repeated.

These results establish readiness for coordinated installation, not physical
acoustic quality, protection, hotplug/resume or macOS-equivalent latency.

## Latency comparison batch — review before acceptance

Three independent agents reviewed the completed PR 5 batch at `768d40f`.
All four findings subsequently cleared focused source re-review before the
new unit acceptance runs.

| Area | Finding | Disposition |
|---|---|---|
| Selective retries | Failed subtests emitted parameterized IDs that the retry selector rejects | Parent method IDs retained; failure and skipped-subtest regression added; source-cleared at `1e1e9ea` |
| CoreAudio completeness | Stable default IDs absent from output inventory could still report complete | Missing default/system outputs yield partial while preserving records; source-cleared at `e419976` |
| Trial removal | Path replacement after hash comparison could delete unarchived user bytes | Atomic retained-inode quarantine, no-overwrite conflict recovery and race regressions; source-cleared at `352762b` |
| Trial installation | Snapshot interval could conceal changed restart environment or candidate restart | Fresh runtime/environment checks after snapshot and before publication, with mutation regressions; source-cleared at `352762b` |

The [compiler-only receipt](../evidence/audio-path-compiler-2026-10-13.json)
records GCC 15.3/PipeWire 1.6.8 compilation separately from native rule execution.
The Mac receipt records the original getter and summary sources used for the
operational snapshots. Its historical summary hash predates the completeness
fix; the getter and collected values remain unchanged. Neither compiler nor
silent operational evidence substitutes for the new post-review unit cases.


The [final acceptance receipt](../evidence/audio-path-acceptance-2026-10-13.json)
records 46 new unit cases passed once, zero skips: path inspection 11, trial
lifecycle 19 and CoreAudio summary 16. Seven inactive native filter cases passed
once. The config parser stage initially failed because `pw-config merge` needs
a section name; the reviewed `filter.rules` correction passed its config-only
retry. No passing unit/native case repeated. All owned test containers were
confirmed absent. Existing accepted speaker, latency and Atmos source was
unchanged and its passes were retained.

## Native lifecycle corrections — review and selective acceptance

Live ThinkPad preparation exposed two assumptions absent from the synthetic
fixtures: systemd's formatted output omits an empty environment-file array,
and controlled quit serializes the preset-use counter. The complete correction
batch received an independent adversarial review at `2fbe0d4`. One finding
was fixed: legacy captures without the new private RC text now retain exact
state matching, while changed counters still require both raw preimages.
The fix cleared source review at `42b8fbe` before acceptance.

Six affected path-inspection cases passed. Twenty-two trial cases passed; one
new method expected the wrong exception for duplicate INI sections/options.
The native parser already rejects them, and both CLI handlers already emit
fixed generic refusals. The reviewed test-only correction at `79ab1d0` passed
its single failed-parent retry. All 29 affected methods now pass, with zero
skips and no repetition of the other 28 passes. Ten are new cases and 19
exercise existing collection/environment/snapshot/install behavior changed
by this batch. Unchanged native filter/config, CoreAudio, selector harness
and earlier speaker/latency/Atmos passes remain retained.

The [acceptance receipt](../evidence/audio-path-lifecycle-acceptance-2026-10-13.json)
binds source, selected methods, attempts and logs. The
[preflight receipt](../evidence/speaker-lifecycle-preflight-2026-10-13.json)
separately records the persistent service transition and live blocker evidence.
All owned acceptance containers were confirmed absent.

## Preset-use list compatibility — eight affected cases passed once

The ROG's native history retained both its selected preset and an unchanged
bypass preset. The single-entry counter contract refused the installation
before creating a fragment or snapshot. The complete list-support correction
received independent adversarial review at `aff7fdb` with no actionable
findings. It permits only the selected counter increase and preserves all
other entries, order, settings and metadata exactly.

Four new and four affected existing methods passed once, with zero skips or
failures. No unchanged path, native, CoreAudio or exact-match lifecycle cases
were repeated. The [receipt](../evidence/audio-path-preset-list-acceptance-2026-10-13.json)
records exact sources, method IDs and log hashes. The owned container was
confirmed absent. Live activation and physical qualification remain separate
from these synthetic regression results.
