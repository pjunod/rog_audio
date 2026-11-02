# Speaker service — quit the owned process and wait for saved state

**Status:** November 2 lifetime fix independently reviewed; eleven affected Linux
methods passed once; live unit updated without restarting audio. Earlier native
helper integration remains inherited evidence · **Updated:** 2026-11-02 ·
**Executes:** the controlled-stop part of [speaker installation](SPEAKER_INSTALL.md).

Companion to [native autoload](SPEAKER_AUTOLOAD.md), [programme loudness](PROGRAMME_LOUDNESS.md)
and [current results](STATUS.md). This change addresses service shutdown;
the native audio engine, original speaker filters and final limiter are unchanged.

## 1. Avoid overlapping shutdown requests

The previous user unit invoked `rog-speaker-effects --quit`. That secondary
command returns after delivering the message, before the primary process has
finished saving settings and exiting. Systemd can then send its normal SIGTERM
while shutdown is already in progress. Upstream systemd documents that
remaining processes receive the configured kill signal after ExecStop returns
and recommends waiting for termination in that command.
[The primary ExecStop documentation](https://github.com/systemd/systemd/blob/main/man/systemd.service.xml#L479-L496)
supports this protocol requirement.

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
bindings. The [verified packaging-only artifact](../evidence/speaker-stop-packaging-only-rog4-2026-10-13.json)
retains all 142 native runtime entries, ELF/source and patch pins from the
accepted programme runtime. The 3,753,142-byte +rog4 package is built and
verified; no compiler or tests were repeated. It is now
[published in v0.2.3](../evidence/speaker-runtime-v023-publication-2026-10-14.json)
with both paired kits, notes and checksums, and remains uninstalled on the
laptops. The corrected service unit is a required separate
companion; the deb contains no automatic service/profile activation scripts.
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

Independent review cleared before all eleven selected Linux methods passed
once, with zero failures, errors or skips: six
process/peer/lifetime/timeout cases, two MAINPID/unit cases and three affected
export cases. The [exact receipt](../evidence/synchronous-stop-unit-acceptance-2026-10-13.json)
binds the reviewed source/helper, selected methods and verified Linux resource
limits; individual fixtures clean themselves up and their durable scratch
parent/logs remain retained. The separately coordinated [native integration](../evidence/speaker-stop-native-integration-2026-10-13.json)
passed first execution with the exact accepted helper and actual native ROG
LocalServer: both returned 0 in 0.321 seconds, expected native settings were
saved and the original preset/IR/full stereo route were verified. No secondary
native CLI or helper signal was used. Fixture-child tests alone would not
establish that protocol. Both owned acceptance containers were removed.

The progress renderer's reversible presentation change receives static HTML
inspection rather than extra cosmetic tests. Passing native/audio suites are
retained, not repeated. Live installation, owner listening, final-configuration
hours, reboot/resume/hotplug and the [physical comparison](PHYSICAL_LATENCY_METHOD.md)
remain distinct evidence. Neither a subsecond shutdown nor a software graph
period measures physical speaker latency.

## 5. Stop tuning before PipeWire disappears

On 2026-11-01, lab5's managed logout stopped PipeWire at 18:01:19.784388
local time. The native engine logged `No connection to PipeWire. Aborting!`
at 18:01:19.814504 and exited with SIGABRT. The saved Apport report was
subsequently presented on November 2. This is a confirmed lifetime-ordering
failure, rather than evidence of a filter or IR failure. The retained native
source's core-error callback invokes `util::fatal` on `connection error`;
that function uses Qt's fatal logger.

The unit now combines `BindsTo=pipewire.service` and
`PartOf=pipewire.service` with its existing `After=pipewire.service`.
Managed PipeWire stop/restart transactions therefore stop tuning first,
using the existing synchronous save-and-exit helper. The install section
also includes `WantedBy=pipewire.service`: enabling the updated unit adds a
reverse wants link so a separate PipeWire start brings tuning back.
[Systemd's dependency documentation](https://www.freedesktop.org/software/systemd/man/261/systemd.unit.html)
defines these lifetime, ordering and install relationships.

After installing the reviewed unit, run `systemctl --user enable
rog-audio-speaker.service` again and `systemctl --user daemon-reload`.
These commands do not restart the running engine. Preserve the original unit
and exact enable-link inventory first. Verify the resolved dependencies and
both `default.target.wants` and `pipewire.service.wants` links. Permanent
bypass uses `systemctl --user disable --now rog-audio-speaker.service`, which
removes both enable links; a temporary stop can be undone by the next
PipeWire start. Rollback restores the retained unit and original link inventory,
then reloads the user manager without restarting audio.

The focused Linux lifecycle test uses UUID-owned fake services and Unix
sockets on a build host. It exercises stop/start, restart and failed backend
startup with the real stop helper and production unit relationships. It never
opens sound devices or operates real audio services. Fixture event receipts
remain outside Git. Unexpected backend process death can still precede a
managed stop; this fix does not claim to eliminate every possible disconnect.
Seven earlier SIGKILL exits have no established sender in the retained journal
windows and remain a separate unresolved observation.

The [November 2 receipt](../evidence/speaker-pipewire-lifecycle-diagnosis-2026-11-02.json)
records eleven passing methods, unchanged live process/invocation and twelve
unchanged protected files. No live shutdown or listening test was performed.
