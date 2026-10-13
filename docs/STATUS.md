# Status — implementation and physical acceptance

**Updated:** 2026-10-13 · **State:** both speaker candidates installed with
login startup configured; ROG stereo tuning restored after four-channel
investigation; 256-frame requests deployed with rollback retained; sustained
check remains active on ThinkPad; ROG stopped on error growth after 67.982
seconds; a ROG post-session startup race is under
offline investigation after restoration of its tuned preset.

| Work | State | Next evidence |
|---|---|---|
| Hardware inventory | Both laptops inspected read-only | Refresh during installation |
| ASUS speaker tuning | Full tuned path preserved after reviewed removal of failed 256-frame request; short 2048-frame observation retained | Review/test startup fix and 512-frame candidate; physical hotplug and measurements |
| ThinkPad speaker tuning | Separate Lenovo music/balanced candidate running; live preset, IR, plugins and hardware output verified | Owner listening, physical hotplug and measurements |
| Laptop installation runtime | Both tuned paths restored/active; ROG session-start autoload bypass observed and restored; inherited acceptance retained | Review/test permanent startup fix, actual post-reboot observation |
| Diagnostics and latency | Both tuned drivers reduced from 42.667 to 5.333 ms in retained paired receipts; PRs 5–7 reviewed/tested | Complete sustained checks, then physical measurements |
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
process. No reboot was performed; actual startup after reboot is pending
observation. Its recovery tools, original source/notices, baseline, startup
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

## Scoped live latency trials — both candidates active

Both laptops now run the full tuning chain under the enabled persistent user
service with the exact 256/48000 output-filter request active. Paired all-zero
PCM observations, each with the same 100 ms client request, showed their
actual driver period changing from 2048/48000 (42.667 ms) to 256/48000
(5.333 ms). ROG sampled driver/DSP error counters stayed zero. ThinkPad's
driver reached count 1 at startup in both runs and stayed at 1 in the later
samples; this is not a zero-error activation result.

Runtime, presets, IR, plugin settings, physical defaults and stock audio
services were preserved. Final owner volume remained 86% on ROG and 20% on
ThinkPad. Each has versioned tools, a private fragment snapshot and rollback
commands; original tuning/package recovery is also retained. Both are ready
for owner listening. Actual post-reboot startup, physical hotplug/resume,
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
binds the sole live operator's [scoped v3 receipt](../evidence/speaker-listening-stability-v3-2026-10-13.json)
and private launch/helper hashes. ThinkPad remains active; the ROG attempt
stopped on monitored error growth and its request was removed using reviewed
rollback. Neither has a completed full-hour receipt. The original
[v2 source](../evidence/speaker-listening-stability-interim-2026-10-13.json)
remains unchanged as a historical launch snapshot. V3 corrects scope and
retains the later failure, cleanup, rollback and listening overlaps.
Expected finish times are targets, not observations of a pass.

| System and attempt | Observed outcome | Separate next interval |
|---|---|---|
| ROG initial attempt | Aborted before the timed interval when startup driver errors increased above the retained baseline; owned test processes removed and failure evidence retained | A new session has its own counter baseline; the earlier failure remains recorded |
| ThinkPad initial attempt | Stopped on volume change; attempt plus cleanup lasted 581.040 seconds from 20% to 74%; sampled driver count stayed at 1, sampled DSP/owned source counts stayed zero | Retry starts a fresh full hour and logs volume adjustments as normal-use conditions |
| ThinkPad normal-use retry | Active from 10:02:02 Eastern; actual 100% physical-default starting volume preserved; full Lenovo chain at 256/48000 | Expected finish 11:02:02; final counter, continuity and preservation receipts pending |
| ROG post-session normal-use run | Started 10:09:39 Eastern; stopped after 67.982 seconds of owned playback on monitored error growth; 256/48000 and physical 94% volume preserved | Failure archived; no automatic counter reset/retry and no full-hour pass |

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

The current ThinkPad retry baseline is 100% physical-default volume, not the
74% final level of its earlier stopped attempt. The v3 launch receipt corrects
that earlier progress report. At the recorded 26-minute observation, driver
count remained 1 with no volume-condition transitions. Separate owner-approved
listening/microphone overlaps are retained with their timestamps, native
recorder exit code 1, private recording hashes and restored temporary input
gain. The silent workload itself emits no acoustic signal and records no
microphone. The nested signal's `playback_performed: false` describes its
preparation stage; later operation entries describe actual playback. Those
scopes do not qualify physical latency or calibrated sound quality.

The runtime owner is preparing the startup correction in a separate offline
source/build workspace. This integration batch currently contains documentation
and progress evidence only. It will receive the runtime source and completed
stability receipts before independent adversarial review and affected tests.
No candidate fix is installed and no active hour is interrupted for that work.
Accepted unchanged units remain retained.

The latency tool now also prepares a 512/48000 candidate (10.667 ms) while
retaining its 256-frame default and guarded file-only install/remove contract.
One new CLI/lifecycle preservation method is prepared but unexecuted. The
candidate is unqualified until actual negotiation, full tuned processing,
error continuity and preservation are observed. It is not deployed during an
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
post-reboot startup, hotplug/resume and the phone-capture pilot remain pending.
