#!/usr/bin/env python3
"""Selected software integration cases in a private, hardware-free PipeWire graph."""
import argparse
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import signal
import struct
import subprocess
import tempfile
import time
from registry_json import MAX_REGISTRY_BYTES, parse_registry
from pw_cat import raw_mode_options

CASES = ('success-stereo', 'success-714', 'success-seek', 'mismatch', 'cancel', 'target-loss', 'policy-target-loss', 'success-joc')
JOC_SHA256 = 'c190089bbb0600b8bcba27dbe07c370252c3c2605fd285b4f596b9c2a9d59432'
JOC_PCM_SHA256 = '4c97fef1e51add1e08ff4a5bbc5b9df81cbc5cc0eb0b65c8077d99ae701cef19'
JOC_FRAMES = 3528192
JOC_LEADING_ZERO_FRAMES = 24065
MAPS = {'stereo-speakers': ['FL', 'FR'],
        '7.1.4': ['FL', 'FR', 'FC', 'LFE', 'RL', 'RR', 'SL', 'SR',
                  'TFL', 'TFR', 'TRL', 'TRR']}
MAX_CAPTURE_BYTES = 268435456
MAX_MEDIA_OBSERVATION_BYTES = 65536
DESTRUCTIVE_CASES = ('cancel', 'target-loss', 'policy-target-loss')


def pcm_comparison(captured, channels, offset, expected=None, *, frames=None, expected_hash=None):
    """Return diagnostic evidence before the caller asserts full PCM equality."""
    width = channels * 4
    length = len(expected) if expected is not None else frames * width
    expected_hash = hashlib.sha256(expected).hexdigest() if expected is not None else expected_hash
    aligned = offset is not None and offset >= 0 and offset % width == 0
    payload = captured[offset:offset + length] if aligned else b''
    payload_hash = hashlib.sha256(payload).hexdigest() if aligned else None
    first_nonzero = next((index for index, value in enumerate(captured) if value), None)
    result = {'captured_bytes': len(captured), 'captured_complete_frames': len(captured) // width,
        'capture_partial_frame_bytes': len(captured) % width,
        'captured_pcm_sha256': hashlib.sha256(captured).hexdigest(),
        'capture_first_nonzero_frame': first_nonzero // width if first_nonzero is not None else None,
        'expected_bytes': length, 'expected_frames': length // width,
        'expected_pcm_sha256': expected_hash, 'payload_offset_bytes': offset,
        'payload_offset_frames': offset // width if aligned else None,
        'alignment_found': aligned, 'payload_bytes': len(payload),
        'payload_complete_frames': len(payload) // width, 'payload_pcm_sha256': payload_hash,
        'missing_payload_bytes': max(0, length - len(payload)),
        'first_mismatch_byte': None, 'last_mismatch_byte': None,
        'first_mismatch_frame': None, 'first_mismatch_channel': None,
        'first_expected_sample_bits': None, 'first_captured_sample_bits': None,
        'pcm_exact': aligned and len(payload) == length and
                     (payload == expected if expected is not None else payload_hash == expected_hash)}
    if expected is not None and aligned and not result['pcm_exact']:
        shared = min(len(payload), length)
        first = None
        last = max(len(payload), length) - 1 if len(payload) != length else None
        # Compare large chunks in C, inspecting individual bytes only inside
        # the first/last differing chunk. Diagnostics stay bounded for JOC.
        for start in range(0, shared, 65536):
            left, right = expected[start:start + min(65536, shared - start)], payload[start:start + min(65536, shared - start)]
            if left != right:
                first = start + next(i for i, pair in enumerate(zip(left, right)) if pair[0] != pair[1])
                break
        if first is None and len(payload) != length:
            first = shared
        if last is None:
            for stop in range(shared, 0, -65536):
                start = max(0, stop - 65536)
                left, right = expected[start:stop], payload[start:stop]
                if left != right:
                    last = stop - 1 - next(i for i, pair in enumerate(zip(reversed(left), reversed(right))) if pair[0] != pair[1])
                    break
        result.update(first_mismatch_byte=first, last_mismatch_byte=last)
        if first is not None:
            sample = first // 4 * 4
            result.update(first_mismatch_frame=first // width,
                          first_mismatch_channel=(first % width) // 4,
                          first_expected_sample_bits=struct.unpack_from('<I', expected, sample)[0] if sample + 4 <= length else None,
                          first_captured_sample_bits=struct.unpack_from('<I', payload, sample)[0] if sample + 4 <= len(payload) else None)
    return result


