# Status — implementation and physical acceptance

**Updated:** 2026-10-14 · **State:** both laptops now run +rog3 with the
reviewed helper/unit backport, original speaker voicing and protection intact.
ROG uses 1024/48000 with −20 LUFS/cap 2.6475 dB; ThinkPad uses 256/48000 with
−16 LUFS/cap 14.1375 dB. Real helper/native stop, saved-state, two automatic
starts, short checks and both final full-stereo software hours passed with
no added driver errors. Both current generated demos are accepted. Physical
recording is deferred to another coordinated window; measurements and broader
media qualification remain open.
**Evidence update:** both final hours completed 2026-10-14 00:12/00:16 UTC; dated receipts below retain separate attempts.

| System | Deployed software | Timing term | Loudness | Current acceptance |
|---|---|---|---|---|
| ROG | +rog3, separately backported merged helper/unit | Graph 1024/48 kHz, 21.333 ms | −20 LUFS, cap 2.6475 dB | Full hour passed, no added errors; accepted demo, improved loudness; physical checks remain |
| ThinkPad | +rog3, separately backported merged helper/unit | Graph 256/48 kHz, 5.333 ms | −16 LUFS, cap 14.1375 dB | Full hour passed, no added errors; accepted sound/loudness demo; physical checks remain |
| M4 Air | Stock output; matched files staged | HAL 512/48 kHz, 10.667 ms | Unchanged | Actual browser/route/phone/keyboard pilot and physical comparison |
| Sonos | Deferred | Unmeasured | Unassessed | Internal-speaker acceptance first |

Both actual laptop packages remain +rog3, ELF `3f110d6a`; the separate helper
is `ba8c4a6a` with MIT notice `b6dfebc6`. +rog4 is a verified packaging-only
artifact, not a published release or installed laptop package. No new reboot,
resume/hotplug, calibrated acoustics or physical speaker-delay pass is inferred.
Graph periods and the HAL buffer are different software terms; final hours
remain separate from the historical ThinkPad hour and intentionally shortened
−20 observation. The ROG observer's two-compressor pre-start refusal was a
procedure error, not an audio failure; only that observation was restarted.

| Work | State | Next evidence |
|---|---|---|
| Hardware inventory | Both laptops inspected read-only | Refresh during installation |
| ASUS speaker tuning | +rog3, original voicing preserved; final 1024 hour and current demo passed | Broader media and physical checks |
| ThinkPad speaker tuning | −16/cap 14.1375 installed; original voicing preserved; final 256 hour and current demo passed | Broader media and physical checks |
| Laptop installation runtime | Both +rog3 with exact merged helper/unit backport; saved-state, automatic starts and final hours passed | Reboot/resume/hotplug separately |
| Diagnostics and latency | Final ROG 1024/ThinkPad 256 hours passed without added errors; earlier failures/partial/old-runtime runs retained | Physical measurements |
| Programme loudness | Reviewed corrected `+rog3` build accepted: 28 units passed once; both model graphs passed after failed-selector-only retry | Both deployments, final hours and current demos accepted; physical checks remain |
| Host Atmos | 15 tests and focused CI cleanup acceptance passed in PR 1 | Actual JOC reference media and physical qualification |
| macOS comparison | M4 Air getter/silent-running snapshots and Linux software observations retained; 16 summary tests passed in PR 5 | Physical comparison in a later coordinated window |
| Physical interaction timing | Ten methods/local M3 unarmed smoke retained; matched files/browser prepared; ROG page unarmed; no physical samples | Deferred coordinated pilot and repeated same-track capture |
| Sonos Arc/eARC | Deferred until internal audio work | TV route and actual received formats |

Companion to [installation](SPEAKER_INSTALL.md), [review](REVIEW.md) and
[implementation](AUDIO_IMPLEMENTATION.md). Source capability, synthetic results,
installation and measured performance remain separate claims.

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
release resolves to v0.2.2. The runtime archive is 9,551,458 bytes, kit archive
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
records two prepared ordinary distribution kits matching the currently deployed
provisional DSP settings, bound to the verified +rog4 package. ASUS kit
`51efcc00` keeps preset `78dba4c0`, −20 LUFS/cap 2.6475 dB. ThinkPad kit
`a292c2c6` keeps preset `c2b90751`, −16 LUFS/cap 14.1375 dB. The paired
121,200-byte kit archive has SHA256
`c0520d9866b0166e194b71f1c18071755d43753c2474980d2bbe006a23cf9e0f`;
44 members and metadata were independently checked for safe/public contents.
The unchanged runtime/source archive `f00fe028` and required service companion
remain paired. These are prepared, not installed, published or owner-approved.
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
