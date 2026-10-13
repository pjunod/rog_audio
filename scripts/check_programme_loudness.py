#!/usr/bin/env python3
"""Exercise bounded programme gain in the real runtime on a device-free graph.

Each model selector runs independently after review. Generated PCM, private
PipeWire/WirePlumber and D-Bus only; no laptop devices or session sockets.
"""
import argparse
import array
import copy
import json
import math
import os
from pathlib import Path
import selectors
import struct
import subprocess
import sys
import threading
import time
import uuid

from check_speaker_graph import Graph, GraphError
import programme_loudness as programme
import speaker_install as kit


class Signal:
    """Keep one source alive across silence and programme-level transitions."""
    def __init__(self, child):
        self.child = child
        self.amplitude = .005
        self.stop = threading.Event()
        self.error = None
        self.thread = threading.Thread(target=self.write, daemon=True)
        self.thread.start()

    def write(self):
        phase = 0
        try:
            while not self.stop.is_set():
                amplitude = self.amplitude
                samples = []
                for _ in range(480):
                    value = amplitude*math.sin(2*math.pi*1000*(phase % 48000)/48000)
                    samples.extend((value, value*.5)); phase += 1
                self.child.stdin.write(struct.pack('<960f', *samples))
                self.child.stdin.flush()
        except (OSError, ValueError) as error:
            if not self.stop.is_set():
                self.error = type(error).__name__

    def close(self, graph):
        self.stop.set()
        graph.stop(self.child)
        self.thread.join(timeout=5)
        if self.thread.is_alive():
            raise GraphError('owned PCM writer did not stop')