def retain_failure_artifacts(private, destination, case):
    """Explicit private failure output; no automatic public capture retention."""
    target = destination / case
    target.mkdir(mode=0o700)
    records = []
    for original, name in ((private / 'capture.pcm', 'capture.pcm'),
                           (private / 'expected.pcm', 'expected-stream.bin')):
        if not original.is_file():
            continue
        size = original.stat().st_size
        if size > MAX_CAPTURE_BYTES:
            raise ValueError('failure artifact exceeds capture bound')
        descriptor = os.open(target / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        digest = hashlib.sha256()
        copied = 0
        with original.open('rb') as source, os.fdopen(descriptor, 'wb') as output:
            while value := source.read(65536):
                copied += len(value)
                if copied > MAX_CAPTURE_BYTES:
                    raise ValueError('failure artifact exceeds capture bound')
                output.write(value)
                digest.update(value)
        records.append({'path': case + '/' + name, 'bytes': copied, 'sha256': digest.hexdigest()})
    return records


def run(command, env, timeout=5):
    return subprocess.run(command, env=env, stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          timeout=timeout, check=True).stdout


class RegistryMonitor:
    """One native monitor; bounded framing and current-state cache, no polling forks."""
    def __init__(self, env):
        self.env = env
        self.child = None
        self.objects = {}
        self.pending = bytearray()
        self.scan = self.depth = 0
        self.in_string = self.escaped = False
        self.document_started = None
        self.started = None
        self.ready = self.failed = False
        self.documents = self.bytes_received = self.processes_started = 0
        self.pipe_capacity_bytes = None
        self.maximum_cache_bytes = self.maximum_partial_bytes = self.maximum_document_bytes = 0

    def start(self):
        if self.child is not None or self.failed:
            raise RuntimeError('registry monitor already started or closed')
        previous = signal.pthread_sigmask(signal.SIG_BLOCK,
            {signal.SIGINT, signal.SIGTERM, signal.SIGHUP})
        def limits():
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
            resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))
            signal.pthread_sigmask(signal.SIG_SETMASK, previous)
        try:
            try:
                self.started = time.monotonic()
                self.child = subprocess.Popen(['pw-dump', '--monitor', '--no-colors'],
                    stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                    env=self.env, preexec_fn=limits, bufsize=0, pipesize=65536)
                self.processes_started += 1
                self.pipe_capacity_bytes = fcntl.fcntl(self.child.stdout.fileno(), fcntl.F_GETPIPE_SZ)
                if not 0 < self.pipe_capacity_bytes <= 65536:
                    raise ValueError('registry monitor pipe capacity')
                os.set_blocking(self.child.stdout.fileno(), False)
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK, previous)
        except BaseException:
            self.close()
            raise

    def feed(self, value):
        if self.failed:
            raise ValueError('registry monitor unavailable')
        try:
            self._feed(value)
        except (OSError, ValueError, RecursionError):
            self.failed = True
            raise

    def _feed(self, value):
        """Frame JSON arrays across arbitrary reads, including quoted brackets."""
        self.pending.extend(value)
        while self.scan < len(self.pending):
            byte = self.pending[self.scan]
            if self.depth == 0:
                if byte in b' \t\r\n':
                    self.scan += 1
                    continue
                if byte != ord('['):
                    raise ValueError('registry monitor expected array')
                self.depth = 1
                self.document_started = time.monotonic()
            elif self.in_string:
                if self.escaped:
                    self.escaped = False
                elif byte == ord('\\'):
                    self.escaped = True
                elif byte == ord('"'):
                    self.in_string = False
            elif byte == ord('"'):
                self.in_string = True
            elif byte in b'[{':
                self.depth += 1
            elif byte in b']}':
                self.depth -= 1
                if self.depth == 0:
                    document = bytes(self.pending[:self.scan + 1])
                    if len(document) > MAX_REGISTRY_BYTES:
                        raise ValueError('registry monitor document limit')
                    self.maximum_document_bytes = max(self.maximum_document_bytes, len(document))
                    parse_registry(document, objects=self.objects)
                    cache_bytes = sum(len(json.dumps(item, ensure_ascii=False).encode())
                                      for item in self.objects.values())
                    if cache_bytes > MAX_REGISTRY_BYTES:
                        raise ValueError('registry monitor cache limit')
                    self.maximum_cache_bytes = max(self.maximum_cache_bytes, cache_bytes)
                    self.documents += 1
                    self.ready = True
                    del self.pending[:self.scan + 1]
                    self.scan = 0
                    self.document_started = None
                    continue
            self.scan += 1
        # Whitespace between documents need not accumulate indefinitely.
        if self.depth == 0:
            self.pending.clear()
            self.scan = 0
        if len(self.pending) > MAX_REGISTRY_BYTES:
            raise ValueError('registry monitor partial-document limit')
        self.maximum_partial_bytes = max(self.maximum_partial_bytes, len(self.pending))

    def snapshot(self):
        if self.failed or self.child is None:
            raise ValueError('registry monitor unavailable')
        try:
            if self.child.poll() is not None:
                raise ValueError('registry monitor exited')
            received = 0
            while True:
                try:
                    value = os.read(self.child.stdout.fileno(), 65536)
                except BlockingIOError:
                    break
                if not value:
                    raise ValueError('registry monitor EOF')
                received += len(value)
                self.bytes_received += len(value)
                if received > MAX_REGISTRY_BYTES:
                    raise ValueError('registry monitor pump limit')
                self.feed(value)
            now = time.monotonic()
            if ((not self.ready and now - self.started >= 2) or
                    (self.document_started is not None and now - self.document_started >= 2)):
                raise ValueError('registry monitor incomplete or startup timeout')
            if self.child.poll() is not None:
                raise ValueError('registry monitor exited')
            return list(self.objects.values())
        except (OSError, ValueError, RecursionError):
            self.failed = True
            raise

    def close(self):
        child, self.child = self.child, None
        self.failed = True
        if child is not None:
            try:
                stop(child)
            finally:
                if child.stdout is not None:
                    child.stdout.close()



