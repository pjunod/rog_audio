"""Explicit privileged Linux integration; owned silent child processes only.

Run directly as root on a host with bpftrace 0.25 and matching kernel BTF.
Never selects or sends a signal to the real speaker process.
"""
import ctypes
import os
from pathlib import Path
import resource
import re
import select
import signal
import subprocess
import sys
import uuid
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
NAME = 'rog-sig-fixture'


def fixture(mode):
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(15, NAME.encode(), 0, 0, 0):
        raise OSError(ctypes.get_errno(), 'set fixture name')
    resource.setrlimit(resource.RLIMIT_CPU, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
    resource.setrlimit(resource.RLIMIT_RTTIME, (resource.RLIM_INFINITY, resource.RLIM_INFINITY))
    if mode == 'main-finite':
        resource.setrlimit(resource.RLIMIT_RTTIME, (123456, 234567))
    if mode == 'rt':
        resource.setrlimit(resource.RLIMIT_RTTIME, (20000, 20000))
        class Param(ctypes.Structure):
            _fields_ = [('priority', ctypes.c_int)]
        if libc.sched_setscheduler(0, 1, ctypes.byref(Param(1))):
            raise OSError(ctypes.get_errno(), 'set fixture scheduler')
        while True:
            pass
    else:
        if mode == 'thread':
            import threading
            def worker():
                libc.prctl(15, b'rog-sig-worker', 0, 0, 0)
                print(threading.get_native_id(), flush=True)
                while True:
                    time.sleep(1)
            threading.Thread(target=worker).start()
        else:
            print(os.getpid(), flush=True)
        while True:
            time.sleep(1)


class SignalTraceTests(unittest.TestCase):
    def setUp(self):
        self.assertEqual(sys.platform, 'linux')
        self.assertEqual(os.geteuid(), 0, 'explicit root invocation required')
        self.root = Path.home() / '.local/state/rog-audio/signal-tests' / uuid.uuid4().hex
        self.root.mkdir(parents=True, mode=0o700)
        self.children = []
        self.log = (self.root / 'signals.log').open('w+')
        self.addCleanup(self.cleanup)
        self.tracer = subprocess.Popen(['bpftrace', '-q', '-B', 'line',
            str(ROOT / 'scripts/trace_speaker_signals.bt'), str(os.getuid()), NAME],
            stdout=self.log, stderr=self.log, start_new_session=True)
        self.wait_text('speaker-signal-trace-ready', 15)

    def output(self):
        return (self.root / 'signals.log').read_text()

    def wait_text(self, text, seconds=5):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if text in self.output():
                return
            if self.tracer.poll() is not None:
                self.fail('tracer exited: ' + self.output())
            time.sleep(.02)
        self.fail('missing ' + text + ': ' + self.output())

    def start(self, mode):
        child = subprocess.Popen([sys.executable, '-B', str(Path(__file__).resolve()),
            '--fixture', mode], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, start_new_session=True)
        self.children.append(child)
        return child

    def ready(self, child):
        self.assertTrue(select.select([child.stdout], [], [], 5)[0], 'fixture not ready')
        line = child.stdout.readline().strip()
        self.assertTrue(line.isdigit(), 'fixture failed: ' + line)
        return int(line)

    def parse_event(self, output, pid):
        headers = [match for match in re.finditer(r'^signal .*$', output, re.M)
                   if f'target_pid={pid} ' in match.group()]
        self.assertEqual(len(headers), 1, 'missing/duplicate event header')
        start = headers[0].start()
        line = headers[0].group()
        identity = dict(re.findall(r'(\w+)=([^\s]+)', line))
        marker = (f"signal_end mono_ns={identity['mono_ns']} "
                  f"target_pid={pid} target_tid={identity['target_tid']}")
        ends = list(re.finditer(r'^signal_end .*$', output[start:], re.M))
        self.assertTrue(ends, 'incomplete event')
        self.assertEqual(ends[0].group(), marker, 'mismatched event end')
        self.assertEqual(sum(match.group() == marker for match in ends), 1,
                         'duplicate event end')
        record = output[start:start + ends[0].end()] + '\n'
        self.assertEqual(len(re.findall(r'^signal ', record, re.M)), 1,
                         'nested/interleaved event')
        targets = re.findall(r'^target .*$', record, re.M)
        self.assertEqual(len(targets), 1, 'missing/duplicate target fields')
        fields = dict(re.findall(r'(\w+)=([^\s]+)', targets[0]))
        self.assertEqual(fields['leader_comm'], NAME)
        self.assertEqual(fields['cpu_soft_s'], str(2**64 - 1))
        self.assertEqual(fields['cpu_hard_s'], str(2**64 - 1))
        return line, fields, record

    def event(self, child):
        self.wait_text(f'target_pid={child.pid} ')
        header = next(line for line in self.output().splitlines()
                      if line.startswith('signal ') and f'target_pid={child.pid} ' in line)
        identity = dict(re.findall(r'(\w+)=([^\s]+)', header))
        self.wait_text(f"signal_end mono_ns={identity['mono_ns']} "
                       f"target_pid={child.pid} target_tid={identity['target_tid']}")
        return self.parse_event(self.output(), child.pid)

    def assert_normal_target(self, fields, record, limits=None):
        self.assertEqual(fields['policy'], '0')
        self.assertEqual(fields['rt_priority'], '0')
        self.assertEqual(fields['rt_timeout_ticks'], '0')
        limits = limits or (2**64 - 1, 2**64 - 1)
        self.assertEqual(fields['rttime_soft_us'], str(limits[0]))
        self.assertEqual(fields['rttime_hard_us'], str(limits[1]))
        self.assertIn('target_ustack=unavailable_context_mismatch', record)
        self.assertNotIn('target_ustack=best_effort_current', record)

    def test_userspace_kill_sender_is_identified(self):
        child = self.start('main'); self.ready(child)
        other = self.start('main-finite'); self.ready(other)
        os.kill(child.pid, signal.SIGKILL)
        os.kill(other.pid, signal.SIGKILL)
        child.wait(timeout=3); other.wait(timeout=3)
        records = []
        for target, limits in ((child, None), (other, (123456, 234567))):
            line, fields, record = self.event(target)
            records.append(record)
            self.assertIn(f'context_pid={os.getpid()} ', line)
            self.assertIn('sig=9 code=0 ', line)
            self.assertIn(f'target_tid={target.pid} ', line)
            self.assert_normal_target(fields, record, limits)
            self.assertEqual(target.returncode, -signal.SIGKILL)
        # Exercise framing rejection inside this existing method, without
        # additional probes or children: partial, duplicate and mixed records.
        record = records[0]
        end = record[record.index('signal_end '):]
        for malformed in (record[:record.index('signal_end ')],
                          record + end, record + record,
                          record.replace(end, records[1][records[1].index('signal_end '):])):
            with self.assertRaises(AssertionError):
                self.parse_event(malformed, child.pid)

    def test_thread_target_resolves_group_leader(self):
        child = self.start('thread'); thread = self.ready(child)
        libc = ctypes.CDLL(None, use_errno=True)
        # tgkill's stable x86-64 syscall number is obtained from the running ABI.
        self.assertEqual(os.uname().machine, 'x86_64')
        self.assertEqual(libc.syscall(234, child.pid, thread, signal.SIGKILL), 0)
        child.wait(timeout=3)
        line, fields, record = self.event(child)
        self.assertIn(f'target_tid={thread} ', line)
        self.assertIn('sig=9 code=-6 ', line)
        self.assertIn(f'context_pid={os.getpid()} ', line)
        self.assert_normal_target(fields, record)

    def test_kernel_realtime_limit_is_distinguished(self):
        child = self.start('rt')
        child.wait(timeout=3)  # Cleanup also bounds a misbehaving fixture.
        line, fields, record = self.event(child)
        self.assertEqual(child.returncode, -signal.SIGKILL)
        self.assertIn('sig=9 code=128 ', line)
        self.assertIn(f'context_tid={child.pid} ', line)
        self.assertIn(f'target_tid={child.pid} ', line)
        self.assertEqual(fields['policy'], '1')
        self.assertEqual(fields['rt_priority'], '1')
        self.assertGreater(int(fields['rt_timeout_ticks']), 0)
        self.assertEqual(fields['rttime_soft_us'], '20000')
        self.assertEqual(fields['rttime_hard_us'], '20000')
        self.assertTrue(any(name in record for name in (
            'check_thread_timers', 'run_posix_cpu_timers', 'posix_cpu_timers_work', 'check_rlimit')),
            'missing CPU-limit kernel stack: ' + record)
        self.assertNotIn('target_ustack=unavailable_context_mismatch', record)
        stack = record.split('target_ustack=best_effort_current\n', 1)[1]
        # At least one frame is required on this supported fixture/kernel pair;
        # symbol names and unwind depth remain best effort, especially after exit.
        self.assertRegex(stack, r'(?m)^\s+(?:0x)?[0-9a-fA-F]+\s+\S+')

    def cleanup(self):
        for child in self.children:
            if child.poll() is None:
                child.kill(); child.wait(timeout=3)
            child.stdout.close(); child.stderr.close()
        if getattr(self, 'tracer', None) and self.tracer.poll() is None:
            os.killpg(self.tracer.pid, signal.SIGINT)
            try:
                self.tracer.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(self.tracer.pid, signal.SIGKILL)
                self.tracer.wait(timeout=3)
        self.log.close()
        # Receipts are retained in the exclusively created private test directory.


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--fixture':
        fixture(sys.argv[2])
    else:
        unittest.main()
