"""Explicit privileged Linux diagnostics; silent owned child processes only.

Run: sudo python3 -B tests/speaker_runnable_trace_integration.py --kernel-hz 1000 -v
CONFIG_HZ must come from the running kernel configuration, never SC_CLK_TCK.
Individual unittest method selectors are supported. No audio service is selected.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import select
import signal
import subprocess
import sys
import time
import unittest
from unittest import mock
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
KERNEL_HZ = None


import importlib.util
_SPEC = importlib.util.spec_from_file_location('observe_speaker_runnable', ROOT / 'scripts/observe_speaker_runnable.py')
_OBSERVER = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_OBSERVER)
proc_identity = _OBSERVER.proc_identity
parse_output = _OBSERVER.parse_output


class RunnableEvidenceParserTests(unittest.TestCase):
    def test_rejects_observation_gaps_and_mismatched_frames(self):
        good = ("Attaching 13 probes...\n"
                "runnable-initialized pid=71 tid=71\n"
                "runnable-stack mono_ns=10 pid=71 tid=71 rt_timeout_ticks=20\n"
                "    abc finite_cpu_work+1\n"
                "runnable-stack-end mono_ns=10 pid=71 tid=71\n"
                "runnable-end pid=71 tid=71 target_exit=1 deadline=0 identity_error=0 running_ns=1 sleep_out=0 runnable_out=0 wakeups=1 poll_enter=0 poll_ready=0 poll_zero=0 poll_error=0 poll_ns=0 poll_max_ns=0 unpaired_poll=0 initial_poll=0 samples=1 max_ticks=20 stacks=1\n")
        self.assertEqual(parse_output(good, '', 0, 71)['stacks'], 1)
        boundary = good.replace('initial_poll=0', 'initial_poll=1')
        self.assertEqual(parse_output(boundary, '', 0, 71)['initial_poll'], 1)
        thread = good.replace('tid=71', 'tid=72')
        self.assertEqual(parse_output(thread, '', 0, 71, 72)['tid'], 72)
        deadline = thread.replace('target_exit=1 deadline=0', 'target_exit=0 deadline=1')
        self.assertEqual(parse_output(deadline, '', 0, 71, 72, expected_end='deadline')['deadline'], 1)
        stopped = thread.replace('target_exit=1 deadline=0', 'target_exit=0 deadline=0')
        self.assertEqual(parse_output(stopped, '', 0, 71, 72, expected_end='bounded_stop')['target_exit'], 0)
        with self.assertRaises(ValueError):
            parse_output(stopped, '', 0, 71, 72)
        with self.assertRaises(ValueError):
            parse_output(thread, '', 0, 71, 73)
        with self.assertRaises(ValueError):
            proc_identity(0, 0)
        for bad, stderr, rc in (
            (good, 'Lost 1 events', 0), (good + 'Lost 1 events\n', '', 0),
            (good, '', 1), (good.replace('mono_ns=10 pid=71 tid=71 rt_timeout_ticks', 'pid=71 tid=71 rt_timeout_ticks'), '', 0),
            (good.replace('stacks=1', 'stacks=1 stacks=1'), '', 0),
            (good.replace(' running_ns=1', ''), '', 0), (good.replace('Attaching 13 probes...\n', ''), '', 0),
            (good.replace('target_exit=1', 'target_exit=0'), '', 0),
            (good.replace('deadline=0', 'deadline=1'), '', 0),
            (good.replace('identity_error=0', 'identity_error=1'), '', 0),
            (good.replace('runnable-stack-end mono_ns=10', 'runnable-stack-end mono_ns=11'), '', 0),
            (good.replace('    abc finite_cpu_work+1\n', ''), '', 0),
            (good[:good.index('runnable-stack-end')], '', 0),
            (good + good[good.index('runnable-end'):], '', 0)):
            with self.subTest(stderr=stderr, rc=rc, text=bad):
                with self.assertRaises(ValueError):
                    parse_output(bad, stderr, rc, 71)

    def test_cleanup_failure_retains_private_receipt(self):
        for mode in ('missing', 'timeout', 'signal-error', 'pidfd-error', 'hash-error'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory(prefix='rog-runnable-cleanup-') as name:
                directory = Path(name)
                (directory / 'stdout.log').write_text('retained private evidence')
                receipt = {'verdict': 'observed', 'missing_coverage': []}
                tracer = mock.Mock(pid=800001, returncode=0)
                tracer.poll.return_value = None
                tracer.wait.return_value = 0
                if mode == 'timeout':
                    tracer.returncode = None
                    tracer.wait.side_effect = subprocess.TimeoutExpired('owned-tracer', 2)
                kill_error = ProcessLookupError('already exited') if mode == 'missing' else (
                    PermissionError('owned cleanup denied') if mode == 'signal-error' else None)
                close_error = OSError('pidfd close failed') if mode == 'pidfd-error' else None
                with mock.patch.object(_OBSERVER.os, 'killpg', side_effect=kill_error) as kill, \
                     mock.patch.object(_OBSERVER.os, 'close', side_effect=close_error) as close:
                    if mode == 'hash-error':
                        with mock.patch.object(_OBSERVER.hashlib, 'sha256', side_effect=OSError('read/hash failed')):
                            _OBSERVER.finalize_observation(directory, receipt, tracer, 900001, time.monotonic())
                    else:
                        _OBSERVER.finalize_observation(directory, receipt, tracer, 900001, time.monotonic())
                saved = json.loads((directory / 'receipt.json').read_text())
                self.assertIn('finished_unix_ns', saved)
                self.assertIn('elapsed_s', saved)
                close.assert_called_once_with(900001)
                self.assertTrue(all(call.args[0] == tracer.pid for call in kill.call_args_list))
                if mode == 'missing':
                    self.assertEqual(saved['verdict'], 'observed')
                    self.assertTrue(saved['cleanup_races'])
                    self.assertFalse(saved['missing_coverage'])
                else:
                    self.assertEqual(saved['verdict'], 'inconclusive')
                    self.assertTrue(saved['missing_coverage'])
                if mode == 'timeout':
                    self.assertEqual(kill.call_count, 2)
                    self.assertEqual(tracer.wait.call_count, 2)


class RunnableTraceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if sys.platform != 'linux' or os.geteuid() != 0:
            raise RuntimeError('explicit Linux root invocation required')
        if KERNEL_HZ not in (100, 250, 300, 1000):
            raise RuntimeError('supply exact running CONFIG_HZ with --kernel-hz')
        cls.receipts = Path.home() / '.local/state/rog-audio/runnable-tests' / uuid.uuid4().hex
        cls.receipts.mkdir(parents=True, mode=0o700)
        cls.binary = cls.receipts / 'fixture'
        result = subprocess.run(['cc', '-pthread', '-O2', '-g', '-fno-omit-frame-pointer', '-Wall', '-Wextra', '-Werror',
            str(ROOT / 'tests/speaker_runnable_fixture.c'), '-o', str(cls.binary)],
            capture_output=True, text=True, timeout=30)
        (cls.receipts / 'compile.json').write_text(json.dumps({'returncode': result.returncode,
            'stdout': result.stdout, 'stderr': result.stderr, 'kernel_hz': KERNEL_HZ,
            'user_hz': os.sysconf('SC_CLK_TCK'), 'kernel': os.uname().release}, indent=2))
        if result.returncode:
            raise RuntimeError('fixture compile failed: ' + result.stderr)

    def run_case(self, mode):
        case = self.receipts / mode
        case.mkdir(mode=0o700)
        child = tracer = None
        pidfd = None
        with (case / 'trace.log').open('w+') as log, (case / 'trace.stderr').open('w+') as err, \
             (case / 'fixture.stderr').open('w+') as fixture_err:
            try:
                child = subprocess.Popen([str(self.binary), mode], stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE, stderr=fixture_err, start_new_session=True)
                pidfd = os.pidfd_open(child.pid)
                # Only this owned process can announce its target; read is bounded.
                self.assertTrue(select.select([child.stdout], [], [], 2)[0], 'fixture announcement timeout')
                announcement = os.read(child.stdout.fileno(), 32)
                self.assertRegex(announcement, rb'^[1-9][0-9]*\n$')
                target_tid = int(announcement)
                if mode == 'ready':
                    self.assertNotEqual(target_tid, child.pid, 'ready fixture must target a real worker')
                else:
                    self.assertEqual(target_tid, child.pid)
                identity = proc_identity(child.pid, target_tid)
                self.assertEqual(identity['exe'], str(self.binary))
                self.assertEqual(identity['comm'], 'rog-rt-fixture')
                (case / 'identity.json').write_text(json.dumps(identity, indent=2))
                warning_ticks = math.ceil(KERNEL_HZ * .020)
                tracer = subprocess.Popen(['bpftrace', '-B', 'line',
                    str(ROOT / 'scripts/trace_speaker_runnable.bt'), str(child.pid), str(target_tid),
                    str(warning_ticks), '10', str(identity['start_ticks']), str(os.sysconf('SC_CLK_TCK'))],
                    stdout=log, stderr=err, start_new_session=True)
                until = time.monotonic() + 15
                while True:
                    output = (case / 'trace.log').read_text()
                    # bpftrace0.25 emits this normal output AFTER attaching probes.
                    # BEGIN alone runs before attachment and is insufficient.
                    if re.search(r'^Attaching [1-9][0-9]* probes?\.\.\.$', output, re.M) and 'runnable-initialized ' in output:
                        break
                    if tracer.poll() is not None or child.poll() is not None or time.monotonic() >= until:
                        self.fail('observer not attached: ' + output + (case / 'trace.stderr').read_text())
                    time.sleep(.02)
                self.assertFalse(select.select([pidfd], [], [], 0)[0], 'fixture exited during attachment')
                self.assertEqual(proc_identity(child.pid, target_tid), identity, 'fixture identity changed')
                self.assertFalse((case / 'trace.stderr').read_text().strip(), 'attachment diagnostics')
                child.stdin.write(b'G'); child.stdin.flush(); child.stdin.close()
                self.assertEqual(child.wait(timeout=5), 0, 'fixture did not finish cleanly')
                self.assertEqual(tracer.wait(timeout=5), 0, 'observer did not stop on target exit')
                output = (case / 'trace.log').read_text()
                fields = parse_output(output, (case / 'trace.stderr').read_text(), tracer.returncode, child.pid, target_tid)
                self.assertFalse((case / 'fixture.stderr').read_text().strip(), 'fixture not silent')
                self.assertGreater(fields['running_ns'], 0)
                self.assertGreater(fields['wakeups'], 0)
                self.assertEqual(fields['poll_error'], 0)
                self.assertEqual(fields['unpaired_poll'], 0)
                self.assertEqual(fields['initial_poll'], 0)
                if mode == 'blocking':
                    self.assertGreaterEqual(fields['sleep_out'], 5)
                    self.assertGreaterEqual(fields['poll_ready'], 5)
                    self.assertGreater(fields['poll_max_ns'], 1000000)
                    self.assertLess(fields['max_ticks'], warning_ticks)
                    self.assertEqual(fields['stacks'], 0)
                else:
                    self.assertGreaterEqual(fields['max_ticks'], warning_ticks)
                    self.assertGreater(fields['samples'], 0)
                    self.assertGreater(fields['stacks'], 0)
                    if mode == 'ready':
                        self.assertGreater(fields['poll_ready'], 50)
                    else:
                        self.assertEqual(fields['poll_enter'], 0)
                (case / 'result.json').write_text(json.dumps(fields, indent=2))
            finally:
                # Only owned Popen handles are signalled, never external selectors.
                for process in (child, tracer):
                    if process is not None and process.poll() is None:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait(timeout=3)
                if child is not None and child.stdin and not child.stdin.closed:
                    child.stdin.close()
                if child is not None and child.stdout:
                    child.stdout.close()
                if pidfd is not None:
                    os.close(pidfd)

    def test_blocking_poll_resets_budget(self):
        self.run_case('blocking')

    def test_ready_poll_accumulates_budget(self):
        self.run_case('ready')

    def test_finite_cpu_work_has_no_poll_flood(self):
        self.run_case('busy')


if __name__ == '__main__':
    if '--kernel-hz' in sys.argv:
        index = sys.argv.index('--kernel-hz')
        KERNEL_HZ = int(sys.argv[index + 1])
        del sys.argv[index:index + 2]
    unittest.main()
