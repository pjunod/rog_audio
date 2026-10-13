"""Invented temp-file speaker state and profiler data; no commands or sound."""
import copy
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import inspect_audio_path as path
import speaker_install as speaker
from test_speaker_install import synthetic_bundle, inventory


def top_frame(quantum=256, errors=0, follower_quantum=1024, state='R'):
    header = 'S   ID  QUANT   RATE    WAIT    BUSY   W/Q   B/Q  ERR FORMAT           NAME \n'
    def row(node, q, name, error):
        return f'{state} {node:4} {q:6} {48000:6}  25.0us  50.0us  0.01  0.02  {error:3} {"F32P 2 48000":>16} {name}\n'
    return header+row(42, quantum, 'alsa_output.test.analog-stereo', errors)+row(50, follower_quantum, ' + rog_audio_soe_output_level', errors)


def observed(active=False):
    inv = inventory()
    graph = json.loads(inv['probes']['graph']['stdout'])
    graph[0].update(id=42); graph[0]['info']['state'] = 'running'
    graph[0]['info']['props']['object.serial'] = 142
    graph[1]['id'] = 7; graph[0]['info']['props']['device.id'] = 7
    graph.append({'type': 'PipeWire:Interface:Core', 'id': 0,
                  'info': {'cookie': 12345, 'name': 'synthetic-core', 'version': '1.6.8',
                           'props': {'default.clock.rate': 48000, 'default.clock.quantum': 1024}}})
    if active:
        graph.append({'type': 'PipeWire:Interface:Node', 'id': 50,
                      'info': {'state': 'running', 'props': {'object.serial': 150,
                               'application.id': path.APP, 'node.name': path.FILTER,
                               'node.group': path.GROUP, 'media.role': 'DSP', 'node.latency': '256/48000'},
                               'params': {'ProcessLatency': [{'quantum': 0, 'rate': 0, 'ns': 1000000}]}}})
    inv['probes']['graph']['stdout'] = json.dumps(graph)
    inv['probes']['pipewire_version'] = {'status': 'ok', 'stdout': 'Compiled with libpipewire 1.6.8'}
    inv['probes']['wireplumber_version'] = {'status': 'ok', 'stdout': 'wireplumber 0.5.17'}
    inv['probes']['settings'] = {'status': 'ok', 'stdout': "key:'clock.force-quantum' value:'0'\nkey:'clock.force-rate' value:'0'"}
    return inv


def setup(root):
    root = Path(root).resolve()
    bundle = synthetic_bundle(root/'source')
    binary = root/'binary'; binary.write_bytes(b'synthetic-runtime-never-executed')
    runtime = root/'runtime.json'; runtime.write_bytes(speaker.encoded({
        'schema_version': 1, 'source_commit': '6d9b1220d3dcebb154ba759a05600662bc0af549',
        'routing_contract': 'exact-device-route-v1', 'binary_sha256': speaker.sha(binary.read_bytes())}))
    inv = observed(); kit = root/'kit'; speaker.prepare(bundle, inv, kit, runtime)
    env = {'ROG_AUDIO_STATE_DIR': str(root/'state')}
    locations = speaker.roots(env)
    speaker.install(kit, root/'speaker-snapshot', binary, inv, locations)
    _, manifest = speaker.load_kit(kit)
    for name in manifest['rc_files']:
        destination = locations['config']/name
        if not destination.exists(): destination.write_bytes(b'[synthetic]\nvalue=unchanged\n')
    state = path.state_snapshot(kit, binary, env)
    active = observed(True)
    context = {'status': 'ok', 'current': {}, 'manager': {}, 'unit': {}}
    capture = {'schema_version': 1, 'kind': 'audio-path-capture', 'status': 'captured',
               'evidence_kind': 'synthetic', 'sample_count_requested': 2,
               'inventory': active, 'after': copy.deepcopy(active['probes']),
               'monitor': {'status': 'ok', 'stdout': top_frame()+top_frame(errors=1)},
               'pulse_inputs': {'status': 'ok', 'stdout': '[{"sink":5,"buffer_latency_usec":12000,"sink_latency_usec":5000,"corked":false}]'},
               'pulse_sinks': {'status': 'ok', 'stdout': '[{"name":"rog_audio_speaker_sink","index":5}]'},
               'speaker_before': state, 'speaker_after': copy.deepcopy(state),
               'process_environment': {'status': 'ok', 'values': {}},
               'process_environment_after': {'status': 'ok', 'values': {}},
               'restart_environment': context, 'restart_environment_after': copy.deepcopy(context)}
    return kit, binary, env, inv, capture
