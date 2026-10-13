# Status — implementation and physical acceptance

**Updated:** 2026-10-13 · **State:** both speaker candidates installed with
login startup configured; ROG stereo tuning restored after four-channel
investigation; PR 5 merged and scoped latency trials are in progress.

| Work | State | Next evidence |
|---|---|---|
| Hardware inventory | Both laptops inspected read-only | Refresh during installation |
| ASUS speaker tuning | Validated stereo restored with full tuned path; prior owner feedback positive | Scoped latency trial, physical hotplug and measurements |
| ThinkPad speaker tuning | Separate Lenovo music/balanced candidate running; live preset, IR, plugins and hardware output verified | Owner listening, physical hotplug and measurements |
| Laptop installation runtime | Both active with private rollback and login startup; inherited 97 unit cases and both isolated graph cases passed | Actual post-reboot observation and physical qualification |
| Diagnostics and latency | PR 5 merged; 46 new unit cases and all native checks passed; prior 42 tests retained | Bounded 256-frame trials with tuning and rollback preserved |
| Host Atmos | 15 tests and focused CI cleanup acceptance passed in PR 1 | Actual JOC reference media and physical qualification |
| macOS comparison | M4 Air getter and silent-running snapshots complete; 16 summary tests passed in PR 5 | Matched Linux software observations, then physical comparison |
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
relationship; measurement equipment is not yet established. No new latency
improvement or Mac parity is claimed. Sonos Atmos remains last.

[PR 5](https://github.com/pjunod/rog_audio/pull/5) contains the complete
implementation, merged at `d02c07178bfaff0c5582cb253d10c8c1738d17c9`,
and received three independent adversarial reviews. All
four findings were fixed and source-cleared before 46 new unit cases passed
once. Seven native filter cases passed; the config stage passed after one
reviewed command correction and config-only retry. No passing case repeated. Existing speaker and unrelated Atmos passes remain retained.

Fresh idle baselines show the ROG now exposes an Analog Surround 4.0 sink while
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

## Scoped live latency trials

The ThinkPad has moved from the original transient process to the already
enabled persistent user service. The controlled quit serialized the four
previously absent plugin settings files through the runtime's native save
path. That serialization is recorded separately from payload preservation;
the preset, IR, runtime, startup unit, default, volume and stock audio service
process IDs were preserved. The reviewed settings snapshot now succeeds.

A fresh baseline under the persistent service used an explicit 4800/48000
client request and all-zero PCM. Its actual driver period remained 2048/48000
with the full Lenovo processing chain connected on both channels. The scoped
256-frame request has not yet been accepted on a live laptop. Preflight found
two tool assumptions to correct: systemd's formatted output omits an empty
`EnvironmentFiles` property, and native controlled quit saves a preset-use
counter. Typed D-Bus inspection proves the former is empty; the latter changed
only `[StreamOutputs] usedPresets`, with no DSP setting change. The ThinkPad
baseline was resumed and its full chain rechecked. Both listeners retain their
working tuning. The complete correction batch passed adversarial review and
29 affected unit methods; one failed test expectation was corrected and only
that method rerun. The corrected live trial is next.
The [preflight receipt](../evidence/speaker-lifecycle-preflight-2026-10-13.json)
records both observations, raw-evidence hashes and the preserved startup state.
