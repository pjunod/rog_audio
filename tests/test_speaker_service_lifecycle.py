"""Real, task-owned systemd user transactions; no sound devices or stock unit changes."""
import json
import os
from pathlib import Path
import select
import signal
import socket
import subprocess
import sys
import time
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[1]


def event(work, name):
    record = json.dumps({'event': name, 'pid': os.getpid(), 'time_ns': time.monotonic_ns()}) + '\n'
    fd = os.open(work / 'events.jsonl', os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
    with os.fdopen(fd, 'w') as stream:
        stream.write(record)
        stream.flush()


def parent(work):
    if (work / 'fail-parent').exists():
        event(work, 'parent-refused')
        return 1
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    endpoint = work / 'upstream.sock'
    endpoint.unlink(missing_ok=True)
    listener.bind(str(endpoint))
    listener.listen()
    running = True
    peers = []
    def stop(*_):
        nonlocal running
        running = False
    signal.signal(signal.SIGTERM, stop)
    event(work, 'parent-start')
    notify = os.environ.get('NOTIFY_SOCKET')
    if notify:
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as client:
            client.connect('\0' + notify[1:] if notify.startswith('@') else notify)
            client.sendall(b'READY=1')
    try:
        while running:
            if select.select([listener], [], [], .02)[0]:
                peer, _ = listener.accept()
                peers.append(peer)
    finally:
        event(work, 'parent-stop')
        for peer in peers:
            peer.close()
        listener.close()
        endpoint.unlink(missing_ok=True)
    return 0


def child(work):
    upstream = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    upstream.connect(str(work / 'upstream.sock'))
    endpoint = work / 'control.sock'
    endpoint.unlink(missing_ok=True)
    control = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    control.bind(str(endpoint))
    control.listen()
    event(work, 'child-start')
    try:
        while True:
            ready, _, _ = select.select([upstream, control], [], [], 3)
            if upstream in ready and not upstream.recv(1):
                event(work, 'child-lost-server')
                return 42  # Model the observed fatal disconnect, without creating a core.
            if control in ready:
                peer, _ = control.accept()
                with peer:
                    peer.settimeout(2)
                    command = b''
                    while not command.endswith(b'\n') and len(command) < 128:
                        part = peer.recv(128)
                        if not part:
                            break
                        command += part
                    if command == b'quit_app\n':
                        event(work, 'child-saved')
                        return 0
    finally:
        upstream.close()
        control.close()
        endpoint.unlink(missing_ok=True)


def stop_child(work):
    sys.path.insert(0, str(ROOT / 'scripts'))
    import stop_speaker_effects
    stop_speaker_effects.stop_process(int(os.environ['MAINPID']), work / 'control.sock',
                                     timeout=3, binary=sys.executable)
    return 0


def quote(value):
    return '"' + str(value).replace('\\', '\\\\').replace('"', '\\"').replace('%', '%%') + '"'


@unittest.skipUnless(sys.platform == 'linux', 'requires Linux systemd user manager')
class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.prefix = 'rog-speaker-lifecycle-' + uuid.uuid4().hex[:12]
        self.work = Path.home() / '.local/state/rog-audio/service-tests' / self.prefix
        self.work.mkdir(parents=True, mode=0o700)
        self.config = Path(os.environ.get('XDG_CONFIG_HOME', str(Path.home() / '.config'))) / 'systemd/user'
        self.config.mkdir(parents=True, exist_ok=True)
        self.audio = self.prefix + '-audio.service'
        self.session = self.prefix + '-session.service'
        self.effects = self.prefix + '-effects.service'
        self.target = self.prefix + '.target'
        self.units = [self.effects, self.audio, self.session, self.target]
        self.created = []
        self.addCleanup(self.cleanup)
        self.ctl('show', 'default.target', '-p', 'ActiveState')
        script = quote(Path(__file__).resolve())
        py = quote(sys.executable)
        work = quote(self.work)
        template = (ROOT / 'systemd/rog-audio-speaker.service').read_text()
        self.template = template
        template = template.replace('pipewire.service', self.audio).replace('wireplumber.service', self.session).replace('default.target', self.target)
        lines = []
        for line in template.splitlines():
            if line.startswith('ExecStart='):
                line = f'ExecStart={py} {script} child {work}'
            elif line.startswith('ExecStop='):
                line = f'ExecStop={py} {script} stop {work}'
            lines.append(line)
        files = {
            self.audio: f'[Unit]\nDescription=Owned speaker lifecycle audio fixture\n[Service]\nType=notify\nExecStart={py} {script} parent {work}\nTimeoutStartSec=5\nTimeoutStopSec=5\n',
            self.session: '[Service]\nType=oneshot\nExecStart=/usr/bin/true\nRemainAfterExit=yes\n',
            self.target: '[Unit]\nDescription=Owned speaker lifecycle login target\n',
            self.effects: '\n'.join(lines) + '\n',
        }
        for name, text in files.items():
            p = self.config / name
            with p.open('x') as stream:
                stream.write(text)
            self.created.append(p)
        self.ctl('daemon-reload')
        self.ctl('enable', self.effects)

    def ctl(self, *args, check=True):
        result = subprocess.run(['systemctl', '--user', *args], capture_output=True, text=True, timeout=12)
        if check and result.returncode:
            self.fail(f'systemctl {args!r}: {result.returncode}: {result.stderr}')
        return result

    def records(self):
        path = self.work / 'events.jsonl'
        return [json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []

    def wait_event_count(self, name, count):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            rows = [x for x in self.records() if x['event'] == name]
            if len(rows) >= count:
                return rows
            time.sleep(.02)
        self.fail(f'missing {count} events {name!r}: {self.records()}')

    def props(self, unit):
        result = self.ctl('show', unit, '-p', 'ActiveState', '-p', 'InvocationID', '-p', 'NRestarts', '-p', 'Result')
        return dict(x.split('=', 1) for x in result.stdout.splitlines())

    def assert_clean_order(self):
        rows = self.records()
        saved = [x for x in rows if x['event'] == 'child-saved']
        stopped = [x for x in rows if x['event'] == 'parent-stop']
        self.assertTrue(saved, rows)
        self.assertTrue(stopped, rows)
        self.assertLess(saved[-1]['time_ns'], stopped[-1]['time_ns'], rows)
        self.assertNotIn('child-lost-server', [x['event'] for x in rows])

    def test_pipewire_stop_saves_before_server_exit_and_return_autostarts(self):
        self.ctl('start', self.audio)
        self.wait_event_count('child-start', 1)
        first = self.props(self.effects)['InvocationID']
        self.ctl('stop', self.audio)
        self.assert_clean_order()
        self.assertEqual(self.props(self.effects)['ActiveState'], 'inactive')
        self.ctl('start', self.audio)
        self.wait_event_count('child-start', 2)
        now = self.props(self.effects)
        self.assertNotEqual(first, now['InvocationID'])
        self.assertEqual(now['ActiveState'], 'active')
        self.assertEqual(now['NRestarts'], '0')

    def test_pipewire_restart_propagates_clean_stop_and_new_invocation(self):
        self.ctl('start', self.effects)
        self.wait_event_count('child-start', 1)
        first = self.props(self.effects)['InvocationID']
        self.ctl('restart', self.audio)
        self.wait_event_count('child-start', 2)
        self.assert_clean_order()
        self.assertNotEqual(first, self.props(self.effects)['InvocationID'])
        self.assertEqual(self.props(self.effects)['NRestarts'], '0')

    def test_failed_pipewire_start_never_launches_effects(self):
        (self.work / 'fail-parent').touch()
        result = self.ctl('start', self.effects, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.wait_event_count('parent-refused', 1)
        self.assertNotIn('child-start', [x['event'] for x in self.records()])
        self.assertNotEqual(self.props(self.effects)['ActiveState'], 'active')

    def cleanup(self):
        # Never discard definitions while an owned process could still be live.
        self.ctl('disable', self.effects, check=False)
        result = self.ctl('stop', *self.units, check=False)
        if result.returncode:
            raise AssertionError(f'Owned fixture stop failed; definitions retained: {result.stderr}')
        for name in self.units:
            result = self.ctl('show', name, '-p', 'MainPID', '-p', 'ActiveState')
            values = dict(line.split('=', 1) for line in result.stdout.splitlines())
            if values.get('MainPID', '0') != '0' or values.get('ActiveState') not in ('inactive', 'failed'):
                raise AssertionError(f'Owned fixture still live; definitions retained: {name}: {values}')
        self.ctl('reset-failed', *self.units, check=False)
        for path in self.created:
            path.unlink(missing_ok=True)
        self.ctl('daemon-reload')
        for name in [self.audio + '.wants', self.target + '.wants']:
            directory = self.config / name
            if directory.is_dir() and not any(directory.iterdir()):
                directory.rmdir()
        # Keep the tiny event receipts in durable task-owned storage.


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] in ['parent', 'child', 'stop']:
        sys.exit({'parent': parent, 'child': child, 'stop': stop_child}[sys.argv[1]](Path(sys.argv[2])))
    unittest.main()