def levels(path):
    values = array.array('f'); values.frombytes(path.read_bytes())
    if sys.byteorder != 'little': values.byteswap()
    if len(values) < 9600 or len(values) % 2:
        raise GraphError('incomplete generated stereo capture')
    if any(not math.isfinite(value) for value in values):
        raise GraphError('nonfinite generated output')
    channels = [values[0::2], values[1::2]]
    return {'rms': [math.sqrt(sum(float(x)*x for x in channel)/len(channel)) for channel in channels],
            'peak': max(abs(x) for x in values), 'frames': len(values)//2}


def relative(measurement, baseline):
    if min(baseline['rms']) <= 0 or min(measurement['rms']) <= 0:
        raise GraphError('silent gain comparison')
    return [20*math.log10(a/b) for a, b in zip(measurement['rms'], baseline['rms'])]


def acceptance(kit_path, case, output, binary, mock, player):
    output = kit.exclusive_directory(output)
    root, manifest = kit.load_kit(kit_path)
    subsystem = {'asus-programme': '10431c63', 'lenovo-programme': '17aa2276'}[case]
    source = json.loads(kit.read(root/'speaker-source/preset.json'))
    settings = kit.document(root/'speaker-source/manifest.json').get('programme_loudness')
    if manifest['hardware']['subsystem'] != subsystem or not settings:
        raise GraphError('wrong model or absent programme bundle')
    if manifest['runtime'].get('programme_loudness_contract') != programme.CONTRACT:
        raise GraphError('runtime lacks native makeup contract')
    if kit.sha(kit.speaker.read_file(Path(binary), limit=64*1024*1024)) != manifest['runtime']['binary_sha256']:
        raise GraphError('candidate binary mismatch')
    if Path('/dev/snd').exists():
        raise GraphError('requires a device-free container')
    state = output/'state'; runtime = output/'runtime'; runtime.mkdir(mode=0o700)
    environment = dict(os.environ, ROG_AUDIO_STATE_DIR=str(state), XDG_RUNTIME_DIR=str(runtime),
                       PIPEWIRE_RUNTIME_DIR=str(runtime), PIPEWIRE_REMOTE='rog-programme-'+uuid.uuid4().hex[:12],
                       XDG_CONFIG_HOME=str(state/'config'), XDG_DATA_HOME=str(state/'data'),
                       XDG_CACHE_HOME=str(state/'cache'), XDG_STATE_HOME=str(state/'session'),
                       QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                       QT_LOGGING_RULES='easyeffects.debug=true')
    for key in ('PIPEWIRE_CONFIG_DIR', 'PIPEWIRE_CONFIG_NAME', 'PULSE_SINK', 'PULSE_SOURCE'):
        environment.pop(key, None)
    locations = kit.roots(environment)
    for name in manifest['files']:
        target = locations['data']/name.split('/', 1)[1]
        kit.mkdir(target.parent); kit.replace(target, kit.read(root/name))
    config = locations['config']/'db/easyeffectsrc'
    kit.mkdir(config.parent); kit.replace(config, kit.settings(b'', manifest))
    conf = state/'config/pipewire/pipewire.conf.d/99-private.conf'; kit.mkdir(conf.parent)
    conf.write_text('context.properties = { core.name = "'+environment['PIPEWIRE_REMOTE']+'" }\n')
    graph = Graph(output, environment); signal = None; captures = {}; assertions = []
    node_name = manifest['binding']['node_name']

    def preset(name, cap=None, bypass=False):
        data = copy.deepcopy(source)
        data['output']['autogain#0'].update({'target': -12.0, 'bypass': bypass})
        if cap is not None: data['output']['autogain#0']['maximum-gain'] = cap
        kit.replace(locations['data']/('output/'+name+'.json'), kit.encoded(data))
        graph.call([binary, '--load-preset', name])
        graph.until(lambda _: graph.preset(binary) == name)

    def capture(name, seconds=.5, transition=None):
        graph.stage = name
        child = graph.start(name, [player, '--capture', node_name, str(output/(name+'.raw'))])
        graph.until(lambda g: graph.linked(g, node_name, 'rog-synthetic-capture'))
        if transition is not None: signal.amplitude = transition
        time.sleep(seconds); graph.stop(child)
        measurement = levels(output/(name+'.raw')); captures[name] = measurement
        if signal.error: raise GraphError('owned PCM writer failed')
        return measurement

    try:
        graph.start('pipewire', ['pipewire']); graph.until(lambda _: True)
        graph.start('wireplumber', ['wireplumber'])
        device = graph.start('mock-device', [mock], pipe=True)
        selector = selectors.DefaultSelector(); selector.register(device.stdout, selectors.EVENT_READ)
        if not selector.select(15): raise GraphError('synthetic device did not export')
        line = device.stdout.readline().decode().strip(); selector.close()
        if not line.startswith('device '): raise GraphError('invalid synthetic device binding')
        device_id = int(line.split()[1])
        graph.call(['pw-cli', 'create-node', 'adapter', json.dumps({
            'factory.name': 'support.null-audio-sink', 'node.name': node_name,
            'node.description': 'Synthetic programme sink', 'media.class': 'Audio/Sink',
            'audio.position': ['FL', 'FR'], 'object.linger': True,
            'device.id': device_id, 'card.profile.device': 0, 'device.api': 'alsa'})])
        physical = graph.until(lambda g: graph.node(g, node_name))
        graph.call(['wpctl', 'set-default', str(physical['id'])])
        app = graph.start('easyeffects', [binary, '--hide-window', '--service-mode'])
        graph.until(lambda g: graph.node(g, 'rog_audio_speaker_sink'))
        graph.until(lambda _: graph.preset(binary) == manifest['preset_name'])
        source_child = graph.start('programme-source', [
            'pw-cat', '--playback', '--rate', '48000', '--channels', '2', '--format', 'f32',
            '--target', 'rog_audio_speaker_sink', '--properties', 'node.name=rog-programme-source', '-'], pipe=True)
        signal = Signal(source_child)
        graph.until(lambda g: graph.linked(g, 'rog-programme-source', 'rog_audio_speaker_sink'))
        log = output/'easyeffects.log'
        deadline = time.monotonic()+15
        while time.monotonic() < deadline and 'kernel correctly loaded' not in log.read_text(errors='replace'):
            time.sleep(.05)
        if 'kernel correctly loaded' not in log.read_text(errors='replace'):
            raise GraphError('real convolver did not load original IR')
        expected = {n.split('#')[0] for n in source['output']['plugins_order']}
        actual = {x.get('info', {}).get('props', {}).get('node.name', '').removeprefix('rog_audio_soe_')
                  for x in graph.dump() if x['type'] == 'PipeWire:Interface:Node'}
        if not expected <= actual: raise GraphError('real model plugin chain missing')
        assertions.append('exact model IR and plugin chain loaded with unchanged voicing')
        preset('programme-baseline', bypass=True); time.sleep(1)
        baseline = capture('baseline')
        cap = settings['maximum_gain_db']
        preset('programme-model-cap', cap=cap); time.sleep(4)
        raised = capture('model-cap'); gains = relative(raised, baseline)
        if any(abs(value-cap) > .35 for value in gains):
            raise GraphError('actual automatic gain did not reach its model cap')
        if abs(gains[0]-gains[1]) > .08:
            raise GraphError('programme gain changed stereo balance')
        assertions.extend(['native preset consumes model maximum-gain', 'shared automatic gain preserves stereo balance'])
        # Same process and source remain alive; an old retained high gain cannot
        # exceed a newly selected zero-makeup cap while smoothing catches up.
        preset('programme-zero-cap', cap=0); time.sleep(.15)
        lowered = capture('lowered-cap')
        if any(value > .25 or value < -.25 for value in relative(lowered, baseline)):
            raise GraphError('retained gain survived a lower selected cap')
        assertions.append('lower cap clamps retained native gain in the same process')
        preset('programme-three-cap', cap=3); time.sleep(3)
        steady = capture('three-cap')
        if any(abs(value-3) > .35 for value in relative(steady, baseline)):
            raise GraphError('ordinary gain control did not settle')
        signal.amplitude = 0; time.sleep(1.2)
        silent = capture('silence')
        if silent['peak'] > .00001: raise GraphError('silence output was not finite and silent')
        capture('after-silence-early', seconds=1.2, transition=.005)
        # Locate the actual output onset, rather than assuming a pipe/source
        # transition is immediate. Skip 50 ms of FIR onset and measure 100 ms.
        raw = array.array('f'); raw.frombytes((output/'after-silence-early.raw').read_bytes())
        if sys.byteorder != 'little': raw.byteswap()
        threshold = baseline['rms'][0]*.4
        onset = next((i for i in range(0, len(raw), 2) if abs(raw[i]) > threshold), None)
        if onset is None or onset+14400 > len(raw):
            raise GraphError('quiet source onset missing from post-silence capture')
        window = raw[onset+4800:onset+14400]
        early = {'rms': [math.sqrt(sum(float(x)*x for x in window[c::2])/4800) for c in (0, 1)]}
        captures['post_silence_early_gain_db'] = relative(early, baseline)
        if any(value >= 2.8 for value in relative(early, baseline)):
            raise GraphError('pre-silence makeup retained across silent programme boundary')
        time.sleep(3)
        recovered = capture('after-silence-recovered')
        if any(abs(value-3) > .35 for value in relative(recovered, baseline)):
            raise GraphError('makeup did not recover after silence reset')
        assertions.append('silence resets retained makeup and normal recovery remains bounded')
        loud = capture('louder-programme-transition', seconds=1, transition=.95)
        if loud['peak'] > math.pow(10, -1/20)+.02:
            raise GraphError('final minus-one-dB limiter failed loud-source transition')
        time.sleep(1)
        late_loud = capture('louder-programme-settled')
        if min(late_loud['rms']) <= min(baseline['rms'])*10:
            raise GraphError('louder source transition never reached the output')
        if late_loud['peak'] > math.pow(10, -1/20)+.02:
            raise GraphError('final limiter failed settled loud programme')
        assertions.append('louder programme transition remains finite behind original final limiter')
        if app.poll() is not None: raise GraphError('processor exited during source/cap transitions')
        for name, digest in manifest['files'].items():
            if kit.sha(kit.read(locations['data']/name.split('/', 1)[1])) != digest:
                raise GraphError('graph case changed original kit or impulse payload')
        assertions.append('original preset/IR/autoload payload unchanged; one processor lifetime')
        receipt = {'schema_version': 1, 'case': case, 'status': 'passed',
                   'evidence_kind': 'isolated-synthetic-runtime',
                   'binary_sha256': manifest['runtime']['binary_sha256'],
                   'speaker_bundle_manifest_sha256': manifest['speaker_bundle_manifest_sha256'],
                   'programme_loudness_contract': programme.CONTRACT,
                   'model_maximum_gain_db': cap, 'measured_model_gain_db': gains,
                   'captures': captures, 'assertions': assertions,
                   'physical_device_or_session_access': False,
                   'acoustic_or_physical_latency_measurement': False}
        kit.replace(output/'receipt.json', kit.encoded(receipt)); return receipt
    finally:
        try:
            if sys.exc_info()[0] is not None:
                try: kit.replace(output/'failure-graph.json', kit.encoded(graph.dump()))
                except (GraphError, ValueError, subprocess.TimeoutExpired): pass
        finally:
            try:
                if signal: signal.close(graph)
            finally: graph.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=('asus-programme', 'lenovo-programme'), required=True)
    parser.add_argument('--kit', required=True); parser.add_argument('--output', required=True)
    parser.add_argument('--binary', default='/opt/rog-audio/easyeffects/bin/easyeffects')
    parser.add_argument('--mock-device', default='/opt/rog-audio/mock-device')
    parser.add_argument('--player', default='/opt/rog-audio/synthetic-player')
    parser.add_argument('--private-dbus', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if not args.private_dbus:
        return subprocess.run(['dbus-run-session', '--', sys.executable, str(Path(__file__).resolve()),
                               *(sys.argv[1:] if argv is None else argv), '--private-dbus']).returncode
    try:
        result = acceptance(args.kit, args.case, args.output, args.binary, args.mock_device, args.player)
        print(json.dumps({'case': args.case, 'status': result['status'], 'assertion_count': len(result['assertions'])})); return 0
    except (GraphError, kit.InstallError, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        try:
            if kit.safe(args.output).is_dir():
                kit.replace(Path(args.output)/'failure.json', kit.encoded({
                    'case': args.case, 'exception': type(error).__name__, 'detail': str(error)}))
        except (kit.InstallError, OSError): pass
        print(json.dumps({'case': args.case, 'status': 'failed', 'reason': 'programme_graph_acceptance_failed'})); return 1


if __name__ == '__main__': raise SystemExit(main())
