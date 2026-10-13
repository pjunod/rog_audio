"""Owned Linux IPC exit contracts; no audio, laptop services or signals from helper."""
import contextlib
import io
import os
import select
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import stop_speaker_effects as stop

SERVER = """import socket,sys,time
from pathlib import Path
s=socket.socket(socket.AF_UNIX);s.bind(sys.argv[1]);s.listen(1)
print('ready',flush=True)
c,_=s.accept();data=b''
while not data.endswith(b'\\n'):
 chunk=c.recv(128)
 if not chunk:break
 data+=chunk
c.close();s.close()
if data==b'quit_app\\n':
 time.sleep(float(sys.argv[3]));Path(sys.argv[2]).write_text('saved-before-exit')
"""

@unittest.skipUnless(sys.platform=='linux' and hasattr(os,'pidfd_open'),'Linux pidfd/peer contracts')
class StopTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.socket=self.root/'ipc';self.saved=self.root/'saved'

    def child(self, delay=.05):
        p=subprocess.Popen([sys.executable,'-c',SERVER,str(self.socket),str(self.saved),str(delay)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        self.addCleanup(self.close,p)
        self.assertTrue(select.select([p.stdout],[],[],5)[0],'owned IPC fixture startup timed out')
        self.assertEqual(p.stdout.readline().strip(),'ready')
        return p

    @staticmethod
    def close(p):
        if p.poll() is None:p.kill()
        p.wait(timeout=5)
        if p.stdout:p.stdout.close()
        if p.stderr:p.stderr.close()

    def test_authenticated_quit_waits_for_saved_state_and_actual_exit(self):
        p=self.child()
        self.assertEqual(stop.stop_process(p.pid,self.socket,timeout=2,binary=sys.executable),'exited')
        self.assertEqual(p.wait(timeout=1),0)
        self.assertEqual(self.saved.read_text(),'saved-before-exit')

    def test_timeout_preserves_process_for_systemd_final_kill(self):
        p=self.child(delay=2)
        with self.assertRaisesRegex(stop.StopError,'timed out'):
            stop.stop_process(p.pid,self.socket,timeout=.1,binary=sys.executable)
        self.assertIsNone(p.poll())
        self.assertFalse(self.saved.exists())

    def test_foreign_socket_peer_never_receives_quit(self):
        server=self.child()
        target=subprocess.Popen([sys.executable,'-c','import time;time.sleep(5)'])
        self.addCleanup(self.close,target)
        with self.assertRaisesRegex(stop.StopError,'socket peer'):
            stop.stop_process(target.pid,self.socket,timeout=1,binary=sys.executable)
        self.assertEqual(server.wait(timeout=2),0)
        self.assertFalse(self.saved.exists())
        self.assertIsNone(target.poll())

    def test_foreign_executable_is_refused_before_socket_connect(self):
        p=self.child()
        with self.assertRaisesRegex(stop.StopError,'executable'):
            stop.stop_process(p.pid,self.socket,timeout=1,binary='/not/the/candidate')
        self.assertIsNone(p.poll())
        self.assertFalse(self.saved.exists())

    def test_exited_pid_is_noop_without_socket(self):
        p=subprocess.Popen([sys.executable,'-c','pass']);p.wait(timeout=5)
        self.assertEqual(stop.stop_process(p.pid,self.root/'absent',binary=sys.executable),'already-exited')

    def test_dead_pinned_handle_never_contacts_replacement(self):
        read,write=os.pipe();os.write(write,b'exited');os.close(write)
        with mock.patch.object(stop.os,'pidfd_open',return_value=read),mock.patch.object(stop,'identity') as identity,mock.patch.object(stop.socket,'socket') as client:
            self.assertEqual(stop.stop_process(os.getpid(),self.socket),'already-exited')
            identity.assert_not_called();client.assert_not_called()

class UnitTests(unittest.TestCase):
    def test_unset_mainpid_is_noop_without_command_or_socket(self):
        with mock.patch.dict(os.environ,{'MAINPID':''}),mock.patch.object(stop.socket,'socket') as client,contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(stop.main(['--socket','/absent']),0)
            client.assert_not_called()

    def test_unit_awaits_helper_and_retains_final_kill_deadline(self):
        root=Path(__file__).resolve().parents[1]
        text=(root/'systemd/rog-audio-speaker.service').read_text()
        self.assertIn('ExecStop=/usr/lib/rog-audio/stop-speaker-effects --socket %t/RogAudioSpeakerEffectsServer',text)
        self.assertIn('TimeoutStopSec=15',text)
        self.assertNotIn('SendSIGKILL=no',text)
        self.assertNotIn('KillMode=none',text)
        self.assertNotIn(' --quit',text)
