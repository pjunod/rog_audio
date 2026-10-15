# Status — implementation and physical acceptance

**Updated:** 2026-10-15 · **State:** the bounded live Atmos software batch has
passed its selected acceptance. Sixty-three distinct live unit methods and
three existing dispatch smoke methods have passing source-bound results.
Full 73.504-second JOC capture matched all 3,528,192 media frames at an observed
1024-frame/48-kHz graph period, with two-logical-CPU affinity, the existing
two-CPU quota and 6 GiB limit. The separate 512 final transport-padding frames
are outside media counts/hashes. Earlier ordinary 256-frame results remain
inherited media evidence; full JOC at 256 frames remains unqualified, with
all failures retained. Final independent evidence/document review and repository/privacy checks passed.
PR 17 merged as `cc5bf674`; the [preview prerelease](https://github.com/pjunod/rog_audio/releases/tag/v0.3.0-atmos-preview.1)
is published with verified asset digests. v0.2.3 remains stable latest. NUC
cleanup is in progress; its retained-evidence/deletion receipt is pending.
Signed manual annotations and the bounded
file-only Atmos API passed independent review and all 27 selected unit methods
once. Fresh JOC rendering and four split continuity groups passed; the original
combined sequence hit a process limit and remains recorded separately.
Earlier laptop demo/hour passes remain exact-condition history. A later read-only
ROG refresh found physical and tuned stereo nodes present with all twelve
protected files unchanged; its idle graph had no links. A later bounded
[connectivity refresh](../evidence/speaker-connectivity-refresh-2026-10-15.json)
at 18:06 UTC timed out on both laptops, so their current running state is
unknown. No remote inspection, playback or change ran during those attempts.
Physical recording is deferred at the owner's request.

| System | Last qualified software | Last qualified timing | Programme settings | October 15 observation / open evidence |
|---|---|---|---|---|
| ROG | +rog3, merged helper/unit backport | Graph 1024/48 kHz, 21.333 ms | −20 LUFS, cap 2.6475 dB | Earlier physical/tuned sink nodes and twelve unchanged files; 18:06 UTC connection timeout; current route/IR/period unknown |
| ThinkPad | +rog3, merged helper/unit backport | Graph 256/48 kHz, 5.333 ms | −16 LUFS, cap 14.1375 dB | 18:06 UTC connection timeout; current boot/tuning state unknown |
| M4 Air | Stock output in retained observation | HAL 512/48 kHz, 10.667 ms | Unchanged in retained observation | Prior files/browser staged; physical comparison pending |
| Sonos | Deferred | Unmeasured | Unassessed | Internal-speaker acceptance first |

The completed hours and demos qualified the earlier running +rog3 invocations,
ELF `3f110d6a`, helper `ba8c4a6a`, MIT notice `b6dfebc6`, kept IR/non-AutoGain
voicing and final limiter. They do not prove current postboot hardware routing.
The [published v0.2.3 distribution](../evidence/speaker-runtime-v023-publication-2026-10-14.json)
is packaging-only +rog4 with unchanged native bytes, paired kits and required
service companion; no laptop +rog4 deployment was performed. Graph/HAL terms
remain different software quantities, not physical latency or Mac parity.

| Work | State | Next evidence |
|---|---|---|
| Hardware/session | Latest read-only connection attempts timed out on both; earlier ROG protected files were unchanged | Reachable read-only refresh, then coordinated playback to observe full active route |
| ASUS speaker tuning | Prior 1024 hour/demo accepted; earlier service/preset/control bindings present; current host unreachable | Full post-login physical route, fresh IR load and negotiated period |
| ThinkPad speaker tuning | Prior 256 hour/demo accepted at −16/cap 14.1375; current state unknown | Reachable read-only refresh; physical qualification |
| Startup/stop | Reviewed helper, prior save/automatic-start checks and ROG service autostart evidence retained | End-to-end post-login routing; repeated boot/resume/hotplug separately |
| Signed annotation analysis | Eleven reviewed methods passed once; signed bounds and provenance retained | Actual private annotations from the later recording session |
| Source-level chain latency | Accepted minimum-phase IR/preset audit found no justified removable fixed delay; no tuning change | Actual same-path physical recording |
| Live Atmos preview | Published v0.3.0-atmos-preview.1; 63 methods + 3 smokes; exact full JOC at observed 1024/48k with two-CPU affinity; ordinary 256 media passes inherited | NUC cleanup receipt; coordinated laptop trial; no 256 full JOC, independent fidelity or physical qualification |
| Host Atmos | Sixteen affected methods passed once; fresh full JOC render and four isolated timeline groups passed | Original long sequence resource failure retained; independent fidelity and later live integration |
| Physical interaction timing | Emitter source/ten-method acceptance and earlier staging retained; no pilot/physical samples | Owner-ready coordinated same-keyboard/phone capture, still deferred |
| Sonos Arc/eARC | Untouched and last | TV route and received-format qualification after internal audio |

Companion to [installation](SPEAKER_INSTALL.md), [review](REVIEW.md),
[manual annotations](MANUAL_LATENCY_ANNOTATIONS.md) and
[implementation](AUDIO_IMPLEMENTATION.md). Source, synthetic, read-only and
physical evidence remain separate.

## October 15 preview publication — exact reviewed assets

[The published prerelease](https://github.com/pjunod/rog_audio/releases/tag/v0.3.0-atmos-preview.1)
resolves to merged PR 17 commit `cc5bf6744faf89d306863610f16021d43f1c6123`.
[Publication verification](../evidence/live-atmos-preview-publication-2026-10-15.json)
records the runtime/source archives, checksums and packaging-inspection JSON:
all four GitHub sizes and SHA-256 digests match the reviewed local assets.
The tag is a prerelease; stable latest remains v0.2.3. Accepted binaries were
packaged without rebuilding or rerunning software acceptance.

The runtime carries the complete pinned .NET runtime and original project,
Cavern, NuGet and PipeWire notices. The source archive preserves merged
project source, pinned Cavern source code and all attributed patches; exactly
five upstream test-media fixture omissions are declared by path/blob. Neither
asset contains publisher reference media or private machine data. See
[download instructions](LIVE_ATMOS.md#download-the-published-preview) for
requirements and verification. NUC cleanup is in progress with its receipt
pending; this publication adds no laptop or physical qualification.

## October 15 selected software acceptance — exact full JOC at 1024

[The source-bound acceptance ledger](../evidence/live-atmos-acceptance-2026-10-15.json)
retains every attempt and review. The final harness correction `312e9cf`
cleared independent adversarial review before its four selected methods ran;
all four passed once. The two new methods bring distinct live coverage to
sixty-three. Existing dispatch smoke passes and unaffected methods are retained.
The metadata review finding was resolved with bounded full settings snapshots
before media and after capture, not continuous completeness claims based on
lossy monitor updates.

The sole 1024-frame full-JOC run passed: all 3,528,192 rendered, submitted,
drained and captured media frames matched SHA256
`4c97fef1e51add1e08ff4a5bbc5b9df81cbc5cc0eb0b65c8077d99ae701cef19`.
Before/after settings and the native maximum callback independently recorded
48 kHz/1024 frames; final padding was 512 frames separately. Native ring
underflows/missing media and capture clock gaps/overflow/writer errors/rejected
frames were zero. Two logical CPUs on distinct cores were selected while
retaining the two-CPU quota and 6 GiB cap. Quota throttling was zero. Playback
wall time was 74.654186 seconds; waited child CPU time was 52.980557 seconds.
The maximum observed DSP block took 35.078107 ms; this is not a hard realtime
guarantee or a physical output-delay measurement.

This is exact same-engine virtual-sink continuity under the stated condition.
It does not establish independent Dolby fidelity, sustained reliability at
256 frames, laptop acoustic output, physical latency or Sonos reception.
Earlier ordinary 256 results qualify their recorded media behavior; they do
not retroactively test the new before/after settings assertions. ROG's historical
speaker period is also 1024, but no live laptop Atmos deployment or new
speaker-tuning change was performed. ThinkPad 256 Atmos remains unqualified.
The earlier 256 failures remain below without retroactive causal attribution.

## October 15 profiler — capture startup deadlines; explicit 1024 condition next

Independent review found and resolved a private profiler-wrapper cleanup
path before its sole execution. The bounded diagnostic stopped at startup
with a capture-clock gap (expected tick 13,056, actual 13,312). The profiler
recorded capture-follower xrun count four at the rejected tick; the sink/driver
count was zero and no playback node appeared. Quota throttling was zero.
Profiler exit and cleanup were clean. All thirty evidence files were verified.

This correlates capture-follower deadline errors with this startup failure,
while leaving the earlier 47.392-second insertion unattributed. The added
profiler workload is explicit. No further 256-frame attempt is planned here.
The harness is gaining explicit isolated 256/512/1024-frame selection with
requested/effective graph evidence. Default 256 remains unchanged. The next
full-JOC condition will use 1024 frames with the same two-CPU affinity/quota
and unchanged production binaries. That corresponds to the ROG's historical
speaker period but will not qualify physical routing or ThinkPad 256-frame
live Atmos. Neither laptop's graph or tuning is being changed.

## October 15 affinity retry — full stream, one inserted silent quantum

The independently reviewed launch restricted inherited affinity to logical
CPUs 0 and 1 on distinct physical cores, retaining the existing two-CPU quota,
6 GiB limit, 256-frame graph, source binaries and exact reference. All
3,528,192 rendered/submitted/drained frames were reported complete and the
submitted PCM hash matched. The captured payload hash did not match. Recorder
clock/ring/writer errors, native ring underflows and quota throttling were
all zero; these counters do not cover every node's graph deadline.

Read-only byte comparison proved an exact 2,274,816-frame prefix, then one
256-frame all-channel-zero insertion, then the entire remaining 1,253,376
reference frames exactly at the shifted offset. There were no other numeric
changes or deleted reference frames. The discrepancy begins at 47.392 seconds.
All twenty-one attempt files and eight analysis files were independently
hash-verified. This attempt remains a failure, not a timing-qualified pass.

The next bounded diagnostic adds the native graph profiler under the same
condition to observe playback, sink, capture and driver deadline evidence.
It will rerun only the failed full JOC case. No laptop configuration or
speaker tuning changed; Sonos remains untouched.

## October 15 clock diagnostics — skipped cycle; bounded affinity retry prepared

The five-file `cada9ea` diagnostic change cleared independent review and
strict capture-only compilation. Its expanded clock regression passed once;
the other sixty methods and prior ordinary cases remain retained. Full JOC
failed again before comparison, after 5.108 seconds. All twenty-three new
receipt files were independently hash-verified.

The first anomaly expected tick 81,664 but observed 81,920. Both queued-buffer
timestamps exactly matched their live-clock snapshots; the two snapshots
were 10,666,666 ns apart, corresponding to two 256-frame cycles at 48 kHz.
This attempt therefore does not support the stale-buffer hypothesis. The
recorder rejected 256 frames with no ring overflow or writer error. Four
quota-throttled periods totalled 165,794 microseconds, without event timing
to establish causation.

Read-only scheduling inspection found eight permitted logical CPUs under
an aggregate two-CPU quota. A single failed-JOC retry will restrict inherited
affinity to two logical CPUs on distinct physical cores while retaining the
same quota, 6 GiB limit, graph quantum, buffers and exact comparison. This is
a changed execution condition, not a production source fix or an established
cause. Original failures remain recorded; no passing unit or ordinary case
will repeat for this scheduling experiment.

## October 15 full JOC attempt — capture-clock failure retained

Independent review cleared `f1fc791`. Its one new native-removal guard method
passed once, followed by the failed-only policy-removal retry. Production
helper, capture observer and managed renderer bytes were unchanged. Earlier
five ordinary passes remain valid; the separate channel-mismatch pass is also
retained. All thirty-one new evidence files were independently hash-verified.

Full JOC then stopped after 5.656 seconds with
`capture-timeline-discontinuity`. The observer accepted and wrote 100,864
frames and rejected 1,024; it reported one clock gap, no ring overflow and no
writer error. Cleanup cancelled playback, which reported no native ring
underflow. No full PCM comparison was reached. The current receipt does not
record the rejected clock stamp, so it cannot distinguish a missed graph
interval from a repeated or stale clock observation. Five cgroup throttled
periods totalled 289,951 microseconds; causation is unestablished. The partial
capture and raw failure receipt remain preserved. No laptop or Sonos action
was performed.

## October 15 final-buffer correction — exact seek; policy status check pending

The reviewed `aabf092` helper fills only the unused suffix of the final
requested output buffer and reports `tail_padding_frames` separately. Strict
compiler iterations nine and ten remain distinct; the final refinement counts
physically queued padding even if an input error races, while forbidding
successful drain after the error. All fourteen compiler-evidence files were
independently verified. Four affected native/client methods passed once;
the other fifty-six method passes were retained.

Stereo and twelve-channel captures each matched all 96,000 expected frames,
with zero padding. Seek matched all 95,223 expected media frames exactly,
with nine padding frames after the final 247-frame media block. Cancellation
and manual target removal passed their positive-media, no-fallback and cleanup
checks. The recorder reported complete accounting and no ring/writer loss.
These source-bound results resolve the observed partial-tail acceptance
failure without retroactively identifying the original 512-frame deletion.

Policy-managed target removal returned application/native
`native-pipewire-failure`, exit 2, after deliberate target destruction. It
submitted 57,344 media frames, reported no drain, made no fallback links and
removed its owned playback nodes. The harness rejected that native status,
which was missing from its older allowed-status list. The failure remains
retained; it is not relabelled as a pass. A narrow reviewed guard correction
will require the same removal conditions and matching native failure evidence.
All thirty-four acceptance files were independently hash-verified. Full JOC
has not started; no passing native or capture method will repeat for a
harness-only status correction unless its behavior is actually invalidated.

## October 15 EOF handoff — reviewed correction, same retained seek failure

The four-file `45eff18` correction cleared independent adversarial review and
strict compilation. It prevents an empty EOF buffer and requires a later
process demand before drain, in addition to successful final media queueing,
validated EOF and complete consumption. The sole affected actual-callback
method passed once; the other fifty-nine live method passes were retained.
Stereo and twelve-channel exact capture passed again because their changed
successful-drain lifecycle needed requalification.

Seek still failed at frame 94,976 with the same captured payload hash. Separate
read-only analysis again found 256 all-zero frames before the complete exact
247-frame tail. Native and recorder counts were complete and their reported
error counters zero. All twenty-eight attempt files and two analysis files
were independently hash-verified. This failure remains distinct from the
prior attempt; no destructive or full JOC case ran.

Pinned adapter source waits for a complete output quantum before publishing
its split buffer. The next bounded candidate fills only the unused suffix of
the last requested transport buffer (nine neutral frames after 247 actual
frames in this case), reports padding separately and leaves media/hash/EOF
counts unchanged. Actual callback and capability/counter regressions will be
reviewed before execution. This is a source-supported correction candidate,
not a claim that the precise internal adapter delay has been proven. There
is no graph/quantum change, arbitrary sleep or weaker exact-PCM criterion.

## October 15 recorder acceptance — exact stereo/714; delayed seek tail

At reviewed `988cb25`, all eleven selected recorder/harness methods passed
once. The other forty-nine live methods and three dispatch smokes were not
repeated. Stereo and twelve-channel 96,000-frame captures then matched their
expected PCM exactly, with complete recorder accounting and zero overflow,
writer errors or usable-clock gaps.

The initial-seek case produced/submitted/consumed 95,223 frames with the correct
hash and reported drain, but exact capture failed. Read-only analysis of the
retained bytes found 94,976 exact frames, then one 256-frame all-zero interval,
then the entire 247-frame expected tail exactly. The tail is delayed, not
absent. The recorder received/accepted/wrote 158,720 frames with zero overflow,
writer errors or clock gaps; optional header/PTS metadata was unavailable.
All twenty-eight acceptance evidence files and both separate read-only
analysis files were independently hash-verified. No failed capture was rerun
for diagnosis, and no passing unit method was repeated.

Pinned PipeWire source shows `pw-cat` initiates drain on the next process
request without queueing an empty EOF buffer. The native helper currently
queues a zero-size buffer after media and can initiate drain directly after
its final media queue. The selected narrow correction follows that upstream
sequence while preserving exact media counts, the final successful queue and
EOF checks. Source/bytes support investigating this boundary; they do not
prove every internal adapter event or explain the earlier 512-frame deletion.

Only the actual-callback ordering method is invalidated among unit methods;
recorder/core/managed tests remain retained. The changed successful-drain
lifecycle also invalidates stereo/714 capture qualification, so those and the
failed seek will run after review. Cancellation, both target-loss cases and
full JOC have not yet run with the recorder. No padding, arbitrary sleep,
weaker comparison, graph change, laptop change or Sonos test is proposed.

## October 15 recorder review — clear; selected acceptance starting

Independent adversarial review cleared `988cb25` and the exact private
acceptance runner after three pre-test findings were resolved:

| Finding | Correction |
|---|---|
| Early evidence hardlink could race the recorder's single-link private-file check | Retain only after positive written output proves validation and armed writer startup |
| Temporary capture-file disappearance could skip wrapper child cleanup | Record ordinary disappearance; other errors fail distinctly and always terminate/reap the owned process group |
| Cancellation could accept a partial source-end receipt while its sink still existed | Only intentional target removal permits partial source end; cancellation requires healthy routing and complete capture |

The existing observer regression now exercises cancellation, pre-action
removal, deliberate removal and independent writer-error distinctions.
Capture C/client/compiler recipe and production playback bytes are unchanged
by these corrections. Compile artifacts are reused by exact source hash.

Eleven selected methods are authorized to run once, followed only on success
by six ordinary capture cases and the full 73.504-second JOC comparison.
Each failed phase stops progression and retains evidence; unchanged methods
and target-mismatch acceptance stay retained. This section records source
clearance and execution start, not a test or capture pass.

## October 15 native recorder — compiled, awaiting adversarial clearance

Capture-only implementation `a135f23` adds the [bounded observer](LIVE_ATMOS_CAPTURE.md),
its separate compiler recipe and loss receipts. The final strict compile
passed with no test or graph execution; all seven compile-evidence files were
independently hash-verified. The native helper has the same GLIBC 2.38 floor
and PipeWire/libc dependencies as the playback helper. Production playback
source, launcher, managed renderer, runtime and binary hashes are unchanged.

Independent review includes the observer, changed harness, eleven selected
methods and the private sequential acceptance runner. Nine methods are new;
two existing methods changed for monitor-port identity and private failure
retention. The other forty-nine live methods and three dispatcher smoke
receipts remain valid. Six ordinary capture cases and the separate complete
JOC comparison require the new observer. The earlier stereo pass remains
historical and the original 512-frame deletion remains unattributed.

No test has run on this candidate. The runner will stop at the first failure
and retain capture evidence. Speaker tuning and rollback remain untouched;
the latest read-only connection attempts timed out before inspection on both
laptops. Sonos and physical measurements remain deferred.

## October 15 capture observer — hardening an unqualified measurement path

The single bounded profiler diagnostic captured all 96,000 twelve-channel
frames exactly, with playback, capture and driver xrun counters all zero,
zero ring underflows and no CPU throttling. Profiling changes the workload;
this result neither replaces the retained formal failure nor attributes its
512-frame deletion. All twenty-one diagnostic evidence files were independently
hash-verified. No buffer/quantum sweep or further repeat-until-pass run is planned.

Source inspection independently establishes that the current `pw-cat` capture
observer performs file writes inside its processing callback and supplies no
capture-loss receipt. The selected correction is a harness-only native capture
client with a fixed ring, separate file writer, explicit ARM/STOP and overflow,
write/error accounting. Available timeline metadata will be interpreted from
its actual API contract; absent metadata will remain unknown. This removes
a measurement weakness without claiming it caused the earlier deletion.

Production playback/core/client, managed renderer and runtime remain unchanged,
with their passing methods retained. The changed observer will invalidate the
stereo measurement path while preserving its earlier pass historically. New
observer methods and affected capture paths require independent review before
execution; exact PCM criteria and the 256/48 kHz, two-CPU/6-GiB environment remain.
Speaker tuning, rollback and all laptop/Sonos sessions remain untouched.

## October 15 native transport — stereo exact, twelve-channel deletion

At reviewed `b476179`, the failed concurrency method passed alone. The first
native stereo case then captured all 96,000 media frames exactly, with ordered
routing and owned-node cleanup. The next twelve-channel case completed native
input, consumption and drain for all 96,000 frames, with zero ring underflow
events or missing-media frames, but its captured payload differed.

Read-only unique-anchor comparison found the first 48,640 frames exact, then
a 512-frame deletion. The remaining stream and exact final 8,192-frame tail
are shifted 512 frames earlier. This is not a floating-point tolerance issue
or zero insertion. The native counter measures ring starvation, not every
playback/server deadline or capture failure, so attribution remains open.

All twenty-two evidence files were independently hash-verified; failed raw
capture and expected stream remain retained privately. The isolated container
exited and was removed. Seek, cancellation, both target-loss cases and full
JOC have not run through this helper. One bounded profiler diagnostic targets
only the failed twelve-channel case with unchanged source, buffers, 256/48 kHz
virtual graph and two-CPU/6-GiB limits. No passing unit/stereo case repeats,
and no new parameter sweep, laptop or Sonos playback is planned.

## October 15 native unit acceptance — twenty passes plus one failed-only retry

Independent review found one allocation-alignment issue: the native ring's
64-byte alignment exceeded the guarantee of ordinary allocation. Correction
`ce2d20f` uses aligned, zero-initialized storage in the helper and its I/O
driver and cleared focused review. All twenty-one selected methods then ran
once: twenty passed and one concurrent fixture hit its ten-second timeout.
The timeout, exact source/artifact bindings and exited/removed container are
retained; no native transport case started during that failed phase.

The test writer used fixed 85-frame chunks. It filled 4,080 of 4,096 frames,
then waited for 85 free frames while the consumer waited for a full prebuffer.
Production input already caps reads to actual available space. Test-only
correction `b476179` caps its chunk similarly, retaining the exact 100,000-frame
order, full startup prebuffer, EOF assertions and ten-second bound. Independent
review cleared it; only that failed method retried and passed. Production
helper and I/O binary bytes are unchanged, and the other twenty passes remain
valid. The six affected ordinary cases now run through the native helper;
full JOC follows only after they pass. Managed renderer, runtime, speaker
tuning, rollback and Sonos remain unchanged.

The dated sections below retain earlier checkpoints; the opening summary
states current acceptance.

## October 15 native playback correction — compiled, under review

Implementation `2316d22` replaces blocking playback stdin callbacks with a
bounded native ring, separate input thread and explicit control protocol.
The final-buffer ordering correction `dd2d076` requires successful queueing
of the last actual media buffer before permitting drain. It includes a
focused real-callback regression; no test-only mode enters the production
helper. [The native contract](LIVE_ATMOS_NATIVE.md) documents capacities,
startup/media accounting, failure behavior, native source and ABI requirements.

The established isolated GCC/PipeWire compiler loop passed before native
changes. One ignored-write warning and one test-driver member-name collision
were retained as compile failures, then corrected. Helper and both test
executables compile with strict warnings; none has executed. The final helper
has a GLIBC 2.38 symbol floor and links the native PipeWire library dynamically.
Its compiler image is separate from the unchanged acceptance runtime image;
managed renderer/Cavern artifacts and bundled runtime stay unchanged.

Independent adversarial review is active on `dd2d076`. The proposed next
validation is twenty-one new/affected unit methods, six affected ordinary
integration cases and the failed full JOC case. The unchanged target-mismatch
case and unrelated passing methods remain retained. Final selection may
change if review fixes invalidate another path. No successful full capture,
laptop installation, hardware playback or Sonos qualification is implied.

## October 15 remaining mismatch — native playback/capture attribution

Two private diagnostics retained the reviewed renderer and changed one
parameter each. The producer-only `DOTNET_PROCESSOR_COUNT=1` hint still
failed: a 768-frame deletion begins at source frame 785,705, after which the
remaining 2,741,719 frames match at the shifted offset. This hint is not a
hard CPU/thread limit and was not added to the implementation.

A separate player-pipe request of 4,096 frames, with the default processor
count restored, also failed. Linux allocated 262,144 bytes for twelve
channels, adding 85.333 ms of byte capacity above the canonical allocation.
The first mismatch replaces 256 frames with zeros at source frame 26,412;
55 later alignment changes leave the exact final tail 17,408 frames later.
An initial search matched ambiguous silence; that is not evidence of repeated
media. Neither diagnostic altered canonical source or qualifies acceptance.
All original reports remain retained, with eighteen files independently
hash-verified for each diagnostic.

Further buffer experiments have stopped. Both raw playback reads and raw
capture writes occur inside `pw-cat` processing callbacks in the pinned
PipeWire source. Capture currently writes to a regular filesystem file, so
playback and observer scheduling remain distinct possible causes. One bounded
native-profiler run uses the canonical `528152b` source and parameters,
without managed or feeder tracing. It reproduced the mismatch. A corrected alignment identifies the first 25
nonzero source frames replaced by zeros. Nearby native playback xrun counts
increase while capture and driver counters are still zero; later capture and
driver xruns are separate. The profiler adds workload, and this correlation
does not assign every earlier or later discrepancy to the same cause. All
27 diagnostic evidence files were independently hash-verified.

The next correction replaces native playback's blocking callback I/O with a
preallocated ring and separate input thread. A fixed 4,096-frame ring and
4,096-byte input pipe retain explicit bounds; for twelve channels the ring
alone adds about 56.89 ms of capacity above the former pipe allocation.
Callback-generated startup silence, submitted media, actual media underflow
and native drain will be reported separately. This is a scheduling correction,
not a measured latency reduction. A matching isolated native compiler loop
must pass before C/build changes; completed implementation then receives
independent adversarial review and affected-only validation. Decoder source,
Cavern pins and unrelated passing tests remain unchanged. Speaker tuning,
rollback, laptop sessions and Sonos remain untouched.

## October 15 reviewed batching/reserve correction — full JOC still fails

Independent review cleared `528152b` with no findings. Release compilation,
twelve selected methods and all six affected ordinary integration cases
passed; the unchanged mismatch case remains accepted. The source and built
runtime copies were unchanged through validation. The corrected live producer
uses 1,536-frame reads; the player requests 1,024 frames of pipe capacity.
The original dependency DLLs, offline API and laptop settings are unchanged.

The full JOC retry produced, submitted and drained all 3,528,192 expected
frames with the retained reference hash, but captured payload hash `a9316394`
differs. Read-only unique-anchor analysis found the first 256-frame skip at
source frame 35,189 (0.7331 seconds), fifteen alignment changes, and the exact
last 8,192 frames displaced by +6,144 frames (128 ms). The run took 75.266
seconds including playback setup/drain; these are software observations, not
physical delay measurements. No profiler/feeder timing trace was inserted,
so this capture alone cannot attribute the remaining skips to queue starvation
or scheduling. The first full failure remains separate and unchanged.

Source inspection found per-channel and per-object ThreadPool jobs and waits
inside the pinned JOC path. One private full-stream diagnostic will set only
`DOTNET_PROCESSOR_COUNT=1` for the producer, keeping the accepted DLL, batches,
pipe, graph and resource bounds. This is a runtime concurrency hint, not a
hard one-CPU/one-worker limit. Its result is pending. No further unit methods,
passing ordinary cases, full reference render or laptop playback repeat.

## October 15 prefix diagnosis — feeding gaps and decode starvation

A complete 156-syncframe excerpt contains 239,616 frames (4.992 seconds).
The retained-PCM control bypasses decoding. With the original 4,096-byte
player pipe, it submitted the expected hash but failed capture matching.
Its longest media write gap was 14.369 ms while 4,011 frames remained queued;
no CPU throttling was recorded for that control. The same control captured
exactly with a player-only 1,024-frame request, rounded by Linux to 65,536
bytes for twelve channels. The producer pipe, 4,096-frame supervisor queue,
frame-aligned write size and 256-frame virtual graph remained unchanged.

The instrumented JOC producer used the same Release/Optimize settings as the
accepted build. It produced and submitted the exact retained-prefix hash,
but capture still failed with that reserve. Its 4,096-frame caller reads
reached 202.896 ms; a 47.018 ms maximum single DSP block is a different
quantity. At the first nonzero capture mismatch, the supervisor queue emptied
while a caller read was still running; the native playback xrun increased
without a capture xrun. This supports a smaller live caller batch as well as
the player reserve. The run also had CPU throttling and a later 51.36 ms
feeding gap despite a healthy queue, so these diagnostics do not establish
that the proposed combined correction solves every full-stream gap.

The candidate uses 1,536-frame live reads, within the existing offline
command/work budgets, and the bounded player reserve. Review and affected
acceptance remain pending. The offline pull API, speaker DSP, graph settings,
laptop tuning and rollback are unchanged. Original failures remain retained.
Two initial setup attempts hit an incorrectly combined outer/capture file
limit before PCM. Subsequent startup attempts identified SIGXFSZ from the
added outer diagnostic file limit; one selector mistake also repeated the
failed PCM control. These are diagnostic/setup failures, not passing tests.
The erroneous outer limit was removed; the reviewed capture limit and
2-CPU/6-GiB container bounds remained in force. No full reference rerender,
laptop playback, physical measurement or Sonos test occurred.

## October 15 ordinary acceptance complete — full JOC delivery still fails

The actual-media barrier cleared source review at `b14b1e8`. Its one new
unit method and all three affected destructive cases passed. The four earlier
success/mismatch cases remain accepted at `4f65188`; no unaffected test was
repeated. Cancellation and target removal now happen after finite nonzero
PCM reaches the controlled virtual sink, with positive submitted counts,
no observed fallback and owned-node cleanup.

The first full official 7.1.4 JOC live run then failed captured PCM comparison.
The publisher MP4 and extracted elementary stream matched their pinned
hashes. All 3,528,192 frames were rendered, submitted and drained, and the
producer/submitted PCM matched the retained full-render reference. Captured
output differed. Read-only comparison found a 256-frame missing block replaced
by silence near media frame 24,346; the final 8,192 reference frames remain
exact later, after accumulated delay. This is a failed live acceptance result,
not a decoder/reference mismatch or a missing-tail success claim.

The original capture and comparison receipts are retained. A short complete-
syncframe prefix diagnostic will compare the managed producer with already
retained reference PCM under the same graph/resource limits, recording batch
and scheduling timing. No full offline reference rerender, blind full-vector
retry, laptop playback or Sonos test is part of that diagnosis.

## October 15 persistent-monitor acceptance — exact 12-channel capture

The sole new review finding was an unclosed monitor stdout descriptor;
`4f65188` closes it in `finally` and cleared re-review. All six selected unit
methods passed: three new monitor methods, two affected parser methods and
the pending native-pipe-closure regression. Thirty-seven distinct live methods
now have source-bound passing receipts, plus the retained three CLI smokes.

All seven observer-invalidated integration cases ran with the same 50 ms
observation cadence and CPU/memory/graph/PCM bounds. Exact stereo, exact
12-channel (96,000 frames), exact initial seek (95,223 frames), mismatch and
policy target loss passed. Each case used one native monitor with an observed
65,536-byte output pipe; both production PCM pipes remained 4,096 bytes.

Cancellation and manual target loss returned the correct failure status,
removed owned nodes and showed no fallback, but failed the required positive
submitted-media count. The fixed one-second action timer fired during startup
silence. The correction will observe finite nonzero generated PCM through an
owned, bounded capture before starting that timer. It applies to all three
destructive cases to remove the same timing assumption consistently; the prior
policy pass remains historical and the four unaffected cases are retained.
These failures are test-precondition failures, not successful acceptance.

## October 15 remaining failures — native pipe closure and observer workload

A private instrumented policy-loss run confirmed `BrokenPipeError(32)` at the
player stdin write. The scoped fix `c2e63f7` maps only that exception to the
existing early-player-termination status. It cleared focused adversarial
review; its new partial-count/unrelated-I/O regression remains pending.

A five-second generated twelve-channel diagnostic without repeated harness
registry processes captured all PCM exactly with no media-period playback,
capture or driver xruns. Its 237 startup playback xruns remain recorded.
A separate ten-second diagnostic added the harness-equivalent 50 ms query
workload: 122 native query processes, seven media-period playback xrun
increments, one capture xrun and two CPU-throttled periods. Native cycle clocks
correlate the reproduced missing 256-frame block and zero gaps with playback
xruns; capture's later xrun has locally exact PCM. These are diagnostic
observations under different workloads, not formal acceptance or proof of the
cause of the original unprofiled failure.

The harness correction uses one bounded native registry monitor at the same
50 ms observation cadence. Exact PCM, channel/target/fallback checks, graph
settings, two-CPU/6-GiB limits and runtime PCM pipe bounds remain unchanged.
All seven harness cases will be checked once after source review because the
observer implementation changed. Earlier outcomes stay in this ledger;
no lighter observer workload is retroactively assigned to an earlier result.
Full live JOC and preview packaging follow that acceptance.

## October 15 modern acceptance — five cases passed, two under diagnosis

Reviewed source `5902c3c` built successfully on the pinned modern image under
two CPUs and 6 GiB. Compiler-only sanity and all thirteen selected unit methods
passed; the original distributable renderer DLLs remained unchanged. This adds
six new startup/worker methods to the twenty-seven earlier distinct methods;
changed methods and the new FFmpeg fixture were checked selectively.

The first seven-case modern run passed exact stereo (96,000 frames), exact
initial seek (95,223 frames, including the final partial block), mismatch,
cancellation and manual target loss. The 12-channel capture begins exactly,
then skips one 256-frame block at media frame 15,891. Its submitted hash/count
and native drain succeeded, but capture acceptance failed. The capture alone
cannot establish whether playback or capture scheduling lost that block.
Policy-driven target loss stopped with no observed fallback and removed owned
nodes, but returned `process-or-io-failure` instead of the required route-loss
classification. Private captures, commands, source/build hashes and failure
logs are retained. Only those failures are being diagnosed before any retry;
passing cases are not repeated without an invalidating change. Official live
JOC, portable preview packaging and final acceptance remain pending.

The entries below preserve earlier observations and their then-pending work;
this newer entry supersedes their current-state descriptions. No laptop
playback, tuning/configuration change or Sonos testing occurred.

## October 15 live CI — target native stack selected

The pending default `live-ci` image now uses the existing pinned Ubuntu base,
PipeWire 1.6.8 and WirePlumber 0.5.17, matching the observed laptop package
versions. It copies the unchanged pinned .NET SDK/runtime. The legacy build
and offline CI stages remain unchanged; the older live diagnostic image and
its partial-tail failures remain distinguishable. This changes the selected
CI backend, not the player's runtime admission rules.

The modern fixture encoder is FFmpeg 8.1.2. Its generated-bed producer method
requires one focused fixture check in addition to the twelve pending
startup/worker methods. Image build, compiler-only sanity, focused review
and selected acceptance are pending. Decoder/renderer DLLs and prior passing
methods are retained unless a result is specifically invalidated.

## October 15 steady-state delivery — registry work leaves the feeder

The guarded startup batch `9e42453` passed focused source review. Its four
new methods and four affected methods remain unrun while the independent
later-gap diagnosis is addressed; no passing case was repeated.

A five-second twelve-channel generated-PCM diagnostic attributed internal
zero gaps to 7.52–12.43 ms observer-process startup pauses and 2.16–6.09 ms
registry parsing on the feeder. A 4-KiB twelve-channel pipe holds only
1.78 ms of frames. A single diagnostic comparison with a 16-KiB player pipe
reduced but did not eliminate the gaps; it remains recorded separately.
Neither diagnostic was a decoder/fidelity qualification or a formal case retry.

The pending fix creates one persistent route worker before startup priming.
That worker owns native query creation, bounded snapshot parsing and exact
route validation. The feeder receives only sequence-bound linked/active/error
responses of at most 1 KiB, with one request in flight and a 2-second watchdog.
Its selector is reused. Private process-group cleanup includes an active
query and reaps the worker. Media queue, pipe bounds and exact PCM requirements
remain unchanged. Two new worker failure/cleanup methods, two changed observer
methods and the eight pending startup/routing/transport methods await focused
review and selected execution. Twenty-seven earlier live methods and three
CLI smoke methods retain their source-bound historical receipts.

## October 15 startup activation — media held until every link is active

Focused review cleared `566ac60`'s bounded raw-mode capability observation.
Its two new methods and changed backend-command method passed once, raising
the distinct accepted live methods to twenty-seven. Three earlier CLI smoke
methods remain retained. The failed-only target-version 7.1.4 and seek retry
then reached completed/drained delivery with matching producer/submitted
counts and hashes, but failed exact captured PCM matching.

Private generated-PCM diagnostics and retained media captures found that
all channel pairs could exist while most playback links were still
negotiating. Capture monitor links were already active. Media consumed in
that interval lost channel-specific prefixes. The newer backend delivered
the seek case's final 247-frame partial fragment exactly; 7.1.4 additionally
showed a later 256-frame zero gap and offset change. These are separate
observations, and the later gap remains under diagnosis.

The pending fix submits bounded startup zeros only after every correct
owned channel pair exists, waits for all of them to become active, then
submits the untouched media. Its report separates priming and media counts;
media hashes and exact capture criteria are unchanged. A 45-second / 2,160,000-frame
priming bound prevents an inactive route from consuming indefinitely.
The isolated capture harness explicitly waits for all monitor links to
become active before launching playback. Four new startup methods and four
affected routing/transport methods await focused review and selected execution.
No microphone/physical recording, laptop playback, tuning change or Sonos
test occurred.

## October 15 asynchronous delivery — stereo exact, two captures remain open

Focused review cleared `7730093`'s asynchronous registry observation,
EOF-before-observer-cleanup ordering and retained capture-failure evidence.
Its seven selected unit methods passed: four new methods and three transport
methods invalidated by the changed observation timing. Twenty-five distinct
new live methods and the earlier three CLI dispatch smoke methods now have
accepted source-bound results; unchanged parser and producer methods were
not repeated.

The six affected ordinary integration cases then ran. `success-stereo`
matched all 96,000 captured frames exactly. `cancel`, `target-loss` and
`policy-target-loss` passed again because their routing observation timing
had changed. `success-714` and `success-seek` still failed full capture
matching despite completed/drained delivery and exact producer/submitted
hashes and counts. Their bounded private captures are retained. Read-only
analysis found channel-dependent startup offsets in 7.1.4 and an exact
94,976-frame seek prefix followed by a missing final 247-frame partial
quantum; these observations do not establish the cause.

A separate failed-only compatibility run of those two cases on PipeWire
1.6.8/WirePlumber 0.5.17 stalled before submission with 4,096 prebuffered
frames and no verified full route. That is a distinct setup failure, not
proof of compatibility or a retest of a passing case. A silent owned-client
diagnostic confirmed that `--raw` creates the newer playback node before
stdin has data; omitting it blocks format probing. The shared bounded
capability observation now selects that advertised option for playback and
virtual capture. Two new capability methods and the changed command method
await focused review and execution. Source inspection also found different
old/new partial-buffer bookkeeping, but its role in the missing tail remains
unconfirmed until the target stack reaches playback. The full PCM criterion
and finite transport bounds remain unchanged. No microphone/physical
recording, laptop playback, tuning change or Sonos test occurred.

## October 15 failed-only retry — delivery succeeds, monitor match remains open

The focused review cleared `daa6dd2`'s bounded chronological JSON parser and
owned manual client-port setup. Its three new parser methods passed once;
the earlier eighteen live methods and three dispatch smoke methods were
retained. No C# or decoder/renderer binary changed.

Only the six failed ordinary integration cases were retried. `cancel`,
`target-loss` and `policy-target-loss` passed, including owned-node cleanup
and no observed fallback. `success-stereo`, `success-714` and `success-seek`
reported completed/drained native playback with exact frame counts and
matching producer/submitted PCM hashes, but failed the full monitor PCM
comparison. Those are failed acceptance cases, despite successful delivery.

Their capture comparison asserted before persisting useful metrics, and
case cleanup removed the temporary payloads. A focused harness fix now
records bounded comparison evidence before assertions and offers explicit
private failed-capture retention. A separate direct generated-PCM diagnostic
confirmed an internal zero gap near the first synchronous registry poll.
The transport now observes the registry asynchronously while feeding PCM,
with the same single-child, 2-second/4-MiB observation bounds and fixed
transport buffers. Focused review, four new unit methods and three affected
transport-method retries are pending before six affected integration cases.
Unchanged parser, producer and dispatch results remain retained.
Official JOC streaming and the separate target-version stack remain unrun.
No laptop playback, speaker tuning change, microphone/physical recording
or Sonos action has occurred.

## October 15 live acceptance — units passed, integration remains incomplete

After independent adversarial review and both P2 fixes, source `4890d18`
passed all eighteen new live-player unit methods and the three affected
existing CLI dispatch smoke methods once, without failures, errors or skips.
The tests covered producer output, initial seek/attenuation, exact EOF,
finite PCM, bounded transport, drain-route enforcement, signal cleanup and
selective CI stage handling. The unchanged DSP/regression suites retain
prior source-bound receipts.

Seven ordinary isolated PipeWire cases then ran once. `mismatch` passed.
`success-stereo`, `success-714` and `success-seek` failed during bounded
capture setup; `cancel`, `target-loss` and `policy-target-loss` reported
`pipewire-registry-unavailable` before their intended route action. These
failures are retained, not counted as playback acceptance. Source and build
artifacts remained unchanged during those runs. Daemon/registry inspection confirmed missing policy-free client DSP port
configuration and concatenated native JSON snapshot/removal arrays under
client churn. Focused fixes configure only harness-owned client ports and
share a bounded chronological registry parser; review and failed-case
retries remain pending. No accepted methods have been repeated.

The official JOC streaming case and the separate target-version PipeWire
stack have not run. A focused source review precedes any failed/invalidated
case retry; passing units and the mismatch case are retained. There was no
laptop playback, configuration change, microphone/physical recording or
Sonos test. Physical
latency, loaded tuning, sound quality and independent Dolby fidelity remain
unmeasured.

## October 15 live preparation — tuned bytes preserved, no audible test

[The later read-only refresh](../evidence/speaker-live-preparation-observation-2026-10-15.json)
finds the ROG service active/running/enabled with zero restarts in the same
invocation. All twelve protected file hashes are stable before/after and
identical to the earlier October 15 observation; eleven match the earlier
accepted gate, with the documented preset usage-count/order difference. Three
physical ALSA nodes, the internal stereo sink and tuned virtual stereo sink
are now visible. The idle graph has zero links, so full active routing, fresh
IR loading and physical playback remain unverified. ThinkPad timed out on
one bounded connection. No settings, service, playback or recording changed.

## October 15 postboot refresh — service present, desktop route not yet ready

[The exact observation](../evidence/speaker-postboot-observation-2026-10-15.json)
records the ROG boot at 11:59:24 UTC and bounded inspection at 12:02:37 UTC.
The enabled +rog3 service was active with no restarts in its new invocation;
its selected preset, nine native AutoGain controls, helper/unit bindings and
1024/48000 request match the retained conditions. Eleven of twelve protected
file hashes match the prior gate; the main configuration changed only preset
usage count/order. All inspected file bytes stayed stable during this check.
ALSA cards and stock audio services were present, but physical PipeWire nodes
were absent and observed nodes suspended. No fresh IR load, full stereo path
or negotiated driver quantum was observed; zero idle counters are not timing.

[The exact route diagnosis](../evidence/speaker-postboot-route-diagnosis-2026-10-15.json)
identifies the stock user PipeWire core and installed ALSA plugin. The local
seat belongs to the display-manager greeter, whose sound-device ACLs do not
grant access to the remote operator/user-manager sessions. This unmet session
precondition is not evidence of lost speaker tuning. A normal operator desktop
login followed by read-only device/route verification is the proposed next
step; restoration after login has not been tested. No group/ACL/configuration
change, service restart, reboot, playback or microphone action was performed.
The ThinkPad had one connection timeout and was not repeatedly polled.

Both receipts are imported byte-for-byte at SHA256 `ce4c212e` and `ce07cdff`.
They preserve prior hours as historical passes without claiming a new physical
or repeated-reboot pass. User-attended recording remains deferred.

## Signed annotations and bounded Atmos API — reviewed acceptance

[PR 16 acceptance](../evidence/audio-playback-and-annotations-acceptance-2026-10-15.json)
records two independent adversarial reviews, both P2 fixes cleared, and all
27 affected methods passed once on `534730a`: eleven annotation methods and
sixteen Atmos methods, with zero failures, errors or skips. No passing units
were repeated; unchanged speaker, emitter and eight other Atmos methods
retain their earlier receipts. Final source hashes match the accepted bytes.

The [annotation tool](MANUAL_LATENCY_ANNOTATIONS.md) preserves signed sample
intervals, conservative onset ranges, unknown timebase/bias declarations,
rejected attempts and recording/condition/block boundaries. File hashing
proves bytes only. Its runner binds four source/fixture inputs before and
after loading; a change invalidates acceptance rather than relabelling it.

The [file-only pull API](../probes/atmos/README.md) implements bounded caller
reads, sample timestamps, history-preserving seek/flush, epochs and exact EOS.
[Fresh reviewed-source compilation](../evidence/audio-atmos-pull-reviewfix-compiler-2026-10-15.json)
passed on native Linux x86_64 with zero warnings/errors. A fresh full official
7.1.4 JOC render consumed all 2297 fresh-OAMD frames. Eight PCM slices across
four separate timeline contexts matched that retained baseline exactly,
including PTS/epochs and the final eleven-frame read followed by EOF.

The original combined seek sequence failed with child signal 9 under unchanged
60 CPU-second/90 wall-second limits. Resource evidence supports CPU exhaustion
but does not independently establish its exact kill cause. Only that failed
diagnostic was split; the full render and passing units were retained.
Separate-context passes do not qualify every seek in one long-lived context.
The 67500-block API ceiling is not a guarantee of completing within the
process budget. Independent Dolby fidelity, delay/tail compensation,
realtime/headphone playback and physical latency remain unqualified.

## Accepted speaker-chain audit — no justified tuning change

[The exact offline audit](../evidence/speaker-chain-algorithmic-delay-audit-2026-10-15.json),
SHA256 `b4c35f9b`, binds the accepted native source, presets and IRs. Both
4096-frame/48 kHz IRs begin and peak at frame zero; the pinned converter uses
minimum-phase construction. Their 85.333 ms file support length is not an
85.333 ms or half-length fixed playback delay. The 99.9% impulse-energy
indices are ROG frame 12 and ThinkPad frames 88/81; these are filter metrics,
not hardware latency or processing benchmarks.

At the accepted power-of-two callback sizes, the inspected host adapter uses
the direct callback path rather than its non-power-of-two FIFO. External Zita
latency was not measured. The preserved limiter has 1 ms configured lookahead,
with no fresh actual LSP latency-port observation. Bypassed compressor stages
and 15-second AutoGain estimation history do not establish active lookahead
or a 15-second audio delay. No removable fixed delay or safe improvement was
justified; IRs, limiter and graph requests remain unchanged. There were no
laptop calls, compiler runs, units or physical measurements in this audit.

## Official Atmos vectors — diagnostics and accepted software

[The reference procedure](ATMOS_REFERENCE.md) and
[allowlisted receipt](../evidence/audio-atmos-official-vectors-2026-10-14.json)
record entire 61.504-second/1922-frame and 73.504-second/2297-frame JOC
inputs from Dolby, all frames with fresh OAMD. The original launcher
64-descriptor failure was reproduced; the revised bounded allowance supported
a sampled 66 native descriptors. Both full files rendered privately with
finite peaks and height activity. Initial object configuration and observed
energy-window order are reported without claiming reference fidelity.
No laptop, playback, microphone or Sonos changes occurred. Four independent
review findings were fixed, and [eight affected methods](../evidence/audio-atmos-official-vectors-acceptance-2026-10-14.json)
passed once with no failures/errors/skips on reviewed source `e1e14f5`. The
original 13 unaffected probe methods are retained. The full-vector diagnostics
remain bound to their original pre-review source; no corrected-binary full
vector render, independent fidelity or physical result is inferred.

## Historical receipts and implementation history

The sections below retain their recorded versions, settings and acceptance
states. Statements such as “current,” “pending” or “undeployed” apply to each
historical snapshot, not the deployed conditions in the current table above.
The kept-settings deployment/hour-start and later listening/hour receipts
follow this history. Earlier failures and old-runtime passes remain unchanged.

### Installation readiness

Both model-specific kits passed their isolated loader/plugin/routing case
with ten assertions. The ASUS ROG GU605MZ is now installed and active on
Ubuntu 26.10 amd64. The ThinkPad X1 Extreme Gen 1 was subsequently installed and
activated in its own authorized window using the separate Lenovo candidate.

The package preserves stock EasyEffects configuration and uses a separate
application identity and data roots. Installation/removal has a durable file
snapshot and conflict detection. Controlled quit restores owned stream targets;
forced termination has no persistent original-target journal. Physical
headphone hotplug, restart/resume, listening, calls, power and latency remain
acceptance work. Stock amplifier firmware and protection remain in place.

Read-only APT simulations resolved the exact final package from each host's
cached metadata: 135 new packages on ASUS and 136 on ThinkPad, with zero
upgrades/removals. Installed-package inventories were unchanged. This proves
cached resolution, not successful download or installation. A fresh ASUS
baseline and private rollback records are retained. These simulations remain
historical preparation receipts, distinct from the completed ROG installation.

### ROG live deployment

The owner authorized the ROG installation and activation. The exact v0.2.0
package installed with 135 new packages and no existing-package upgrades or
removals. The installed binary hash matches the reviewed artifact, and the
runtime prerequisite inspector now reports compatible. Five managed candidate
files were installed with a durable private snapshot before activation.

The active candidate selected the ASUS music/balanced preset. Its actual IR
loader confirmed the kernel, all expected plugin nodes appeared, an existing
application stream entered the candidate and the effects output linked to the
physical speakers. The internal speaker route and physical default were
preserved. The initial speaker volume was reduced from 76% to 20%; its prior
value is retained. No deployment-generated playback or recording occurred.

Stock PipeWire/WirePlumber process IDs, amplifier controls and Cirrus firmware
hashes were unchanged. The initial deployment used a transient user service;
login startup was enabled subsequently without interrupting it. Versioned
recovery tools, corresponding source, logs and the
rollback snapshot are retained privately outside temporary storage. Immediate
bypass uses controlled quit; removal restores managed files and retains the
post-install state. Newly installed dependencies are retained on candidate
removal; no automatic dependency cleanup is part of rollback.

[The deployment receipt](../evidence/rog-speaker-deployment-2026-10-12.json)
records live operational checks. The inherited unit and isolated graph passes
were not repeated. The owner subsequently reported substantial audible
improvement. That subjective listening feedback is distinct from measurement.
Headphone/HDMI hotplug, resume, calls, power, calibrated response/distortion and
physical latency remain unmeasured.
ThinkPad and Sonos were not changed in this window.

### ROG automatic startup

The owner requested that the tuning persist after reboot. The installed
`rog-audio-speaker.service` is enabled under the user's `default.target`, starts
after PipeWire and WirePlumber, and uses the existing candidate settings and
verified runtime without a visible window. Its stop action requests controlled
quit; restart on failure handles process crashes. No system audio service was
restarted while enabling it, and the current listening process and selected
preset were unchanged.

[The startup receipt](../evidence/rog-speaker-startup-2026-10-12.json) records
successful native unit validation, enabled state and the resolved login-target
link. No reboot or session restart was performed, so actual post-reboot startup
is pending observation. The prior absent unit state and updated rollback
instructions are retained privately. Rollback disables future startup before
stopping the candidate, removing its owned unit and restoring managed files.

### ThinkPad live deployment and startup

The owner separately authorized ThinkPad installation, activation and automatic
startup. Fresh model, codec/subsystem and current route checks matched its
Lenovo kit. The exact v0.2.0 package installed with 136 new packages and no
existing-package upgrades or removals. Its installed binary hash matches the
reviewed runtime, and all dependency groups are satisfied. Five managed files
were verified against the kit and retained with a durable rollback snapshot.

The Lenovo music/balanced preset and IR loaded. All expected plugin nodes
appeared, the effects output connected to the physical speakers, and the
speaker route and hardware default stayed selected. Stock audio process IDs
and Auto-Mute mode were preserved. Initial volume was reduced from 40% to
20%; the prior value is retained. No agent-generated playback or recording
occurred. The amplifier implementation remains unknown; this is not a
protection or acoustic qualification receipt.

The same user-login startup unit passed native validation and is enabled with
its resolved `default.target` link. Enabling it preserved the active listening
process. No reboot was performed during initial enablement. A later externally
initiated boot loaded the original Lenovo tuning automatically on v0.2.0;
[one bounded observation](../evidence/thinkpad-postboot-observation-v1-2026-10-13.json)
records startup 18.711 seconds after boot and a separate 6.086-second silent
check at 256/48000 with all nine sampled components reporting zero errors.
That observation remains separate from the pre-boot hour with driver count 1,
repeated startup and corrected-runtime qualification. Its recovery tools, original source/notices, baseline, startup
preimage and snapshot are retained privately on the ThinkPad and locally.
The ROG and Sonos were unchanged during this window.

[The ThinkPad receipt](../evidence/thinkpad-speaker-deployment-2026-10-12.json)
records these live operational checks. Owner listening feedback, physical
hotplug/resume, calls, power, acoustics and latency remain pending. Accepted
unit and isolated graph cases were not repeated for deployment.

### Review and acceptance

The completed PR 2 batch received three independent adversarial reviews.
All seven findings were fixed and cleared focused source re-review before
unit execution. The Lenovo/shared speaker suite passed 55 cases, dependency
inspection nine, source staging one, installation 12 and native routing 20:
97 affected cases passed, with zero skips. The first native run encountered
20 execution errors from a noexec container mount; only those failed cases
were retried. Unchanged latency and Atmos passes from PR 1 were retained.

The ASUS graph passed on attempt five; the ThinkPad graph passed on its first
attempt. Three ASUS attempts failed on fixture export/module registration,
and one timed out without retaining the precise observation stage. Reviewed
fixture corrections and private writable session state preceded the final
pass; the earlier state warning was not established as the timeout's cause.
No graph assertion was relaxed and no passing graph case was repeated.
Production package bytes and accepted unit source remained unchanged.

[Unit receipts](../evidence/speaker-installation-unit-validation-2026-10-12.json),
[shared/importer receipt](../evidence/speaker-importer-inspector-acceptance-2026-10-12.json)
and [graph receipt](../evidence/speaker-runtime-graph-validation-2026-10-12.json)
bind the accepted code, artifacts and results. The release includes exact
corresponding runtime source and original notices.

### Recovery and implementation decisions

The original ASUS tuning came from recovery; the Lenovo tuning came from the
matching official download. The ThinkPad WinRE index contained 25,538 paths,
with no exact matching speaker XML/INF filename. Six Dolby-named DSP firmware
paths were not extracted. A reader reference-count warning limits this to
filename evidence; image authenticity was not established. The recovery
partition was unmounted and the temporary reader removed.

The repository is public. The owner requested original OEM profiles be
published with their notices; raw captures, access credentials and private
rollback records remain excluded. Original tools use MIT and third-party
terms remain separate. Work uses owned clones outside the owner's code tree.
Hosted CI is manual to avoid duplicating review-bound acceptance runs.
Music/balanced speaker candidates are the delivery default; no Mac parity,
Dolby certification or acoustic accuracy is claimed.

### Latency comparison — 2026-10-13

The owner requested latency improvements next, using both tuned laptops and
the M4 Air reference. Fresh inventories will retain actual negotiated graph
timing, client buffering, DSP latency, driver parameters and error counters.
The Linux deployment session remains the only live audio configuration writer;
the implementation sessions build tools in separate owned clones.

Preserve the working model-specific presets, IR files, stock protection,
physical default and automatic startup. Select one reversible candidate from
the observed bottleneck, then verify its actual negotiated timing and error
behaviour. No system-wide low-buffer setting or tuning bypass is presumed.

CoreAudio device/buffer timing and PipeWire scheduling periods are software
evidence. A physical comparison needs a documented capture path and clock
relationship; measurement equipment is not yet established. The bounded software-period improvement is recorded below; physical
latency and Mac parity remain unmeasured. Sonos Atmos remains last.

[PR 5](https://github.com/pjunod/rog_audio/pull/5) contains the complete
implementation, merged at `d02c07178bfaff0c5582cb253d10c8c1738d17c9`,
and received three independent adversarial reviews. All
four findings were fixed and source-cleared before 46 new unit cases passed
once. Seven native filter cases passed; the config stage passed after one
reviewed command correction and config-only retry. No passing case repeated. Existing speaker and unrelated Atmos passes remain retained.

Initial idle baselines showed the ROG exposing an Analog Surround 4.0 sink while
its kit targets Analog Stereo. A remembered preset label does not prove active
correction on that changed route. The owner selected four-channel output manually, reported the settings UI
closing, and requested that four-channel output remain selected while its
compatibility is investigated. Active capture subsequently showed that the physical speaker DAC consumes
channels 2/3 in this profile, while the installed stereo processor would feed
ports 0/1. Correct four-channel routing needs a runtime extension. The owner
authorized stereo fallback if needed. The validated stereo route was restored
at 20% volume without restarting the candidate or stock audio services. The
full ASUS pipeline and hardware FL/FR links were observed during ten seconds
of silent PCM; the speaker DAC returned to channel 0 and all five running
error-counter observations were zero. Startup, preset, IR and managed
configuration hashes remained unchanged. The profile/default/volume preimage
and reversal instructions are retained privately. The ThinkPad still matches its
installed Lenovo route.

The M4 Air retained a 512-frame buffer at 48 kHz during silent playback, with
its device-running flag changing false/true/false. Separate device, stream and
safety-offset values are retained. Both Linux endpoints ran at 2048/48000
under the initial client's 100 ms request. The ThinkPad processed the full DSP
chain; the ROG bypassed it because of route drift. ThinkPad's first active
error counter was 1, then stable; this is not a zero-error startup pass.
[The comparison](LATENCY_COMPARISON.md) records these bounded software
observations separately from a physical benchmark.

The original ASUS profile declares two output channels. The inspected upstream
GU605 driver fixup shares the main and bass speaker DAC, and the current codec
connection report is consistent with that mapping. A four-channel ACP profile
label is not proof of four independent acoustic outputs. Source and active codec evidence ruled out simple kit rebinding as a correct
four-channel solution. No production runtime patch or invented four-channel
DSP coefficients were introduced.


The [Linux baseline receipt](../evidence/linux-audio-latency-baselines-2026-10-13.json)
and [ROG recovery receipt](../evidence/rog-speaker-stereo-recovery-2026-10-13.json)
record the route investigation and restoration. The
[Mac receipt](../evidence/m4-coreaudio-timing-2026-10-13.json) records its getter
compilation and idle/running snapshots. None is unit or physical acceptance
of the forthcoming latency request.

### Paired 256-frame observations — historical

Both laptops ran the full tuning chain under the enabled persistent user
service with the exact 256/48000 output-filter request active during this
paired window. The later ROG rollback restored 2048/48000 while ThinkPad
retained 256/48000; see the current progress below. Paired all-zero
PCM observations, each with the same 100 ms client request, showed their
actual driver period changing from 2048/48000 (42.667 ms) to 256/48000
(5.333 ms). ROG sampled driver/DSP error counters stayed zero. ThinkPad's
driver reached count 1 at startup in both runs and stayed at 1 in the later
samples; this is not a zero-error activation result.

Runtime, presets, IR, plugin settings, physical defaults and stock audio
services were preserved. Final owner volume remained 86% on ROG and 20% on
ThinkPad. Each has versioned tools, a private fragment snapshot and rollback
commands; original tuning/package recovery is also retained. That paired window established readiness for owner listening; later
listening and failure/rollback observations are recorded below. Actual post-reboot startup, physical hotplug/resume,
60-minute representative load, power and physical latency remain unqualified.

The [paired result](../evidence/linux-speaker-latency-trials-2026-10-13.json)
and [comparison](LATENCY_COMPARISON.md) retain durations, counters, preservation
and the separate M4 Air HAL reference. The Mac's 10.667 ms buffer and Linux's
5.333 ms graph period are different software quantities; neither establishes
physical speaker delay or Mac parity.

The [preflight receipt](../evidence/speaker-lifecycle-preflight-2026-10-13.json)
records native serialization of the original transient processor's plugin
settings and the initial systemd/counter assumptions. Typed environment
inspection and exact native-counter handling passed review and 29 affected
methods; the ROG list extension passed review and eight affected methods.
Only one failed test expectation was retried. The refused ROG installation
created no fragment or snapshot, resumed its working baseline, and retained
its evidence before the corrected retry.

### Physical interaction measurement plan — 2026-10-13

The [physical method](PHYSICAL_LATENCY_METHOD.md) documents a practical
phone/tablet capture of a mechanical key click and the resulting speaker
chirp on one audio track, retaining full ASUS/Lenovo tuning. A common wired
external keyboard is preferred when available; built-in keyboards leave
systematic input differences in the interaction-to-sound comparison.
The plan records pilot validation, 100 included events per condition,
median/tail statistics, uncertainty and private raw annotations. It does
not claim pure audio-output latency, calibrated accuracy or Mac parity.

The existing offline analyser accepts nonnegative annotated physical trials.
A condition containing any valid negative click-to-chirp interval needs a
separate signed summary of the whole condition; no presses are removed solely
because of their sign. The new local browser emitter requires explicit
arming and a trusted, non-repeat Space press for a bounded ramped chirp. It exports private diagnostics and a
reference waveform, opens no microphone and uses no network. Its continuously
warm silent source is not an idle-power baseline. Automatic waveform detection
is not implemented; the external recording needs manual pilot annotations.
Two independent source reviews found waveform/session mismatch after a failed
arm and biased rejection of valid negative interaction intervals. Both fixes
cleared focused source re-review at `66080621`; all ten new synthetic methods
passed once, with zero failures or skips. The [acceptance receipt](../evidence/physical-emitter-acceptance-2026-10-13.json)
retains source, runtime, method IDs and log hashes. No browser or audio device
was opened by those tests. Separate unarmed Chrome smoke passed for the
local-file page, CSP, initial controls and diagnostic JSON download, with no
AudioContext created. Real-browser reference WAV download was not exercised.
Matched Firefox 157.0.1 and pinned emitter files are now staged on the actual
remote M4 Air, with a host-bound private model/file/package receipt. Staging
performed no browser launch, playback or new tests. An earlier private handoff
had mislabelled local M3 preparation as M4 readiness; its correction is retained.
The local unarmed Chrome smoke and separately collected actual M4 HAL results
remain their own evidence classes. Remote receipts/host paths stay private;
armed route validation and the pilot remain open.

Pilot capture and physical comparison remain pending. Coordinated listening
and 60-minute stability outcomes will be recorded in their own receipts; this plan does not mark either check passed. Accepted
units remain retained because their sources are unchanged.

### Startup and sustained-check progress — 2026-10-13

The [progress record](../evidence/speaker-startup-stability-progress-2026-10-13.json)
binds the sole live operator's [frozen v4 receipt](../evidence/speaker-listening-stability-v4-2026-10-13.json).
ThinkPad's existing-runtime hour is complete. ROG stopped on error growth and
its request was removed using reviewed rollback. The original v2/v3 receipts
remain unchanged historical snapshots; final v4 binds completion and retained
failure/rollback/listening evidence. The corrected runtime and 512 candidate
have passed focused offline acceptance; the later ROG deployment and short
512 check are recorded separately below. ThinkPad deployment remains held.
The earlier expected finish times remain historical targets; the actual
ThinkPad completion is bound to its final receipt.

| System and attempt | Observed outcome | Separate next interval |
|---|---|---|
| ROG initial attempt | Aborted before the timed interval when startup driver errors increased above the retained baseline; owned test processes removed and failure evidence retained | A new session has its own counter baseline; the earlier failure remains recorded |
| ThinkPad initial attempt | Stopped on volume change; attempt plus cleanup lasted 581.040 seconds from 20% to 74%; sampled driver count stayed at 1, sampled DSP/owned source counts stayed zero | Retry starts a fresh full hour and logs volume adjustments as normal-use conditions |
| ThinkPad normal-use retry | Completed 3600.177 seconds from 10:02:02 Eastern on v0.2.0; full Lenovo chain at 256/48000, sampled driver 1 constant/followers 0, physical 100% unchanged | Completed-workload receipt retained; corrected-runtime qualification remains separate |
| ROG post-session normal-use run | Started 10:09:39 Eastern; stopped after 67.982 seconds of owned playback on monitored error growth; 256/48000 and physical 94% volume preserved | Failure archived; no automatic counter reset/retry and no full-hour pass |

The ThinkPad receipt retains 3,616 monitor frames matching the controller's
count, including 3,608 in the required active window with all nine monitored
components present and running. Driver errors stayed at 1 and all follower
counts stayed zero; no growth/reset was observed. Maximum monitor reception
gap was 1.002 seconds. There are 360 retained graph observations, including
ten with other playback clients. Start, midpoint and end protected state and
start/end audio-unit identities matched exactly. Physical volume stayed at
100%, and all owned test processes were verified absent after cleanup.
This is the declared continuous software workload on runtime hash
`e5061dcc1e0b925933eceeacffb576536d24f609307166b97d0e159c0f1772d1`.
It is not zero-error startup, +rog2 acceptance, a gaming/power benchmark or
physical/acoustic latency qualification.

After the authorized HDR package/logout handoff, the ROG user session initially
loaded bypass although the retained tuning and route file bytes were
consistent. The sole live operator diagnosed an autoload ordering race between
device-route availability and the node. Restoring the exact native tuned
preset recovered the full ASUS chain and both hardware channels; bounded
all-zero samples reported zero errors. This restoration is distinct from a
permanent runtime fix or proof of reliable startup. The earlier startup error
history is retained across the PipeWire session boundary, not reset or stitched
into the new timed interval.

At 67.958 seconds in the post-session ROG run, sampled physical driver errors
rose from 0 to 1, and the owned zero-PCM client and convolver each rose from
0 to 2; other sampled counts stayed zero. The guard covers growth or reset,
but the retained packet shows growth. Owned playback ended at 67.982 seconds.
The operator removed all owned test processes, retained the full failure
archive and preserved physical volume, service process identities and restart
counts. The startup correction was not installed for this run. These findings
do not identify the cause of the error growth or qualify a successful hour.

The reviewed removal quarantined the owned 256-frame rule and restarted only
the candidate service once; stock PipeWire and WirePlumber stayed running.
Runtime, speaker preset/IR and physical 94% volume were preserved. The preset
was correct after restart without manual reload. One 8.094-second all-zero
check verified the full ASUS stereo chain at 2048/48000. Its cumulative driver
count was 3 in all five valid samples; the monitor did not establish a
pre-start baseline. This is bounded restoration evidence, not a zero-error
startup or sustained pass. A readiness wrapper checked the raw runtime too
early; read-only inspection confirmed completion without repeating removal
or restart.

The separate [ROG owner-listening receipt](../evidence/rog-owner-listening-2026-10-13.json)
records 45.542 seconds of the original speech/music demo, exit 0 and owner
feedback “Sounded good.” Speaker state, service identities and virtual-sink
volume matched before/after. The last operator-verified 2048/48000 timing
preceded this demo; driver timing was not sampled during it. The receipt
claims neither a 256-frame listening pass nor sustained stability, microphone
capture, calibrated quality or physical latency. Its source/private hashes
are retained separately, without changing the frozen v4 receipt.

The [ThinkPad demo receipt](../evidence/thinkpad-owner-listening-2026-10-13.json)
records 45.871 seconds, exit 0, owner “sounded good” and preserved speaker
state, services and virtual-sink volume. Its 256/48000 condition comes from
the separate post-boot 6.086-second preflight; driver timing was not sampled
during the demo. The subsequent owner report says ordinary movies/shows on
both laptops are too quiet at maximum output, so everyday loudness acceptance
remains unresolved. Positive demo clarity does not establish overall sound
quality. A separate gain-stage investigation owns the next coherent change;
this startup/latency batch and its tuning stay frozen.

The completed ThinkPad retry baseline was 100% physical-default volume, not the
74% final level of its earlier stopped attempt. The v3 launch receipt corrects
that earlier progress report. The final receipt confirms driver count 1 throughout its sampled active
window and no volume-condition transitions. Separate owner-approved
listening/microphone overlaps are retained with their timestamps, native
recorder exit code 1, private recording hashes and restored temporary input
gain. The silent workload itself emits no acoustic signal and records no
microphone. The nested signal's `playback_performed: false` describes its
preparation stage; later operation entries describe actual playback. Those
scopes do not qualify physical latency or calibrated sound quality.

The native builder's authored commit `d9a9cad7` is integrated with its
additive route-cache patch, source/header pins, `+rog2` package/build contract,
focused synthetic cases and [upgrade procedure](SPEAKER_AUTOLOAD.md).
The original accepted patch bytes and licences are preserved. The
[review-fixed compiler/export receipt](../evidence/speaker-autoload-reviewed-build-2026-10-13.json)
binds `b6d5f1e`, final ELF/package hashes and 711 exact corresponding source
files. The existing-runtime ThinkPad final receipt is integrated. All source
findings and final artifact bindings cleared independent focused re-review.
The [final selective acceptance receipt](../evidence/speaker-autoload-acceptance-2026-10-13.json)
records all 29 affected unit methods and six isolated graph selectors passing
on their first execution, with zero failures or skips. The focused coverage comprises the extended
source method, 17 actual-header autoload cases, 10 build-orchestration cases,
four event-order/binding graph selectors, the two existing ASUS/Lenovo loader-route
selectors invalidated by the new runtime, and one new 512-frame lifecycle
method: 29 affected unit methods and six graph selectors in total. No
unrelated passing suites repeat; unit and graph counts remain separate.
Two independent reviews found late profile-index storage, Docker backend
compatibility and stale install-guide package names. The guide is corrected;
native/model and Docker corrections at `b6d5f1e` and the guide at `3775486c`
have all cleared focused re-review. The approved bounded corrective build
compiled/exported successfully and its matching receipt is integrated.
One detached-container setup failure occurred before any Linux test method
executed. The attached runner then completed acceptance. Receipts were retained
before cleanup; the owned container was removed, and its SSH keeper ended
with exit 137 after the owned PID 1 stop timeout. No host service or linger
setting changed. This integration lane ran no units. The [intermediate receipt](../evidence/speaker-autoload-build-2026-10-13.json)
for `135c60f` remains unchanged and superseded. The final build used two compiler
workers within two CPUs/6 GiB; the production CLI's one-worker default is
unchanged. No duplicate test lane or unchanged passing suite is run.

The ROG subsequently installed the corrected candidate and completed a short
512-frame check; no active hour was interrupted. Those later observations
remain separate from the earlier v0.2.0 hour and 256-frame failure. Accepted
unchanged units remain retained.

The ThinkPad reported `ENOSPC` while copying pilot files after its completed
existing-runtime hour. Its frozen evidence is retained separately on the
coordinator's machine. The owner then authorized backup and scoped cleanup of
164 cached installers and disabled Firefox revision 8969. The private backup
was verified before removal. Cleanup completed with installed packages, active
Firefox, the recovery seed alias, audio settings, services and volume preserved.
The [sanitized cleanup/hold receipt](../evidence/thinkpad-capacity-cleanup-runtime-hold-2026-10-13.json)
records 45,326,336 bytes (43.23 MiB) available; the earlier 92 MiB was a
projection, not a measured result. That receipt's conservative footprint is
for `+rog2`, not the forthcoming `+rog3` package. A later
[retained-source cleanup](../evidence/thinkpad-retained-agent-source-cleanup-2026-10-13.json)
verified all 710 original source files against offhost retention before removing
only their redundant agent-owned copy. It measured 45,293,568 bytes before and
68,956,160 bytes after; these are fresh observations rather than rewritten
earlier values. The old installer, kits, tools and configuration snapshots
remained onhost. Finally, [two retained observer copies](../evidence/thinkpad-retained-observer-capture-cleanup-2026-10-13.json)
were removed after exact private archive verification, leaving 80,625,664 bytes
(76.89 MiB) available. Its first completion-label check refused before any
quarantine, journal creation or removal; the reviewed retry used the retained
completion receipt. All ten other observation files and audio state were
preserved. Raw cleanup records stay private.

The corrected `+rog3` package is 3,751,126 bytes compressed and has 26,125,232
regular unpacked bytes; its 4 KiB block estimate including directories is
26,669,056 bytes. Those artifact values do not by themselves qualify a live
installation/recovery budget. At that capacity-maintenance snapshot, the runtime upgrade was held pending the
accepted merged source and the sole live operator's final budget and service
checks. No partition, boot, reservation or owner recovery data changed. These
maintenance observations do not extend the completed old-runtime hour or
imply acceptance of the new laptop runtime.

The latency tool now also prepares a 512/48000 candidate (10.667 ms) while
retaining its 256-frame default and guarded file-only install/remove contract.
The new CLI/lifecycle preservation method passed once in the affected selection. The
ROG subsequently completed the bounded negotiated check recorded below;
sustained stability and physical delay remain unqualified. It is not deployed during an
active hour, and matching the M4 Air's reported buffer duration is not physical
Mac parity. See [the candidate procedure](LINUX_AUDIO_PATH.md#prepare-an-inactive-filter-request).

All-zero stereo PCM uses the same 100 ms client request and full model-specific
tuning at 256/48000. The test adds no artificial CPU load, microphone capture
or volume writes. Volume adjustments and separately owner-coordinated listening
or recording overlaps are conditions to record, rather than reasons to reset
the owner's chosen level. Processing identity, DSP settings, physical routing,
services, counter growth/reset and monitoring continuity remain strict guards.
These silent runs do not establish absence of audible gaps, representative
gaming-load reliability, calibrated acoustics or physical latency. Actual
ROG post-reboot startup, repeated startup, ThinkPad corrected-runtime deployment,
hotplug/resume and the phone-capture pilot remain pending.


The [v0.2.1 release](https://github.com/pjunod/rog_audio/releases/tag/v0.2.1)
was published after direct authorization for the reviewed runtime, full
corresponding source/notices, ASUS/Lenovo kits and checksums. The
[publication receipt](../evidence/speaker-runtime-v021-publication-2026-10-13.json)
records its resolved tag at merged `30125c0`, exactly three uploaded assets
with matching reviewed sizes/hashes, matching notes and `releases/latest`
verified as v0.2.1. Existing v0.2.0 runtime/kit remote digests were unchanged.
Private recordings, inventories and keys were not uploaded. Installation
and sustained/physical qualification remain separate from publication.
The [subsequent guide-link correction](../evidence/speaker-runtime-v021-guide-correction-2026-10-13.json)
changed only the release installation-guide URL to the corrected immutable
document at `af706406`; the tag and all three asset hashes/sizes stayed
unchanged. The historical v0.2.0 package identity remains in its own acceptance
paragraph, separate from the current v0.2.1 download hash.


### Digital loudness diagnosis — 2026-10-13

The [paired digital transfer receipt](../evidence/both-laptop-digital-gain-transfer-2026-10-13.json)
records the same prepared ten-second speech clip on the original v0.2.0
runtime, with twenty-second input/output sink-monitor captures. The ROG
speech transfer was -0.343 dB in both channels; ThinkPad was -3.903/-3.783 dB.
Each output matched its exact existing FIR response without additional runtime
gain loss for this clip. Both monitors retained 960,000 frames per channel at
48 kHz, and nineteen full-chain observations per laptop. Protected state,
service identities and volumes matched; owned nodes were gone after cleanup.
Native sample-limit exit code 1 for the players and captures is retained,
rather than reported as exit 0. Two ROG target-binding refusals occurred before
playback and remain separate failed attempts.

This low-level clip does not explain or dismiss the owner's movie/show
loudness report. Ordinary programme and level-dependent processing remain
unmeasured; aligned digital signals are not physical speaker latency or
calibrated acoustic output. No gain fix was applied by this diagnosis. The ThinkPad's measured filter attenuation accounts for meaningful loss in
this clip; the larger ROG everyday volume loss remains unresolved. A
separate coherent implementation batch owns adjustable loudness management
while preserving the speaker filters and final limiter. The current AutoGain
stage is bypassed, so defects found in its inactive gain handling are not a
proven cause of the current attenuation. At that diagnostic observation the leveler was not yet
accepted or deployed; later implementation acceptance is recorded below.
Fresh software hours bind to the installed settings, with everyday listening
acceptance separate; Sonos remains deferred.


### ROG corrected runtime and short 512-frame check — 2026-10-13

The operator's [runtime upgrade receipt](../evidence/rog-speaker-runtime-upgrade-2026-10-13.json)
binds the merged source, reviewed binary/package and freshly bound ASUS kit.
Only the candidate package changed to `8.2.8+rog2`; dependency packages were
not added, upgraded or removed. The processor automatically loaded the
original tuned preset without manual restoration. Preset/IR/autoload and
non-main plugin RC byte records were preserved. Main RC semantic settings
were preserved, with the selected-preset use counter changing 5→6 and one
installer-added trailing blank line recorded explicitly. The old package and
private rollback snapshot remain verified. Owner physical and virtual volume
were 100% and unchanged; login startup stayed enabled, and PipeWire and
WirePlumber stayed running. A 12.108-second silent check retained four usable
2048/48000 samples with cumulative driver count 3 constant.

The separate [512-frame receipt](../evidence/rog-speaker-latency512-short-trial-2026-10-13.json)
records a new canonical baseline after the native save, then actual negotiated
512/48000 processing for 20.065 seconds with the full tuned stereo chain.
All twelve usable driver observations retained count 3, with no observed
counter growth or reset. Its immediately preceding 8.177-second baseline had
four usable 2048/48000 samples at count 3. Tuning, volumes, stock services and
startup unit were preserved; owned probe nodes were gone after cleanup.
At that short-check snapshot, the private 512 request remained installed with its distinct snapshot
and both latency/runtime rollback retained. This changes the observed period
from 42.667 to 10.667 ms, rather than measuring physical speaker delay.

A parser-wrapper failure occurred before preparation or live changes. The
first prepared installation then refused byte drift when the native save
removed the extra blank line and persisted counter 6→7; it published neither
latency fragment nor snapshot and resumed the tuned processor. The successful
attempt used a fresh canonical baseline and unchanged preservation guard.
A later read-only fence wrapper found differing collector record shapes;
corrected command-level evidence matched without live changes. All failed
attempts remain recorded separately.

Zero-quantum startup placeholders remain in private captures and are excluded
from usable period/counter comparisons. Count 3 is a nonzero historical
baseline, not a zero-error startup claim. These silent checks generated no
audible signal or recording, and do not establish absence of audible gaps,
reboot/resume reliability, acoustic quality, Mac parity or a final-runtime
hour. The receipt's `v0.2.1` identifies the artifact version, subsequently
published with matching hashes; publication does not extend this observation. ThinkPad still
ran the prior runtime at 256 frames at that observation. Fresh software hours
follow the reviewed programme-default deployment and resolution of the storage
hold; listening acceptance of those defaults remains separate.


### Programme loudness candidate — reviewed build and selective acceptance

The initial `8.2.8+rog3` build and its 712-file receipt remain immutable and
superseded. Six adversarial findings required analyser lifetime and reset/error
handling, preparation output ownership and ordered active graph-evidence fixes.
Both focused source/harness reviews cleared the corrected source. The
[corrective build receipt](../evidence/programme-loudness-reviewed-build-2026-10-13.json)
binds 713 exact files, reviewed native source `1db1e9f`, the full source map,
ELF `3f110d6a…` and package `92349a51…`. Compilation/export used one compiler
worker within two CPUs, 6 GiB memory and 6 GiB total memory/swap; builder PID
limits remain unverified engine defaults, while export was bounded at 2048.
Native and prepared-model artifact bindings also cleared review.

The [acceptance receipt](../evidence/programme-loudness-acceptance-2026-10-13.json)
records all 28 affected unit methods passing once, with zero failures or skips:
eight native makeup-header methods, four threaded analyser methods, twelve
profile methods, one source-preparation method and three export methods.
One source method ran on the Mac; 27 ran in the isolated Linux environment.
Previously passed unchanged PR 9 and Mac/emitter suites were retained.

Both model programme graph selectors initially failed at startup before gain
assertions: raw stdin lacked explicit `pw-cat --raw`. The independently
reviewed harness-only correction at `a624b54` preserved native source/artifact
bytes. Only those two failed selectors repeated; both passed on attempt two
with eight assertions each. Retained failures and successful logs/graphs were
verified offhost before owned-container removal. Ordered active FL/FR paths,
model-cap consumption, stereo balance, same-process lower-cap changes,
ingestion-error reset/recovery, silence and louder-source transitions, finite
output and the original limiter were observed. Each selector injected 23 real
ingestion failures through an acceptance-only shim absent from production.
Generated -12 LUFS graph settings, a 0.025-amplitude tone and 4.0-amplitude float
stress are synthetic test conditions, not the laptop's -20 LUFS defaults or
ordinary speaker playback. Final stress sample peaks were about 0.89125.

The native makeup control is separate from the LUFS target; its default is
0 dB, so a runtime upgrade alone does not boost old profiles. Derived ordinary
kits retain exact IR bytes and every non-AutoGain stage, insert an independent
leveler before the original final limiter and keep original profiles/recovery.
Candidate defaults remain -20 LUFS with normalization-derived makeup budgets
of 2.6475 dB for ROG and 10.1375 dB for ThinkPad. These are adjustable engineering
budgets, not measured acoustic headroom or accepted everyday settings.

At this acceptance receipt's freeze, no loudness package or preset had been
installed on either laptop: ROG was `+rog2` at 512 frames, ThinkPad `+rog1`
at 256. Subsequent live attempts and recovery are recorded separately below.
The ThinkPad's measured speech loss tracks its FIR response, while the larger
ROG ordinary-media volume loss remains unresolved. Current AutoGain was
bypassed; prospective enablement defects are not proven causes of quietness.
Matched programme observation and owner listening must evaluate everyday
loudness. Absence of feedback is not acceptance. Fresh 60-minute software
checks may run on the reviewed provisional -20 LUFS/model-cap defaults before
owner feedback, preserving speaker voicing, stock protection, startup, owner
volume and rollback. Each result binds to its actual source/runtime/settings
and interval; it does not transfer listening acceptance to changed settings. Physical delay and calibrated
acoustics remain unmeasured; Sonos stays last.

[PR 10](https://github.com/pjunod/rog_audio/pull/10) merged at
`589aec2f1a2ff7f20ff03f951ebffd6191abd7d9` on 2026-10-13 at 20:10:53 UTC,
from accepted head `d7ba126f5fc955ebe84636ec401153da946063f7`. The final
repository check passed once; no accepted unit methods repeated for merge.

[v0.2.2](https://github.com/pjunod/rog_audio/releases/tag/v0.2.2) was published
after direct approval for the exact reviewed runtime/source/notices, ordinary
fresh-inventory-bound programme kits and checksums. Publication completed at
20:25:47 UTC on 2026-10-13; its tag resolves to the exact PR 10 merge. All three
remote asset sizes/digests and notes match the reviewed files, and latest
release resolved to v0.2.2 at that publication checkpoint. The runtime archive is 9,551,458 bytes, kit archive
130,663 bytes and checksum file 207 bytes. v0.2.1's three remote asset hashes
remain unchanged. The [publication receipt](../evidence/speaker-runtime-v022-publication-2026-10-13.json)
retains those exact bindings. The earlier approval refusal executed no command;
direct exact-payload approval preceded the successful same-route retry. Publication
and merge do not establish new laptop deployment, everyday loudness, final-
configuration stability or physical measurements.

The reviewed live procedure is pinned to the merged source. It calls for one
automatic new-preset start, a controlled quit to serialize and verify loaded
native settings, then a second automatic start with fresh IR/load and route
evidence. No laptop execution is claimed by this plan. Any hour anchors to
the final active invocation; the two starts remain distinct observations,
not a reboot test or a stitched continuous run.


### Larger driver-period recovery — current preflight failure before gain update

The ROG's existing +rog2 512/48000 condition failed a fresh six-second baseline:
sampled cumulative driver ERR values were 3→4→4. The +rog3 update refused before
package, preset or service mutation. This is a real timing-error
observation, distinct from the earlier successful 20.065-second 512 check and
from two earlier procedural preflight refusals (wrong rollback path, then
missing private inventory headers). Those wrappers were corrected and checked
against both saved inventories without repeating accepted audio unit/graph
suites. ThinkPad separately refused before changes because its older +rog1
kit omitted package-version metadata; private compatibility review is separate.
Raw captures and private deployment manifests remain outside Git.

The trial tool implements shared 128/256/512/1024/2048 integer request
validation, retaining default 256 and every protected-state/file/environment
contract. Independent source/docs review cleared; four unique focused methods
are accepted. The invalid-type/size method passed on macOS; three lifecycle
methods errored only at Linux-only atomic quarantine removal, then passed in
the retained isolated Linux image. Only those three failed methods were retried;
reviewed source hashes stayed identical. [The acceptance receipt](../evidence/larger-period-focused-acceptance-2026-10-13.json)
retains both attempts, exact selectors, log hashes and verified limits. Native
code, packages, original profiles and patches are unchanged.

[The dated progress receipt](../evidence/programme-installation-recovery-progress-2026-10-13.json)
records removal of the ROG's private 512 fragment, original +rog2 tuning active,
and actual shared 1024/48000 negotiation: 11 usable observations at unchanged
driver ERR 4, with a browser requesting 1024/48000. Earlier 2048 negotiation
was not reproduced; a private assertion expecting it failed. This is neither
a new error at 2048 nor an explicit guarded 1024 trial. After accepted tool
merge, the operator can request and qualify 1024 explicitly, with recoverable
2048 available if necessary. No ROG +rog3 deployment or fresh hour is claimed.
ThinkPad retains its independent 256 request. Physical delay remains unmeasured.


### ThinkPad programme-update attempt — query failure and completed recovery

The +rog3 package installed, then the first-start preset query failed. The
active process identity was valid. The native journal independently recorded
automatic loading and successful selection of the exact new Lenovo preset
`rog-speaker-7220525a0db116ba`. Diagnosis found that the query-only command
lacked `QT_QPA_PLATFORM=offscreen`; its false empty result is a procedural
query failure, not evidence of a native autoload regression. Retain that genuine
first-start autoload observation separately from the failed overall deployment.
No completed gain-settings check, listening or hour pass is claimed.

Recovery removed the new kit and restored all old settings. Whole-tree equality
then refused a single changed Qt-generated ephemeral settings lock. The +rog3
binary initially remained installed and the service stopped at that refusal.
Targeted recovery subsequently completed: exact original +rog1 was restored
and the old Lenovo preset automatically loaded. Gains, route, persistent unit
and target link, stock services and hardware controls were verified unchanged.
That is restored working state, not a successful new programme deployment.
The [corrected retry receipt](../evidence/thinkpad-programme-runtime-live-2026-10-13.json)
subsequently records successful +rog3 installation and two automatic starts.
Native serialization verifies target −20 LUFS, cap 10.1375 dB, history 15 s,
silence −50 dB and manual input/output gain 0 dB. The original IR and all
non-AutoGain plugin settings remain identical. Fresh native IR loading and the
ordered full stereo route were observed; a 20.162-second check yielded ten
usable 256/48000 driver observations with ERR 0 unchanged. Owner gains,
route, startup, stock services and protection were preserved; original +rog1
rollback assets remain retained. The debug override was removed from the unit,
while that recorded process retained its debug environment until normal restart.
At that checkpoint, a new hour and programme listening were pending. Source/runtime
unit and isolated graph acceptance remain separate. ROG +rog2 was unchanged;
no ROG gain update is claimed. Raw locks, captures, manifests and recovery
data remain private.


### Accepted larger-request source and programme listening follow-up

[PR 11](https://github.com/pjunod/rog_audio/pull/11) merged at
2026-10-13 21:39:23 UTC as `5ce6205987c858a4e700ce5ac86486b6a13e5e25`,
from accepted head `682aea9608df553929927f2194a43f0e6c14bf19`. The final
repository checker passed once at 21:39:08 UTC; its retained output SHA256 is
`09a0398419bb39417b3b8fdbda88fe42610055286a7fbcdc1f953104851455ad`.
No passing unit methods were repeated for merge. The larger requests are now
in accepted main source; the v0.2.2 tag and release bytes remain unchanged.

[The ThinkPad programme demo receipt](../evidence/thinkpad-programme-owner-listening-2026-10-13.json)
records 45 seconds of generated speech/music on +rog3, target −20 LUFS, cap
10.1375 dB and 256/48000. Owner feedback was “Clear but still too quiet”: clarity
accepted, everyday loudness unaccepted. The player did not measure physical
or virtual volume or acoustic loudness. Protected files, preset and unit were
unchanged; no settings change or microphone recording occurred. This remains
separate from the active stability observation and any later gain condition.

The [subsequent isolated comparison](../evidence/thinkpad-programme-target-comparison-2026-10-13.json)
measured −21.8 LUFS at the current −20 target/10.1375 dB cap, −19.8 at
−16/the same cap, and −17.9 at −16/a 14.1375 dB cap. The last two cases
shared a −5.9 dBFS digital peak; all non-AutoGain stages and the final limiter
were unchanged. The last case is a provisional listening candidate, not a
live deployment, acoustic measurement or owner-accepted loudness result.
These three device-free diagnostic cases are separate from acceptance units;
no native build or passing unit suite repeated.

### Synchronous service stop — review clear; eleven units and native integration passed

[The explicit ROG 1024/recovery receipt](../evidence/rog-explicit1024-programme-recovery-2026-10-13.json)
records eleven positive 1024/48000 observations at driver ERR 4 unchanged,
full ordered stereo tuning and preserved final trial process identity. The
subsequent +rog3 first automatic preset load succeeded, but user-service stop
timed out and killed the runtime after settings saving began; new AutoGain
settings were absent. Targeted original +rog2 recovery completed with automatic
original-preset loading, explicit 1024 retained and owner gains, stock services,
route, startup, hardware controls and firmware preserved. The retained inactive
KConfig settings-write lock is distinct from the application single-instance
lock; the agent did not edit it. This is recovery, not a ROG programme pass.

[The ThinkPad partial-run receipt](../evidence/thinkpad-provisional-hour-ended-for-settings-2026-10-13.json)
records 1647.944 seconds at −20 LUFS/cap 10.1375 dB, 256/48000, driver ERR 0
unchanged and observed followers at zero. Two externally changed volume
conditions were recorded; the agent made no volume changes. All owned player,
monitor and graph nodes were independently confirmed gone after explicit stop.
The agent chose a louder candidate in response to owner feedback; the owner
did not select its exact target/cap. It was prepared offline only at this
receipt. The partial run does not qualify that later condition.

[The isolated shutdown diagnosis](../evidence/rog-speaker-shutdown-diagnosis-2026-10-13.json)
reproduced the old service sequence: secondary quit followed immediately by
SIGTERM hung at ten seconds and left AutoGain settings unsaved. Direct SIGTERM
exited in 0.315 seconds; quit followed by awaiting primary exit in 0.440 seconds;
both saved native settings. The exact internal lock mechanism remains unproven.
The rejected archive containing private metadata was not transferred; the
normal-approved diagnostic used the verified published preset/IR and a new
minimal synthetic binding. No native source, build or unit suites changed for
these diagnostics, and their exit times are not physical audio latency.

The [service helper](SPEAKER_SERVICE.md) authenticates the exact owned runtime
and Unix socket peer, pins its process lifetime, sends the native quit message
directly and waits up to ten seconds for exit. It creates no secondary process
and sends no signals; systemd retains its final kill policy and the public
template's 15-second stop deadline. The native ELF and patch pins remain
unchanged. Packaging +rog4 adds the helper, Python dependency, MIT notice and
exact export contract; it is not a new native compiler or acceptance receipt.
Live deployment will backport the exact reviewed helper and a reversible
ExecStop change to existing +rog2/+rog3 packages, with their bindings reported
separately; no unnecessary full package rewrite or OS cleanup is planned.

The authored source `ecd2d9b` and fixture-only robustness follow-up `b5a0ad0c`
were imported preserving authorship as `3b8ac6c` and `c8ec251`. Independent
adversarial review cleared the combined source and final unsigned UID/GID
correction before all eleven selected Linux unit methods passed once, with
zero failures, errors or skips. [The authentic unit receipt](../evidence/synchronous-stop-unit-acceptance-2026-10-13.json)
records the exact reviewed `8c2c234f` source, unchanged hashes, retained log
and verified isolated two-CPU/6-GiB/2048-PID/network-none environment. The
owned container was removed. The separately coordinated [actual helper-to-native integration](../evidence/speaker-stop-native-integration-2026-10-13.json)
passed first execution: exact reviewed helper `ba8c4a6a` and accepted native
ELF `3f110d6a`; helper and primary returned 0 in 0.321 seconds with expected
ROG AutoGain settings saved, automatic preset/IR and full stereo route
verified. No secondary native CLI or helper signals were used. This is an
isolated native protocol result; live backport and final settings-bound hours
remain pending. Earlier unchanged native/audio
suites were not repeated; one changed export method was legitimately
invalidated and re-executed. No native compiler pass is claimed.

### Synchronous-stop merge and live rollout boundary

[PR 12](https://github.com/pjunod/rog_audio/pull/12) merged at
2026-10-13 22:39:55 UTC as `ba269db84c5f6877014dfc2e124af7c0b74d8f06`,
from accepted head `f0490adc243562e94b95afc5f23def75132b37cd`. The coordinator's
final repository checker passed once at 22:39:42 UTC; retained output SHA256
is `09a0398419bb39417b3b8fdbda88fe42610055286a7fbcdc1f953104851455ad`.
No passing tests or native integration were repeated for merge.

The live helper/notice/unit transaction remains separately coordinated and
undeployed at that earlier deployment-planning snapshot. Its operational review found incomplete MIT
notice copying, interrupted-publication ownership and effective-unit baseline
issues before laptop mutation; those wrapper corrections do not alter the
accepted public helper/source or invalidate its tests. Existing ROG +rog2
tuning at explicit 1024 and ThinkPad +rog3 at 256 remain the working conditions.
The selected louder ThinkPad settings remain uninstalled until a verified
transaction and coordinated settings change. No fresh completed hour is claimed.

The [packaging-only +rog4 receipt](../evidence/speaker-stop-packaging-only-rog4-2026-10-13.json)
records a built and verified 3,753,142-byte package, SHA256
`17e8dcdd0f59461a035fa0eea8ec6c692194878ed788765a39c7de54ce732e91`.
All 142 native runtime entries match +rog3 in paths/types/file bytes/modes and
symlink targets; ELF `3f110d6a` and corresponding native source remain unchanged.
The additions are the exact reviewed helper `ba8c4a6a`, MIT notice `b6dfebc6`
and Python 3 dependency. No compiler, acceptance tests, laptop package rewrite
or publication occurred. The retained sealed artifact archive is 9,567,774
bytes, SHA256 `f00fe028e3c65e669bbb9a696cf0357b67bd0c1642f4fab6ae96f30aa6c0df1c`.
The merged service unit `65beb0fa` is a required separate companion; it is not
inside the deb or automatically installed/activated by package scripts.
Actual laptop backports remain bound to their older package identities.

## Kept programme settings — deployment and hour-start receipt

This immutable v2 snapshot records active hours and predates the later owner
feedback; final-hour outcomes are separate receipts. [The exact allowlisted live summary](../evidence/programme-service-autoload-and-current-settings-v2-2026-10-13.json)
binds both actual +rog3 packages/ELF `3f110d6a` and the separately installed
merged helper `ba8c4a6a`, MIT notice `b6dfebc6` and user unit `65beb0fa`.
Real helper and native exits returned 0 with service-stop success. Native
serialization, nine authenticated property getters, two automatic preset
starts, fresh IR and the identical full ordered stereo path were verified.
The original IR/non-AutoGain voicing, final −1 dB limiter, owner gains/defaults,
physical Speakers route, stock services/firmware and recovery assets remain
preserved. No +rog4 package or native rebuild was installed for this backport.

ROG now runs preset `rog-speaker-78dba4c0ea3a6e68`, target −20 LUFS/cap
2.6475 dB, 1024/48000. Its new 20-second short check yielded eleven positive
driver observations at ERR 4 unchanged. ThinkPad now runs preset
`rog-speaker-c2b907510d3d8500`, target −16 LUFS/cap 14.1375 dB, 256/48000.
Its two changed preset fields are target and maximum makeup; a fresh full
package-ledger readback matched before/after. Its 20-second check yielded
eleven positive observations at ERR 0 unchanged. Both exact rollback paths
retain the corrected stop helper and independent timing requests.

ThinkPad's new observation began at 2026-10-13 23:12:23.423583 UTC, expected
end 2026-10-14 00:12:23.423583 UTC. ROG's corrected observation began at
23:16:14.228573 UTC, expected end 00:16:14.228574 UTC. Both are active, not
completed receipts. The initial ROG observer wrongly required one generic
compressor node despite the original two sequential instances; it refused
before counting owned active time and retained its failure/cleanup. The narrow
correction requires exactly the intended multiplicities plus the existing
stereo edge, identity and counter checks. Only the ROG observation retried;
ThinkPad was not restarted. Normal owner playback is allowed by the declared
observer contract. Current programme listening is waiting for owner readiness;
no absent feedback, active hour or old pass is treated as acceptance.

The exact three emitter files were copied to ThinkPad's intended Documents
location with accepted `ac9be696` source/hashes verified. This was unarmed,
unlaunched staging with no audio or recording. All file prep is complete;
actual browser/route/phone/keyboard verification and manual pilot remain open.
The shared private handoff is maintained by its owning lane, with corrected
current M4 instructions and historical staging receipts kept separately.
No cold reboot, suspend/resume, physical hotplug, calibration or physical delay
result is claimed. Sonos remains last and untouched.

[The exact provisional +rog4 kit manifest](../evidence/speaker-stop-provisional-rog4-kit-manifest-2026-10-13.json)
records two ordinary distribution kits prepared at that checkpoint, matching
the kept DSP settings and bound to the verified +rog4 package. ASUS kit
`51efcc00` keeps preset `78dba4c0`, −20 LUFS/cap 2.6475 dB. ThinkPad kit
`a292c2c6` keeps preset `c2b90751`, −16 LUFS/cap 14.1375 dB. The paired
121,200-byte kit archive has SHA256
`c0520d9866b0166e194b71f1c18071755d43753c2474980d2bbe006a23cf9e0f`;
44 members and metadata were independently checked for safe/public contents.
The unchanged runtime/source archive `f00fe028` and required service companion
remain paired. At this preparation checkpoint they were not installed,
published or owner-approved; the later scoped demo/hour evidence and verified
v0.2.3 publication are recorded separately below.
No source defaults, current laptop packages or old v0.2.2 assets changed.
If listening feedback changes settings, reprepare only the affected kit using
the accepted tool and reviewed metadata; never edit output hashes manually.

The final current-state receipt is authored v2, imported unchanged at
SHA256 `460ab3ed`. It clarifies that ROG's cap equals its source inverse-FIR
normalization budget, whereas ThinkPad's provisional cap adds 4 dB above its
10.1375 dB source budget and retains the ordinary above-source-budget advisory.
Neither budget/cap is measured speaker headroom or an OEM safety/loudness
limit. The original v1 `72635c3f` remains retained privately; all other live
software, hour and physical claims are unchanged.

## Owner listening at the kept conditions — demo acceptance on both laptops

[The current ROG receipt](../evidence/rog-programme-owner-listening-2026-10-13.json)
records one 45.973-second generated speech/music playback, return 0, at
+rog3/1024/48000, −20 LUFS/cap 2.6475 dB. Owner feedback was “sounded good”
and “yeah the loudness is better.” The [current ThinkPad receipt](../evidence/thinkpad-target16-programme-owner-listening-2026-10-13.json)
records one 46.380-second playback, return 0, at +rog3/256/48000, −16
LUFS/cap 14.1375 dB. Feedback was “yeah the sound and loudness sound good.”
Both use the same pinned generated signal. Each confirms all twelve protected
file hashes, selected preset and service invocation unchanged before/after.
There was no recording or repeated test/playback for these authored receipts.

The owner accepted these demos at these conditions, with improved ROG loudness
and accepted ThinkPad sound/loudness. This later evidence does not overwrite
the earlier quiet −20 ThinkPad feedback or pre-feedback v2 summary. Both kept
settings remained unchanged during their subsequently completed hours. No acoustic level, physical
latency or proof for all everyday media is inferred. The provisional sealed
archives retain their preparation-era qualification metadata; later outer
release notes/manifest may record these scoped demo passes without changing
preset, IR or payload hashes. Sonos remains held for a coordinated next step.


## Final kept-settings software hours — 2026-10-14

The independently read/hash-verified allowlisted [ROG receipt](../evidence/programme-final-software-hour-lab5-v2-2026-10-14.json)
and [ThinkPad receipt](../evidence/programme-final-software-hour-lab6-v2-2026-10-14.json)
record completed guarded intervals of at least 3600 seconds on the actual kept
+rog3 packages with the separate merged helper/unit backport. Elapsed values
below are retained as source-reported values. The observer supplied continuous
all-zero stereo PCM to keep the complete tuned path active; ordinary playback
could coexist, and the accepted demos occurred during these observations.
This was a normal-use software continuity check, without artificial CPU stress
or observer-generated audible signals; it was not acoustic measurement.

| Condition | ROG / lab5 | ThinkPad / lab6 |
|---|---|---|
| Source-reported owned elapsed | 3600.258197174 seconds | 3600.4026909890017 seconds |
| Actual driver quantum/rate | 1024/48000 | 256/48000 |
| Programme target / makeup cap | −20 LUFS / 2.6475 dB | −16 LUFS / 14.1375 dB |
| Driver error counter | 4 → 4; no added errors | 0 → 0; no added errors |
| Other watched-chain errors | 0 across ten watched nodes | 0 across nine watched nodes |
| Monitor frames / graph observations | 3607 / 360 | 3609 / 358 |
| Maximum monitor reception gap | 1.002606875 seconds | 1.002331482 seconds |
| Final active verification UTC | 00:16:14.486758 | 00:12:23.826268 |
| Owned cleanup finished UTC | 00:16:14.492327 | 00:12:23.831181 |

Both complete compressed streams passed CRC and all-JSON verification, with
final events exactly matching retained final JSON and transport return 0.
The same ordered full stereo path, node/core/default/internal route identities,
selected preset, native settings and candidate/stock service identities were
preserved. No default-output or physical/virtual output gain changes were
observed; the physical default reported volume 1.0/unmuted before and after.
The observer applied no volume/settings setters. Each saw at most one other
playback client; per-client details remain private. Aggregate journal growth
was zero and the declared recovery/reserve floor remained available.

Cleanup stopped only the owned zero player, monitor and reader/writer threads;
their graph nodes were confirmed absent. The tuning service and stock audio
remained active. The current invocation's debug environment is retained until
its next normal restart; no extra restart was made to remove it. Independent
post-cleanup readback checked all nine native properties, automatic-start
bindings, complete package ledger, current runtime and retained rollback
packages/configuration preimages. Original IR/non-AutoGain voicing, final
limiter, owner gain, stock protection and recoverable rollback remain intact.

These receipts qualify software continuity for these exact conditions. They
do not overwrite the earlier ROG 256/512 failures, observer preflight refusal,
old ThinkPad hour, intentionally shortened −20 interval or shutdown recovery.
Owner demo acceptance remains the separate listening evidence above. Physical
recording was deferred by the owner to another coordinated window; the ROG
page remains unarmed, with no additional playback or microphone use tonight.
No physical latency, calibrated acoustics, cold reboot, suspend/resume or
headphone/HDMI qualification is inferred. Sonos remains untouched and last.


## Reviewed final results and v0.2.3 publication — 2026-10-14

[PR 13](https://github.com/pjunod/rog_audio/pull/13) merged at 00:29:50 UTC,
commit `d08a6489e0fe0f2fcc2fd99af7d23d57659f49dd`, after independent
adversarial review of final head `77a108c55e4b248ee7b87d38f445393fd3d6422d`.
Two documentation findings were fixed before clearance: the new +rog4 procedure
now names its exact package/kit/binary/service paths instead of forwarding to
a legacy +rog3 literal; managed stop uses only the synchronous unit, with
an authenticated-helper fallback for a verified existing unmanaged primary.
Native `--quit` is not used as an absent-primary stop check. One final
repository check passed at 00:29:10 UTC, retained log SHA256 `09a03984`;
no already-passing unit or native integration suite was repeated.

[The exact publication receipt](../evidence/speaker-runtime-v023-publication-2026-10-14.json),
imported unchanged at SHA256 `f1673c78`, records
[v0.2.3](https://github.com/pjunod/rog_audio/releases/tag/v0.2.3) published
at 00:31:43 UTC and verified at 00:32:26 UTC. Its tag resolves to that PR 13
merge; all five remote asset sizes/digests and release notes match, and the
latest-release link resolves to v0.2.3. Previous v0.2.2 asset identities,
sizes and digests remain unchanged.

| Public asset | Bytes | SHA256 prefix |
|---|---|---|
| `rog-audio-packaging-only-8.2.8+rog4.tar.gz` | 9,567,774 | `f00fe028` |
| `rog-audio-provisional-speaker-kits-8.2.8+rog4.tar.gz` | 121,200 | `c0520d98` |
| `rog-audio-speaker.service` | 551 | `65beb0fa` |
| `RELEASE_NOTES.md` | 5,350 | `bd697218` |
| `SHA256SUMS` | 403 | `76b2c46f` |

The two sealed archives and service companion are unchanged from their
verified prepared payloads. Only outer notes/manifest/checksums were finalized
with the merged target and later software/listening acceptance. Private cleanup
inventory and raw captures were excluded from upload. The laptops still run
+rog3 with the separate helper/unit backport, at the exact hour-qualified
settings; publication did not rewrite their packages, change tuning or restart
an audio/session service. Spent owned observer source/options/status files and
empty directories were cleaned after off-host retention, with full logs,
rollback, current native/configuration and physical-session inputs retained.

Both demos and exact software hours remain passed. Physical recording is
owner-deferred, the page remains unarmed, and no further user-attended action
is planned tonight. Physical latency against the M4 Air, calibrated acoustics,
reboot/resume/hotplug and broader media qualification remain open. Sonos stays
untouched and last. Use the current [installation procedure](SPEAKER_INSTALL.md)
for a future coordinated +rog4 installation; publication alone does not qualify
an actual +rog4 laptop deployment.
