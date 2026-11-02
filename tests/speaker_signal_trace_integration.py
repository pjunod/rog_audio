"""Explicit privileged Linux integration; owned silent child processes only.

Run directly as root on a host with bpftrace 0.25 and matching kernel BTF.
Never selects or sends a signal to the real speaker process.
"""
import ctypes
import os
from pathlib import Path
import resource
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

    def event(self, child):
        self.wait_text(f'target_pid={child.pid} ')
        return next(line for line in self.output().splitlines()
                    if line.startswith('signal ') and f'target_pid={child.pid} ' in line)

    def test_userspace_kill_sender_is_identified(self):
        child = self.start('main'); self.ready(child)
        os.kill(child.pid, signal.SIGKILL); child.wait(timeout=3)
        line = self.event(child)
        self.assertIn(f'context_pid={os.getpid()} ', line)
        self.assertIn('sig=9 code=0 ', line)
        self.assertEqual(child.returncode, -signal.SIGKILL)

    def test_thread_target_resolves_group_leader(self):
        child = self.start('thread'); thread = self.ready(child)
        libc = ctypes.CDLL(None, use_errno=True)
        # tgkill's stable x86-64 syscall number is obtained from the running ABI.
        self.assertEqual(os.uname().machine, 'x86_64')
        self.assertEqual(libc.syscall(234, child.pid, thread, signal.SIGKILL), 0)
        child.wait(timeout=3)
        line = self.event(child)
        self.assertIn(f'target_tid={thread} ', line)
        self.assertIn('sig=9 code=-6 ', line)

    def test_kernel_realtime_limit_is_distinguished(self):
        child = self.start('rt')
        child.wait(timeout=3)  # Cleanup also bounds a misbehaving fixture.
        line = self.event(child)
        self.assertEqual(child.returncode, -signal.SIGKILL)
        self.assertIn('sig=9 code=128 ', line)
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            if any(name in self.output() for name in ('check_thread_timers', 'run_posix_cpu_timers', 'posix_cpu_timers_work', 'check_rlimit')):
                break
            time.sleep(.02)
        else:
            self.fail('missing CPU-limit kernel stack: ' + self.output())

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
