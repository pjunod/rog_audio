"""Focused live-player contracts; no host PipeWire or audio devices are used."""
import contextlib
import errno
import hashlib
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import signal
import socket
import struct
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'probes/atmos'))
from registry_json import MAX_REGISTRY_BYTES, parse_registry
import pw_cat
import native_playback
import native_capture
loader = importlib.machinery.SourceFileLoader('atmos_live', str(ROOT / 'probes/atmos/atmos-live'))
spec = importlib.util.spec_from_loader(loader.name, loader)
live = importlib.util.module_from_spec(spec)
loader.exec_module(live)
ci_spec = importlib.util.spec_from_file_location('live_ci_options', ROOT / 'probes/atmos/live_ci_options.py')
ci_options = importlib.util.module_from_spec(ci_spec)
ci_spec.loader.exec_module(ci_options)
integration_spec = importlib.util.spec_from_file_location('live_integration', ROOT / 'probes/atmos/live_integration.py')
integration = importlib.util.module_from_spec(integration_spec)
integration_spec.loader.exec_module(integration)
BUILD = None
BED = None


def registry(channels=None):
    channels = channels or ['FL', 'FR']
    result = [{'id': 42, 'type': 'PipeWire:Interface:Node', 'info': {'props': {
        'media.class': 'Audio/Sink', 'node.name': 'tuned-sink',
        'object.serial': 142, 'audio.position': ','.join(channels)}}},
        {'id': 7, 'type': 'PipeWire:Interface:Node', 'info': {'props': {'node.name': 'stream-test'}}}]
    for index, channel in enumerate(channels):
        result += [{'id': 100 + index, 'type': 'PipeWire:Interface:Port',
                    'info': {'props': {'audio.channel': channel}}},
                   {'id': 200 + index, 'type': 'PipeWire:Interface:Port',
                    'info': {'props': {'audio.channel': channel}}},
                   {'id': 300 + index, 'type': 'PipeWire:Interface:Link', 'info': {
                       'output-node-id': 7, 'input-node-id': 42,
                       'output-port-id': 100 + index, 'input-port-id': 200 + index,
                       'state': 'active'}}]
    return result


def scene(samples=10001):
    return {'schema_version': 1, 'sample_rate': 48000, 'samples': samples, 'objects': [{
        'amplitude': 0.125, 'frequency_hz': 997,
        'keyframes': [{'sample': 0, 'position': [-1, 0, 1]}]}]}


class ImmediateObservation:
    """A ready registry for transport-only tests, without native IPC."""
    active = False

    def __init__(self, _env, *_configuration):
        pass

    def start(self):
        self.active = True

    def poll(self):
        if not self.active:
            return None
        self.active = False
        return registry()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.active = False


class LiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='atmos-live-unit-')
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_explicit_target_and_channel_contract(self):
        data = registry()
        expected = {'id': 42, 'serial': '142'}
        self.assertEqual(live.resolve_target(data, 'tuned-sink', ['FL', 'FR']), expected)
        self.assertEqual(live.resolve_target(data, '142', ['FL', 'FR']), expected)
        for target, channels in [('absent', ['FL', 'FR']), ('tuned-sink', ['FR', 'FL'])]:
            with self.assertRaises(live.PlaybackError):
                live.resolve_target(data, target, channels)
        with self.assertRaises(live.PlaybackError):
            live.resolve_target(data + [data[0]], 'tuned-sink', ['FL', 'FR'])
        data[0]['info']['props']['object.serial'] = '١٤٢'
        with self.assertRaises(live.PlaybackError):
            live.resolve_target(data, 'tuned-sink', ['FL', 'FR'])

    def test_exact_channel_links_and_target_lifetime(self):
        target = {'id': 42, 'serial': '142'}
        data = registry()
        self.assertTrue(live.verify_links(data, target, 'stream-test', ['FL', 'FR']))
        self.assertFalse(live.verify_links(data[:-1], target, 'stream-test', ['FL', 'FR']))
        data[-1]['info']['input-node-id'] = 99
        with self.assertRaisesRegex(live.PlaybackError, 'unrequested'):
            live.verify_links(data, target, 'stream-test', ['FL', 'FR'])
        data = registry()
        data[-2]['info']['props']['audio.channel'] = 'FL'
        with self.assertRaisesRegex(live.PlaybackError, 'channel-link'):
            live.verify_links(data, target, 'stream-test', ['FL', 'FR'])
        data = registry()
        data[0]['info']['props']['object.serial'] = 143
        with self.assertRaisesRegex(live.PlaybackError, 'disappeared'):
            live.verify_links(data, target, 'stream-test', ['FL', 'FR'])

    def test_backend_command_and_environment_cannot_override_target(self):
        with mock.patch.dict(os.environ, {'PIPEWIRE_PROPS': 'target.object=wrong',
                'PIPEWIRE_QUANTUM': '1/1', 'PIPEWIRE_NODE': 'wrong',
                'PIPEWIRE_REMOTE': 'isolated', 'DOTNET_EnableDiagnostics': '1'}, clear=True):
            env = live.child_environment()
        self.assertEqual(env['PIPEWIRE_REMOTE'], 'isolated')
        self.assertEqual(env['DOTNET_EnableDiagnostics'], '0')
        self.assertFalse(any(key in env for key in ('PIPEWIRE_PROPS', 'PIPEWIRE_QUANTUM', 'PIPEWIRE_NODE')))
        command = live.native_command(Path('/private/build/atmos-pw-playback'),
            {'serial': '142'}, ['FL', 'FR'], 'stream-test', 9)
        self.assertEqual(command, ['/private/build/atmos-pw-playback', '--target', '142',
            '--channels', '2', '--name', 'stream-test', '--control-fd', '9'])
        self.assertNotIn('pw-cat', command)

    def test_raw_capability_old_and_modern_help_select_exact_options(self):
        common = b'  -p, --playback  Playback\n  -r, --record  Record\n      --format FORMAT\n'
        for advertised, expected in ((b'', []), (b'  -a, --raw  Raw PCM\n', ['--raw'])):
            with self.subTest(options=expected):
                def help_command(command, **options):
                    self.assertEqual(command, ['pw-cat', '--help'])
                    self.assertEqual(options['timeout'], 2)
                    self.assertEqual(options['stdin'], subprocess.DEVNULL)
                    self.assertEqual(options['env']['LC_ALL'], 'C')
                    self.assertEqual(options['env']['PIPEWIRE_REMOTE'], 'private')
                    options['stdout'].write(common + advertised)
                    return subprocess.CompletedProcess(command, 0)
                with mock.patch.object(pw_cat.subprocess, 'run', side_effect=help_command):
                    self.assertEqual(pw_cat.raw_mode_options({'PIPEWIRE_REMOTE': 'private'}), expected)

    def test_raw_capability_failure_timeout_and_output_bound_fail_closed(self):
        for payload, code in ((b'', 0), (b'not pw-cat help', 0),
                              (b'x' * (pw_cat.MAX_HELP_BYTES + 1), 0),
                              (b'--playback --record --format', 1)):
            with self.subTest(length=len(payload), code=code):
                def help_command(command, **options):
                    options['stdout'].write(payload)
                    return subprocess.CompletedProcess(command, code)
                with mock.patch.object(pw_cat.subprocess, 'run', side_effect=help_command):
                    with self.assertRaisesRegex(ValueError, 'capabilities-unavailable'):
                        pw_cat.raw_mode_options({})
        for error in (subprocess.TimeoutExpired('pw-cat', 2), FileNotFoundError('pw-cat')):
            with mock.patch.object(pw_cat.subprocess, 'run', side_effect=error):
                with self.assertRaisesRegex(ValueError, 'capabilities-unavailable'):
                    pw_cat.raw_mode_options({})

    def native_core_case(self, name):
        if BUILD is None:
            self.fail('native core methods require a compiled --build output')
        result = subprocess.run([str(BUILD / 'native-tests'), name],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10, check=True)
        self.assertEqual(result.stdout, b'passed\n')

    def test_native_core_full_ring_control_and_cancellation_are_independent(self):
        if BUILD is None:
            self.fail('native core methods require a compiled --build output')
        result = subprocess.run([str(BUILD / 'native-io-tests')],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15, check=True)
        self.assertEqual(result.stdout, b'passed\n')

    def test_native_core_concurrent_ring_wrap_preserves_order(self):
        self.native_core_case('concurrent')

    def test_native_core_media_boundary_and_exact_partial_tail(self):
        self.native_core_case('partial-tail')

    def test_native_core_starvation_and_input_eof_bounds(self):
        self.native_core_case('starvation')

    def test_native_core_begin_rejects_duplicate_out_of_order_and_oversize(self):
        self.native_core_case('protocol')

    def capture_core_case(self, name):
        if BUILD is None:
            self.fail('capture core methods require a compiled --build output')
        result = subprocess.run([str(BUILD / 'native-capture-tests'), name],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10, check=True)
        self.assertEqual(result.stdout, b'passed\n')

    def test_capture_core_concurrent_ring_wrap_overflow_and_limit(self):
        self.capture_core_case('ring')

    def test_capture_core_optional_timeline_flags_wrap_and_regressions(self):
        self.capture_core_case('timeline')

    def test_capture_core_writer_short_write_and_failure_accounting(self):
        self.capture_core_case('writer')

    def test_capture_core_arm_stop_callback_and_writer_quiescence(self):
        self.capture_core_case('lifecycle')

    def test_capture_core_rejects_nonprivate_or_unbounded_output_descriptors(self):
        self.capture_core_case('fd-contract')

    @staticmethod
    def capture_final(**changes):
        return {'protocol': native_capture.PROTOCOL, 'status': 'completed', 'complete': True,
            'callback_received_frames': 4, 'ring_accepted_frames': 4, 'writer_taken_frames': 4,
            'written_bytes': 32, 'written_complete_frames': 4, 'ring_capacity_frames': 4096,
            'maximum_ring_frames': 4, 'rejected_frames': 0, 'ignored_before_arm_frames': 256,
            'overflow_events': 0, 'writer_io_errors': 0,
            'metadata_request_accepted': False, 'clock_observations': 0,
            'unavailable_clock_observations': 1, 'clock_gap_events': 0,
            'header_observations': 0, 'unavailable_pts_observations': 1,
            'sequence_regressions': 0, 'pts_regressions': 0, 'header_discontinuities': 0,
            'largest_sequence_step': 0, 'first_ticks': None, 'last_ticks': None,
            'first_sequence': None, 'last_sequence': None, 'first_pts': None, 'last_pts': None, **changes}

    def capture_helper(self, mode='good'):
        helper = self.root / ('capture-helper-' + mode)
        final = self.capture_final()
        if mode == 'badcount':
            final['written_bytes'] = 31
        if mode in ('source-end', 'source-write-error'):
            final.update(status='capture-pipewire-failure', complete=False)
            if mode == 'source-write-error':
                final['writer_io_errors'] = 1
        code = ('#!' + sys.executable + '\nMODE = ' + repr(mode) + '\nFINAL = ' + repr(final) + '\n')
        code += r"""
import json,os,signal,socket,sys,time
if sys.argv[1:] == ['--describe']:
 print(json.dumps({'protocol':'rog-atmos-capture-v1','ring_frames':4096,'maximum_file_bytes':268435456,'rate':48000,'channels':[2,12]}))
 raise SystemExit(0)
options = dict(zip(sys.argv[1::2],sys.argv[2::2]))
control = socket.socket(fileno=int(options['--control-fd']))
output = int(options['--output-fd'])
assert control.recv(128) == b'ARM 1\n'
if MODE == 'eof':
 control.close(); raise SystemExit(0)
if MODE == 'oversize':
 control.send(b'x'*2049); raise SystemExit(2)
if MODE == 'badack':
 control.send(b'ACK 2\n'); time.sleep(20)
if MODE == 'unresponsive':
 signal.signal(signal.SIGTERM,signal.SIG_IGN)
control.send(b'ACK 1\n')
if MODE == 'unresponsive':
 time.sleep(20)
os.write(output,bytes(32))
assert control.recv(128) == b'STOP 2\n'
control.send(b'ACK 2\n')
control.send(b'FINAL '+json.dumps(FINAL).encode()+b'\n')
raise SystemExit(2 if MODE.startswith('source-') else 0)
"""
        helper.write_text(code)
        helper.chmod(0o700)
        return helper

    def test_capture_observer_capability_probe_fails_closed(self):
        helper = self.capture_helper()
        value = native_capture.capture_capabilities(helper, {})
        self.assertEqual(value['protocol'], native_capture.PROTOCOL)
        for payload in (b'{}', b'x' * 2049, b'{"protocol":"other"}'):
            def run(argv, **options):
                options['stdout'].write(payload)
                return subprocess.CompletedProcess(argv, 0)
            with mock.patch.object(native_capture.subprocess, 'run', side_effect=run), \
                    self.assertRaises(native_capture.CaptureError):
                native_capture.capture_capabilities(helper, {})
        for error in (FileNotFoundError(), subprocess.TimeoutExpired('capture', 2)):
            with mock.patch.object(native_capture.subprocess, 'run', side_effect=error), \
                    self.assertRaises(native_capture.CaptureError):
                native_capture.capture_capabilities(helper, {})

    def test_capture_observer_arm_stop_and_complete_accounting(self):
        for mode in ('good', 'badcount'):
            path = self.root / (mode + '.pcm')
            observer = native_capture.CaptureObserver(self.capture_helper(mode), path, 2, {})
            try:
                observer.arm()
                self.assertEqual(observer.acknowledged, 1)
                if mode == 'good':
                    value = observer.finish()
                    self.assertTrue(value['complete'])
                    self.assertEqual(value['written_bytes'], path.stat().st_size)
                    self.assertEqual(path.stat().st_mode & 0o777, 0o600)
                    self.assertFalse(value['metadata_request_accepted'])
                else:
                    with self.assertRaisesRegex(native_capture.CaptureError, 'accounting-mismatch'):
                        observer.finish()
            finally:
                observer.close()
            self.assertIsNotNone(observer.child.returncode)
            self.assertEqual(observer.endpoint.fileno(), -1)
        original = path.read_bytes()
        with self.assertRaises(FileExistsError):
            native_capture.CaptureObserver(self.capture_helper('good'), path, 2, {})
        self.assertEqual(path.read_bytes(), original)

    def test_capture_observer_control_failure_and_partial_source_end_are_explicit(self):
        for mode in ('badack', 'oversize', 'eof'):
            observer = native_capture.CaptureObserver(self.capture_helper(mode), self.root / (mode + '.pcm'), 2, {})
            try:
                with self.assertRaises(native_capture.CaptureError):
                    observer.arm()
            finally:
                observer.close()
            self.assertIsNotNone(observer.child.returncode)
            self.assertEqual(observer.endpoint.fileno(), -1)
        for case, action, mode, allowed in (
                ('cancel', True, 'source-end', False),
                ('target-loss', False, 'source-end', False),
                ('policy-target-loss', False, 'source-end', False),
                ('target-loss', True, 'source-end', True),
                ('policy-target-loss', True, 'source-end', True),
                ('target-loss', True, 'source-write-error', False)):
            with self.subTest(case=case, action=action, mode=mode):
                path = self.root / f'{case}-{action}-{mode}.pcm'
                observer = native_capture.CaptureObserver(self.capture_helper(mode), path, 2, {})
                try:
                    observer.arm()
                    require_complete = not integration.capture_source_end_allowed(case, action)
                    if not allowed:
                        with self.assertRaises(native_capture.CaptureError):
                            observer.finish(require_complete=require_complete)
                    else:
                        value = observer.finish(require_complete=require_complete)
                        self.assertEqual(value['status'], 'capture-pipewire-failure')
                        self.assertFalse(value['complete'])
                        self.assertEqual(observer.child.returncode, 2)
                        self.assertEqual(observer.receipt()['native'], value)
                finally:
                    observer.close()

    def test_capture_observer_cleanup_reaps_unresponsive_child(self):
        observer = native_capture.CaptureObserver(self.capture_helper('unresponsive'), self.root / 'stalled.pcm', 2, {})
        observer.arm()
        with mock.patch.object(native_capture, 'CONTROL_SECONDS', .05):
            observer.close()
        self.assertEqual(observer.child.returncode, -signal.SIGKILL)
        self.assertEqual(observer.endpoint.fileno(), -1)
        self.assertEqual(observer.cleanup_error, 'capture-stop-timeout')

    def test_native_capabilities_require_exact_colocated_protocol(self):
        description = {'protocol': native_playback.PROTOCOL, 'ring_frames': 4096,
                       'rate': 48000, 'channels': [2, 12], 'format': 'f32le',
                       'final_buffer_policy': 'fill-request'}
        def command(payload, code=0):
            def run(argv, **options):
                self.assertEqual(argv, ['/build/atmos-pw-playback', '--describe'])
                self.assertEqual(options['timeout'], 2)
                options['stdout'].write(payload)
                return subprocess.CompletedProcess(argv, code)
            return run
        for change in ({}, {'protocol': 'old'}, {'ring_frames': 65536}, {'format': 's16'},
                       {'final_buffer_policy': None}, {'final_buffer_policy': 'short-chunk'}):
            value = {**description, **change}
            with mock.patch.object(native_playback.subprocess, 'run', side_effect=command(json.dumps(value).encode())):
                if change:
                    with self.assertRaises(native_playback.NativeError):
                        native_playback.capabilities(Path('/build/atmos-pw-playback'), {})
                else:
                    self.assertEqual(native_playback.capabilities(Path('/build/atmos-pw-playback'), {}), description)
        for error in (FileNotFoundError(), subprocess.TimeoutExpired('helper', 2)):
            with mock.patch.object(native_playback.subprocess, 'run', side_effect=error), \
                    self.assertRaisesRegex(native_playback.NativeError, 'unavailable-or-incompatible'):
                native_playback.capabilities(Path('/build/atmos-pw-playback'), {})
        for payload, code in ((b'x' * 2049, 0), (b'{}', 2), (b'bad', 0)):
            with mock.patch.object(native_playback.subprocess, 'run', side_effect=command(payload, code)), \
                    self.assertRaises(native_playback.NativeError):
                native_playback.capabilities(Path('/build/atmos-pw-playback'), {})

    @staticmethod
    def native_final(priming=5, media=777, **changes):
        return {'protocol': native_playback.PROTOCOL, 'status': 'completed',
            'input_frames': priming + media, 'consumed_frames': priming + media,
            'stdin_priming_frames': priming, 'media_frames': media,
            'startup_silence_frames': 256, 'prefill_silence_frames': 512, 'tail_padding_frames': 247,
            'underflow_events': 0, 'missing_media_frames': 0, 'ring_capacity_frames': 4096,
            'maximum_ring_frames': 777, 'maximum_callback_frames': 256,
            'input_eof': True, 'ring_consumed': True, 'drained': True, **changes}

    def test_native_control_boundary_ack_and_terminal_counts(self):
        endpoint, server = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        report = {}
        client = native_playback.NativeControl(endpoint, report)
        try:
            client.begin(5, 777)
            self.assertEqual(server.recv(128), b'BEGIN 1 5 777\n')
            self.assertFalse(client.poll())
            server.send(b'ACK 1 5 777\n')
            self.assertTrue(client.poll())
            server.send(b'FINAL ' + json.dumps(self.native_final()).encode() + b'\n')
            client.finish(5, 777)
            self.assertTrue(report['native_playback']['drained'])
            self.assertEqual(report['native_playback']['media_frames'], 777)
            self.assertEqual(report['native_playback']['tail_padding_frames'], 247)
            with self.assertRaises(native_playback.NativeError):
                client.begin(5, 777)
        finally:
            client.close()
            server.close()
        self.assertEqual(endpoint.fileno(), -1)

    def test_native_control_rejects_wrong_duplicate_oversize_and_missing_ack(self):
        for packets in ((b'ACK 2 5 777\n',), (b'ACK 1 6 777\n',),
                        (b'ACK 1 5 777\n', b'ACK 1 5 777\n'), (b'x' * 2049,),
                        (b'FINAL {}\n',)):
            endpoint, server = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
            client = native_playback.NativeControl(endpoint, {})
            try:
                client.begin(5, 777)
                for packet in packets:
                    server.send(packet)
                with self.assertRaises(native_playback.NativeError):
                    client.poll()
            finally:
                client.close()
                server.close()
        endpoint, server = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        client = native_playback.NativeControl(endpoint, {})
        try:
            server.send(b'ACK 1 5 777\n')
            with self.assertRaises(native_playback.NativeError):
                client.poll()
            client.begin(5, 777)
            with mock.patch.object(native_playback.time, 'monotonic', return_value=client.started + 2), \
                    self.assertRaisesRegex(native_playback.NativeError, 'ack-timeout'):
                client.poll()
        finally:
            client.close()
            server.close()

    def test_native_control_disconnect_and_failed_terminal_never_complete(self):
        invalid_shapes = ({'tail_padding_frames': -1}, {'tail_padding_frames': True},
                          {'tail_padding_frames': None}, {'tail_padding_frames': 256})
        for changes in ({'status': 'native-media-underrun', 'underflow_events': 1},
                        {'input_eof': False}, {'ring_consumed': False}, {'drained': False},
                        {'input_frames': 781}, {'consumed_frames': 781}, {'media_frames': 776},
                        {'underflow_events': 1}, {'missing_media_frames': 256},
                        *invalid_shapes, {'maximum_callback_frames': 0, 'tail_padding_frames': 0}):
            endpoint, server = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
            report = {}
            client = native_playback.NativeControl(endpoint, report)
            try:
                client.begin(5, 777)
                server.send(b'ACK 1 5 777\n')
                server.send(b'FINAL ' + json.dumps(self.native_final(**changes)).encode() + b'\n')
                with self.assertRaises(native_playback.NativeError):
                    client.finish(5, 777)
                if changes in invalid_shapes:
                    self.assertNotIn('native_playback', report)
                else:
                    self.assertEqual(report['native_playback'], self.native_final(**changes))
            finally:
                client.close()
                server.close()
        endpoint, server = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        client = native_playback.NativeControl(endpoint, {})
        server.close()
        try:
            with self.assertRaisesRegex(native_playback.NativeError, 'disconnected'):
                client.poll()
        finally:
            client.close()

    def test_header_and_pcm_validation(self):
        header = {'protocol': 'rog-atmos-pcm-v1', 'sample_rate': 48000, 'channels': 2,
                  'start_sample': 7, 'input_samples': 100, 'format': 'f32le'}
        self.assertEqual(live.validate_header(header, 'stereo-speakers', 7), 93 * 8)
        for key, value in [('input_samples', True), ('input_samples', 4320001),
                           ('channels', 12), ('start_sample', 0), ('format', 's16')]:
            with self.assertRaises(live.PlaybackError):
                live.validate_header(dict(header, **{key: value}), 'stereo-speakers', 7)
        live.checked_pcm(struct.pack('<3f', -1, 0, 1))
        for value in (float('nan'), float('inf'), -1.01, 1.01):
            with self.assertRaises(live.PlaybackError):
                live.checked_pcm(struct.pack('<f', value))

    def test_registry_snapshot_and_removals_preserve_chronology_and_serials(self):
        original = registry()[0]
        replacement = dict(original, info={'props': dict(original['info']['props'], **{'object.serial': 143})})
        removed_after = json.dumps([original]).encode() + b'\n[{"id":42,"info":null}]\n'
        self.assertEqual(parse_registry(removed_after), [])
        recreated = removed_after + json.dumps([replacement]).encode()
        current = parse_registry(recreated)
        self.assertEqual(live.resolve_target(current, '143', ['FL', 'FR']), {'id': 42, 'serial': '143'})
        with self.assertRaises(live.PlaybackError):
            live.resolve_target(current, '142', ['FL', 'FR'])
        removed_before = b'[{"id":99,"props":null}]\n' + json.dumps([original]).encode()
        self.assertEqual(parse_registry(removed_before), [original])
        self.assertEqual(parse_registry(b'[]\n[{"id":42,"info":null}]'), [])
        # Link and port removals must change route validation as well as targets.
        changed = json.dumps(registry()).encode() + b'\n[{"id":301,"info":null}]'
        self.assertFalse(live.verify_links(parse_registry(changed), {'id': 42, 'serial': '142'},
                                          'stream-test', ['FL', 'FR']))

    def test_registry_rejects_malformed_tail_objects_and_bounds(self):
        invalid = [b'', b' ', b'{}', b'[] trailing', b'[] [', b'[{"id":true,"info":null}]',
                   b'[{"id":-1,"info":null}]', b'[{"id":4294967295,"info":null}]',
                   b'[{"id":42,"info":null,"extra":1}]', b'[{"id":42}]', b'[{"id":42,"id":43,"info":null}]',
                   b'[{"id":42,"info":null},{"id":42,"info":null}]',
                   b'[]' + b' ' * MAX_REGISTRY_BYTES, b'[]\xff']
        for data in invalid:
            with self.subTest(data=data[:80]), self.assertRaises(ValueError):
                parse_registry(data)

    def test_snapshot_consumes_bounded_registry_event_stream(self):
        payload = json.dumps(registry()).encode() + b'\n[{"id":42,"info":null}]\n'
        def completed(command, **kwargs):
            self.assertEqual(command, ['pw-dump'])
            self.assertEqual(kwargs['timeout'], live.SNAPSHOT_SECONDS)
            kwargs['stdout'].write(payload)
            return subprocess.CompletedProcess(command, 0)
        with mock.patch.object(live.subprocess, 'run', side_effect=completed):
            result = live.snapshot({})
        with self.assertRaisesRegex(live.PlaybackError, 'target-disappeared'):
            live.verify_links(result, {'id': 42, 'serial': '142'}, 'stream-test', ['FL', 'FR'])

    def fake_registry_environment(self, code):
        executable = self.root / 'pw-dump'
        executable.write_text('#!' + sys.executable + '\n' + code)
        executable.chmod(0o700)
        return dict(live.child_environment(), PATH=str(self.root) + os.pathsep + os.environ.get('PATH', ''))

    def observation_result(self, observation):
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            result = observation.poll()
            if result is not None:
                return result
            time.sleep(.005)
        self.fail('bounded observation did not complete')

    def test_async_registry_has_one_inflight_child_and_collects_completed_events(self):
        fixture = self.root / 'registry.json'
        fixture.write_text(json.dumps(registry()))
        env = self.fake_registry_environment('from pathlib import Path\nprint(Path(' + repr(str(fixture)) + ').read_text())\n')
        with live.RegistryObservation(env, {'id': 42, 'serial': '142'}, 'stream-test', ['FL', 'FR']) as observation:
            child = observation.child
            observation.start()
            with self.assertRaises(RuntimeError):
                observation.start()
            result = self.observation_result(observation)
            self.assertTrue(result['linked'])
            self.assertTrue(result['active'])
            self.assertFalse(observation.active)
            fixture.write_text(json.dumps(registry()) + '\n[{"id":42,"info":null}]')
            observation.start()
            with self.assertRaisesRegex(live.PlaybackError, 'target-disappeared'):
                self.observation_result(observation)
            self.assertIs(observation.child, child)  # No new observer process per request.
        self.assertIsNotNone(child.returncode)
        self.assertTrue(child.stdin.closed and child.stdout.closed)

    def test_async_registry_timeout_parse_failure_and_cancellation_close_resources(self):
        for code, timeout in (('import time\ntime.sleep(20)\n', .1),
                              ('print("[] trailing")\n', 2),
                              ('print("[]" + " " * 4194304)\n', 2)):
            env = self.fake_registry_environment(code)
            with self.subTest(code=code[:20]), mock.patch.object(live, 'SNAPSHOT_SECONDS', timeout):
                with self.assertRaisesRegex(live.PlaybackError, 'registry-unavailable'):
                    with live.RegistryObservation(env, {'id': 42, 'serial': '142'}, 'stream-test', ['FL', 'FR']) as observation:
                        child = observation.child
                        observation.start()
                        self.observation_result(observation)
                self.assertIsNotNone(child.returncode)
                self.assertTrue(child.stdin.closed and child.stdout.closed)

    def test_persistent_registry_rejects_wrong_sequence_oversize_crash_and_invalid_state(self):
        original = subprocess.Popen
        replies = (b'{"sequence":2,"linked":true,"active":true}\n',
                   b'x' * 1025, b'{"sequence":1,"linked":false,"active":true}\n',
                   b'{"sequence":1,"linked":true,"active":true}\ntrailing')
        for reply in replies:
            code = 'import os,time\nos.read(0,1)\nos.write(1,' + repr(reply) + ')\ntime.sleep(20)'
            def launch(_command, **options):
                return original([sys.executable, '-c', code], **options)
            with self.subTest(reply=reply[:30]), mock.patch.object(live.subprocess, 'Popen', side_effect=launch):
                with self.assertRaisesRegex(live.PlaybackError, 'registry-protocol'):
                    with live.RegistryObservation(live.child_environment(), {}, '', []) as observation:
                        child = observation.child
                        observation.start()
                        self.observation_result(observation)
                self.assertIsNotNone(child.returncode)
                self.assertTrue(child.stdin.closed and child.stdout.closed)
        def crash(_command, **options):
            return original([sys.executable, '-c', 'raise SystemExit(4)'], **options)
        with mock.patch.object(live.subprocess, 'Popen', side_effect=crash):
            with self.assertRaisesRegex(live.PlaybackError, 'registry-unavailable'):
                with live.RegistryObservation(live.child_environment(), {}, '', []) as observation:
                    child = observation.child
                    observation.start()
                    self.observation_result(observation)
        self.assertNotEqual(child.returncode, 0)

    def test_persistent_registry_cancel_reaps_worker_and_active_dump(self):
        marker = self.root / 'dump.pid'
        env = self.fake_registry_environment('import os,time\nfrom pathlib import Path\nPath(' +
            repr(str(marker)) + ').write_text(str(os.getpid()))\ntime.sleep(20)\n')
        with self.assertRaisesRegex(live.PlaybackError, 'cancelled'):
            with live.RegistryObservation(env, {'id': 42, 'serial': '142'}, 'stream-test', ['FL', 'FR']) as observation:
                child = observation.child
                observation.start()
                deadline = time.monotonic() + 2
                while not marker.exists() and time.monotonic() < deadline:
                    time.sleep(.005)
                self.assertTrue(marker.exists(), 'owned pw-dump child did not start')
                dump_pid = int(marker.read_text())
                raise live.PlaybackError('cancelled')
        self.assertIsNotNone(child.returncode)
        self.assertTrue(child.stdin.closed and child.stdout.closed)
        self.assertFalse(Path('/proc', str(dump_pid)).exists(), 'active dump was not reaped')

    def test_monitor_split_documents_preserve_updates_removals_and_id_reuse(self):
        monitor = integration.RegistryMonitor({})
        data = registry()
        data[0]['info']['props']['description'] = 'brackets [}] and quote " plus é'
        replacement = dict(data[0], info={'props': dict(data[0]['info']['props'], **{'object.serial': 144})})
        changed_link = dict(data[-1], info=dict(data[-1]['info'], state='negotiating'))
        documents = [data, [changed_link], [{'id': 42, 'info': None}], [replacement]]
        for value in b' \n'.join(json.dumps(document, ensure_ascii=False).encode() for document in documents):
            monitor.feed(bytes([value]))  # Includes splits inside UTF-8 and escaped strings.
        current = list(monitor.objects.values())
        self.assertEqual(live.resolve_target(current, 'tuned-sink', ['FL', 'FR']), {'id': 42, 'serial': '144'})
        self.assertFalse(live.verify_links(current, {'id': 42, 'serial': '144'},
                                          'stream-test', ['FL', 'FR'], require_active=True))
        self.assertEqual(monitor.documents, 4)
        self.assertFalse(monitor.pending)
        monitor.feed(b'[{"id":42,"info":null}]')
        with self.assertRaisesRegex(live.PlaybackError, 'target-disappeared'):
            live.verify_links(list(monitor.objects.values()), {'id': 42, 'serial': '144'},
                              'stream-test', ['FL', 'FR'])
        # A removal in a separate document must not be lost by array replacement.
        self.assertIn(7, monitor.objects)

    def test_monitor_malformed_partial_document_and_complete_cache_bounds_fail_closed(self):
        for malformed in (b'[] trailing', b'[{"id":1}]', b'[{"id":1,"id":2}]'):
            monitor = integration.RegistryMonitor({})
            with self.subTest(malformed=malformed), self.assertRaises(ValueError):
                monitor.feed(malformed)
            self.assertTrue(monitor.failed)
            with self.assertRaisesRegex(ValueError, 'unavailable'):
                monitor.feed(b'[]')
        with mock.patch.object(integration, 'MAX_REGISTRY_BYTES', 512):
            monitor = integration.RegistryMonitor({})
            with self.assertRaisesRegex(ValueError, 'partial-document limit'):
                monitor.feed(b'[' + b' ' * 512)
            monitor = integration.RegistryMonitor({})
            with self.assertRaisesRegex(ValueError, 'document limit'):
                monitor.feed(b'[' + b' ' * 512 + b']')
            first = {'id': 1, 'type': 'PipeWire:Interface:Node', 'info': {'props': {'padding': 'x' * 240}}}
            second = dict(first, id=2)
            monitor = integration.RegistryMonitor({})
            monitor.feed(json.dumps([first]).encode())
            with self.assertRaisesRegex(ValueError, 'cache limit'):
                monitor.feed(json.dumps([second]).encode())
            self.assertTrue(monitor.failed)

    def test_monitor_child_eof_and_partial_timeout_do_not_serve_stale_cache(self):
        original = subprocess.Popen
        fixture = json.dumps(registry()).encode() + b'\n'
        release = self.root / 'monitor-release'
        scripts = (
            'import os,time\nfrom pathlib import Path\nos.write(1,' + repr(fixture) + ')\n' +
            'while not Path(' + repr(str(release)) + ').exists(): time.sleep(.005)\n' +
            'os.close(1)\ntime.sleep(20)',
            'import os,time\nos.write(1,b"[")\ntime.sleep(20)',
            'import time\ntime.sleep(20)',
            'raise SystemExit(3)')
        for index, code in enumerate(scripts):
            def launch(command, **options):
                self.assertEqual(command, ['pw-dump', '--monitor', '--no-colors'])
                return original([sys.executable, '-c', code], **options)
            monitor = integration.RegistryMonitor(live.child_environment())
            with self.subTest(case=index), mock.patch.object(integration.subprocess, 'Popen', side_effect=launch) as spawn:
                try:
                    monitor.start()
                    child = monitor.child
                    deadline = time.monotonic() + 2
                    if index == 0:
                        while not monitor.ready and time.monotonic() < deadline:
                            monitor.snapshot()
                            time.sleep(.005)
                        self.assertTrue(monitor.ready)
                        self.assertTrue(monitor.snapshot())
                        release.write_text('close stdout')
                    elif index == 1:
                        while not monitor.pending and time.monotonic() < deadline:
                            monitor.snapshot()
                            time.sleep(.005)
                        self.assertTrue(monitor.pending)
                        monitor.document_started -= 3
                    elif index == 2:
                        monitor.started -= 3
                    with self.assertRaises(ValueError):
                        while time.monotonic() < deadline:
                            monitor.snapshot()
                            time.sleep(.005)
                        self.fail('monitor did not fail within bound')
                    with self.assertRaisesRegex(ValueError, 'unavailable'):
                        monitor.snapshot()
                    self.assertEqual(spawn.call_count, 1)
                finally:
                    monitor.close()
                self.assertIsNotNone(child.returncode)
                self.assertTrue(child.stdout.closed)

    def test_destructive_action_waits_for_finite_media_with_bounded_partial_reads(self):
        path = self.root / 'action-capture.pcm'
        path.write_bytes(struct.pack('<2f', 0, -0.0)[:7])
        arrival = integration.MediaArrival(path, 2)
        descriptor = arrival.descriptor
        try:
            with mock.patch.object(integration, 'MAX_MEDIA_OBSERVATION_BYTES', 8):
                self.assertFalse(arrival.ready(1))
                self.assertEqual(arrival.checked_bytes, 0)  # Incomplete frames are retried.
                path.write_bytes(struct.pack('<6f', 0, -0.0, 0, 0, .125, 0))
                self.assertFalse(arrival.ready(2))
                self.assertFalse(arrival.ready(20))  # Time alone and signed zero cannot trigger.
                self.assertIsNone(arrival.first_nonzero_frame)
                self.assertFalse(arrival.ready(30))
                self.assertEqual(arrival.first_nonzero_frame, 2)
                self.assertFalse(arrival.ready(30.999))
                self.assertTrue(arrival.ready(31))
                self.assertLessEqual(arrival.maximum_read_bytes, 8)
                self.assertEqual(arrival.checked_bytes, 24)
        finally:
            arrival.close()
        with self.assertRaises(OSError):
            os.fstat(descriptor)
        path.write_bytes(struct.pack('<2f', float('nan'), .125))
        arrival = integration.MediaArrival(path, 2)
        try:
            with self.assertRaisesRegex(ValueError, 'nonfinite PCM'):
                arrival.ready(1)
            self.assertIsNone(arrival.first_nonzero_frame)
        finally:
            arrival.close()

    def test_capture_comparison_preserves_mismatch_and_truncation_evidence(self):
        expected = struct.pack('<16f', *([.125] * 16))
        prefix = bytes(3 * 8)
        changed = bytearray(expected)
        struct.pack_into('<f', changed, 11 * 4, .25)
        result = integration.pcm_comparison(prefix + changed, 2, len(prefix), expected=expected)
        self.assertFalse(result['pcm_exact'])
        self.assertEqual(result['payload_complete_frames'], 8)
        self.assertEqual(result['first_mismatch_frame'], 5)
        self.assertEqual(result['first_mismatch_channel'], 1)
        self.assertEqual(result['first_expected_sample_bits'], struct.unpack('<I', struct.pack('<f', .125))[0])
        self.assertEqual(result['first_captured_sample_bits'], struct.unpack('<I', struct.pack('<f', .25))[0])
        self.assertEqual(result['captured_pcm_sha256'], hashlib.sha256(prefix + changed).hexdigest())
        truncated = integration.pcm_comparison(prefix + expected[:-8], 2, len(prefix), expected=expected)
        self.assertFalse(truncated['pcm_exact'])
        self.assertEqual(truncated['missing_payload_bytes'], 8)
        self.assertEqual(truncated['first_mismatch_frame'], 7)
        self.assertIsNone(truncated['first_captured_sample_bits'])
        absent = integration.pcm_comparison(prefix, 2, -1, expected=expected)
        self.assertFalse(absent['alignment_found'])
        self.assertIsNone(absent['first_mismatch_byte'])
        exact = integration.pcm_comparison(prefix + expected, 2, len(prefix), expected=expected)
        self.assertTrue(exact['pcm_exact'])

    def test_failed_capture_artifacts_are_private_bounded_and_exclusive(self):
        source, output = self.root / 'source', self.root / 'artifacts'
        source.mkdir()
        output.mkdir(mode=0o700)
        (source / 'capture.pcm').write_bytes(b'\0' * 16)
        (source / 'expected.pcm').write_bytes(b'header\n' + b'\0' * 16)
        report = {'status': 'completed', 'submitted_complete_frames': 777}
        (source / 'playback.json').write_text(json.dumps(report))
        records = integration.retain_failure_artifacts(source, output, 'case-test')
        self.assertEqual(len(records), 3)
        self.assertEqual(json.loads((output / 'case-test/playback.json').read_text()), report)
        self.assertEqual((output / 'case-test').stat().st_mode & 0o777, 0o700)
        for record in records:
            path = output / record['path']
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertEqual(record['sha256'], hashlib.sha256(path.read_bytes()).hexdigest())
        with self.assertRaises(FileExistsError):
            integration.retain_failure_artifacts(source, output, 'case-test')
        with mock.patch.object(integration, 'MAX_CAPTURE_BYTES', 8), self.assertRaises(ValueError):
            integration.retain_failure_artifacts(source, output, 'oversize')

    def test_cli_rejects_invalid_input_volume_and_collisions(self):
        source = self.root / 'scene.json'
        source.write_text(json.dumps(scene()))
        base = ['--input', str(source), '--target', 'tuned-sink', '--report',
                str(self.root / 'report.json'), '--dotnet', sys.executable]
        with contextlib.redirect_stderr(open(os.devnull, 'w')), mock.patch.object(live.platform, 'system', return_value='Linux'):
            for value in ('nan', 'inf', '1.1', '-.1'):
                with self.assertRaises(SystemExit):
                    live.arguments(base + ['--volume', value])
            fifo = self.root / 'fifo'
            os.mkfifo(fifo)
            with self.assertRaises(SystemExit):
                live.arguments(['--input', str(fifo)] + base[2:])
            output = self.root / 'report.json'
            output.symlink_to(self.root / 'absent')
            with self.assertRaises(SystemExit):
                live.arguments(base)

    def transfer_case(self, payload, *, expected=None, player_code=None, producer_code=None,
                      observation=ImmediateObservation, report=None, backend_factory=None):
        source = self.root / 'payload.pcm'
        source.write_bytes(payload)
        producer = subprocess.Popen([sys.executable, '-c', producer_code or
                                    'import pathlib,sys;sys.stdout.buffer.write(pathlib.Path(sys.argv[1]).read_bytes())', str(source)],
                                    stdout=subprocess.PIPE, stdin=subprocess.DEVNULL, bufsize=0, pipesize=4096)
        sink = self.root / 'sink.pcm'
        player_request, player_maximum = live.player_pipe_bounds(2)
        player = subprocess.Popen([sys.executable, '-c', player_code or
                                  'import pathlib,sys;pathlib.Path(sys.argv[1]).write_bytes(sys.stdin.buffer.read())', str(sink)],
                                  stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, bufsize=0, pipesize=player_request)
        if report is None:
            report = {'received_complete_frames': 0, 'submitted_complete_frames': 0}
        try:
            live.bounded_pipe(producer.stdout)
            live.bounded_pipe(player.stdin, player_request, player_maximum)
            class CompactObservation(observation):
                def poll(self):
                    data = super().poll()
                    if data is None:
                        return None
                    target = {'id': 42, 'serial': '142'}
                    return {'linked': live.verify_links(data, target, 'stream-test', ['FL', 'FR']),
                            'active': live.verify_links(data, target, 'stream-test', ['FL', 'FR'], require_active=True)}
            class AcceptedBackend:
                boundary = None
                ready = False
                def begin(self, priming, media):
                    self.boundary = (priming, media)
                    self.ready = True
                def poll(self):
                    return self.ready
                def finish(self, priming, media):
                    if self.boundary != (priming, media):
                        raise AssertionError('media crossed a different boundary')
            backend = (backend_factory or AcceptedBackend)()
            with mock.patch.object(live, 'snapshot', return_value=registry()), \
                    mock.patch.object(live, 'RegistryObservation', CompactObservation):
                live.transfer(producer, player, len(payload) if expected is None else expected,
                              {'id': 42, 'serial': '142'}, 'stream-test', ['FL', 'FR'], {}, report, backend)
            return report, sink.read_bytes()
        finally:
            live.stop_children([producer, player])

    def test_player_pipe_reserve_scales_channels_and_enforces_actual_capacity(self):
        for channels, expected in ((2, (4096, 4096)), (12, (4096, 4096))):
            requested, maximum = live.player_pipe_bounds(channels)
            self.assertEqual((requested, maximum), expected)
            reader, writer = os.pipe()
            try:
                with os.fdopen(writer, 'wb', buffering=0) as stream:
                    capacity = live.bounded_pipe(stream, requested, maximum)
                    self.assertEqual(capacity, 4096)
                    self.assertLessEqual(capacity, maximum)
                    self.assertFalse(os.get_blocking(stream.fileno()))
                    for unsupported in (requested - 4096, maximum + 4096):
                        with mock.patch.object(live.fcntl, 'fcntl', side_effect=[0, unsupported]):
                            with self.assertRaisesRegex(live.PlaybackError, 'unsupported-pipe-capacity'):
                                live.bounded_pipe(stream, requested, maximum)
            finally:
                os.close(reader)
        for channels in (0, 1, 16, True):
            with self.assertRaisesRegex(live.PlaybackError, 'unsupported-channel-count'):
                live.player_pipe_bounds(channels)

    def test_startup_priming_waits_for_active_links_and_preserves_media(self):
        payload = struct.pack('<f', .125) * 2 * 10001
        sink = self.root / 'sink.pcm'
        case = self
        class NegotiatingObservation(ImmediateObservation):
            phase = 0
            def poll(self):
                if not self.active:
                    return None
                self.active = False
                self.phase += 1
                data = registry()
                if self.phase == 1:
                    case.assertEqual(sink.read_bytes() if sink.exists() else b'', b'')
                    return data[:-1]  # No bytes may cross an incomplete route.
                if self.phase == 2 or not sink.exists() or not sink.stat().st_size:
                    data[-1]['info']['state'] = 'negotiating'
                return data
        code = ('import os,sys\nwith open(sys.argv[1], "wb", buffering=0) as output:\n'
                ' while data := os.read(0, 4096): output.write(data)\n')
        with mock.patch.object(live, 'REGISTRY_INTERVAL_SECONDS', .01):
            report, output = self.transfer_case(payload, observation=NegotiatingObservation, player_code=code)
        primed = report['startup_priming_frames']
        self.assertGreater(primed, 0)
        self.assertEqual(output, bytes(primed * 8) + payload)
        self.assertEqual(report['submitted_pcm_sha256'], hashlib.sha256(payload).hexdigest())
        self.assertEqual(report['submitted_complete_frames'], 10001)
        self.assertEqual(report['backend_submitted_frames'], primed + 10001)
        self.assertEqual(report['drained_frames'], 10001)
        self.assertTrue(report['media_start_verified_active'])
        self.assertLessEqual(report['maximum_queued_bytes'], 4096 * 8)

    def test_native_boundary_ack_holds_media_until_exact_handoff(self):
        payload = struct.pack('<f', .125) * 2 * 10001
        sink = self.root / 'sink.pcm'
        case = self
        class DelayedAck:
            boundary = None
            ready = False
            polls = 0
            def begin(self, priming, media):
                self.boundary = (priming, media)
            def poll(self):
                if self.boundary is not None and not self.ready:
                    case.assertLessEqual(sink.stat().st_size if sink.exists() else 0,
                                         self.boundary[0] * 8)
                    self.polls += 1
                    self.ready = self.polls >= 3
                return self.ready
            def finish(self, priming, media):
                case.assertEqual(self.boundary, (priming, media))
                case.assertTrue(self.ready)
        report, output = self.transfer_case(payload, backend_factory=DelayedAck)
        self.assertEqual(output, bytes(report['startup_priming_frames'] * 8) + payload)
        self.assertEqual(report['submitted_complete_frames'], 10001)
        self.assertEqual(report['drained_frames'], 10001)

    def test_startup_priming_rejects_route_loss_before_media(self):
        class LosingObservation(ImmediateObservation):
            phase = 0
            def poll(self):
                if not self.active:
                    return None
                self.active = False
                self.phase += 1
                data = registry()
                data[-1]['info']['state'] = 'init'
                return data if self.phase == 1 else data[:-1]
        report = {'submitted_complete_frames': 0}
        with mock.patch.object(live, 'REGISTRY_INTERVAL_SECONDS', .01):
            with self.assertRaisesRegex(live.PlaybackError, 'stream-links-lost'):
                self.transfer_case(struct.pack('<f', .125) * 20002,
                                   observation=LosingObservation, report=report)
        self.assertFalse(report['media_start_verified_active'])
        self.assertEqual(report['submitted_complete_frames'], 0)

    def test_startup_priming_frame_and_time_budgets_are_finite(self):
        class PendingObservation(ImmediateObservation):
            def poll(self):
                data = super().poll()
                if data is not None:
                    data[-1]['info']['state'] = 'negotiating'
                return data
        for limits, error in (({'MAX_PRIMING_FRAMES': 4}, 'priming-frame-limit'),
                              ({'STARTUP_SECONDS': .1, 'MAX_PRIMING_FRAMES': 100000000}, 'startup-timeout')):
            report = {'submitted_complete_frames': 0}
            with self.subTest(error=error), \
                    mock.patch.multiple(live, REGISTRY_INTERVAL_SECONDS=0, **limits):
                with self.assertRaisesRegex(live.PlaybackError, error):
                    self.transfer_case(struct.pack('<f', .125) * 20002,
                                       observation=PendingObservation, report=report)
                self.assertEqual(report['submitted_complete_frames'], 0)
                self.assertFalse(report['media_start_verified_active'])
                self.assertLessEqual(report['startup_priming_frames'],
                                     report['startup_priming_limit_frames'])

    def test_startup_and_capture_require_every_matching_link_active(self):
        data = registry()
        target = {'id': 42, 'serial': '142'}
        for item in data:
            if item['id'] in (100, 101):
                item['info']['props']['port.monitor'] = True
        self.assertTrue(live.verify_links(data, target, 'stream-test', ['FL', 'FR'], require_active=True))
        self.assertTrue(integration.capture_links_active(data, 7, 42, ['FL', 'FR']))
        for state in ('init', 'negotiating', 'paused'):
            data[-1]['info']['state'] = state
            self.assertTrue(live.verify_links(data, target, 'stream-test', ['FL', 'FR']))
            self.assertFalse(live.verify_links(data, target, 'stream-test', ['FL', 'FR'], require_active=True))
            self.assertFalse(integration.capture_links_active(data, 7, 42, ['FL', 'FR']))
        data[-1]['info']['state'] = 'error'
        with self.assertRaisesRegex(live.PlaybackError, 'stream-link-error'):
            live.verify_links(data, target, 'stream-test', ['FL', 'FR'], require_active=True)
        with self.assertRaisesRegex(AssertionError, 'capture link error'):
            integration.capture_links_active(data, 7, 42, ['FL', 'FR'])
        data[-1]['info']['state'] = 'active'
        data[2]['info']['props']['port.monitor'] = False
        with self.assertRaisesRegex(AssertionError, 'unexpected capture route'):
            integration.capture_links_active(data, 7, 42, ['FL', 'FR'])
        data[2]['info']['props']['port.monitor'] = True
        data[-1]['info']['output-node-id'] = 99
        with self.assertRaisesRegex(AssertionError, 'unexpected capture route'):
            integration.capture_links_active(data, 7, 42, ['FL', 'FR'])

    def test_bounded_transfer_exact_eof_and_drain(self):
        payload = struct.pack('<f', .125) * 2 * 13001
        report, output = self.transfer_case(payload)
        self.assertEqual(output, payload)
        self.assertEqual(report['drained_frames'], 13001)
        self.assertEqual(report['submitted_pcm_sha256'], hashlib.sha256(payload).hexdigest())
        self.assertLessEqual(report['maximum_queued_bytes'], 4096 * 8)
        self.assertTrue(report['pipewire_drain_completed'])

    def test_transfer_rejects_short_extra_and_nonfinite_pcm(self):
        for data, expected, message in [(b'\0' * 80, 88, 'truncated'),
                                        (b'\0' * 80, 72, 'extra'),
                                        (struct.pack('<2f', float('nan'), 0), 8, 'pcm-invalid')]:
            with self.subTest(message=message), self.assertRaisesRegex(live.PlaybackError, message):
                self.transfer_case(data, expected=expected)

    def test_player_epipe_after_partial_submission_preserves_other_io_failures(self):
        original = os.write
        payload = struct.pack('<f', .125) * 2 * 10001
        for error, expected in ((BrokenPipeError(errno.EPIPE, 'Broken pipe'), live.PlaybackError),
                                (OSError(errno.EIO, 'I/O error'), OSError)):
            calls = 0
            report = {'submitted_complete_frames': 0}
            def interrupted_write(descriptor, data):
                nonlocal calls
                calls += 1
                if calls == 1:
                    return original(descriptor, data)
                raise error
            with self.subTest(error=type(error).__name__), \
                    mock.patch.object(live.os, 'write', side_effect=interrupted_write):
                with self.assertRaises(expected) as failure:
                    self.transfer_case(payload, report=report)
            if isinstance(error, BrokenPipeError):
                self.assertEqual(str(failure.exception), 'pipewire-player-ended-early')
            else:
                self.assertIs(failure.exception, error)
            self.assertGreater(report['submitted_complete_frames'], 0)
            self.assertLess(report['submitted_complete_frames'], 10001)
            self.assertFalse(report.get('pipewire_drain_completed', False))

    def test_stall_watchdog_and_child_cleanup(self):
        with mock.patch.object(live, 'STALL_SECONDS', .1):
            with self.assertRaisesRegex(live.PlaybackError, 'stall'):
                self.transfer_case(b'', expected=100, producer_code='import time;time.sleep(20)')
        child = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(20)'],
                                 stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        live.stop_children([child])
        self.assertIsNotNone(child.returncode)
        self.assertTrue(child.stdin.closed)
        self.assertTrue(child.stdout.closed)

    def test_drain_rejects_missing_links_while_player_survives(self):
        for code in (None, 0):
            player = mock.Mock(returncode=code)
            player.poll.return_value = None
            player.wait.return_value = code
            with mock.patch.object(live, 'snapshot', return_value=registry()[:-1]), \
                    self.assertRaisesRegex(live.PlaybackError, 'stream-links-lost'):
                live.wait_for_drain(player, {'id': 42, 'serial': '142'}, 'stream-test', ['FL', 'FR'], {})
            player.wait.assert_not_called()
        player = mock.Mock()
        player.poll.return_value = None
        player.wait.side_effect = subprocess.TimeoutExpired('pw-cat', .25)
        absent_node = [item for item in registry() if live.props(item).get('node.name') != 'stream-test']
        with mock.patch.object(live, 'snapshot', return_value=absent_node), \
                self.assertRaisesRegex(live.PlaybackError, 'stream-links-lost'):
            live.wait_for_drain(player, {'id': 42, 'serial': '142'}, 'stream-test', ['FL', 'FR'], {})
        player.wait.assert_called_once()
        self.assertLessEqual(player.wait.call_args.kwargs['timeout'], .25)

    def test_drain_teardown_race_requires_successful_exit_and_preserved_target(self):
        absent_node = [item for item in registry() if live.props(item).get('node.name') != 'stream-test']
        for code in (0, 2):
            player = mock.Mock(returncode=code)
            player.poll.return_value = None
            player.wait.return_value = code
            with mock.patch.object(live, 'snapshot', return_value=absent_node):
                if code == 0:
                    live.wait_for_drain(player, {'id': 42, 'serial': '142'}, 'stream-test', ['FL', 'FR'], {})
                else:
                    with self.assertRaisesRegex(live.PlaybackError, 'player-failure'):
                        live.wait_for_drain(player, {'id': 42, 'serial': '142'}, 'stream-test', ['FL', 'FR'], {})
        player = mock.Mock(returncode=0)
        player.poll.return_value = None
        with mock.patch.object(live, 'snapshot', return_value=registry()[1:]), \
                self.assertRaisesRegex(live.PlaybackError, 'target-disappeared'):
            live.wait_for_drain(player, {'id': 42, 'serial': '142'}, 'stream-test', ['FL', 'FR'], {})
        player.wait.assert_not_called()

    def test_ci_retry_defaults_select_only_the_requested_stage(self):
        self.assertEqual(ci_options.select_stage(None, ['method'], [], None), 'units')
        self.assertEqual(ci_options.select_stage(None, [], ['case'], None), 'integration')
        self.assertEqual(ci_options.select_stage(None, [], [], Path('vector')), 'integration')
        self.assertEqual(ci_options.select_stage(None, [], [], None), 'all')
        self.assertEqual(ci_options.select_stage('units', ['method'], [], None), 'units')
        self.assertEqual(ci_options.select_stage('integration', [], ['case'], None), 'integration')

    def test_ci_invalid_retry_selection_fails_before_external_commands(self):
        wrapper = ROOT / 'probes/atmos/live-ci.sh'
        # Execute the wrapper's actual Python entry point with external calls
        # forbidden, rather than testing a second copy of its selection logic.
        source = wrapper.read_text().split("<<'PY'\n", 1)[1].rsplit('\nPY', 1)[0]
        base = ['embedded-wrapper', str(wrapper), '--image', 'unused-image',
                '--compiler-image', 'unused-compiler', '--source',
                str(ROOT), '--report', str(self.root / 'report.json')]
        invalid = [
            ['--test-id', 'method', '--case', 'case'],
            ['--test-id', 'method', '--joc-input', 'vector'],
            ['--stage', 'all', '--test-id', 'method'],
            ['--stage', 'all', '--case', 'case'],
            ['--stage', 'all', '--joc-input', 'vector'],
            ['--stage', 'units', '--case', 'case'],
            ['--stage', 'integration', '--test-id', 'method']]
        with mock.patch.object(subprocess, 'run', side_effect=AssertionError('unexpected process execution')), \
                mock.patch.object(subprocess, 'check_output', side_effect=AssertionError('unexpected process execution')), \
                contextlib.redirect_stderr(open(os.devnull, 'w')):
            for selection in invalid:
                with self.subTest(selection=selection), mock.patch.object(sys, 'argv', base + selection), \
                        mock.patch.dict(sys.modules, {'live_ci_options': ci_options}), \
                        self.assertRaises(SystemExit) as failure:
                    exec(compile(source, str(wrapper), 'exec'), {})
                self.assertEqual(failure.exception.code, 2)

    def test_ci_compiler_failure_records_phase_without_runtime_execution(self):
        wrapper = ROOT / 'probes/atmos/live-ci.sh'
        source = wrapper.read_text().split("<<'PY'\n", 1)[1].rsplit('\nPY', 1)[0]
        report = self.root / 'ci.json'
        argv = ['embedded-wrapper', str(wrapper), '--image', 'runtime-image',
            '--compiler-image', 'compiler-image', '--source', str(ROOT),
            '--report', str(report), '--stage', 'units', '--test-id', 'selected-method']
        commands = []
        def output(command, **options):
            if command[:3] == ['podman', 'image', 'inspect']:
                value = json.dumps([{'Id': command[3]}]).encode()
            elif command[-1] == '--show-toplevel':
                value = (str(ROOT) + '\n').encode()
            elif 'status' in command:
                value = b''
            else:
                value = b'7d85d1880666ca5ea323848cff47ce7f50b29f7d\n'
            return value.decode() if options.get('text') else value
        def run(command, **_options):
            commands.append(command)
            if command[:2] == ['podman', 'run']:
                self.assertIn('compiler-image', command)
                self.assertNotIn('runtime-image', command)
                self.assertIn('--pull', command)
                self.assertIn('never', command)
                return subprocess.CompletedProcess(command, 42)
            return subprocess.CompletedProcess(command, 0)
        with mock.patch.object(subprocess, 'run', side_effect=run), \
                mock.patch.object(subprocess, 'check_output', side_effect=output), \
                mock.patch.object(sys, 'argv', argv), mock.patch.object(sys, 'platform', 'linux'), \
                mock.patch.dict(os.environ, {'XDG_STATE_HOME': str(self.root), 'ATMOS_CONTAINER_ENGINE': 'podman'}), \
                mock.patch.dict(sys.modules, {'live_ci_options': ci_options}), \
                contextlib.redirect_stdout(open(os.devnull, 'w')), self.assertRaises(SystemExit) as failure:
            exec(compile(source, str(wrapper), 'exec'), {})
        self.assertEqual(failure.exception.code, 1)
        result = json.loads(report.read_text())
        self.assertEqual(result['compiler_image_id'], 'compiler-image')
        self.assertEqual(result['image_id'], 'runtime-image')
        self.assertEqual(result['compile_exit_code'], 42)
        self.assertIsNone(result['container_exit_code'])
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(sum(command[:2] == ['podman', 'run'] for command in commands), 1)
        self.assertTrue(any(command[:3] == ['podman', 'rm', '-f'] for command in commands))
        self.assertEqual(report.stat().st_mode & 0o777, 0o600)
        self.assertFalse(list((self.root / 'rog-audio/work').glob('live-atmos-ci.*')))

    def test_signal_failure_report_is_private_and_exclusive(self):
        source = self.root / 'scene.json'
        source.write_text(json.dumps(scene()))
        report = self.root / 'report.json'
        arguments = ['--input', str(source), '--target', 'tuned-sink', '--report',
                     str(report), '--dotnet', sys.executable]
        with mock.patch.object(live.platform, 'system', return_value='Linux'), \
                mock.patch.object(live, 'playback', side_effect=lambda *_: signal.raise_signal(signal.SIGTERM)), \
                contextlib.redirect_stdout(open(os.devnull, 'w')):
            self.assertEqual(live.main(arguments), 2)
        self.assertEqual(json.loads(report.read_text())['status'], 'cancelled-signal-15')
        self.assertEqual(report.stat().st_mode & 0o777, 0o600)
        self.assertFalse(list(self.root.glob('.atmos-live-*')))
        original = report.read_bytes()
        with contextlib.redirect_stderr(open(os.devnull, 'w')), self.assertRaises(SystemExit), \
                mock.patch.object(live.platform, 'system', return_value='Linux'):
            live.main(arguments)
        self.assertEqual(report.read_bytes(), original)

    def producer(self, *, layout='stereo-speakers', start=0, volume=1, data=None, suffix='.json'):
        if BUILD is None:
            self.skipTest('explicit reviewed Linux build required')
        source = self.root / ('input' + suffix)
        source.write_bytes(json.dumps(scene() if data is None else data).encode() if suffix == '.json' else data)
        receipt = self.root / 'producer.json'
        result = subprocess.run(['dotnet', str(BUILD / 'AtmosProbe.dll'), 'stream', '--input', str(source),
                                 '--report', str(receipt), '--layout', layout, '--start-sample', str(start),
                                 '--volume', str(volume)], capture_output=True, timeout=90,
                                 preexec_fn=live.producer_limits, env=live.child_environment())
        report = json.loads(receipt.read_text())
        receipt.unlink()
        header, pcm = result.stdout.split(b'\n', 1) if result.stdout else (b'{}', b'')
        return result, json.loads(header), pcm, report

    def test_producer_release_boundaries_preserve_pcm_and_command_budget(self):
        result, _, reference, report = self.producer(data=scene(samples=3089))
        self.assertEqual(result.returncode, 0, report)
        for frames in (1535, 1536, 1537, 3073):
            with self.subTest(frames=frames):
                result, header, pcm, report = self.producer(data=scene(samples=frames))
                self.assertEqual(result.returncode, 0, report)
                self.assertEqual(pcm, reference[:frames * 8])
                self.assertEqual(header['input_samples'], frames)
                self.assertEqual(report['stream']['written_frames'], frames)
                caller = report['stream']['caller_frames']
                self.assertEqual(caller, 1536)
                self.assertEqual(report['dsp_processing']['commands'], (frames + caller - 1) // caller + 1)
                self.assertLessEqual((90 * 48000 + caller - 1) // caller + 2, 4096)

    def test_producer_stereo_partial_eof_and_hash(self):
        result, header, pcm, report = self.producer()
        self.assertEqual(result.returncode, 0, report)
        self.assertEqual(live.validate_header(header, 'stereo-speakers', 0), len(pcm))
        self.assertEqual(len(pcm), 10001 * 8)
        live.checked_pcm(pcm)
        self.assertEqual(report['stream']['pcm_sha256'], hashlib.sha256(pcm).hexdigest())
        self.assertEqual(report['stream']['written_frames'], 10001)
        self.assertEqual(report['status'], 'synthetic-stream')

    def test_producer_surround_seek_attenuation_and_eof(self):
        result, _, original, report = self.producer(layout='7.1.4')
        self.assertEqual(result.returncode, 0, report)
        result, header, sought, report = self.producer(layout='7.1.4', start=777, volume=.5)
        self.assertEqual(result.returncode, 0, report)
        self.assertEqual(live.validate_header(header, '7.1.4', 777), len(sought))
        expected = struct.pack('<' + 'f' * (len(sought) // 4),
                               *[item[0] * .5 for item in struct.iter_unpack('<f', original[777 * 48:])])
        self.assertEqual(sought, expected)
        result, header, pcm, report = self.producer(start=10001)
        self.assertEqual(result.returncode, 0, report)
        self.assertEqual(live.validate_header(header, 'stereo-speakers', 10001), 0)
        self.assertEqual(pcm, b'')

    def test_producer_invalid_options_and_input_fail_before_pcm(self):
        for options in ({'volume': 1.1}, {'volume': 'NaN'}, {'start': 10002}, {'data': {'invalid': True}}):
            result, _, pcm, report = self.producer(**options)
            self.assertEqual(result.returncode, 2, report)
            self.assertEqual(pcm, b'')
            self.assertEqual(report['status'], 'invalid-input')

    def test_producer_cli_rejects_stream_only_options_on_offline_commands(self):
        if BUILD is None:
            self.skipTest('explicit reviewed Linux build required')
        for command in ('inspect', 'render', 'timeline'):
            for option in ('--volume', '--start-sample'):
                arguments = ['dotnet', str(BUILD / 'AtmosProbe.dll'), command,
                             '--input', str(self.root / 'absent.eac3'),
                             '--report', str(self.root / 'report.json'), option, '0']
                if command == 'render':
                    arguments += ['--output', str(self.root / 'output.wav')]
                if command == 'timeline':
                    arguments += ['--timeline', str(self.root / 'absent-timeline.json')]
                result = subprocess.run(arguments, capture_output=True, timeout=10,
                                        env=live.child_environment(), preexec_fn=live.producer_limits)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, b'')
                self.assertFalse((self.root / 'report.json').exists())

    def test_producer_generated_bed_metadata_and_exact_count(self):
        if BED is None:
            self.skipTest('explicit generated bed fixture required')
        result, header, pcm, report = self.producer(data=BED.read_bytes(), suffix='.eac3')
        self.assertEqual(result.returncode, 0, report)
        self.assertEqual(len(pcm), header['input_samples'] * 8)
        self.assertEqual(report['status'], 'bed-fallback-stream')
        self.assertIs(report['object_metadata_consumed'], False)
        live.checked_pcm(pcm)
