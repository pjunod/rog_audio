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

## Physical interaction emitter — source review before focused acceptance

Two independent adversarial reviews examined the PR 8 batch at `d70ab967`.
They found two issues. A failed arm after waveform creation could overwrite
the downloadable reference while leaving the prior session metadata. The
emitter now holds that waveform locally and publishes it only with a
successful session. The existing failure method now covers both an initial
post-buffer failure and a later failure preserving the prior matching pair.

The method also rejected valid negative click-to-chirp intervals, although
switch actuation can precede the audible mechanical click. It now retains
valid signed values. Any condition containing a negative value uses a signed
summary of the whole condition; the existing nonnegative analyser receives
no truncated subset, shifted values or replacement presses. Its source is
unchanged.

Both reviewers cleared exact source `66080621` before execution. All ten new
methods passed once in 0.513 seconds, with zero failures or skips under
Python 3.14.7 and Node v26.8.1. The [acceptance receipt](../evidence/physical-emitter-acceptance-2026-10-13.json)
binds the five exact source/test hashes, reviewed source archive, method IDs
and private log/result hashes. No unchanged analyser, native, speaker or
CoreAudio methods were repeated. No browser or audio device was opened by
the synthetic cases.

Separate unarmed Chrome 155.0.8059.40 smoke passed at the same runtime
source for local-file/CSP load, initial controls and diagnostic JSON download.
It observed zero AudioContext creations, only three local page/script
requests and no console errors. The private receipt, screenshot and script
hashes are bound in the public acceptance receipt. Real-browser reference
WAV download was not exercised because the page was never armed.

Armed browser/device behaviour and actual physical captures remain separate
acceptance work. The interrupted laptop stability attempts do not qualify
the emitter or either full-hour check.


## Startup/stability batch — adversarial findings before affected acceptance

Two independent adversarial reviews examined the completed native/512 source
at integration `24a8feef`. They identified three P2 findings:

- The real node model did not retain late `card.profile.device` updates, so
  current-node/timer paths could continue to see the old unknown binding.
  Native storage correction and a real late-profile-binding graph regression
  are implemented in `b6d5f1e` and cleared focused source re-review; the matching
  rebuilt artifact and late-profile-binding graph passed acceptance.
- Docker's default BuildKit/Buildx path did not support the legacy build
  resource arguments. The builder now selects the compatible bounded legacy backend explicitly
  in only the Docker build subprocess. The existing Docker unit assertion
  is extended; `b6d5f1e` cleared focused source re-review.
- The install guide's current build emitted `+rog2` while its package/install
  commands still named `+rog1`. Section 5 now consistently names `+rog2`,
  directs the current procedure to the authored autoload topic, and preserves
  the old receipt/release as history. The correction at `3775486c` cleared
  focused documentation re-review.

The intermediate compiler/export receipt for source `135c60f` remains
unchanged. It does not qualify the forthcoming corrected source or artifact.
The completed selection is
29 unit methods and six graph selectors (four new event-order/binding cases
plus the ASUS and Lenovo loader-route regressions). Both reviewers cleared all three fixes before execution. The approved corrective build now has a [matching receipt](../evidence/speaker-autoload-reviewed-build-2026-10-13.json)
for reviewed `b6d5f1e`, final ELF/package hashes and 711 exact source files.
The earlier receipt remains historical. Final artifact binding/receipt checks also cleared independently. The [final acceptance receipt](../evidence/speaker-autoload-acceptance-2026-10-13.json)
records 29 unit methods and six isolated graph selectors passing on first
execution, with zero failures or skips. One earlier container-lifetime setup
failure executed zero Linux methods. Four unit-log hashes and all six graph
receipt hashes were independently checked against retained originals. Receipts
were retained before owned-container cleanup; the SSH keeper ended with exit
137 after the owned PID 1 stop timeout. No host services or linger settings
changed. This integration lane executed no units. Physical startup, actual
ROG 512 negotiation and fresh final-configuration hours remain separate.
Only failed or subsequently invalidated cases repeat; unrelated accepted
speaker, latency, Mac and emitter suites remain retained.


