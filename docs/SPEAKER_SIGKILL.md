# Speaker SIGKILL diagnosis

**Status:** two new CPU-timer kills captured; offending code path unresolved ·
**Updated:** 2026-11-04 · **Related:** [speaker service](SPEAKER_SERVICE.md).

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

## 7. Isolated reproduction and source audit

The operator reports intermittent crash notifications, not audible dropouts.
The only retained audio Apport report found in this inspection was from
November 1, the separately fixed shutdown abort. That does not prove which
notification the operator saw; it must not be relabelled as a new SIGKILL.

[Five private diagnostic runs](../evidence/speaker-sigkill-isolated-observations-2026-11-03.json)
used the exact accepted native engine, private PipeWire/D-Bus, generated PCM
and a null sink. The sandbox could not access physical audio devices or the
desktop buses. Each run had two-CPU, 2 GiB and 180-second bounds. Before input,
only the copied engine's verified data thread was converted from direct-limit
FIFO to RR20, retaining RESET_ON_FORK and the 200,000 us soft/hard limit.
This matches the priority/limit values but differs from production RTKit
acquisition. No production scheduler setting changed.

| Diagnostic | Scope | Result |
|---|---|---|
| Full chain | Three cycles, twelve acknowledged 512/1024 quantum requests, quiet idle unlink | No kill in 43.736 s |
| Empty chain | Same three-cycle sequence without preset plugins | No kill in 43.774 s |
| Rapid quantum | One cycle, forty acknowledged quantum requests | No kill in 24.105 s |
| Rate requests | Twenty acknowledged 44.1/48 kHz requests | No kill in 23.896 s; callback rates unmeasured |
| Observed driver rates | Four requests and bounded `pw-top` snapshots | No kill in 23.985 s; private output driver observed at 44.1/48/44.1/48 kHz, quantum 1024 |

Four setup failures are retained separately: file-size limit, socket-path
length, session-manager readiness and direct-acquisition scheduling mismatch.
They stopped before generated input and are not successful crash reproductions.
Every completed diagnostic preserved the production invocation and thirteen
protected paths. The private units stopped and ephemeral runtimes were removed.
Graph/preset checks do not add independent IR, output-fidelity, physical latency
or acoustic acceptance. A short negative case cannot exclude an intermittent
failure. Rate cases deliberately exceed the observed production allowed-rate
list of 48 kHz; hidden UI may bypass spectrum visualization. No diagnostic
proved execution of that component's LV2 branch.

**Source finding:** `Spectrum::ready` is a plain bool written by a worker
under `data_mutex` but read by the realtime process without that lock. A
queued rate-change job can publish readiness for an older request before a
later job destroys/recreates the instance. Worker-job serialization does not
serialize those jobs with the realtime callback. This is a concrete source
hazard, not attribution of the captured CPU-timer kills. An atomic bool alone
would not protect instance lifetime or reject stale publication. Limiter and
multiband setup share the creation-before-lock pattern and require the same
care if a future trace selects that path.

