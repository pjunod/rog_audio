#!/usr/bin/env python3
"""Selected software integration cases in a private, hardware-free PipeWire graph."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import tempfile
import time

CASES = ('success-stereo', 'success-714', 'success-seek', 'mismatch', 'cancel', 'target-loss', 'policy-target-loss', 'success-joc')
JOC_SHA256 = 'c190089bbb0600b8bcba27dbe07c370252c3c2605fd285b4f596b9c2a9d59432'
JOC_PCM_SHA256 = '4c97fef1e51add1e08ff4a5bbc5b9df81cbc5cc0eb0b65c8077d99ae701cef19'
JOC_FRAMES = 3528192
JOC_LEADING_ZERO_FRAMES = 24065
MAPS = {'stereo-speakers': ['FL', 'FR'],
        '7.1.4': ['FL', 'FR', 'FC', 'LFE', 'RL', 'RR', 'SL', 'SR',
                  'TFL', 'TFR', 'TRL', 'TRR']}


def run(command, env, timeout=5):
    return subprocess.run(command, env=env, stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          timeout=timeout, check=True).stdout


def registry(env):
    # This graph is created only by the harness inside an isolated container.
    data = json.loads(run(['pw-dump'], env))
    if not isinstance(data, list):
        raise AssertionError('invalid registry')
    return data


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


def one_case(name, probe, config, parent, joc_input=None):
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
        daemon = capture = player = manager = None
        policy_version = None
        daemon_log = (private / 'daemon.log').open('xb')
        capture_handle = None
        try:
            daemon = subprocess.Popen(['pipewire', '-c', str(config)], env=env,
                                      stdin=subprocess.DEVNULL, stdout=daemon_log, stderr=daemon_log)
            wait_for(lambda: (runtime / 'pipewire-live-atmos').is_socket())
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
                    and props(item).get('application.name') == 'WirePlumber' for item in registry(env)))
            layout = '7.1.4' if name in ('success-714', 'success-joc') else 'stereo-speakers'
            channels = MAPS[layout]
            sink_name = 'live-atmos-null' if layout == '7.1.4' else 'live-atmos-stereo'
            sink = wait_for(lambda: next(iter(nodes(registry(env), sink_name)), None))
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
            if name.startswith('success'):
                capture_path = private / 'capture.pcm'
                capture_handle = capture_path.open('xb')
                def capture_limits():
                    resource.setrlimit(resource.RLIMIT_FSIZE, (268435456, 268435456))
                    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
                capture = subprocess.Popen(['pw-cat', '--record', '--format', 'f32',
                    '--rate', '48000', '--channels', str(len(channels)),
                    '--channel-map', ','.join(channels), '--target', '0',
                    '--properties', json.dumps({'node.name': 'integration-capture',
                    'stream.dont-remix': True, 'channelmix.disable': True}), '-'],
                    stdin=subprocess.DEVNULL, stdout=capture_handle, stderr=subprocess.DEVNULL,
                    env=env, preexec_fn=capture_limits)
                capture_node = wait_for(lambda: next(iter(nodes(registry(env), 'integration-capture')), None))
                wait_for(lambda: scoped_links(registry(env), sink_id, capture_node['id'], channels, env, monitor=True))
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
            unexpected_links = []
            deadline = time.monotonic() + (150 if name == 'success-joc' else 70)
            while player.poll() is None:
                assert time.monotonic() < deadline, 'player exceeded harness deadline'
                data = registry(env)
                streams = nodes(data, 'rog-atmos-')
                assert len(streams) <= 1, 'multiple playback nodes'
                if streams:
                    observed_stream = streams[0]['id']
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
                    # Give the supervisor time to verify links and submit PCM.
                    if linked and not action and name in ('cancel', 'target-loss', 'policy-target-loss'):
                        time.sleep(1)
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
            wait_for(lambda: not nodes(registry(env), 'rog-atmos-'), timeout=5)
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
                    assert first_byte is not None, 'JOC monitor stayed silent'
                    first_frame = first_byte // (len(channels) * 4)
                    offset = (first_frame - JOC_LEADING_ZERO_FRAMES) * len(channels) * 4
                    length = JOC_FRAMES * len(channels) * 4
                    payload = captured[offset:offset + length] if offset >= 0 else b''
                    expected_hash = JOC_PCM_SHA256
                    assert len(payload) == length, 'JOC PCM missing/truncated'
                    assert hashlib.sha256(payload).hexdigest() == expected_hash, 'JOC monitor PCM differs from prior accepted render'
                    assert report['producer']['status'] == 'joc-stream-unqualified'
                    assert report['producer']['object_metadata_consumed'] is True
                    result.update(joc_input_sha256=JOC_SHA256,
                        comparison='prior accepted Cavern full-render PCM; same-engine continuity, not independent fidelity',
                        expected_first_nonzero_frame=JOC_LEADING_ZERO_FRAMES)
                else:
                    anchor = pcm[:min(len(pcm), 4096 * len(channels) * 4)]
                    offset = captured.find(anchor)
                    expected_hash = hashlib.sha256(pcm).hexdigest()
                    assert captured[offset:offset + len(pcm)] == pcm, 'monitor PCM differs or truncates'
                assert offset >= 0 and offset % (len(channels) * 4) == 0, 'PCM start absent/unaligned'
                assert report['submitted_pcm_sha256'] == expected_hash
                result.update(expected_pcm_sha256=expected_hash,
                              captured_pcm_sha256=hashlib.sha256(captured).hexdigest(),
                              captured_bytes=len(captured), payload_offset_frames=offset // (len(channels) * 4),
                              compared_frames=frames, pcm_exact=True)
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
            if capture_handle:
                capture_handle.close()
            stop(manager, group=True)
            stop(daemon)
            daemon_log.close()
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
    args = parser.parse_args()
    if args.case and len(set(args.case)) != len(args.case):
        parser.error('duplicate cases')
    if os.path.lexists(args.report):
        parser.error('report collision')
    if Path('/dev/snd').exists():
        parser.error('hardware device mount forbidden')
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
                    'live-ci.sh', 'live_ci_options.py', 'build.sh', 'source_manifest.json', 'Dockerfile', 'AtmosProbe.csproj',
                    'global.json', '../../tests/test_atmos_live.py', '../../scripts/validate_atmos_live.py')
    def bindings():
        items = {name: hashlib.sha256((Path(__file__).parent / name).read_bytes()).hexdigest()
                 for name in source_files if (Path(__file__).parent / name).is_file()}
        for name in ('AtmosProbe.dll', 'Cavern.dll', 'Cavern.Format.dll', 'atmos-live'):
            items['build/' + name] = hashlib.sha256((args.probe.parent / name).read_bytes()).hexdigest()
        return items
    report['source_before_sha256'] = bindings()
    with tempfile.TemporaryDirectory(prefix='.live-integration-', dir=args.report.parent) as parent:
        for name in selected:
            report['results'].append(one_case(name, args.probe, args.config, Path(parent), args.joc_input))
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