PR 9 merged as `30125c0d5769fbc43925012e00a0c3fc185f9c1a` from accepted head
`31c211a04aea64290c7ac3d6c61fe5e9bd289e26`. The final repository check passed
once; no already-passing units were repeated for merge. The next loudness
implementation and its affected validation remain a separate coherent batch.
The [digital diagnosis receipt](../evidence/both-laptop-digital-gain-transfer-2026-10-13.json)
provides a low-level speech baseline, not acceptance of louder programme,
a new gain implementation, acoustics or physical latency. The PR 9 release was subsequently authorized directly and published as
v0.2.1 with its reviewed archives and notes unchanged. Its tag target,
three remote asset hashes/sizes and preserved v0.2.0 digests were verified
without repeating unit tests; see the [publication receipt](../evidence/speaker-runtime-v021-publication-2026-10-13.json).


A follow-up documentation review found that a current download-hash replacement
had also changed the historical PR 2 acceptance hash. Correction `af706406`
restored that historical v0.2.0 identity and explicitly separated its receipt
from current v0.2.1 acceptance. Focused re-review cleared the correction before
a release-body update changed only the installation-guide URL to that immutable
corrected document. The [link-correction receipt](../evidence/speaker-runtime-v021-guide-correction-2026-10-13.json)
retains original/new notes hashes and verified unchanged tag/three assets.
No code, patch, runtime or test result was changed, and no units repeated.


## Programme loudness batch — corrected build accepted, live checks open

Two independent adversarial reviews found six issues in analyser lifetime,
reset/error handling, preparation output ownership and graph-chain evidence.
The corrected source and harness cleared focused re-review. The
[reviewed build receipt](../evidence/programme-loudness-reviewed-build-2026-10-13.json)
binds 713 exact source files to native `1db1e9f`, ELF `3f110d6a…` and package
`92349a51…`; final source/artifact/model bindings cleared review. The initial
712-file build remains superseded and immutable. Three source-staging refusals
from missing new-file patch metadata remain retained; the metadata correction
did not alter native source bytes.

All 28 affected unit methods passed on first execution, with zero failures or
skips: eight makeup, four threaded analyser, twelve profile, one source and
three export methods. Both model graph selectors failed initially before gain
assertions because raw PCM was not explicitly selected in `pw-cat`. The small
harness-only `--raw` and owned-pipe shutdown correction at `a624b54` cleared
focused review. Only the two failed selectors repeated; both passed on attempt
two with eight assertions each. No unit or unchanged accepted suite repeated.
The [acceptance receipt](../evidence/programme-loudness-acceptance-2026-10-13.json)
retains exact log/graph bindings, failure history and isolated-runner bounds.
Generated -12 LUFS and float overdrive conditions test native caps and the
existing limiter; they do not qualify laptop defaults or acoustic output.
The ingestion-failure shim is absent from the production package.

The measured ThinkPad FIR contribution, unresolved ROG ordinary-media loss
and bypassed installed AutoGain remain distinct from prospective gain-policy
improvements. No new laptop gain installation, everyday-loudness acceptance
or final-configuration hour is claimed. Three chronological sanitized ThinkPad
maintenance receipts record backed-up cleanup and retained duplicate removal,
ending at 80,625,664 available bytes; old packages, tuning, owner levels and
recovery remain preserved. Raw maintenance records stay private. See
[status](STATUS.md) for those separate live observations. v0.2.2 assets are
reviewed and published after direct exact-payload owner approval. Final review
verified every runtime/kit member hash/mode and the sole refreshed archive
README. Remote tag, three asset sizes/digests and notes were then verified;
v0.2.1 asset digests stayed unchanged; the [publication receipt](../evidence/speaker-runtime-v022-publication-2026-10-13.json)
retains exact identities. The earlier approval refusal executed no command and remains separate from the successful same-route retry. PR 10
merged at `589aec2f` from accepted `d7ba126f` after its one final repository
check passed, without repeating accepted unit methods. The separately reviewed private deployment
controller and actual laptop outcomes are later evidence, not new native
code acceptance.


## Guarded larger-period follow-up — review clear and four methods accepted

