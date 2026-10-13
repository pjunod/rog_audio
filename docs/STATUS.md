# Status — implementation and physical acceptance

**Updated:** 2026-10-13 · **State:** both speaker candidates installed with
login startup configured; ThinkPad completed the declared hour at 256 frames
on v0.2.0; ROG's 256-frame run failed, then corrected-runtime deployment and
a separate short 512-frame check succeeded with the original tuning retained.
All source/artifact findings cleared re-review; 29 affected unit methods and
six isolated graph selectors passed once, with zero failures or skips. PR 9
is merged. Fresh final-configuration hours and physical measurements remain open.

| Work | State | Next evidence |
|---|---|---|
| Hardware inventory | Both laptops inspected read-only | Refresh during installation |
| ASUS speaker tuning | Full tuned path restored; demo clarity feedback positive, everyday movie/show loudness unresolved | Reviewed startup fix installed, short 512 trial passed; final gain configuration, hour and physical checks |
| ThinkPad speaker tuning | Separate Lenovo candidate running; demo clarity positive, everyday loudness unresolved; old-runtime hour retained | Resolve storage before corrected-runtime deployment; separate gain investigation and physical checks |
| Laptop installation runtime | ROG corrected runtime active; ThinkPad old runtime retained; 29 affected units/six isolated graphs passed | Reboot/resume and sustained qualification; ThinkPad storage resolution |
| Diagnostics and latency | ThinkPad old-runtime hour at 256 complete; ROG short check at 512 passed after 256 failure | Fresh final-configuration hours and physical measurements |
| Host Atmos | 15 tests and focused CI cleanup acceptance passed in PR 1 | Actual JOC reference media and physical qualification |
| macOS comparison | M4 Air getter and silent-running snapshots complete; 16 summary tests passed in PR 5 | Matched Linux software observations, then physical comparison |
| Physical interaction timing | Phone/tablet method source-reviewed; ten methods and unarmed Chrome smoke passed, no physical samples | Manual pilot, then repeated same-track capture |
| Sonos Arc/eARC | Deferred until internal audio work | TV route and actual received formats |

Companion to [installation](SPEAKER_INSTALL.md), [review](REVIEW.md) and
[implementation](AUDIO_IMPLEMENTATION.md). Source capability, synthetic results,
installation and measured performance remain separate claims.

## Installation readiness

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

## ROG live deployment

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

## ROG automatic startup

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

## ThinkPad live deployment and startup

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

## Review and acceptance

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

## Recovery and implementation decisions

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

## Latency comparison — 2026-10-13

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

## Paired 256-frame observations — historical

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

## Physical interaction measurement plan — 2026-10-13

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
Pilot capture and physical comparison remain pending. Coordinated listening
and 60-minute stability outcomes will be recorded in their own receipts; this plan does not mark either check passed. Accepted
units remain retained because their sources are unchanged.

## Startup and sustained-check progress — 2026-10-13

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
coordinator's machine. The runtime upgrade and further file staging are held
pending the sole live operator's read-only capacity audit. No unrelated files
or recovery assets are removed. This deployment hold does not change the
completed old-runtime result or imply acceptance of the new runtime.

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


## Digital loudness diagnosis — 2026-10-13

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
proven cause of the current attenuation. The proposed leveler is not yet
accepted or deployed. Fresh full-hour
checks follow the final kept configuration; Sonos remains deferred.


## ROG corrected runtime and short 512-frame check — 2026-10-13

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
The one private filter request remains installed, with its distinct snapshot
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
runs the prior runtime at 256 frames. Fresh full hours follow the final kept
loudness configuration and resolution of its storage hold.