class MediaArrival:
    """A bounded, private capture proves nonzero generated media before an action."""
    def __init__(self, path, channels):
        self.descriptor = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
        self.frame_bytes = channels * 4
        self.checked_bytes = self.maximum_read_bytes = 0
        self.first_nonzero_frame = self.observed_at = None

    def ready(self, now):
        if self.first_nonzero_frame is None:
            remaining = MAX_CAPTURE_BYTES - self.checked_bytes
            if remaining <= 0:
                raise ValueError('media observation capture limit')
            data = os.pread(self.descriptor, min(MAX_MEDIA_OBSERVATION_BYTES, remaining), self.checked_bytes)
            self.maximum_read_bytes = max(self.maximum_read_bytes, len(data))
            complete = len(data) // self.frame_bytes * self.frame_bytes
            for index, (value,) in enumerate(struct.iter_unpack('<f', data[:complete])):
                if not math.isfinite(value):
                    raise ValueError('media observation nonfinite PCM')
                if value != 0 and self.first_nonzero_frame is None:
                    self.first_nonzero_frame = (self.checked_bytes + index * 4) // self.frame_bytes
            self.checked_bytes += complete
            if self.first_nonzero_frame is not None:
                self.observed_at = now
        return self.observed_at is not None and now - self.observed_at >= 1

    def receipt(self):
        return {'evidence': 'finite numerically nonzero PCM at the owned virtual sink monitor',
                'first_nonzero_capture_frame': self.first_nonzero_frame,
                'checked_bytes': self.checked_bytes, 'maximum_read_bytes': self.maximum_read_bytes,
                'read_limit_bytes': MAX_MEDIA_OBSERVATION_BYTES, 'delay_after_observation_seconds': 1}

    def close(self):
        if self.descriptor is not None:
            os.close(self.descriptor)
            self.descriptor = None


def props(item):
    return item.get('info', {}).get('props', {})


def nodes(data, prefix):
    return [item for item in data if item.get('type') == 'PipeWire:Interface:Node'
            and props(item).get('node.name', '').startswith(prefix)]


def wait_for(callback, timeout=10):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        value = callback()
        if value:
            return value
        time.sleep(.05)
    raise AssertionError('bounded wait expired')


def stop(process, group=False):
    if process is None:
        return
    if process.poll() is None:
        if group:
            os.killpg(process.pid, signal.SIGTERM)
        else:
            process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            if group:
                os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()
            process.wait(timeout=3)


def configure_client_ports(node, channels, env, capture=False):
    name = props(node).get('node.name', '')
    if (capture and name != 'integration-capture') or (not capture and not name.startswith('rog-atmos-')):
        raise AssertionError('refusing to configure an unrelated node')
    configuration = {'direction': 'Input' if capture else 'Output', 'mode': 'dsp',
        'format': {'mediaType': 'audio', 'mediaSubtype': 'raw', 'format': 'F32',
                   'rate': 48000, 'channels': len(channels), 'position': channels}}
    # A policy-free daemon does not configure client adapter DSP ports. This
    # setter is confined to the harness's own silent clients and private core.
    run(['pw-cli', 'set-param', str(node['id']), 'PortConfig', json.dumps(configuration)], env)