Source commit `fff0936c` was imported with authorship preserved as `2c940fa2`.
A shared 128/256/512/1024/2048 set drives rule and CLI validation; bundle and
snapshot readers reconstruct the same rule. Default 256 and protected-state,
file ownership, environment and rollback guards are unchanged. Four methods
are selected after independent final source/docs review: the refactored 512
lifecycle, new 1024/2048 CLI preparation and full API lifecycles, and
invalid-type/size rejection.
Independent adversarial review cleared the source/docs at `26cc384c`; its
P3 wording correction states CLI preparation and full API lifecycles. Four
unique methods are accepted: validation passed first on macOS; the three
lifecycles errored at the unchanged Linux-only `renameat2` removal guard and
passed on Linux retry. Only the errored selectors repeated. The bounded
Linux image used 2 CPU, 6 GiB memory and total memory/swap, 2048 PIDs and no
network, with read-only public source and owned scratch. Source hashes were
identical before/after; the owned container was removed and logs retained.
[The authentic receipt](../evidence/larger-period-focused-acceptance-2026-10-13.json)
records both attempts and a staging-runner TypeError before container/test
execution. No native/programme suites repeated. The final repository checker
passed once before PR 11 merged as `5ce62059`. Native +rog3/source/patch/package bytes remain unchanged.

The current ROG 512 baseline counter growth is real live timing evidence;
wrong rollback-path/inventory-header refusals are procedural and pre-mutation.
The ThinkPad's later +rog3 query failure and initial lock-related recovery
refusal are separate live evidence. Native logs confirmed the exact new preset
automatically loaded despite the false query result. Targeted old+rog1 recovery
then completed with original preset and protected controls/services verified;
the corrected +rog3 retry subsequently succeeded, as its separately cleared
public receipt records. Two automatic starts, native settings/original IR
verification and a 20.162-second 256-frame ERR-0 check passed. No fresh hour
is inferred. The two cleared public summaries are imported unchanged; raw
captures/manifests stay private. ROG shared 1024 negotiation after fragment
removal is distinct from an explicit guarded trial and remains on +rog2.


## Progress-page presentation follow-up

The HTML ledger now renders inline links, bold text and code safely and joins
wrapped source paragraphs. Its headings/table remain readable, with horizontal
scrolling for the table on narrow screens. Static generated-HTML inspection
confirmed anchors, formatting and paragraph grouping; the in-app browser's
file-URL policy prevented a visual preview. No workaround or duplicate audio
test was used for this reversible presentation change.

## Synchronous service stop — review clear; eleven units and native integration passed

Authored commits `ecd2d9b` and test-only `b5a0ad0c` were imported as `3b8ac6c`
and `c8ec251`, preserving author identity. The helper, service template and
packaging +rog4 changes are combined with the progress renderer and exact
cleared listening, diagnostic, partial-run and recovery summaries. The native
ELF, corresponding native source, patch bytes and earlier receipts are unchanged.

Independent adversarial review cleared initial head `e9a976ef` and the exact
unsigned UID/GID source correction `813d6ad5`, imported as `4f77287`. The final
reviewed head is `8c2c234f`. One executor ran all eleven Linux methods once:
six helper process/peer/timeout/exit cases, two MAINPID/unit cases, one
previously passing mocked-export method invalidated by the packaging/export
changes and two new export rejection methods. All passed first execution,
with zero failures, errors or skips. The [exact unit receipt](../evidence/synchronous-stop-unit-acceptance-2026-10-13.json)
binds the source/helper/license hashes, 2925-byte retained log, Python 3.14.8,
Linux image, actual resource limits, read-only source/invocation mounts and
owned scratch. The owned unit container was removed; source hashes remained equal.

The separately coordinated [native integration receipt](../evidence/speaker-stop-native-integration-2026-10-13.json)
records one first-execution pass against the actual accepted ROG LocalServer,
with the exact reviewed helper SHA256 `ba8c4a6a` and native ELF `3f110d6a`.
Helper and primary returned 0 in 0.321 seconds, expected native AutoGain
settings were saved, automatic preset/IR and full ordered stereo routing were
verified, and no secondary native CLI or helper signal was used. Its owned
container was removed. This supplies the native contract that fixture-child
units alone cannot establish; it is not live hardware or acoustic acceptance.

