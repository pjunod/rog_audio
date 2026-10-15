# Native Atmos playback helper

This document owns the native helper's transport, build and failure contract.
The [live player](LIVE_ATMOS.md) owns user invocation and routing. Source
implementation and compile receipts are separate from accepted virtual-sink
PCM and physical playback; current acceptance is recorded in [status](STATUS.md).
The new helper does not imply that prior failed JOC captures have passed.

## Purpose and callback boundary

The native profiler diagnostic placed the earliest mismatch alongside
playback xruns before capture reported an xrun. Later capture and driver
errors also occurred, and profiling perturbed the graph. This supports
replacing playback's blocking `pw-cat` callback; it does not establish a
universal cure or attribute every prior failure to playback.

`atmos-pw-playback` uses PipeWire's `RT_PROCESS` stream flag. Its callback
performs bounded copies from a preallocated single-producer/single-consumer
ring, lock-free atomic accounting, buffer dequeue/queue and PipeWire event
notification. It performs no stdin/file/socket I/O, allocation, logging,
mutex acquisition or wait. An ordinary reader thread polls stdin and a
wakeup descriptor; the mainloop handles control, signals and drain. The
[PipeWire ring example](https://github.com/PipeWire/pipewire/blob/1.6.8/src/examples/audio-src-ring.c)
supplies the callback/event pattern, with its MIT attribution retained.

The ring holds 4096 frames, independent of channel count. The stdin pipe is
4096 bytes; the Python queue remains 4096 frames, producer pipe 4096 bytes
and live decoder release 1536 frames. The reader has a 4096-byte scratch
buffer and one incomplete frame. No buffer grows with input duration.
At twelve channels this adds 56.889 ms of native capacity compared with the
old 65,536-byte input pipe. Capacity is not measured acoustic latency.
The callback rejects a requested quantum above its 4096-frame ring bound
rather than changing graph quantum. No C# renderer, Cavern source, runtime,
volume, default device or existing speaker tuning is changed by this helper.

## Input, control and completion

The launcher resolves an explicit sink serial and exact ordered layout.
The helper accepts 48-kHz interleaved little-endian float32, stereo FL/FR or
`FL FR FC LFE RL RR SL SR TFL TFR TRL TRR`. It repeats native no-fallback,
no-reconnect, no-move and no-remix properties. The supervisor continues exact
identity/channel/link observations throughout startup, transfer and drain.
Python owns finite/bounded samples, SHA256 and source/media frame validation;
the helper does not repeat hashing or decode work.

A private `SOCK_SEQPACKET` control descriptor is independent of PCM stdin.
There is one bounded command, `BEGIN 1 PRIMING_FRAMES MEDIA_FRAMES\n`, followed
by its exact `ACK`. The offset counts stdin frames, not zero-valued samples.
The mainloop can acknowledge while the ring and input pipe are full. The
supervisor sends BEGIN only after all exact links are active, stops further
priming, and waits for ACK before writing media. Duplicate, malformed,
oversized, out-of-order or disconnected control fails closed.

Before BEGIN, stdin frames are priming. After BEGIN the consumer stops at
the declared boundary and waits for `min(4096, media remaining)` frames before
starting media. Callback-generated startup/prefill silence is separately
counted and never advances the media cursor. Once media starts, a shortage
of required frames is `native-media-underrun`, not successful silence.
A declared last partial callback queues exactly the remaining media frames,
without counting its absent padding as missing media. Extra input, incomplete
frame bytes, early EOF and EOF before BEGIN fail explicitly.

Completion requires three distinct states: exact complete stdin EOF, all
priming/media frames consumed from the ring, and PipeWire's drained event.
A separate callback publication after `queue_buffer` prevents an EOF or
older mainloop event from flushing before the final partial buffer is queued.
A final bounded packet reports the completion states and counters before exit. Python
requires exact agreement with its priming/submitted counts and zero native
underflows before publishing a successful drain count. Native counters cover
ring starvation, not every server/device deadline or hardware presentation.

Control EOF, signals, input error, native stream error or route failure
stops the helper. Cleanup wakes the reader, joins it, destroys only its own
stream and closes descriptors. Parent-side deadlines and bounded kill/reap
fallback still apply. There are no runtime pause/seek commands or fallback
backend. Missing or incompatible native helper fails before playback.

## Build and standalone artifacts

The established managed [build](AUDIO_ATMOS_BUILD.md) stays unchanged.
`build-native.sh --output EXISTING_PRIVATE_BUILD` separately compiles the
helper and two test executables with pinned GCC 15.3.0, C11, `-O2`, strict
warnings, pthreads and PipeWire 1.6.8/SPA 0.2 headers. The exact compiler
package versions and public package hashes are in
[compiler-packages.json](../probes/atmos/native/compiler-packages.json).
The `live-compiler` Docker stage extends `live-ci`; selected acceptance uses
the unchanged runtime stage, with both image identities recorded and no
implicit image pulls.

The helper dynamically requires `libpipewire-0.3.so.0` and libc. The actual
NEEDED libraries and maximum required GLIBC symbol version are recorded in
`native-build.json` alongside source/artifact hashes. A modern compiler can
require a newer libc than other Linux machines provide. The matching target
stack is the supported packaging target; this is not a universally portable
Linux binary. No native system library is copied into the private bundle.

A live bundle adds `atmos-pw-playback`, `native_playback.py`,
`native-build.json`, `native-source.tar` and `PIPEWIRE-EXAMPLE-LICENSE` beside the existing launcher,
managed DLLs, registry module, source manifest, Cavern notice and optional
pinned .NET runtime with its notices. Retain corresponding native source and
recipe with build receipts. `native-tests` and `native-io-tests` are separate
acceptance executables; the production helper has no test mode. Its bounded
`--describe` capability probe does not connect to PipeWire.

Focused core tests cover concurrent ring wrap/order, exact priming boundary,
prefill, short final tail, native underflow, malformed input/control and
control/cancellation while ring and pipe are full. Python tests cover helper
capability/ACK/final-count failure and the unchanged route guards. Transport
acceptance must run through the actual new helper before earlier synthetic
or full JOC success can be claimed. Capture remains the existing isolated
`pw-cat` observer for this change; no microphone/physical recording is added.
