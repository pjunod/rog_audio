# Speaker service — quit the owned process and wait for saved state

**Status:** implemented; independent review, eleven focused Linux methods and
one actual helper-to-native integration pending · **Updated:** 2026-10-13 ·
**Executes:** the controlled-stop part of [speaker installation](SPEAKER_INSTALL.md).

Companion to [native autoload](SPEAKER_AUTOLOAD.md), [programme loudness](PROGRAMME_LOUDNESS.md)
and [current results](STATUS.md). This change addresses service shutdown;
the native audio engine, original speaker filters and final limiter are unchanged.

## 1. Avoid overlapping shutdown requests

The previous user unit invoked `rog-speaker-effects --quit`. That secondary
command returns after delivering the message, before the primary process has
finished saving settings and exiting. Systemd can then send its normal SIGTERM
while shutdown is already in progress.

[The isolated diagnosis](../evidence/rog-speaker-shutdown-diagnosis-2026-10-13.json)
used the exact accepted native ELF and published ROG preset/IR. Quit followed
immediately by SIGTERM hung at the ten-second diagnostic deadline and left
AutoGain settings absent. Direct SIGTERM alone exited in 0.315 seconds; quit
followed by waiting for primary exit took 0.440 seconds. Both positive controls
saved the expected settings. The exact internal lock mechanism remains
unproven; repeated save-log lines alone do not establish it.

[The live recovery receipt](../evidence/rog-explicit1024-programme-recovery-2026-10-13.json)
records successful new-preset loading followed by the failed service stop,
missing serialization and verified restoration of original +rog2 tuning.
Its inactive KConfig settings-write lock is distinct from the runtime's
single-instance lock. The successful 1024 timing trial remains separate.

## 2. Authenticate the existing primary and await its exit

[The helper](../scripts/stop_speaker_effects.py) opens a Linux pidfd and checks
the primary's effective owner, fixed runtime executable path and process start
time. It authenticates the connected Unix socket's peer PID and UID, checks
the pinned lifetime again, sends `quit_app` followed by a newline directly,
then waits for the actual primary to exit. It never starts a secondary audio
process or sends a signal.

The CLI accepts `--socket PATH` and optional `--pid PID`. Without `--pid`, it
uses systemd's `MAINPID`; an absent/zero or already-exited primary is a no-op.
A foreign executable or peer is refused. PID lifetime pinning prevents a
replacement process from receiving the request. The helper uses a ten-second
protocol deadline and returns failure for an incomplete stop. Systemd
retains its final kill policy; the public template keeps `TimeoutStopSec=15`.

The [public unit](../systemd/rog-audio-speaker.service) now uses:

```ini
ExecStop=/usr/lib/rog-audio/stop-speaker-effects --socket %t/RogAudioSpeakerEffectsServer
TimeoutStopSec=15
```

`%t` is the existing user's runtime directory. The fixed executable is
`/opt/rog-audio/easyeffects/bin/easyeffects`. The helper does not select a
preset, change gain, install a profile, restart PipeWire/WirePlumber, remove a
lock or modify hardware protection. A clean command exit alone is insufficient:
verification must also observe the primary exit and expected saved settings.

## 3. Distinguish package distribution from the live backport

Packaging `8.2.8+rog4` adds `/usr/lib/rog-audio/stop-speaker-effects`, Python 3,
the project's existing MIT notice and exact helper/license hashes under
`stop_contract: owned-synchronous-exit-v1`. The exporter supplies those exact
source bytes to its self-contained packaging input and checks their manifest
bindings. The native ELF, corresponding native source and patch pins remain
those of the accepted programme runtime. No native rebuild is needed for the
stop correction; +rog4 packaging is separately reviewed acceptance work.
The published v0.2.2 package and assets remain unchanged.

The coordinated laptop plan instead retains the existing +rog2/+rog3 packages
and backports the exact accepted helper plus a reversible ExecStop edit. This
avoids rewriting a full runtime payload. Retain the previous unit/helper state,
source hashes and package/kit/recovery bindings before the window. Copy the
reviewed helper to an owned persistent path, retain its MIT notice and point
only the existing unit's ExecStop at that exact helper and current socket.
For example, an operator-owned helper can use this unit line:

```ini
ExecStop="%h/.local/lib/rog-audio/stop-speaker-effects" --socket "%t/RogAudioSpeakerEffectsServer"
```

That helper must be installed explicitly from the accepted source before
unit replacement. Validate the actual unit with `systemd-analyze --user verify`,
then reload the user manager. Retain the existing deadline, startup ordering,
state directory, enabled target link and remaining unit content. Do not infer
that an older package acquired +rog4 identity from this backport. Its receipt
must bind the actual old package, copied helper and changed unit separately.
No repository check installs or activates the helper or tuning.

In the coordinated stop/start window, verify native serialization after the
owned process exits, then automatic preset/IR loading and the complete tuned
route on the new invocation. Keep owner volume, stock audio services and
amplifier controls intact. Restore retained unit/helper preimages explicitly
if recovery is needed; preserve failures and their saved state. Fresh software
hours bind the final running invocation and settings.

## 4. Keep focused and physical acceptance separate

After independent review, run only the eleven selected Linux methods: six
process/peer/lifetime/timeout cases, two MAINPID/unit cases and three affected
export cases. Linux pidfd cases must execute on Linux, with zero skips. A
separate device-free integration must exercise the exact accepted helper
against the actual native ROG LocalServer, expected settings save and real
exit; fixture-child tests alone do not establish that protocol.

The progress renderer's reversible presentation change receives static HTML
inspection rather than extra cosmetic tests. Passing native/audio suites are
retained, not repeated. Live installation, owner listening, final-configuration
hours, reboot/resume/hotplug and the [physical comparison](PHYSICAL_LATENCY_METHOD.md)
remain distinct evidence. Neither a subsecond shutdown nor a software graph
period measures physical speaker latency.