No required methods/integration remain unexecuted. The final repository
checker passed once before PR 12 merged as `ba269db8`. The reversible renderer change uses
static generated-HTML inspection; no cosmetic unit tests. Native/source/patch
bytes remain unchanged and no source/native acceptance suites were repeated.

## Packaging-only verified artifact and later live receipts

The [exact packaging receipt](../evidence/speaker-stop-packaging-only-rog4-2026-10-13.json)
was independently read and cleared for import at SHA256 `8908010c`. It records
+rog4 built/verified from the accepted native payload: all 142 entries equal
+rog3 in paths, types, regular-file bytes, modes and symlink targets. Helper,
MIT notice and Python dependency are added; the merged service unit remains a
required separate companion. The original +rog3 package is unchanged. No
compiler, unit/native integration repeat, laptop rewrite or publication is
claimed. Later live transactions and kept-settings hours remain separate.


## Final live-results and publication ledger — PR 13

PR 13's documentation/evidence batch preserved the completed source/test
identities while importing the exact final ROG/ThinkPad hours and listening
receipts. Independent adversarial review found two P2 documentation issues:
version forwarding could select the legacy +rog3 package for +rog4 assets,
and a native `--quit` fallback after managed stop could create a new primary.
The exact version-bound installation block and managed-stop/authenticated-helper
instructions fixed both; changed-diff review cleared final head `77a108c`.

One final repository check passed at 2026-10-14 00:29:10 UTC; no affected
unit/native tests were invalidated or repeated. The batch merged as `d08a6489`
at 00:29:50 UTC. [Publication verification](../evidence/speaker-runtime-v023-publication-2026-10-14.json)
subsequently bound v0.2.3 to that merge and all five exact public assets,
with older v0.2.2 assets unchanged. The current release-reference follow-up
records a publication event that occurred after that reviewed merge; it does
not change code, sealed payloads, actual laptop packages or qualification.
Both exact software hours and scoped demos passed; physical recording remains
owner-deferred and unmeasured. Sonos remains untouched.


## Official JOC vectors — four fixes and eight selected methods

PR 15 exercised Dolby's complete 5.1.4/7.1.4 channel-ID vectors as private
pre-review development diagnostics. The prior 64-descriptor cap failed during
report serialization after rendering; a sampled native count of 66 supported
the revised 128 allowance. Encoded duration is bounded to 90 seconds with
consistent output/resource limits. Those successful diagnostic receipts remain
bound to source `0f913a5`; no corrected-binary full-vector rerender is claimed.

| Independent finding | Fix and affected coverage |
|---|---|
| Opening a FIFO could block before regular-file validation | Nonblocking descriptor/fstat before fdopen; timeout-bounded FIFO CLI case |
| Detailed private report used default 0644 permissions | Exclusive 0600 create; successful CLI mode assertion under umask 022 and collision preservation |
| Initial-bed/later-JOC inspection could report a stale null shape | Report final configuration after processing; null-before-first-OAMD and later shape coverage |
| New analyzer cases lacked a selective hosted acceptance route | Independent `atmos-energy` workflow/runner; strict exact IDs and unknown/duplicate/cross-module negative coverage |

The coordinator reported all four fixes cleared on
`e1e14f5c45bab1cd25601a673def1616731c7b1c`. The changed C# source compiled with
zero errors and the same two inherited Cavern CS0649 warnings. The first formal
[affected acceptance](../evidence/audio-atmos-official-vectors-acceptance-2026-10-14.json)
ran three probe methods and five analyzer/selector methods once in isolated
Linux, with zero failures, errors or skips. No retries or passing-case repeats
were needed. The original 13 unaffected probe methods remain retained.

This is source/synthetic acceptance plus separately bound actual JOC diagnostic
observations. It does not establish independent PCM/metadata/motion fidelity,
late-JOC bitstream acceptance, physical speaker delay, calibrated acoustics,
binaural output, TrueHD or realtime integration. No laptop or Sonos changed.


