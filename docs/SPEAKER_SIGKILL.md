# Speaker SIGKILL diagnosis

**Status:** two new CPU-timer kills captured; offending code path unresolved ·
**Updated:** 2026-11-03 · **Related:** [speaker service](SPEAKER_SERVICE.md).

## 1. Historical evidence

Seven lab5 speaker-service invocations ended with SIGKILL on October 20, 21,
25 (three), 27 and 30, 2026. The November 1 SIGABRT was a separate managed
PipeWire shutdown-order failure, fixed by PR 19. Retained whole-system JSON
journal windows span each SIGKILL and include no matching kernel OOM message,
userspace OOM-killer action, systemd stop deadline or RTKit canary action.
This narrows the evidence; it does not identify a sender or rule out missing
telemetry. The service's recorded peak memory was approximately 136–161 MiB.

The current process has a 200,000 microsecond soft/hard `RLIMIT_RTTIME`,
despite an unlimited service-level setting. PipeWire's RT module can set this
process limit when obtaining scheduling through RTKit. That limit concerns
uninterrupted realtime CPU execution, not a 200 ms audio buffer.
[PipeWire documents these realtime limits](https://pipewire.pages.freedesktop.org/pipewire/page_module_rt.html).
The host's `kernel.print-fatal-signals` is zero; Linux's CPU-timer code
conditions its watchdog message on that setting. Absence of a watchdog log
therefore does not exclude this hypothesis. No limit was increased or removed.

The current cgroup has no recorded OOM kills, but those counters belong to the
current invocation and cannot establish historical conditions. Later unrelated
host memory-pressure events are not attributed to the speaker process.

## 2. Observe the source without changing DSP

[The signal probe](../scripts/trace_speaker_signals.bt) requires root,
bpftrace 0.25 and matching kernel BTF. It observes only SIGKILL and SIGXCPU
for a selected UID and thread-group leader name. Checking the leader includes
renamed audio threads and follows restarted engine processes. The name is a
diagnostic selector, not proof of executable identity; correlate the event
with the service invocation and native executable before assigning blame.

Each event is emitted as one asynchronous print record with matching
monotonic timestamp/PID/TID boundary markers. Discard incomplete, duplicate or
mismatched records instead of assigning another event's limits or stack.
It records monotonic time, current execution PID/TID/UID, target PID/TID,
signal, signal-info code, generation result and kernel stack. The November 3
extension adds target leader name, scheduler policy/RT priority, `rt.timeout`
in scheduler ticks, and CPU/RTTIME soft/hard limits at signal generation.
CPU limits are seconds; RTTIME limits are microseconds; the unsigned all-ones
value represents infinity. Do not interpret timeout ticks as microseconds.

A userspace stack is attempted only when the current thread is the target.
Other cases explicitly report a context mismatch; a sender stack must not be
called the target stack. Unwinding and symbols remain best effort, especially
when a process exits before symbol resolution. Retain loaded-file hashes and
private mappings to interpret unresolved addresses. It does not
record media, microphone input, process arguments or environment. Keep the
raw log private because it contains process identifiers and kernel stacks.
The [Linux tracepoint contract](https://www.kernel.org/doc/html/latest/core-api/tracepoint.html)
defines this generation event; generation does not by itself prove delivery.

**How to read it:** a userspace sender normally has `code=0` (`kill`) or
`code=-6` (`tgkill`), with its execution PID in `context_pid`. `code=128`
means kernel-origin signal information; the stack is required to distinguish
CPU timers, OOM and other kernel sources. For kernel-origin records the
current execution PID is not necessarily a culpable sender. Match the target
to the simultaneous service exit and retained process identity. A quiet log
proves only that no matching event was observed during that interval.

## 3. Explicit tests and bounded operation

The [privileged integration test](../tests/speaker_signal_trace_integration.py)
is outside ordinary unit discovery. Run it explicitly on a Linux build/test
host with the required BPF privileges:

```bash
sudo python3 -B tests/speaker_signal_trace_integration.py -v
```

It selects only fixed fixture name `rog-sig-fixture`, creates its
own child PIDs, tests ordinary and thread-directed kills, and validates a
20 ms hard realtime-limit signal with a CPU-timer stack. Each child has a
three-second supervisory deadline. It never selects the real speaker engine.
Test logs are retained in an exclusively created private directory.

A live observation must use an owned transient diagnostic unit with no enable
links, a seven-day runtime limit, an 8 MiB file-size limit, a 512 MiB memory
limit and a 10% userspace CPU quota. Stop it explicitly to detach the probe;
it also expires at its deadline or on reboot. Use `Restart=no`; a quota,
log-size limit or deadline ending the trace is an observation gap, never
evidence that no crash occurred. Retain source hashes, startup
receipt and the exact stop command privately. Do not restart audio, induce a
failure in the real engine or weaken realtime/OOM protection to obtain a log.

## 4. Scope and remaining work

This is observation, not a claimed fix for the seven historical kills. No DSP,
preset/IR, gain, limiter, graph period, stock firmware or Sonos setting changes.
The PR 19 unit/link rollback remains untouched. A future matching signal plus
service exit can support a specific corrective change; without that evidence,
changing realtime scheduling or memory protection would be speculation.

## 5. November 2 observation

Independent adversarial review passed after clarifying execution-context
attribution and moving fixture receipts to durable private storage. All three
privileged integration methods passed once on the target kernel/bpftrace pair,
including a real watchdog kill of an owned silent fixture. The test cgroup
finished successfully and was collected.

At that November 2 checkpoint, the original transient capture was active
with the documented bounds. Startup
verification found the same audio PID/invocation/restart counter and thirteen
unchanged runtime/protected-file paths, including the PR 19 service unit.
Its stop command, root-owned probe copy and startup receipt are retained
privately. Neither laptop's tuning or rollback changed; no live playback,
recording, audio restart, scheduling-limit change or Sonos operation occurred.
The [allowlisted receipt](../evidence/speaker-sigkill-investigation-2026-11-02.json)
records exact source/test hashes. Historical attribution remains unresolved;
no native-engine repair is claimed from this observation setup.

## 6. November 3 readback — two real CPU-timer kills

[The follow-up receipt](../evidence/speaker-sigkill-trace-followup-2026-11-03.json)
records two signals captured on November 2 at 21:19:18 and 21:22:16 UTC
(16:19:18 and 16:22:16 Eastern). Both are kernel-origin SIGKILLs on the
PipeWire data thread, through `posix_cpu_timers_work`; their matching service
exits followed within 19 ms. Automatic restart recovered both invocations.
The November 3 readback found tuning active with restart count two and no
additional recorded exits in that observation interval.

The running process has unlimited `RLIMIT_CPU` and a 200,000 microsecond
soft/hard `RLIMIT_RTTIME`. The current native file matches the accepted engine.
These observations make the realtime watchdog the leading explanation, but
the old probe did not capture limits at the exact signal or the userspace
stack. They do not prove the offending DSP/PipeWire call or retroactively
attribute the seven October kills. The matched windows contain no OOM or
managed-stop action. No native repair is claimed yet.

All thirteen protected paths were stable during collection; the twelve
non-unit paths match the November 2 preimage, and the unit matches PR 19.
The saved rollback is readable. The observed graph remains 1024/48 kHz.
Source inspection found several external DSP calls and realtime hazards,
but no evidence selects one for a corrective patch. The enhanced event-time
probe is the next diagnostic step; the watchdog and audio settings stay intact.

The enhanced probe has compiled with `bpftrace --mode=codegen`, which exits
before attachment. In bpftrace 0.25, `-d codegen` alone is debug output and
must not be used as a no-attachment compiler check. Independent adversarial review cleared the corrected atomic event framing
and bounded replacement workflow. All three affected fixture methods passed
once on the enhanced source, including distinct-limit record matching and a
nonempty userspace stack from a silent watchdog fixture. The test unit was
collected successfully; no unchanged suite was repeated.

The enhanced seven-day observer is active. It was ready before the previous
observer stopped; the original trace is retained on the host and privately
offhost. Replacement preserved the running speaker PID, invocation, restart
count and all thirteen protected files. It did not restart audio or alter
the graph, DSP, realtime limit or rollback. A future matching event can now
identify the userspace call; an empty or unresolved stack must still be
reported as incomplete evidence. The observer expires after seven days or
on reboot and has no restart policy. Its stop command and receipts are
retained privately. This merge delivers diagnosis and instrumentation, not
a claim that the CPU overrun is repaired.