def scoped_links(data, source_id, target_id, channels, env, monitor=False):
    ports = [item for item in data if item.get('type') == 'PipeWire:Interface:Port']
    sources = {}
    targets = {}
    for port in ports:
        p = props(port)
        node = int(p.get('node.id', -1))
        channel = p.get('audio.channel')
        if node == source_id and p.get('port.direction') == 'out':
            # A sink's monitor ports, a client's ordinary playback ports.
            if not monitor or p.get('port.monitor') is True or str(p.get('port.name', '')).startswith('monitor_'):
                sources[channel] = port['id']
        if node == target_id and p.get('port.direction') == 'in':
            targets[channel] = port['id']
    if any(channel not in sources or channel not in targets for channel in channels):
        return False
    existing = {(item.get('info', {}).get('output-port-id'),
                 item.get('info', {}).get('input-port-id')) for item in data
                if item.get('type') == 'PipeWire:Interface:Link'}
    for channel in channels:
        pair = sources[channel], targets[channel]
        if pair not in existing:
            run(['pw-link', str(pair[0]), str(pair[1])], env)
    return True


def capture_links_active(data, source_id, target_id, channels):
    """The capture callback has no stdin dependency; wait before media starts."""
    ports = {item['id']: props(item) for item in data
             if item.get('type') == 'PipeWire:Interface:Port'}
    active = []
    for item in data:
        if item.get('type') != 'PipeWire:Interface:Link':
            continue
        info = item.get('info', {})
        if info.get('input-node-id') != target_id:
            continue
        source = ports.get(info.get('output-port-id'), {})
        target = ports.get(info.get('input-port-id'), {})
        if (info.get('output-node-id') != source_id or
                source.get('audio.channel') != target.get('audio.channel') or
                source.get('audio.channel') not in channels):
            raise AssertionError('unexpected capture route')
        if info.get('state') == 'error':
            raise AssertionError('capture link error')
        if info.get('state') == 'active':
            active.append(source['audio.channel'])
    return sorted(active) == sorted(channels)


def expected_pcm(probe, scene, layout, private, env, start=0, volume=1):
    receipt = private / 'expected.json'
    output = private / 'expected.pcm'
    dotnet = probe.parent / 'runtime' / 'dotnet'
    executable = str(dotnet) if dotnet.is_file() else 'dotnet'
    with output.open('xb') as handle:
        subprocess.run([executable, str(probe.parent / 'AtmosProbe.dll'), 'stream',
                        '--input', str(scene), '--layout', layout,
                        '--start-sample', str(start), '--volume', str(volume), '--report', str(receipt)],
                       env=env, stdin=subprocess.DEVNULL, stdout=handle,
                       stderr=subprocess.DEVNULL, timeout=90, check=True)
    with output.open('rb') as handle:
        header = json.loads(handle.readline(4097))
        pcm = handle.read(230400001)
    channels = len(MAPS[layout])
    assert header['protocol'] == 'rog-atmos-pcm-v1'
    assert header['sample_rate'] == 48000 and header['channels'] == channels
    assert len(pcm) == (header['input_samples'] - start) * channels * 4
    report = json.loads(receipt.read_text())
    assert report['stream']['pcm_sha256'] == hashlib.sha256(pcm).hexdigest()
    return pcm


def scene_file(private, seconds):
    path = private / 'scene.json'
    path.write_text(json.dumps({'schema_version': 1, 'sample_rate': 48000,
        'samples': seconds * 48000, 'objects': [
            {'frequency_hz': 997, 'amplitude': .1, 'keyframes': [
                {'sample': 0, 'position': [-.8, .6, .7]},
                {'sample': seconds * 48000 - 1, 'position': [.8, -.4, -.7]}]},
            {'frequency_hz': 733, 'amplitude': .07, 'keyframes': [
                {'sample': 0, 'position': [.7, -.4, -.6]},
                {'sample': seconds * 48000 - 1, 'position': [-.7, .6, .6]}]}
        ]}))
    return path


