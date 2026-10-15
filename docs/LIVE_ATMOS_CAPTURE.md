# Isolated native capture observer

This document owns the virtual-sink acceptance recorder. The
[live player](LIVE_ATMOS.md) and [production native helper](LIVE_ATMOS_NATIVE.md)
retain their separate interfaces and buffering. This recorder is a test
observer, not a production capture feature or microphone tool.

## Why the observer changes

A native twelve-channel run submitted, consumed and drained its exact media
count with zero reported input-ring starvation, yet its recording contained
a 512-frame deletion. One bounded profiler run then matched exactly, with
zero reported playback/capture/driver xruns. The original loss remains
**unattributed**; the nonreproduction does not establish that capture caused it.

The pinned [pw-cat capture source](https://github.com/PipeWire/pipewire/blob/1.6.8/src/tools/pw-cat.c)
calls `fwrite` from its process callback and provides no observer-loss receipt.
The new observer removes that measurement weakness and makes future ring,
write and available continuity failures explicit. It does not retroactively
repair or reclassify retained failures. Current reviewed acceptance and all
attempts remain in [status](STATUS.md).

## Bounded callback and writer

`atmos-pw-capture` requests `RT_PROCESS`. Its callback validates a bounded
48-kHz interleaved float32 chunk, copies to a fixed 4096-frame SPSC ring,
requeues the buffer and signals a PipeWire event. It performs no file writes,
allocation, mutex waits or formatting. The ordinary writer copies at most
4096 bytes per iteration and handles partial writes/EINTR explicitly.

The ring holds at most 32,768 stereo or 196,608 twelve-channel bytes.
Separate fixed callback scratch, used only for wrapped or neutral SPA chunks,
is at most 196,608 bytes. Writer scratch is 4096 bytes. These observer buffers
do not queue playback audio or establish physical latency. An overflowing
ring fails explicitly rather than silently dropping frames. File and wakeup
I/O errors have separate counters even when another error occurred first.

The caller creates an exclusive, mode-0600, empty regular file. The native
helper checks ownership, single link, write-only/non-append mode and descriptor
type before connecting. Both core accounting and `RLIMIT_FSIZE` cap output
at 256 MiB. No preallocation exposes unwritten zeros to the media-arrival
barrier. No native system library or service is installed.

## Routes, ARM and STOP

The observer has no autoconnect flag and sets no-autoconnect, no-fallback,
no-reconnect, no-move, no-remix and sink-capture properties. The private
harness alone links its inputs to explicitly identified output **monitor**
ports of its own null sink, with exact matching channel names. Capture route
checks reject non-monitor ports, unrelated nodes and channel mismatches.
There is no `/dev/snd`, host session socket or hardware monitor in the
isolated graph; no default source or microphone is selected.

Before playback, the harness waits for every exact monitor link to be active,
then sends `ARM 1` over a separate bounded sequenced-packet socket and waits
for its ACK. Earlier callback frames are ignored and counted. After ARM,
callback-received frames, ring-accepted frames and successfully written bytes
are independent counters. Ring losses, file errors or invalid chunks never
produce a successful complete recording.

`STOP 2` first disables capture and destroys the input stream, waiting for
any callback which had already observed ARM. Only then may the writer drain
the remaining ring, join and publish its final receipt. Success requires
ACK/normal exit, complete accounting, no rejected/overflow/write/continuity
errors, and exact agreement with file size. Signals/control closure use the
same stream-before-writer cleanup order; the client adds bounded terminate,
kill and reap fallback. A blocked file write can therefore fail cleanup;
no complete receipt is invented after a forced kill.

The success cases require a healthy complete recording **before** the full
retained-reference PCM comparison. The finite-nonzero media barrier remains
required before destructive actions. After an intentional target removal,
a structured partial source-removal receipt is allowed without pretending
that capture completed; unexpected overflow/write failure remains a failure.
The player must still fail appropriately, show positive submitted frames,
avoid fallback and remove its owned nodes. Available playback.json is
embedded and privately retained even if observer failure interrupts normal
result collection.

## Continuity evidence and limits

The observer requests optional SPA header metadata. Missing/unsupported
metadata is reported, not interpreted as loss or used as a qualification gate.
Unavailable first/last timestamp or sequence values are `null`.

A usable `pw_time` observation must have the same 1/48000 frame domain and
cycle size as the captured chunk. Consecutive usable observations check
frame-clock progression; unavailable intervals are explicitly counted.
Header sequence numbers are media-specific, so there is no `seq + 1` rule.
The bounded run uses unsigned half-range comparison to allow normal uint64
wrap while rejecting backward sequence movement. Valid PTS may not regress;
`SPA_TIME_INVALID` is unavailable. Corrupted flags and a discontinuity after
the first armed header fail. Wrapped SPA offsets and neutral chunks follow
the pinned [buffer](https://github.com/PipeWire/pipewire/blob/1.6.8/spa/include/spa/buffer/buffer.h)
and [header](https://github.com/PipeWire/pipewire/blob/1.6.8/spa/include/spa/buffer/meta.h)
semantics.

Zero observer ring loss proves only that accepted callback frames reached
its writer. It cannot prove that the server delivered every source sample
to that callback. Metadata coverage, full bit-exact PCM comparison and any
separately collected profiler evidence remain distinct. No global server,
driver or physical-device xrun count is claimed by this recorder.

## Build and selected acceptance

Run `build-capture.sh --output EXISTING_PRIVATE_BUILD` in the established
pinned native compiler image. It builds only `atmos-pw-capture` and the
separate `native-capture-tests`, copies the capture client, and writes a
normalized `capture-source.tar` plus `capture-build.json` with actual source,
artifact and linked ABI hashes. The current compiler requires GLIBC 2.38 and
`libpipewire-0.3.so.0`; matching runtime dependencies are required. Production
playback source, binary, managed renderer and runtime remain unchanged.
The manual CI compiler phase invokes this recipe after the separate playback
build; acceptance still runs in the unchanged runtime image under 2 CPUs,
6 GiB and the existing 48-kHz/256-frame nonfreewheel private graph.

Focused methods exercise concurrent ring ordering/overflow/limit, optional
metadata and wraps, partial/error writes, real ARM/STOP/callback/quiescence,
private-FD rejection and bounded client cleanup. Their source is reviewable
before execution. The changed observer invalidates prior capture-path
acceptance, including the historical native stereo pass. The six affected
ordinary cases and separate full JOC capture must use this exact recorder;
unchanged target-mismatch and production unit receipts remain retained.
