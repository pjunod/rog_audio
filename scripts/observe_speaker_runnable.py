#!/usr/bin/env python3
"""Bounded read-only observation of one explicitly verified Linux thread.

Never signals the target. Requires root, bpftrace0.25/BTF and actual CONFIG_HZ.
Private output includes process mappings/stacks. Failures produce inconclusive
receipts; quiet observations do not establish stability or a SIGKILL repair.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import resource
import select
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def proc_identity(pid, tid=None):
    tid = pid if tid is None else tid
    if pid <= 0 or tid <= 0:
        raise ValueError('PID and TID must be positive')
    leader = Path(f'/proc/{pid}')
    thread = leader / 'task' / str(tid)
    def start(path):
        return int((path / 'stat').read_text().rsplit(')', 1)[1].split()[19])
    exe = (leader / 'exe').resolve(strict=True)
    status = (thread / 'status').read_text()
    if not re.search(rf'^Tgid:\s+{pid}$', status, re.M):
        raise ValueError('thread does not belong to requested process')
    return {'pid': pid, 'tid': tid, 'leader_start_ticks': start(leader),
            'start_ticks': start(thread), 'exe': str(exe),
            'exe_sha256': hashlib.sha256(exe.read_bytes()).hexdigest(),
            'comm': (thread / 'comm').read_text().strip()}


def parse_output(output, stderr, returncode, pid, tid=None, expected_end='target_exit'):
    """Fail closed: attachment, loss, identity, completion and framing matter."""
    tid = pid if tid is None else tid
    if returncode != 0 or stderr.strip():
        raise ValueError(f'observer failed or reported diagnostics: rc={returncode} {stderr}')
    if re.search(r'(?i)\b(lost|error|warning|failed|unable)\b', output):
        raise ValueError('observer loss/error output')
    if len(re.findall(r'^Attaching [1-9][0-9]* probes?\.\.\.$', output, re.M)) != 1:
        raise ValueError('missing/duplicate after-attachment confirmation')
    initialized = re.findall(r'^runnable-initialized .*$', output, re.M)
    if len(initialized) != 1:
        raise ValueError('missing/duplicate initialization')
    initial = dict(re.findall(r'(\w+)=(\d+)', initialized[0]))
    if initial.get('pid') != str(pid) or initial.get('tid') != str(tid):
        raise ValueError('wrong initial identity')
    ends = re.findall(r'^runnable-end .*$', output, re.M)
    if len(ends) != 1:
        raise ValueError('missing/duplicate final record')
    pairs = re.findall(r'(\w+)=(\d+)', ends[0])
    fields = {key: int(value) for key, value in pairs}
    if len(pairs) != len(fields):
        raise ValueError('duplicate final field')
    if fields.get('pid') != pid or fields.get('tid') != tid:
        raise ValueError('wrong final identity')
    required = {'pid', 'tid', 'target_exit', 'deadline', 'identity_error', 'running_ns',
        'sleep_out', 'runnable_out', 'wakeups', 'poll_enter', 'poll_ready', 'poll_zero',
        'poll_error', 'poll_ns', 'poll_max_ns', 'unpaired_poll', 'initial_poll', 'samples', 'max_ticks', 'stacks'}
    if set(fields) != required:
        raise ValueError('incomplete final fields')
    if fields['initial_poll'] not in (0, 1) or fields['stacks'] > 60:
        raise ValueError('invalid bounded counter')
    if fields['identity_error'] or fields['unpaired_poll']:
        raise ValueError('identity or syscall coverage gap')
    reason = 'target_exit' if fields['target_exit'] == 1 and fields['deadline'] == 0 else (
        'deadline' if fields['deadline'] == 1 and fields['target_exit'] == 0 else (
        'bounded_stop' if fields['deadline'] == 0 and fields['target_exit'] == 0 else None))
    allowed = (expected_end,) if isinstance(expected_end, str) else expected_end
    if reason not in allowed:
        raise ValueError('incomplete observation or unexpected end reason')
    headers = list(re.finditer(r'^runnable-stack .*$', output, re.M))
    trailers = list(re.finditer(r'^runnable-stack-end .*$', output, re.M))
    if len(headers) != len(trailers) or len(headers) != fields.get('stacks'):
        raise ValueError('missing/duplicate stack record')
    for header, trailer in zip(headers, trailers):
        if header.end() >= trailer.start():
            raise ValueError('interleaved/incomplete stack')
        identity = dict(re.findall(r'(\w+)=(\d+)', header.group()))
        if not {'mono_ns', 'pid', 'tid'} <= set(identity):
            raise ValueError('incomplete stack identity')
        expected = f"runnable-stack-end mono_ns={identity['mono_ns']} pid={pid} tid={tid}"
        if trailer.group() != expected or identity.get('pid') != str(pid) or identity.get('tid') != str(tid):
            raise ValueError('mismatched stack identity')
        between = output[header.end():trailer.start()]
        if 'runnable-stack ' in between or not re.search(r'(?m)^\s+(?:0x)?[0-9a-fA-F]+\s+\S+', between):
            raise ValueError('interleaved/empty stack')
    return fields


def log_limits():
    resource.setrlimit(resource.RLIMIT_FSIZE, (8 * 1024 * 1024, 8 * 1024 * 1024))


def finalize_observation(output, receipt, tracer, pidfd, started):
    """Attempt owned-process cleanup and always attempt a durable final receipt."""
    def failure(stage, error):
        receipt['verdict'] = 'inconclusive'
        receipt.setdefault('missing_coverage', []).append(f'{stage}: {type(error).__name__}: {error}')

    try:
        if tracer is not None:
            try:
                status = tracer.poll()
            except Exception as error:
                failure('cleanup poll', error)
                status = None
            if status is None:
                receipt['observer_forced_stop'] = True
                for signum in (signal.SIGINT, signal.SIGKILL):
                    try:
                        os.killpg(tracer.pid, signum)
                    except ProcessLookupError:
                        # The owned tracer can exit between poll and signal.
                        receipt.setdefault('cleanup_races', []).append('tracer already exited')
                    except Exception as error:
                        failure('cleanup signal', error)
                    try:
                        tracer.wait(timeout=2)
                        break
                    except Exception as error:
                        failure('cleanup wait', error)
            receipt['observer_returncode'] = tracer.returncode
    except Exception as error:
        failure('cleanup', error)
    finally:
        try:
            if pidfd is not None:
                os.close(pidfd)
        except Exception as error:
            failure('pidfd close', error)
        finally:
            receipt['finished_unix_ns'] = time.time_ns()
            receipt['elapsed_s'] = time.monotonic() - started
            receipt['files'] = {}
            try:
                for path in output.iterdir():
                    if path.is_file() and path.name != 'receipt.json':
                        try:
                            receipt['files'][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
                        except Exception as error:
                            failure('evidence hash ' + path.name, error)
            except Exception as error:
                failure('evidence listing', error)
            finally:
                # Cleanup/hash failures must not bypass this final write attempt.
                (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')


def observe(args):
    if sys.platform != 'linux' or os.geteuid() != 0:
        raise ValueError('explicit Linux root invocation required')
    if args.pid <= 0 or args.tid <= 0 or not 1 <= args.duration <= 300:
        raise ValueError('positive PID/TID and duration1..300 seconds required')
    if args.kernel_hz not in (100, 250, 300, 1000):
        raise ValueError('supply exact running CONFIG_HZ (100,250,300,1000)')
    if not re.fullmatch(r'[0-9a-fA-F]{64}', args.expected_exe_sha256):
        raise ValueError('expected executable SHA256 must have64 hexadecimal digits')
    output = args.output.absolute()
    output.mkdir(mode=0o700, parents=False, exist_ok=False)
    receipt = {'verdict': 'inconclusive', 'requested_pid': args.pid,
        'requested_tid': args.tid, 'kernel_hz': args.kernel_hz,
        'user_hz': os.sysconf('SC_CLK_TCK'), 'duration_s': args.duration,
        'kernel': os.uname().release, 'started_unix_ns': time.time_ns(),
        'missing_coverage': [], 'target_signalled': False}
    tracer = None
    pidfd = None
    started = time.monotonic()
    try:
        identity = proc_identity(args.pid, args.tid)
        receipt['identity'] = identity
        if identity['exe_sha256'] != args.expected_exe_sha256.lower():
            raise ValueError('target executable hash mismatch')
        pidfd = os.pidfd_open(args.pid)
        if select.select([pidfd], [], [], 0)[0]:
            raise ValueError('target already exited')
        script = ROOT / 'scripts/trace_speaker_runnable.bt'
        receipt['probe_sha256'] = hashlib.sha256(script.read_bytes()).hexdigest()
        receipt['runner_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        receipt['warning_ticks'] = math.ceil(args.kernel_hz * .020)
        # Private mapping snapshot is evidence for best-effort stack symbolization.
        (output / 'maps.txt').write_text(Path(f'/proc/{args.pid}/maps').read_text())
        command = ['bpftrace', '-B', 'line', str(script), str(args.pid), str(args.tid),
            str(receipt['warning_ticks']), str(args.duration + 20), str(identity['start_ticks']), str(receipt['user_hz'])]
        receipt['command'] = command
        with (output / 'stdout.log').open('w') as out, (output / 'stderr.log').open('w') as err:
            tracer = subprocess.Popen(command, stdout=out, stderr=err,
                start_new_session=True, preexec_fn=log_limits)
            attach_until = time.monotonic() + 15
            while True:
                stdout = (output / 'stdout.log').read_text()
                stderr = (output / 'stderr.log').read_text()
                if stderr.strip() or re.search(r'(?i)\b(lost|error|warning|failed|unable)\b', stdout):
                    raise ValueError('observer reported error/loss; inspect private logs')
                if re.search(r'^Attaching [1-9][0-9]* probes?\.\.\.$', stdout, re.M) and 'runnable-initialized ' in stdout:
                    break
                if tracer.poll() is not None or time.monotonic() >= attach_until:
                    raise ValueError('missing after-attachment confirmation')
                if select.select([pidfd], [], [], 0)[0]:
                    raise ValueError('target exited before attachment confirmation')
                time.sleep(.02)
            if proc_identity(args.pid, args.tid) != identity or select.select([pidfd], [], [], 0)[0]:
                raise ValueError('target identity changed during attachment')
            receipt['attachment_confirmed'] = True
            receipt['attached_unix_ns'] = time.time_ns()
            window_start = time.monotonic()
            bounded_stop = False
            # Independent post-attachment duration; BPF deadline is backup only.
            stop_until = window_start + args.duration + 3
            exit_seen = None
            while tracer.poll() is None:
                stdout = (output / 'stdout.log').read_text()
                stderr = (output / 'stderr.log').read_text()
                if stderr.strip() or re.search(r'(?i)\b(lost|error|warning|failed|unable)\b', stdout):
                    raise ValueError('observer reported error/loss; inspect private logs')
                if select.select([pidfd], [], [], 0)[0] or not Path(f'/proc/{args.pid}/task/{args.tid}').exists():
                    exit_seen = exit_seen or time.monotonic()
                    if time.monotonic() - exit_seen > 1:
                        raise ValueError('observer missed target exit deadline')
                if not exit_seen and time.monotonic() - window_start >= args.duration:
                    if proc_identity(args.pid, args.tid) != identity or select.select([pidfd], [], [], 0)[0]:
                        raise ValueError('target identity changed before bounded stop')
                    receipt['observed_window_s'] = time.monotonic() - window_start
                    bounded_stop = True
                    os.killpg(tracer.pid, signal.SIGINT)
                    tracer.wait(timeout=2)
                    break
                if time.monotonic() >= stop_until:
                    raise ValueError('observer exceeded independent hard deadline')
                time.sleep(.02)
            receipt['observer_returncode'] = tracer.returncode
        fields = parse_output((output / 'stdout.log').read_text(),
            (output / 'stderr.log').read_text(), tracer.returncode, args.pid, args.tid,
            expected_end=('target_exit', 'bounded_stop') if bounded_stop else 'target_exit')
        receipt['counters'] = fields
        receipt['boundary_ambiguity'] = ['poll exit preceded attachment; duration and result not classified'] if fields['initial_poll'] else []
        receipt['end_reason'] = 'target_exit' if fields['target_exit'] else 'bounded_stop'
        # A full requested window also requires the selected thread to survive.
        if receipt['end_reason'] == 'bounded_stop' and proc_identity(args.pid, args.tid) != identity:
            raise ValueError('target identity changed at completion')
        receipt.setdefault('observed_window_s', time.monotonic() - window_start)
        receipt['verdict'] = 'observed'
    except Exception as error:
        receipt['missing_coverage'].append(str(error))
    finally:
        finalize_observation(output, receipt, tracer, pidfd, started)
    return 0 if receipt['verdict'] == 'observed' else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid', type=int, required=True)
    parser.add_argument('--tid', type=int, required=True)
    parser.add_argument('--expected-exe-sha256', required=True)
    parser.add_argument('--kernel-hz', type=int, required=True)
    parser.add_argument('--duration', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        return observe(args)
    except (ValueError, OSError) as error:
        parser.exit(2, str(error) + '\n')


if __name__ == '__main__':
    sys.exit(main())
