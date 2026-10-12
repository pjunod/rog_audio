"""Mocked interruption regressions; no Docker, SSH or audio process runs."""
import contextlib
import io
import json
from pathlib import Path
import signal
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import validate_audio_linux as validator

COMMAND=['docker','run','--name','audio-latency-test-owned']
CLEANUP=['docker','rm','-f','audio-latency-test-owned']


def success(code=0):
    return SimpleNamespace(returncode=code,stdout=b'',stderr=b'')


class CleanupTests(unittest.TestCase):
    def test_cleanup_on_success_failure_ssh_disconnect_and_timeout(self):
        scenarios=[success(),success(1),success(255),
                   validator.subprocess.TimeoutExpired(COMMAND,600),OSError('private')]
        for scenario in scenarios:
            with self.subTest(scenario=type(scenario).__name__):
                run=mock.Mock(side_effect=[scenario,success()])
                command=['ssh','lab-alias','docker run'] if getattr(scenario,'returncode',None)==255 else COMMAND
                result,_=validator.run_validation(command,CLEANUP,b'archive',runner=run)
                self.assertEqual(run.call_args_list[1].args[0],CLEANUP)
                self.assertEqual(result['cleanup']['returncode'],0)
                if getattr(scenario,'returncode',None)==255:
                    self.assertEqual(result['status'],'ssh-disconnected')
                if isinstance(scenario,validator.subprocess.TimeoutExpired):
                    self.assertEqual(result['status'],'timeout')

    def test_keyboard_and_sigterm_interrupt_cleanup_and_restore_handlers(self):
        before={s:signal.getsignal(s) for s in (signal.SIGINT,signal.SIGTERM)}
        for interruption in (KeyboardInterrupt(),validator.ValidationInterrupted(signal.SIGTERM)):
            with self.subTest(kind=type(interruption).__name__):
                run=mock.Mock(side_effect=[interruption,success()])
                with validator.signal_handlers(validator.handle_interrupt):
                    result,code=validator.run_validation(COMMAND,CLEANUP,b'',runner=run)
                self.assertEqual(result['status'],'interrupted')
                self.assertEqual(code,143 if isinstance(interruption,validator.ValidationInterrupted) else 130)
                self.assertEqual(run.call_args_list[1].args[0],CLEANUP)
                self.assertEqual({s:signal.getsignal(s) for s in before},before)

    def test_sigterm_handler_during_run_is_handled_and_cleanup_failure_recorded(self):
        def terminate(_command,**_kwargs):
            signal.getsignal(signal.SIGTERM)(signal.SIGTERM,None)
        # Invoke the installed handler while the mocked command is running.
        calls=[]
        def dispatch(command,**kwargs):
            calls.append(command)
            if command==COMMAND:return terminate(command,**kwargs)
            raise validator.subprocess.TimeoutExpired(CLEANUP,30)
        with validator.signal_handlers(validator.handle_interrupt):
            result,code=validator.run_validation(COMMAND,CLEANUP,b'',runner=dispatch)
        self.assertEqual(calls,[COMMAND,CLEANUP])
        self.assertEqual(code,143)
        self.assertEqual(result['cleanup']['status'],'unavailable')

    def test_cli_interrupt_writes_private_receipt_and_closes_reserved_descriptor(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'receipt.json'
            calls=[]
            streams=[]
            real_fdopen=validator.os.fdopen
            def fdopen(*args,**kwargs):
                stream=real_fdopen(*args,**kwargs);streams.append(stream);return stream
            def dispatch(command,**kwargs):
                calls.append(command)
                if command[:2]==['docker','run']:raise KeyboardInterrupt()
                return success()
            with mock.patch.object(sys,'argv',['validate_audio_linux.py','--stage','unit-validator','--output',str(output)]), \
                 mock.patch.object(validator,'archive',return_value=b'archive'), \
                 mock.patch.object(validator.os,'fdopen',side_effect=fdopen), \
                 mock.patch.object(validator.subprocess,'run',side_effect=dispatch), \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(validator.main(),130)
            receipt=json.loads(output.read_text())
            self.assertEqual(receipt['result']['status'],'interrupted')
            self.assertEqual(receipt['result']['cleanup']['returncode'],0)
            self.assertEqual(calls[1],['docker','rm','-f',receipt['container']])
            self.assertEqual(output.stat().st_mode&0o777,0o600)
            self.assertEqual(len(streams),1)
            self.assertTrue(streams[0].closed)

if __name__=='__main__':unittest.main()
