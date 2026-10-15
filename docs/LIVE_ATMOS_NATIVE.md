# Native Atmos playback helper

This document owns the native helper's transport, build and failure contract.
The [live player](LIVE_ATMOS.md) owns user invocation and routing. Source
implementation and compile receipts are separate from accepted virtual-sink
PCM and physical playback; current acceptance is recorded in [status](STATUS.md).
The [accepted full JOC capture](../evidence/live-atmos-acceptance-2026-10-15.json)
used this helper at 48 kHz/1024 frames under the documented two-CPU condition.
Prior failed 256-frame captures remain failed; software acceptance does not
qualify realtime scheduling or physical presentation.

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
A declared last partial callback preserves exactly the remaining media frames
and fills only the unused suffix of that final requested output buffer with
neutral zeros. `tail_padding_frames` counts those extra transport frames only
after successful queueing; it is zero for an aligned final buffer and strictly
less than that callback's requested frames (at most 4096). It is separate from
input, consumed/media, priming, startup silence and missing-media counts.
Extra input, incomplete
frame bytes, early EOF and EOF before BEGIN fail explicitly.

Completion requires exact complete stdin EOF, all priming/media frames
consumed from the ring, successful queueing of the final actual-media buffer,
a subsequent graph process demand, and PipeWire's drained event.
A separate callback publication after successful `queue_buffer` prevents an EOF
or older mainloop event from flushing before the final partial buffer is queued.
The next process request publishes a second prerequisite without queueing an
empty EOF buffer. The mainloop waits for both publications and validated input
EOF before requesting drain. This follows the EOF sequence in pinned
[PipeWire 1.6.8 pw-cat](https://github.com/PipeWire/pipewire/blob/1.6.8/src/tools/pw-cat.c).
The next-demand correction alone did not change the retained seek failure:
its complete final 247-frame fragment arrived after one silent 256-frame cycle.
The final-request fill addresses the split adapter's full-duration output
contract in pinned
[PipeWire 1.6.8 audioconvert](https://github.com/PipeWire/pipewire/blob/1.6.8/spa/plugins/audioconvert/audioconvert.c).
It changes neither media samples nor their count, and adds no sleep. For the
observed 256-frame request, 247 media frames receive nine neutral suffix frames
(0.1875 ms of transport audio). The corrected seek case captured all 95,223
media frames exactly with nine separately counted padding frames. The accepted
full JOC run at a 1024-frame request similarly counted 512 transport-padding
frames outside its 3,528,192 media frames. The exact internal cause of the earlier
adapter delay remains an inference. No complete extra quantum or DSP filter
tail is generated.
The capability description requires `final_buffer_policy: fill-request`; an
older or incompatible colocated helper fails before playback. The Python client
requires the separate nonnegative padding counter and bounds it below the
largest callback request without including it in media/EOF accounting.
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

The smallest runnable layout is below. The complete pinned runtime version
directory is retained rather than selecting individual framework assemblies.
The executable apphost `AtmosProbe`, PDBs, SDK, regression executables,
`pw_cat.py` and isolated capture tools are not needed by `atmos-live`.

```text
private-build/
  atmos-live                       # executable Python launcher
  registry_json.py
  native_playback.py
  atmos-pw-playback                 # executable native backend
  AtmosProbe.dll
  AtmosProbe.deps.json
  AtmosProbe.runtimeconfig.json
  Cavern.dll
  Cavern.Format.dll
  source_manifest.json
  native-build.json
  native-source.tar
  PROJECT-LICENSE
  PROJECT-LICENSES.md
  CAVERN-LICENSE.md
  CAVERN-NUGET-LICENCE.md
  PIPEWIRE-EXAMPLE-LICENSE
  runtime/                         # optional with --dotnet or a PATH runtime
    dotnet
    LICENSE.txt
    ThirdPartyNotices.txt
    host/fxr/8.0.20/libhostfxr.so
    shared/Microsoft.NETCore.App/8.0.20/  # entire retained version directory
```

The package assembler must supply the project licence and current attribution
index, the unmodified Cavern `LICENSE.md`, and its pinned
`docs/NuGet Licence.md` variant under the labelled names above. These notices
are not implied by a successful build or by the source manifest. Retain the
original author/repository links, restrictive Cavern terms and the PipeWire
example's complete MIT notice. The separate .NET runtime keeps both its licence
and third-party notices. No system PipeWire library is bundled.

`native-source.tar` covers the native helper, client, tests, recipe and notice;
it is not the complete corresponding project/Cavern source. Any separate
preview source archive should retain this repository's exact source revision,
all three attributed Cavern patches and their manifests/hashes, the pristine
Cavern source at its pinned revision, and both upstream licence files. The
runnable archive's per-file inventory should bind the actual managed, native,
Python, runtime and notice bytes to the build and acceptance receipts. Test
observers/executables belong in private acceptance artifacts, with their source
retained separately. Any preview publication follows the recorded acceptance and merge.

Focused core tests cover concurrent ring wrap/order, exact priming boundary,
prefill, short final tail, native underflow, malformed input/control and
control/cancellation while ring and pipe are full. Python tests cover helper
capability/ACK/final-count failure and the unchanged route guards. Transport
acceptance used the actual native helper. The final full-vector pass is
limited to the documented 48-kHz/1024-frame condition; ordinary 256-frame
receipts remain inherited, and full JOC failures at 256 are retained. The
isolated harness uses an independent
[native capture observer](LIVE_ATMOS_CAPTURE.md); its implementation and
acceptance do not alter this production helper. No microphone/physical recording is added.