The earlier quantum-recreation hypothesis was too broad:
[`Lv2Wrapper::create_instance`](https://github.com/wwmm/easyeffects/blob/6d9b1220d3dcebb154ba759a05600662bc0af549/src/lv2_wrapper.cpp)
already returns early for an existing instance at the same rate. No native
patch was made on the strength of that mistaken assumption. Inspection of
PipeWire 1.6.8's [filter callback](https://github.com/PipeWire/pipewire/blob/1.6.8/src/pipewire/filter.c),
[node scheduling](https://github.com/PipeWire/pipewire/blob/1.6.8/src/pipewire/impl-node.c)
and [support loop](https://github.com/PipeWire/pipewire/blob/1.6.8/spa/plugins/support/loop.c)
found candidate retry/drain paths but no evidence selecting one as the cause.

**Next evidence:** a matching enhanced live event or an actual reproducer
must identify the userspace call before claiming a SIGKILL repair. The bounded
observer remains available for normal-use recurrence. Keep its expiry/reboot
limit in mind; a quiet or stopped observer is not a stability result. Speaker
tuning, watchdog protection, rollback and Sonos stay unchanged.


## 8. Runnable-loop diagnosis — distinguish ready work from one slow callback

**Status:** implementation and Linux compile preflight complete; independent
review and selected fixture acceptance pending as of November 4. No native
repair or production runnable-loop observation is claimed here. The existing
signal observer is unchanged.

The [source-bound kernel receipt](../evidence/speaker-runnable-kernel-accounting-2026-11-04.json)
records the running kernel provenance and exact accounting files. The RT
scheduler resets `rt.timeout` on `ENQUEUE_WAKEUP`; RR timeslice rotation does
not reset it. A poll syscall that returns immediately need not put the thread
to sleep. Several cheap callbacks can therefore accumulate a realtime budget
when the loop stays ready. This is a mechanism to distinguish, not proof that
it caused either captured kill. PipeWire 1.6.8's
[data loop](https://github.com/PipeWire/pipewire/blob/1.6.8/src/pipewire/data-loop.c)
immediately iterates again, and its
[invoke dispatcher](https://github.com/PipeWire/pipewire/blob/1.6.8/spa/plugins/support/loop.c)
drains queued work until no item remains without an explicit time/item budget.

**Run one bounded observation:** use the
[one-shot runner](../scripts/observe_speaker_runnable.py) as root on the
BTF-equipped Linux host with bpftrace 0.25. Obtain the actual process ID, data
thread ID and accepted executable SHA-256 from your read-only service
inspection. Supply the running kernel's `CONFIG_HZ`, not `getconf CLK_TCK`.
Use an owned transient unit with the resource limits in §3, a hard runtime
limit of the requested duration plus 30 seconds, and no restart/enable links.
The output directory must be new; its parent must already exist.

```bash
sudo python3 scripts/observe_speaker_runnable.py \
  --pid "$ENGINE_PID" --tid "$DATA_TID" \
  --expected-exe-sha256 "$ACCEPTED_SHA256" \
  --kernel-hz 1000 --duration 30 \
  --output "$NEW_PRIVATE_OUTPUT"  # Creates a private directory; no target signal
```

The runner verifies leader/thread start times, thread-group membership and
executable hash, opens a leader pidfd, captures private mappings, and checks
identity again after attachment. The BPF program independently compares the
selected thread's `start_boottime` against its `/proc` start tick value.
Those start ticks use `USER_HZ` (`SC_CLK_TCK`), separately supplied to the
probe; they are not scheduler RTTIME ticks. The probe stops on selected
thread exit and rejects an identity mismatch. The runner never signals the
target and stops only its owned tracer.

**Readiness and completion:** bpftrace 0.25 runs `BEGIN` before ordinary
probe attachment. The runner requires both its initialization record and the
normal, nonquiet `Attaching N probes...` record, emitted after attachment.
A `BEGIN` marker alone announces initialization. This corrects the convention
for new launches; it does not establish an unobserved historical gap in the
existing long-running signal observer.

The requested 1–300 second window starts after attachment and identity
verification. A normal bounded stop sends SIGINT only to the tracer after
that window and rechecks target identity. A natural target exit is an explicit
shorter observation. The probe's duration-plus-20-second timer is backup;
expiry, missing completion, observer failure, stderr diagnostics, reported
loss or unexpected unmatched syscall/stack records make the receipt
inconclusive. A single initial poll exit before any observed entry is
`initial_poll` boundary ambiguity: its entry may precede attachment, so its
duration and return category are omitted. It is not itself evidence of loss. The
runner also enforces attachment, exit-drain and shutdown deadlines.
`receipt.json`, `stdout.log`, `stderr.log` and `maps.txt` remain private.
Exit 0 means a completed observation, not a crash repair or stability pass.

**How to read it:** counters are cumulative; each summary and each framed
stack uses a single output record. Raw `max_ticks` and sampled
`rt_timeout_ticks` require the exact kernel `CONFIG_HZ` for conversion. On the
retained 1000 Hz kernel, the 20-tick warning is a nominal 20 ms budget, not a
precise callback stopwatch. `running_ns` sums scheduler residency and includes
interrupt time. `poll_ns` and `poll_max_ns` are syscall wall durations and can
include descheduling. Raw scheduler `preempt` and `prev_state` distinguish
runnable preemption from nonrunnable switch-out; wakeups are counted separately.

| Evidence together | Interpretation to investigate |
|---|---|
| Many positive poll returns, growing ticks, little sleeping | Continuously ready event work; inspect sampled paths |
| Negative poll returns with growing ticks | Error/retry loop candidate |
| Few poll returns, growing ticks, DSP-heavy samples | Expensive callback candidate |
| Few poll returns, growing ticks, invoke-dispatch samples | Queue-drain saturation candidate |

These patterns support the next focused inspection; samples cannot prove a
complete callback lifetime. The sampler runs at 99 Hz, emits stacks only at
or above the warning threshold, limits stack output to ten per second and
sixty total, and keeps scalar maps rather than an unbounded event history.
An idle thread can produce no samples or poll activity during a valid window;
that supplies no DSP conclusion. A quiet short run does not exclude the
intermittent failure.

**Acceptance scope:** the
[silent compiled fixture](../tests/speaker_runnable_fixture.c) has three
independent paths: drained 10 ms timerfd waits, an intentionally undrained
always-ready eventfd, and finite CPU work with no epoll call. The ready case targets an actual
worker TID distinct from its leader PID; the leader joins that worker. Each
case announces only its owned target TID through a bounded private pipe and
then waits at the attachment gate. Each uses only
its owned process, RR1, the unchanged 200,000 us hard/soft limit, a 20 second
attachment gate alarm and a three second work alarm. The
[explicit integration runner](../tests/speaker_runnable_trace_integration.py)
checks their distinct scheduler/poll/tick evidence and shares the live
runner's strict parser. Independent malformed-evidence coverage includes
distinct PID/TID, bounded stop, deadline, loss and incomplete records.
A separate mocked cleanup-failure method requires private receipt retention
when the tracer disappears, cleanup times out, or cleanup/hash operations
fail. Cleanup errors make the result inconclusive; a process-exit race is
recorded separately. Linux strict C and BPF codegen-only compilation have
passed; these five new test
methods have not yet run. No audio devices, production settings, playback,
recording, native deployment or Sonos changes are part of these fixtures.
