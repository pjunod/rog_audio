# Speaker SIGKILL diagnosis

**Status:** historical sender unresolved; reviewed trace active; three fixture tests passed ·
**Updated:** 2026-11-02 · **Related:** [speaker service](SPEAKER_SERVICE.md).

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

It records monotonic time, current execution PID/TID/UID, target PID/TID,
signal, signal-info code, generation result and kernel stack. It does not
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

The private transient capture is active with the documented bounds. Startup
verification found the same audio PID/invocation/restart counter and thirteen
unchanged runtime/protected-file paths, including the PR 19 service unit.
Its stop command, root-owned probe copy and startup receipt are retained
privately. Neither laptop's tuning or rollback changed; no live playback,
recording, audio restart, scheduling-limit change or Sonos operation occurred.
The [allowlisted receipt](../evidence/speaker-sigkill-investigation-2026-11-02.json)
records exact source/test hashes. Historical attribution remains unresolved;
no native-engine repair is claimed from this observation setup.
