# Live Atmos — render bounded files into an explicit PipeWire sink

Companion to the [offline Atmos contract](../probes/atmos/README.md) and
[reference vectors](ATMOS_REFERENCE.md). This document owns the small Linux
player's invocation, routing contract and interpretation. It is an
implementation prototype awaiting independent review and selective acceptance;
physical playback, independent Dolby fidelity and realtime qualification are
unmeasured. Sonos Arc/eARC testing remains last.

## Run the player through your existing tuned sink

Build with the pinned [Atmos build recipe](AUDIO_ATMOS_BUILD.md), or use the
reviewed private Linux build. The build copies `atmos-live` beside
`AtmosProbe.dll`. You need Python 3.10 or newer, native PipeWire tools `pw-cat` and
`pw-dump`, and a .NET 8 runtime. The launcher chooses sibling
`runtime/dotnet`, then `dotnet` on `PATH`; `--dotnet` selects an explicit
runtime host. No global SDK/runtime installation is required for a private
bundle containing the pinned 8.0.20 runtime and its licence notices. The
existing offline launcher keeps its established interface; put that same
private runtime on `PATH` when using it.

```bash
mkdir -p -m 700 private-live  # Keep media and detailed reports private.
private-build/atmos-live \
  --input private-live/channel-id.eac3 \
  --target rog_audio_speaker_sink \
  --layout stereo-speakers --volume 0.5 \
  --start-sample 0 --report private-live/playback.json
```

Choose the existing tuned virtual sink by its exact `node.name` or current
`object.serial`. The ROG's observed tuned name is
`rog_audio_speaker_sink`; discover the actual current sink on each machine
with a read-only `pw-dump`. Do not substitute a physical sink merely because
it is the default: that would bypass the existing speaker processor. The
player does not select a target automatically or change any default device,
volume, profile, EQ, graph quantum, service or persistent routing configuration.
The ordinary act of creating a playback client is explicit in this command.

`--volume` is a finite linear attenuation in `[0, 1]`, applied to rendered
PCM. It does not adjust the sink or application mixer. The default is unity.
`--start-sample` is an exact integer sample PTS at 48 kHz, from zero through
validated input EOF. The initial seek replays from frame zero to preserve
decoder/object/filter history before output starts; long seeks may hit the
existing CPU budget. Seeking exactly to EOF succeeds without creating a
PipeWire playback client.

`stereo-speakers` pans objects to FL/FR. It supplies no HRTF, binaural
headphone processing or height reproduction. Your existing tuned speaker
chain still owns tonal correction and protection. `7.1.4` requires an explicit
sink whose ordered positions exactly match
`FL FR FC LFE RL RR SL SR TFL TFR TRL TRR`. These are PipeWire's names for
the Cavern/WAV order `FL FR FC LFE BL BR SL SR TFL TFR TBL TBR`; no samples
are reordered or synthesized by that spelling translation.

## Boundaries — what actually streams

```text
 bounded raw E-AC-3 / synthetic scene snapshot
              │  decode objects before metadata loss
              ▼
 .NET pull renderer, 256-frame DSP / 4096-frame caller buffer
              │  readiness header, then interleaved float32 PCM
              ▼
 4096-byte producer pipe → 4096-frame supervisor queue
              │  finite samples, exact count and backpressure
              ▼
 4096-byte player pipe → pw-cat stdin → selected PipeWire sink
```

The input is privately snapshotted as a bounded regular file before managed
parsing. Raw E-AC-3 remains limited to 64 MiB, 48 kHz and 90 seconds by the
existing scanner. Synthetic JSON remains limited to 10 seconds. JOC/OAMD
consumption, conventional-channel fallback and unsupported formats keep the
offline engine's explicit classifications. Stereo E-AC-3, TrueHD, arbitrary
containers and changing stream configurations retain their existing limits.

There is no complete rendered WAV or PCM file between decoder and output.
The producer writes at most 4096 frames per caller block; a full pipe stops
further decoding. The supervisor prebuffers one 4096-frame queue (85.333 ms
at 48 kHz), or the complete shorter final fragment. Its writes are frame
aligned and no larger than the 4096-byte atomic pipe-write bound. Each
kernel pipe is explicitly limited to 4096 bytes before the child starts; a
host unable to provide that exact pipe capacity is unsupported. These are application
transport bounds, not the size or latency of PipeWire's internal buffers.