## PR 16 — signed annotations and offline playback sessions

Two independent adversarial agents reviewed the completed batch at `18bf902`
without executing tests. Both actionable P2 findings were fixed and cleared
focused source re-review before acceptance execution:

| Area | Finding | Resolution |
|---|---|---|
| Annotation acceptance | Post-test hashes could attribute old loaded code to changed disk bytes | Snapshot analyzer, runner, test module and generated fixture before loading; compare afterward and fail on change; add a fake-runner provenance regression |
| Public Atmos API | Malformed synthetic JSON escaped the documented input-error type | Translate `JsonException` to stable `InvalidInput` at `Open`; extend bounds coverage and verify reopening after failed input |

The annotation fix cleared at `b4465ff`; the Atmos fix cleared at `69f0cd5`.
[Fresh API/regression compilation](../evidence/audio-atmos-pull-reviewfix-compiler-2026-10-15.json)
passed on native Linux x86_64 with zero warnings/errors. The original compiler
receipt remains separate. Eleven annotation methods and sixteen affected
Atmos methods are selected for the first post-review acceptance pass.
Unchanged speaker, physical-emitter and other prior suites are retained.


### PR 16 final selected acceptance

[The source-bound receipt](../evidence/audio-playback-and-annotations-acceptance-2026-10-15.json)
records all 27 selected methods passing once with zero failures/errors/skips:
eleven annotation and sixteen Atmos methods. Source/fixture hashes stayed
unchanged; no hosted duplicate or passing-unit retry ran.

The full official 7.1.4 JOC render passed. A combined replay diagnostic failed
under the original process limits; retained resource evidence supports CPU
exhaustion without independently proving the kill cause. Only the failed
diagnostic was split into four isolated groups. All eight read hashes and
PTS/epoch/EOS checks matched the retained full-render PCM. This proves scoped
same-engine continuity, not every seek in one context or independent fidelity.


## PR 17 — live PipeWire playback

Independent source review found two P2 issues in the initial live-player
batch: incomplete channel links could be ignored near native exit, and retry
selectors could execute unrelated acceptance stages. Both were fixed and
cleared at `4890d18` before the first selected test execution. A later review
found that bounded daemon diagnostics incorrectly depended on optional raw
capture retention; the unconditional diagnostic tail cleared at `7730093`.

| Reviewed correction | Source clearance | Scope |
|---|---|---|
| Exact drain-route checks and strict retry selection | `4890d18` | Missing links on a surviving node fail; only whole-node successful teardown permits the bounded exit race; selectors cannot broaden stages |
| Chronological native registry events and private client ports | `daa6dd2` | Bounded JSON array sequences preserve removals and serial identity; manual test ports belong only to isolated clients |
| Nonblocking registry child observation and failure evidence | `7730093` | Feeding continues while the query runs; retained capture metrics precede comparison assertions; every failed case retains a bounded daemon tail |
| Advertised raw-mode compatibility | `566ac60` | Bounded capability discovery selects native raw input/output without version gating; package and receipt bind the shared helper |
| Guarded startup silence and all-active media start | `9e42453` | Only verified target/channel pairs receive bounded silence; actual media waits for every channel to be active and keeps its own frame/hash accounting |
| Persistent route worker | `d1aa227` | Native query creation and bounded parsing leave the PCM feeder; one bounded sequence-checked response, watchdog and process-group cleanup |
| Modern selected CI image | `5902c3c` | Pinned target PipeWire/WirePlumber stack and unchanged SDK/runtime; old offline/build stages and legacy diagnostics remain distinct |

These clearances concern source correctness within each delta. They do not
turn a failed sample comparison into a pass. Thirty-three distinct live unit
methods and three existing dispatcher smoke methods have passing receipts.
The thirteen selected startup/worker/modern-fixture methods passed. Five of
seven modern integration cases passed; a missing 12-channel capture block and
policy target-loss classification remain under diagnosis. Earlier failed comparisons remain retained in the
[status ledger](STATUS.md). The original renderer binaries and their prior
source-bound regression results remain unchanged. No physical playback or
Sonos acceptance is implied.