def one_case(name, probe, config, parent, joc_input=None, failure_artifacts=None):
    started = time.monotonic()
    result = {'case': name, 'status': 'failed', 'physical_audio': False}
    with tempfile.TemporaryDirectory(prefix='case-', dir=parent) as directory:
        private = Path(directory)
        runtime = private / 'runtime'
        runtime.mkdir(mode=0o700)
        env = {k: v for k, v in os.environ.items()
               if not k.startswith(('PIPEWIRE_', 'SPA_')) and k != 'DBUS_SESSION_BUS_ADDRESS'}
        for key in ('XDG_CONFIG_HOME', 'XDG_CACHE_HOME', 'XDG_STATE_HOME', 'XDG_DATA_HOME'):
            folder = private / key.lower()
            folder.mkdir()
            env[key] = str(folder)
        env.update(XDG_RUNTIME_DIR=str(runtime), PIPEWIRE_RUNTIME_DIR=str(runtime),
                   PIPEWIRE_REMOTE='pipewire-live-atmos')
        daemon = capture = player = manager = monitor = media_arrival = None
        policy_version = None
        daemon_log = (private / 'daemon.log').open('xb')
        capture_handle = None
        try:
            daemon = subprocess.Popen(['pipewire', '-c', str(config)], env=env,
                                      stdin=subprocess.DEVNULL, stdout=daemon_log, stderr=daemon_log)
            wait_for(lambda: (runtime / 'pipewire-live-atmos').is_socket())
            monitor = RegistryMonitor(env)
            monitor.start()
            if name == 'policy-target-loss':
                wp = Path(env['XDG_CONFIG_HOME']) / 'wireplumber'
                policy_version = run(['wireplumber', '--version'], env).decode().strip()
                if 'libwireplumber 0.5.' in policy_version:
                    # WirePlumber 0.5 replaced Lua configuration with SPA-JSON.
                    # These feature names come from the 0.5.17 shipped profiles.
                    (wp / 'wireplumber.conf.d').mkdir(parents=True)
                    (wp / 'wireplumber.conf.d' / '80-disable-hardware.conf').write_text(
                        'wireplumber.profiles = { main = {\n'
                        '  hardware.audio = disabled\n'
                        '  hardware.bluetooth = disabled\n'
                        '  hardware.video-capture = disabled\n'
                        '  monitor.alsa = disabled\n'
                        '  monitor.alsa-midi = disabled\n'
                        '  monitor.bluez = disabled\n'
                        '  monitor.bluez-midi = disabled\n'
                        '  monitor.v4l2 = disabled\n'
                        '  monitor.libcamera = disabled\n'
                        '} }\n')
                elif 'libwireplumber 0.4.' in policy_version:
                    (wp / 'main.lua.d').mkdir(parents=True)
                    (wp / 'bluetooth.lua.d').mkdir()
                    (wp / 'main.lua.d' / '80-disable-hardware.lua').write_text(
                        'alsa_monitor.enabled = false\nv4l2_monitor.enabled = false\nlibcamera_monitor.enabled = false\n')
                    (wp / 'bluetooth.lua.d' / '80-disable-hardware.lua').write_text('bluez_monitor.enabled = false\n')
                else:
                    raise AssertionError('unsupported WirePlumber configuration version')
                manager = subprocess.Popen(['dbus-run-session', '--', 'wireplumber'],
                    stdin=subprocess.DEVNULL, stdout=daemon_log, stderr=daemon_log,
                    env=env, start_new_session=True)
                wait_for(lambda: any(item.get('type') == 'PipeWire:Interface:Client'
                    and props(item).get('application.name') == 'WirePlumber' for item in monitor.snapshot()))
            layout = '7.1.4' if name in ('success-714', 'success-joc') else 'stereo-speakers'
            channels = MAPS[layout]
            sink_name = 'live-atmos-null' if layout == '7.1.4' else 'live-atmos-stereo'
            sink = wait_for(lambda: next(iter(nodes(monitor.snapshot(), sink_name)), None))
            sink_id = sink['id']
            target_serial = str(props(sink)['object.serial'])
            start, volume = (777, .5) if name == 'success-seek' else (0, 1)
            source = joc_input if name == 'success-joc' else scene_file(private,
                10 if name in ('cancel', 'target-loss', 'policy-target-loss') else 2)
            if name == 'success-joc':
                assert hashlib.sha256(source.read_bytes()).hexdigest() == JOC_SHA256, 'JOC input pin mismatch'
                pcm = None  # The prior accepted full render supplies the fixed PCM hash.
            else:
                pcm = expected_pcm(probe, source, layout, private, env, start, volume) if name.startswith('success') else None
            report_path = private / 'playback.json'
            if name.startswith('success') or name in DESTRUCTIVE_CASES:
                capture_path = private / 'capture.pcm'
                capture_handle = capture_path.open('xb')
                def capture_limits():
                    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_CAPTURE_BYTES, MAX_CAPTURE_BYTES))
                    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
                raw_options = raw_mode_options(env)
                result['capture_explicit_raw'] = bool(raw_options)
                capture_properties = {'node.name': 'integration-capture',
                    'stream.dont-remix': True, 'channelmix.disable': True}
                if name in DESTRUCTIVE_CASES:
                    capture_properties.update({'node.autoconnect': False, 'node.dont-fallback': True,
                        'node.dont-reconnect': True, 'node.dont-move': True})
                capture = subprocess.Popen(['pw-cat', *raw_options, '--record', '--format', 'f32',
                    '--rate', '48000', '--channels', str(len(channels)),
                    '--channel-map', ','.join(channels), '--target', '0',
                    '--properties', json.dumps(capture_properties), '-'],
                    stdin=subprocess.DEVNULL, stdout=capture_handle, stderr=subprocess.DEVNULL,
                    env=env, preexec_fn=capture_limits)
                capture_node = wait_for(lambda: next(iter(nodes(monitor.snapshot(), 'integration-capture')), None))
                configure_client_ports(capture_node, channels, env, capture=True)
                wait_for(lambda: scoped_links(monitor.snapshot(), sink_id, capture_node['id'], channels, env, monitor=True))
                wait_for(lambda: capture_links_active(monitor.snapshot(), sink_id, capture_node['id'], channels))
                result['capture_links_active_before_playback'] = True
                if name in DESTRUCTIVE_CASES:
                    media_arrival = MediaArrival(capture_path, len(channels))
            selected_layout = '7.1.4' if name == 'mismatch' else layout
            playback_started = time.monotonic()
            usage_before = resource.getrusage(resource.RUSAGE_CHILDREN)
            player = subprocess.Popen([str(probe), '--input', str(source), '--target', target_serial,
                '--layout', selected_layout, '--start-sample', str(start),
                '--volume', str(volume), '--report', str(report_path)],
                env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            action = False
            linked = False
            observed_stream = None
            configured_nodes = set()
            unexpected_links = []
            deadline = time.monotonic() + (150 if name == 'success-joc' else 70)
            while player.poll() is None:
                assert time.monotonic() < deadline, 'player exceeded harness deadline'
                data = monitor.snapshot()
                streams = nodes(data, 'rog-atmos-')
                assert len(streams) <= 1, 'multiple playback nodes'
                if streams:
                    observed_stream = streams[0]['id']
                    if manager is None and observed_stream not in configured_nodes:
                        configure_client_ports(streams[0], channels, env)
                        configured_nodes.add(observed_stream)
                    for item in data:
                        info = item.get('info', {})
                        if (item.get('type') == 'PipeWire:Interface:Link' and
                                info.get('output-node-id') == observed_stream and
                                info.get('input-node-id') != sink_id):
                            unexpected_links.append(item['id'])
                    if name == 'policy-target-loss':
                        observed = [item for item in data if item.get('type') == 'PipeWire:Interface:Link'
                            and item.get('info', {}).get('output-node-id') == observed_stream
                            and item.get('info', {}).get('input-node-id') == sink_id]
                        linked = len(observed) == len(channels)
                    elif not action:
                        linked = scoped_links(data, observed_stream, sink_id, channels, env) or linked
                    if media_arrival is not None:
                        capture_active = capture_links_active(data, sink_id, capture_node['id'], channels)
                        if not action:
                            assert capture_active, 'media observation capture route lost'
                            # Startup priming is zero. Observe actual generated media,
                            # then keep pumping for one second before the action.
                            if linked and media_arrival.ready(time.monotonic()):
                                result['action_after_media_observation_seconds'] = time.monotonic() - media_arrival.observed_at
                                if name == 'cancel':
                                    player.send_signal(signal.SIGTERM)
                                else:
                                    run(['pw-cli', 'destroy', str(sink_id)], env)
                                action = True
                time.sleep(.05)
            code = player.wait(timeout=3)
            usage_after = resource.getrusage(resource.RUSAGE_CHILDREN)
            playback_seconds = time.monotonic() - playback_started
            report = json.loads(report_path.read_text())
            assert (report_path.stat().st_mode & 0o777) == 0o600
            assert not unexpected_links, 'unexpected fallback link'
            assert report['physical_playback_observed'] is False
            wait_for(lambda: not nodes(monitor.snapshot(), 'rog-atmos-'), timeout=5)
            assert not list(private.glob('.atmos-live-*')), 'private child directory leaked'
            result.update(exit_code=code, playback_status=report['status'],
                          playback_report=report, unexpected_links=unexpected_links,
                          stream_observed=observed_stream is not None, owned_nodes_removed=True,
                          routing_policy=policy_version if manager else 'manual scoped links; no policy-manager qualification',
                          link_observation_interval_seconds=.05,
                          playback_wall_seconds=round(playback_seconds, 6),
                          waited_descendants_cpu_seconds=round((usage_after.ru_utime + usage_after.ru_stime) -
                              (usage_before.ru_utime + usage_before.ru_stime), 6),
                          cpu_scope='all waited harness descendants during playback, including registry clients',
                          virtual_graph={'rate': 48000, 'quantum': 256, 'freewheel': False})
            if name.startswith('success'):
                assert code == 0 and report['status'] == 'completed'
                assert linked and report['pipewire_drain_completed'] is True
                assert report['media_start_verified_active'] is True
                assert report['backend_submitted_frames'] == (
                    report['submitted_complete_frames'] + report['startup_priming_frames'])
                frames = JOC_FRAMES if name == 'success-joc' else len(pcm) // (len(channels) * 4)
                result['media_duration_seconds'] = frames / 48000
                result['playback_wall_to_media_ratio'] = playback_seconds / (frames / 48000)
                assert all(report[key] == frames for key in ('expected_frames', 'rendered_frames',
                    'submitted_complete_frames', 'drained_frames'))
                time.sleep(.3)
                stop(capture)
                capture_handle.close()
                capture_handle = None
                captured = capture_path.read_bytes()
                if name == 'success-joc':
                    first_byte = next((i for i, value in enumerate(captured) if value), None)
                    first_frame = first_byte // (len(channels) * 4) if first_byte is not None else None
                    offset = (first_frame - JOC_LEADING_ZERO_FRAMES) * len(channels) * 4 if first_frame is not None else None
                    expected_hash = JOC_PCM_SHA256
                    comparison = pcm_comparison(captured, len(channels), offset, frames=JOC_FRAMES, expected_hash=expected_hash)
                    result.update(joc_input_sha256=JOC_SHA256,
                        comparison='prior accepted Cavern full-render PCM; same-engine continuity, not independent fidelity',
                        expected_first_nonzero_frame=JOC_LEADING_ZERO_FRAMES)
                else:
                    anchor = pcm[:min(len(pcm), 4096 * len(channels) * 4)]
                    offset = captured.find(anchor)
                    expected_hash = hashlib.sha256(pcm).hexdigest()
                    comparison = pcm_comparison(captured, len(channels), offset, expected=pcm)
                # Persist all diagnostic fields before any capture assertion.
                result.update(comparison)
                result['compared_frames'] = frames
                assert comparison['alignment_found'], 'PCM start absent/unaligned'
                assert comparison['pcm_exact'], 'monitor PCM differs or truncates'
                if name == 'success-joc':
                    assert report['producer']['status'] == 'joc-stream-unqualified'
                    assert report['producer']['object_metadata_consumed'] is True
                assert report['submitted_pcm_sha256'] == expected_hash
            elif name == 'mismatch':
                assert code == 2 and report['status'] == 'target-channel-map-mismatch'
                assert observed_stream is None and report['submitted_bytes'] == 0
            elif name == 'cancel':
                assert action and code == 2 and report['status'] == 'cancelled-signal-15'
                assert report['submitted_complete_frames'] > 0
            else:
                assert action and code == 2 and report['status'] in (
                    'target-disappeared-or-changed', 'stream-links-lost', 'pipewire-player-ended-early')
                assert report['submitted_complete_frames'] > 0
                assert report['pipewire_drain_completed'] is False
            result['status'] = 'passed'
        except Exception as exc:
            result['failure'] = type(exc).__name__ + ': ' + str(exc)
        finally:
            stop(player)
            stop(capture)
            if media_arrival is not None:
                result['media_action_barrier'] = media_arrival.receipt()
                media_arrival.close()
            if monitor is not None:
                result['registry_observation'] = {
                    'mode': 'persistent-native-monitor', 'processes_started': monitor.processes_started,
                    'requested_pipe_bytes': 65536, 'pipe_capacity_bytes': monitor.pipe_capacity_bytes,
                    'document_limit_bytes': MAX_REGISTRY_BYTES,
                    'cache_limit_bytes': MAX_REGISTRY_BYTES, 'partial_document_seconds': 2,
                    'documents': monitor.documents, 'bytes_received': monitor.bytes_received,
                    'maximum_document_bytes': monitor.maximum_document_bytes,
                    'maximum_cache_bytes': monitor.maximum_cache_bytes,
                    'maximum_partial_bytes': monitor.maximum_partial_bytes,
                    'failed_before_cleanup': monitor.failed}
                monitor.close()
            if capture_handle:
                capture_handle.close()
            stop(manager, group=True)
            stop(daemon)
            daemon_log.close()
        if result['status'] == 'failed' and failure_artifacts is not None:
            try:
                result['retained_failure_artifacts'] = retain_failure_artifacts(private, failure_artifacts, name)
            except (OSError, ValueError) as exc:
                result['failure_artifact_error'] = type(exc).__name__
        if result['status'] != 'passed':
            result['private_daemon_log_tail'] = (private / 'daemon.log').read_bytes()[-8192:].decode(errors='replace')
    result['elapsed_seconds'] = round(time.monotonic() - started, 3)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--probe', type=Path, required=True, help='built atmos-live launcher')
    parser.add_argument('--config', type=Path, default=Path(__file__).with_name('live-pipewire.conf'))
    parser.add_argument('--case', action='append', choices=CASES)
    parser.add_argument('--joc-input', type=Path, help='explicit publisher vector elementary stream, never fetched here')
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--failure-artifacts', type=Path, help='new private directory for bounded captures from failed cases only')
    args = parser.parse_args()
    if args.case and len(set(args.case)) != len(args.case):
        parser.error('duplicate cases')
    if os.path.lexists(args.report):
        parser.error('report collision')
    if Path('/dev/snd').exists():
        parser.error('hardware device mount forbidden')
    if args.failure_artifacts:
        args.failure_artifacts = args.failure_artifacts.parent.resolve(strict=True) / args.failure_artifacts.name
        report_target = args.report.parent.resolve(strict=True) / args.report.name
        if os.path.lexists(args.failure_artifacts) or args.failure_artifacts == report_target:
            parser.error('failure-artifact directory collision')
    selected = args.case or tuple(name for name in CASES if name != 'success-joc')
    if 'success-joc' in selected and args.joc_input is None:
        parser.error('success-joc requires --joc-input')
    if args.joc_input:
        args.joc_input = args.joc_input.resolve(strict=True)
    report = {'schema_version': 1, 'evidence_class': 'isolated-virtual-pipewire-integration',
              'physical_audio': False, 'selected_cases': list(selected), 'results': []}
    args.probe = args.probe.resolve(strict=True)
    args.config = args.config.resolve(strict=True)
    source_files = ('Program.cs', 'LiveStream.cs', 'OfflinePullRenderer.cs', 'ObjectFrameGuard.cs',
                    'atmos-live', 'atmos-probe', 'live_integration.py', 'live-pipewire.conf',
                    'live-ci.sh', 'live_ci_options.py', 'registry_json.py', 'pw_cat.py', 'build.sh', 'source_manifest.json', 'Dockerfile', 'AtmosProbe.csproj',
                    'global.json', '../../tests/test_atmos_live.py', '../../scripts/validate_atmos_live.py')
    def bindings():
        items = {name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                 for name in source_files if (Path(__file__).parent / name).is_file()}
        for name in ('AtmosProbe.dll', 'Cavern.dll', 'Cavern.Format.dll', 'atmos-live', 'registry_json.py', 'pw_cat.py'):
            items['build/' + name] = hashlib.sha256((args.probe.parent / name).read_bytes()).hexdigest()
        return items
    report['source_before_sha256'] = bindings()
    if args.failure_artifacts:
        args.failure_artifacts.mkdir(mode=0o700)
    with tempfile.TemporaryDirectory(prefix='.live-integration-', dir=args.report.parent) as parent:
        for name in selected:
            report['results'].append(one_case(name, args.probe, args.config, Path(parent), args.joc_input, args.failure_artifacts))
        report['source_after_sha256'] = bindings()
        report['source_unchanged'] = report['source_before_sha256'] == report['source_after_sha256']
        report['passed'] = sum(item['status'] == 'passed' for item in report['results'])
        report['failed'] = len(selected) - report['passed']
        if not report['source_unchanged']:
            report['failed'] += 1
        report['status'] = 'passed' if report['failed'] == 0 else 'failed'
        prepared = Path(parent) / 'report.json'
        fd = os.open(prepared, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, 'w') as handle:
            json.dump(report, handle, indent=2, allow_nan=False)
            handle.write('\n')
        os.link(prepared, args.report)
    print(json.dumps({'status': report['status'], 'passed': report['passed'], 'failed': report['failed']}))
    return 0 if report['failed'] == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