The managed decoder runs in a separate process, outside the PipeWire
processing callback. `pw-cat` owns the native output callback and may starve
if its input is late. The prototype does not measure underruns or prove
realtime scheduling. A buffer bound is not a latency measurement.

Startup/header preparation has a 45-second wall bound. Route activation has
a separate 45-second wall bound and at most 2,160,000 startup zero frames.
The first bound reached stops startup. These zeros do not replace media.
Decoding retains the 60 CPU-second, 128-descriptor and 512 MiB managed-heap
launcher bounds.
Transfer has a wall bound of remaining media duration plus 60 seconds, a
15-second no-progress watchdog, and a 15-second final drain bound. Each
registry observation has a 2-second/4 MiB bound. The shared registry parser
reads every JSON array in order, validates object IDs and removals, and
applies tombstones; malformed trailing data fails. This handles native
[`pw-dump` removal events](https://github.com/PipeWire/pipewire/blob/0.3.65/src/tools/pw-dump.c)
which may precede or follow its snapshot even without monitor mode. The whole playback can
therefore take longer than the original 90-second offline wall timeout.
Native allocations and filesystem/network access are not sandboxed by the
launcher; use the isolated acceptance container for untrusted inputs.

## Routing is pinned for the whole invocation

The supervisor resolves one `Audio/Sink` to a positive unique `object.serial`
and checks its ordered channel map. Before submitting PCM, it requires all
matching channel links from its unique playback node to that same node.
Some native callbacks begin consuming stdin before every link finishes
negotiating. After verifying all exact pairs, the supervisor may feed
bounded startup silence while it waits for every link to report `active`.
It holds the media prebuffer unchanged until that observation, then sends
the complete media without dropping or padding its samples. Startup silence
uses the same bounded pipe and is counted separately from all media hashes,
frame counts and source receipts. Missing, wrong or failed routes stop
priming. The private capture harness also waits for all its monitor links
to become active before launching playback.
During streaming and drain it checks for disappearance, serial replacement,
layout change, lost links and links to unrelated nodes. It fails and stops
the producer and player on a routing error. One persistent route worker is
created before any startup silence or media. It performs native registry
queries, parses their bounded JSON and applies the same exact route checks
outside the feeder. At most one request is in flight, with a 2-second
response watchdog and 4-MiB native snapshot limit. A new observation starts
500 ms after the previous result. The worker returns only a sequence-bound
linked/active/error result of at most 1 KiB over private nonblocking pipes.
Unexpected sequence, malformed/oversized response, worker exit or timeout
stops playback. The feeder reuses one selector and never forks a registry
query or parses its large JSON while delivering PCM. No
bytes are submitted before the first complete route verification; actual
media also requires the all-active observation. Drain retains synchronous
bounded observations. The stream's native target
properties additionally prevent fallback and reconnection between
observations. A partial or missing route on a still-present playback
node fails immediately during drain, even if the child exits successfully
a moment later. Only complete playback-node disappearance can coincide with
normal client teardown after its drain callback; the supervisor accepts that
race only if the child exits successfully within 250 ms. Target disappearance,
identity changes and wrong links still fail immediately.

The native client sets `target.object`, `node.dont-fallback`,
`node.dont-reconnect`, `node.dont-move`, `stream.dont-remix` and
`channelmix.disable`. These follow the official
[PipeWire property contract](https://docs.pipewire.org/page_man_pipewire-props_7.html).
`PIPEWIRE_*`, `SPA_*`, `DOTNET_*` and `COMPlus_*` overrides are sanitized;
the explicitly selected PipeWire remote/runtime directory is preserved.
The chosen .NET host directory supplies `DOTNET_ROOT` with multilevel lookup
disabled. No shell receives media paths or target names.

The source-inspected native backends include
[`pw-cat` 0.3.65](https://github.com/PipeWire/pipewire/blob/0.3.65/src/tools/pw-cat.c).
That version takes raw PCM from `-` plus explicit format/rate/channel options;
it has no `--raw` option. In
[`pw-cat` 1.6.8](https://github.com/PipeWire/pipewire/blob/1.6.8/src/tools/pw-cat.c),
`--raw` bypasses file-format probing before the playback node is created.
The launcher and isolated capture harness observe `pw-cat --help` with a
2-second / 64-KiB bound and add `--raw` only when advertised. A failed or
malformed capability observation stops startup. The report records
`pw_cat_explicit_raw`; this observation is not playback qualification.
A normal session manager supplies channel links in
desktop use. The policy-free isolated harness configures only its own client adapter
DSP ports and explicit test links because its private daemon has no desktop
session manager. The normal player does not apply those harness setters.

Ctrl-C, SIGTERM and SIGHUP stop the producer and player, wait briefly, then
kill a child which will not stop. The route worker has its own process group;
cleanup signals that group, lets the worker reap an active `pw-dump`, then
uses bounded kill/reap fallback. Final media EOF is sent before worker
cleanup so a final partial native read can finish promptly. The player has no runtime pause, seek,
input append, gap handling or interactive volume command. Stop it and start
another invocation with `--start-sample` or attenuation; the initial prototype
does not retain an old output queue across a restart.

## Read the private report without inferring sound

Exit zero and `status: completed` mean that validated PCM reached the
requested native stream, both children exited successfully, exact byte/frame
counts matched, and the producer/submitted PCM hashes matched. For a nonempty
stream, `pw-cat` returned zero after its drain callback. This is software
delivery evidence. It does not say that a speaker was audible, that a tuned
chain's filters loaded, or that Dolby reference output matched.

| Field | What it proves |
|---|---|
| `startup_priming_frames` | Zero frames sent only to the verified route before media activation; excluded from media counts |
| `media_start_verified_active` | Every matching link reported active before the first media frame was submitted |
| `backend_submitted_frames` | Startup zero frames plus submitted media frames; not hardware presentation |
| `expected_frames` | Validated input duration minus requested initial sample |
| `rendered_frames` | Completed producer receipt's written PCM frames; null after incomplete producer failure |
| `received_complete_frames` | Whole PCM frames received by the supervisor |
| `submitted_complete_frames` / `submitted_bytes` | Data accepted into the player's stdin pipe; not device presentation |
| `drained_frames` | Submitted frames after successful native drain; null on failed drain |
| `pipewire_drain_completed` | Native player's successful drained exit; false for an empty EOF invocation |
| `producer.decoded_frames` | Encoded syncframes observed by Cavern; not PCM frames or physical samples |
| `producer.object_metadata_consumed` | The actual JOC/synthetic object branch was used; false for bed fallback |
| `underruns` | Null: no trustworthy underrun counter is collected |
| `physical_playback_observed` | Always false: no acoustic observation is performed |

A failure may leave submitted frames greater than zero: cancellation cannot
unplay bytes already delivered. A native stdin `BrokenPipeError` during
media submission reports `pipewire-player-ended-early`, including the race
between the process check and a write. It proves early input closure, not
its cause. Other I/O errors keep the generic process/I/O failure status. No successful drain count is invented from a
write count. Error reports preserve the received/submitted prefix and any
available producer receipt, with upstream/private exception text suppressed.
The report is prepared in a private same-filesystem directory, mode 0600,
then published with an exclusive hard link. Existing files, directories,
broken symlinks and a raced publication collide; no public target is deleted.
No report is promised for an invalid command or an unavailable/colliding
report destination. Detailed reports from personal media remain private.

## Acceptance — run selected methods only after independent review

The [selectable unit runner](../scripts/validate_atmos_live.py) rejects unknown,
duplicate, skipped and empty acceptance. It binds source manifests before
and after execution. The five producer methods need the reviewed Linux build;
the generated-bed method also needs an explicit locally generated fixture.

```bash
python3 scripts/validate_atmos_live.py \
  --build private-build --bed-fixture private-live/bed.eac3 \
  --report private-live/units.json
# Retry only a failed or invalidated exact method, using repeated --test-id:
python3 scripts/validate_atmos_live.py \
  --test-id test_atmos_live.LiveTests.test_header_and_pcm_validation \
  --report private-live/header-retry.json
```

The `live-ci` image stage uses the repository's pinned Ubuntu base with
PipeWire 1.6.8 / WirePlumber 0.5.17 and copies the existing pinned .NET SDK
8.0.414 / runtime 8.0.20 from the build stage. The separate legacy `ci`
stage and its encoder remain unchanged. Modern live fixture generation uses
FFmpeg 8.1.2; the generated-bed producer method must qualify that new fixture
once. Exact direct package versions are in the
[source manifest](../probes/atmos/source_manifest.json). The older
`live-ci-legacy` diagnostic stage remains available, with its failed
partial-fragment captures retained as evidence; it is not the default live lane.
Changing the CI backend does not create a runtime version gate.

The isolated harness observes its private graph through one persistent
`pw-dump --monitor --no-colors` client per case. It pumps that client's
nonblocking 64-KiB output pipe at the existing 50-ms cadence instead of creating a new
registry client on every observation. Complete changed objects and tombstones
are applied chronologically; ID reuse retains the new serial. Each JSON
document, pump and complete current-state cache has a 4-MiB bound. Startup
and partial-document completion each have a 2-second bound. Malformed data,
EOF or child failure stops the case; cached state is never silently reused
after failure. The monitor is stopped and reaped during case cleanup.
The three destructive cases also capture their own controlled virtual sink
with automatic routing/fallback disabled and exact monitor links checked.
They incrementally inspect at most 64 KiB per pump, require a complete frame
containing finite numerically nonzero PCM, then continue pumping for one
second before cancellation or target removal. Startup silence and signed
zero cannot satisfy that barrier. Nonfinite PCM in the inspected prefix fails
the case.
This proves generated media reached the virtual monitor before the action;
it does not measure physical presentation. Positive submitted-frame and
cleanup assertions remain required. No runtime test hook or full ten-second
prerender is used.

This changes observer workload because diagnostic client churn caused
playback/capture xruns; it does not weaken channel, target, fallback or full
PCM checks, or change runtime player buffers. Earlier failed captures retain
their original observed results; the later diagnostic does not retroactively
prove their cause.

The [separate virtual-sink lane](../probes/atmos/live-ci.sh) uses a pinned native PipeWire daemon with no
`/dev/snd` or desktop session socket. It checks streamed capture/hash/count,
initial seek/attenuation, target mismatch/loss, cancellation and node cleanup.
Public official JOC-vector streaming is separate from generated-scene/bed
unit evidence. None of those checks qualifies laptop hardware, physical
latency, independent Dolby fidelity, binaural rendering or Sonos reception.
Passing inherited offline receipts remain bound to their original sources.

The manual-only `atmos-live` workflow lane accepts selection `units`,
`integration` or `all`. Its `test_ids` input means exact full unittest IDs
for `units` and exact case IDs for `integration`; the `all` selection takes
no retry selectors or JOC input. At the local wrapper, `--test-id` alone
defaults to `units`; `--case` or `--joc-input` alone defaults to `integration`.
Mixing unit and integration retry selectors, or combining explicit `all`
with a selector/input, fails before Git, image inspection or container work.
It runs no legacy Atmos, speaker or laptop lane. The local
container wrapper needs an already prepared pinned image and source checkout:

```bash
probes/atmos/live-ci.sh --image PRIVATE_PINNED_LIVE_IMAGE \
  --source PRIVATE_PINNED_CAVERN --report private-live/integration.json \
  --stage integration --case success-seek
```

The ordinary integration selection contains `success-stereo`, `success-714`,
`success-seek`, `mismatch`, `cancel`, `target-loss` and `policy-target-loss`.
The policy case uses a private WirePlumber 0.4 or 0.5/D-Bus session, with
version-matched private configuration and hardware monitors disabled and an alternative sink available, to exercise native
no-fallback behavior. The other cases use explicit test-owned links.
`success-joc` is a separate opt-in case requiring `--joc-input` with the
[exact official 7.1.4 E-AC-3 vector](ATMOS_REFERENCE.md). It compares the
captured stream against the retained source-bound PCM hash; it does not
rerun the earlier accepted full offline render. These distinctions keep
synthetic, official-input and actual desktop policy evidence separate.

Failed full-PCM comparisons retain capture/expected/payload frame and byte
counts, SHA-256 values, alignment offset and first/last mismatch positions
before the assertion. Generated-scene comparisons also report the first
mismatching channel and exact 32-bit sample representations; a missing
anchor or missing tail is explicit. These diagnostics do not relax the full
byte comparison or turn a failed capture into a successful playback result.

A direct isolated `live_integration.py` invocation can add
`--failure-artifacts NEW_PRIVATE_DIR`. It creates mode-0700 directories and
mode-0600 capture/expected-stream files only for failed cases, at most
256 MiB per file, with sizes and hashes in the detailed report. Existing
paths collide. The expected-stream file includes the producer readiness
header before its raw float PCM; the capture file is raw float PCM. This
optional private output is separate from the cleaned temporary case tree;
retain it for diagnosis and remove it deliberately after its receipt is
preserved. The ordinary CI report keeps diagnostic metrics without retaining
raw payloads. Personal-media captures must remain private.
