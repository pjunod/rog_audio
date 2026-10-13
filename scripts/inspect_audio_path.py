#!/usr/bin/env python3
"""Observe a Linux speaker path without starting audio or changing its graph."""
import configparser
import json
import math
import os
from pathlib import Path
import platform
import re
import shlex
import stat
import time

from audio_common import PrivateArgumentParser, digest, load_json, schema, unique, write_private
import inspect_audio as inventory
import speaker_install as speaker

APP = 'org.rog_audio.SpeakerEffects'
FILTER = 'rog_audio_soe_output_level'
GROUP = 'rog_audio_speaker_sink_group'
PLUGINS = {'convolver', 'limiter', 'multiband_compressor', 'equalizer', 'spectrum', 'output_level'}
OVERRIDES = ('PIPEWIRE_LATENCY', 'PIPEWIRE_QUANTUM', 'PIPEWIRE_PROPS',
             'PIPEWIRE_RATE', 'PIPEWIRE_CONFIG_DIR', 'PIPEWIRE_CONFIG_NAME')
HEADER = 'S ID QUANT RATE WAIT BUSY W/Q B/Q ERR FORMAT NAME'
ROW = re.compile(r'^([ECSIRtT!])\s+(\d+)\s+(\d+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\d+) (.{16}) (.*)$')


def finite(value, maximum=1e12):
    return value if type(value) in (int, float) and math.isfinite(value) and 0 <= value <= maximum else None


def json_text(text):
    return json.loads(text, object_pairs_hook=unique,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite')))


def parse_time(value):
    if value in ('---', '+++'):
        return None
    match = re.fullmatch(r'(\d+(?:\.\d+)?)(us|ms|s)', value)
    if not match:
        raise ValueError('unknown monitor time')
    result = float(match[1]) * {'us': .001, 'ms': 1, 's': 1000}[match[2]]
    if finite(result) is None:
        raise ValueError('invalid monitor time')
    return result


def ratio(value):
    if value in ('---', '+++', '???'):
        return None
    if not re.fullmatch(r'\d+(?:\.\d+)?', value) or finite(float(value)) is None:
        raise ValueError('unknown monitor ratio')
    return float(value)


def parse_top(text):
    """Pinned 1.6.8 batch format: fixed 16-column FORMAT; names stay private."""
    frames = []
    current = None
    driver = None
    for line in text.splitlines():
        if not line.strip():
            continue
        if ' '.join(line.split()) == HEADER:
            current = []; frames.append(current); driver = None
            continue
        match = ROW.fullmatch(line)
        if current is None or not match:
            raise ValueError('unsupported monitor output')
        state, node, quantum, rate, wait, busy, wq, bq, errors, fmt, name = match.groups()
        node, quantum, rate, errors = map(int, (node, quantum, rate, errors))
        if node > 2**32-1 or quantum > 1048576 or rate > 768000 or errors > 2**32-1:
            raise ValueError('monitor bounds')
        if any(row['node_id'] == node for row in current):
            raise ValueError('duplicate monitor node')
        follower = name.startswith((' + ', ' = '))
        asynchronous = name.startswith(' = ')
        if follower and driver is None:
            raise ValueError('follower without driver')
        if not follower:
            driver = node
        current.append({'node_id': node, 'driver_id': driver,
                        'role': 'follower' if follower else 'driver',
                        'async': asynchronous, 'state': state,
                        'quantum_frames': quantum, 'rate_hz': rate,
                        'period_ms': quantum*1000/rate if quantum and rate else None,
                        'wait_ms': parse_time(wait), 'busy_ms': parse_time(busy),
                        'wait_ratio': ratio(wq), 'busy_ratio': ratio(bq),
                        'errors': errors, 'format': fmt.strip(),
                        'name': name[3:] if follower else name})
    if not frames or len(frames) > 30:
        raise ValueError('missing or excessive monitor samples')
    return frames


def state_snapshot(kit_path, runtime, environment=None):
    """Retain hashes and private preimages, without copying raw binary bytes."""
    root, kit = speaker.load_kit(kit_path)
    locations = speaker.roots(environment)
    binary = speaker.speaker.read_file(Path(runtime), limit=64*1024*1024)
    if speaker.sha(binary) != kit['runtime']['binary_sha256']:
        raise ValueError('runtime mismatch')
    files = {}
    for name, expected in kit['files'].items():
        current = locations['data']/name.split('/', 1)[1]
        value = speaker.file_record(current)
        files[name] = value
        if value.get('sha256') != expected:
            raise ValueError('installed payload mismatch')
    rc = {name: speaker.file_record(locations['config']/name) for name in kit['rc_files']}
    if not all(value['exists'] for value in rc.values()):
        raise ValueError('runtime settings unavailable')
    config = locations['config']/'db/easyeffectsrc'
    parser = configparser.ConfigParser(interpolation=None); parser.optionxform = str
    parser.read_string(speaker.read(config).decode('utf-8'))
    required = {'outputDevice': kit['binding']['node_name'],
                'speakerCorrectionDevice': kit['binding']['node_name'],
                'speakerCorrectionRoute': kit['binding']['route_name'],
                'useDefaultOutputDevice': 'false'}
    if any(parser.get('StreamOutputs', k, fallback=None) != v for k, v in required.items()):
        raise ValueError('speaker route settings changed')
    state = locations['config'].parent.parent
    return {'kit_sha256': speaker.sha(speaker.read(root/'kit.json')),
            'binary_sha256': speaker.sha(binary), 'binding': kit['binding'],
            'payload': files, 'rc': rc, 'state_root': str(state),
            'pipewire_config': speaker.tree(state/'config/pipewire')}


def process_environment(runtime_binary, environment=None):
    env = os.environ if environment is None else environment
    runtime = env.get('XDG_RUNTIME_DIR')
    if not runtime:
        return {'status': 'unavailable'}
    try:
        lines = speaker.read(Path(runtime)/'rog-audio-speaker-effects.lock').splitlines()
        if not lines or not re.fullmatch(rb'[1-9][0-9]{0,9}', lines[0]):
            return {'status': 'parse-error'}
        pid = int(lines[0])
        if Path(os.readlink(Path('/proc')/str(pid)/'exe')) != Path(runtime_binary).absolute():
            return {'status': 'unavailable'}
        # Read only this candidate's existing process, not arbitrary processes.
        # procfs reports st_size=0 even when content exists. The regular-file
        # artifact reader correctly rejects that mismatch, so use a bounded
        # reader only for this fixed procfs endpoint, never an arbitrary path.
        descriptor = os.open(Path('/proc')/str(pid)/'environ', os.O_RDONLY|os.O_NONBLOCK|getattr(os, 'O_NOFOLLOW', 0))
        try:
            info = os.fstat(descriptor)
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid():
                return {'status': 'unavailable'}
            data = bytearray()
            while len(data) <= 65536:
                part = os.read(descriptor, 65537-len(data))
                if not part: break
                data.extend(part)
            if len(data) > 65536:
                return {'status': 'parse-error'}
        finally: os.close(descriptor)
        if Path(os.readlink(Path('/proc')/str(pid)/'exe')) != Path(runtime_binary).absolute():
            return {'status': 'unavailable'}
        selected = {}
        for field in data.split(b'\0'):
            key, separator, value = field.partition(b'=')
            if separator and key.decode('utf-8', 'replace') in OVERRIDES:
                if key.decode() in selected:
                    return {'status': 'parse-error'}
                selected[key.decode()] = value.decode('utf-8', 'strict')
        return {'status': 'ok', 'values': selected}
    except (OSError, UnicodeError, speaker.InstallError, speaker.speaker.ProfileError):
        return {'status': 'unavailable'}



def override_context(runner=inventory.run_command, environment=None):
    """Selected current/manager/unit variables only; arbitrary values stay out."""
    env = os.environ if environment is None else environment
    result = {'current': {k: env[k] for k in OVERRIDES if k in env}}
    manager = runner(['systemctl', '--user', 'show-environment'], 5)
    unit = runner(['systemctl', '--user', 'show', 'rog-audio-speaker.service',
                   '--property=Environment,EnvironmentFiles'], 5)
    if manager.get('status') != 'ok' or unit.get('status') != 'ok':
        result['status'] = 'unavailable'; return result
    selected = {}
    for line in manager.get('stdout', '').splitlines():
        key, separator, value = line.partition('=')
        if separator and key in OVERRIDES:
            selected[key] = value
    result['manager'] = selected
    properties = {}
    for line in unit.get('stdout', '').splitlines():
        key, separator, value = line.partition('=')
        if separator and key in ('Environment', 'EnvironmentFiles'):
            if key in properties:
                result['status'] = 'parse-error'; return result
            properties[key] = value
    if set(properties) != {'Environment', 'EnvironmentFiles'} or properties['EnvironmentFiles']:
        result['status'] = 'unavailable'; return result
    selected = {}
    try:
        for field in shlex.split(properties['Environment']):
            key, separator, value = field.partition('=')
            if separator and key in OVERRIDES:
                selected[key] = value
    except ValueError:
        result['status'] = 'parse-error'; return result
    result['unit'] = selected
    result['status'] = 'ok'
    return result


def collect(kit_path, runtime, samples=3, runner=inventory.run_command,
            system=None, environment=None):
    if type(samples) is not int or not 2 <= samples <= 30:
        raise ValueError('sample count')
    if (system or platform.system()) != 'Linux':
        return {'schema_version': 1, 'kind': 'audio-path-capture',
                'evidence_kind': 'live-read-only', 'status': 'unsupported-platform'}
    first = time.monotonic_ns()
    before_state = state_snapshot(kit_path, runtime, environment)
    before_environment = process_environment(runtime, environment)
    restart_environment = override_context(runner, environment)
    before = inventory.collect(runner=runner, system='Linux', environment=environment)
    # Reuse inventory's bounded runner: no setters, shell, sound streams or services.
    top = runner(['pw-top', '-b', '-n', str(samples)], samples+8)
    pulse = runner(['pactl', '-f', 'json', 'list', 'sink-inputs'], 5)
    pulse_sinks = runner(['pactl', '-f', 'json', 'list', 'sinks'], 5)
    after = {'graph': runner(['pw-dump'], 5),
             'settings': runner(['pw-metadata', '-n', 'settings'], 5)}
    after_state = state_snapshot(kit_path, runtime, environment)
    return {'schema_version': 1, 'kind': 'audio-path-capture',
            'evidence_kind': 'live-read-only', 'status': 'captured',
            'monotonic_start_ns': first, 'monotonic_end_ns': time.monotonic_ns(),
            'sample_count_requested': samples, 'inventory': before,
            'after': after, 'monitor': top, 'pulse_inputs': pulse, 'pulse_sinks': pulse_sinks,
            'speaker_before': before_state, 'speaker_after': after_state,
            'process_environment': before_environment,
            'process_environment_after': process_environment(runtime, environment),
            'restart_environment': restart_environment,
            'restart_environment_after': override_context(runner, environment),
            'limits': ['sequential snapshots are not an atomic graph trace',
                       'host monotonic timestamps are not cross-device audio clocks',
                       'no playback, recording, activation or service change']}


def after_inventory(capture):
    result = dict(capture['inventory']); result['probes'] = dict(result['probes'])
    result['probes'].update(capture['after'])
    return result


def identity(graph):
    result = {}
    for item in graph:
        if item.get('type') != 'PipeWire:Interface:Node' or type(item.get('id')) is not int:
            continue
        if item['id'] in result:
            raise ValueError('duplicate graph identity')
        serial = item.get('info', {}).get('props', {}).get('object.serial')
        result[item['id']] = serial if type(serial) is int and 0 <= serial <= 2**64-1 else None
    return result


def core_identity(graph):
    cores = [x.get('info', {}) for x in graph if x.get('type') == 'PipeWire:Interface:Core']
    if len(cores) != 1 or type(cores[0].get('cookie')) is not int:
        return None
    return {key: cores[0].get(key) for key in ('cookie', 'name', 'version')}


def hashed_state(value):
    if not isinstance(value, dict):
        raise ValueError('invalid speaker state')
    for key in ('binary_sha256', 'kit_sha256'):
        if not isinstance(value.get(key), str) or not speaker.DIGEST.fullmatch(value[key]):
            raise ValueError('invalid digest')
    for key in ('payload', 'rc'):
        if not isinstance(value.get(key), dict) or not 1 <= len(value[key]) <= 32:
            raise ValueError('invalid file scope')
        for record in value[key].values():
            if not isinstance(record, dict) or not isinstance(record.get('sha256'), str) or not speaker.DIGEST.fullmatch(record['sha256']):
                raise ValueError('invalid file digest')
    return value


def components(graph, binding):
    result = []
    for node in graph:
        props = node.get('info', {}).get('props', {})
        name = props.get('node.name', '')
        if node.get('type') != 'PipeWire:Interface:Node':
            continue
        if name == binding['node_name']:
            role = 'physical-output'
        elif props.get('application.id') == APP and isinstance(name, str) and name.startswith('rog_audio_soe_'):
            role = 'speaker-dsp'
        else:
            continue
        values = node.get('info', {}).get('params', {}).get('ProcessLatency', [])
        if not isinstance(values, list) or len(values) > 32:
            raise ValueError('invalid latency components')
        for value in values:
            if not isinstance(value, dict):
                raise ValueError('invalid latency object')
            quantum, rate, ns = (finite(value.get(k)) for k in ('quantum', 'rate', 'ns'))
            plugin = name.removeprefix('rog_audio_soe_')
            result.append({'role': role, 'plugin': plugin if plugin in PLUGINS else None,
                           'quantum_periods': quantum,
                           'rate_frames': rate, 'ns': ns,
                           'constant_ms': ns/1e6 if ns is not None else None})
    return result


def summary(capture, source_hash):
    schema(capture, 'audio-path-capture')
    if not isinstance(source_hash, str) or not speaker.DIGEST.fullmatch(source_hash):
        raise ValueError('invalid capture digest')
    if capture.get('evidence_kind') not in ('live-read-only', 'synthetic'):
        raise ValueError('unknown capture evidence')
    result = {'schema_version': 1, 'kind': 'audio-path-summary',
              'evidence_kind': 'synthetic-software-path' if capture['evidence_kind'] == 'synthetic' else 'reported-software-path', 'source_sha256': source_hash,
              'physical_latency_ms': None, 'end_to_end_latency_ms': None,
              'limits': ['driver period, DSP declarations and client queues are separate',
                         'no additive physical or end-to-end estimate',
                         'short observation cannot establish a 60-minute stability result']}
    if capture.get('status') == 'unsupported-platform':
        result['status'] = 'unsupported-platform'; return result
    before = inventory.graph(capture['inventory'])
    after = inventory.graph(after_inventory(capture))
    first, last = identity(before), identity(after)
    state = hashed_state(capture['speaker_before']); hashed_state(capture['speaker_after'])
    binding = state['binding']
    node_indexes = {node: index for index, node in enumerate(sorted(first))}
    result['versions'] = {k: inventory.version(capture['inventory'], k) for k in ('pipewire', 'wireplumber')}
    result['core_identity_consistent'] = core_identity(before) is not None and core_identity(before) == core_identity(after)
    result['speaker_state_consistent'] = state == capture['speaker_after']
    result['binary_sha256'] = state['binary_sha256']
    result['kit_sha256'] = state['kit_sha256']
    result['payload_sha256'] = sorted(v['sha256'] for v in state['payload'].values())
    result['rc_sha256'] = sorted(v['sha256'] for v in state['rc'].values())
    try:
        route_before = speaker.observed_route(capture['inventory'], binding)
        route_after = speaker.observed_route(after_inventory(capture), binding)
        result['route_consistent'] = route_before == route_after == binding
    except (speaker.InstallError, ValueError, KeyError, TypeError):
        result['route_consistent'] = False
    result['reported_process_latency'] = components(after, binding)
    filters = [n for n in after if n.get('type') == 'PipeWire:Interface:Node' and all(n.get('info', {}).get('props', {}).get(k) == v for k, v in (('application.id', APP), ('node.name', FILTER), ('node.group', GROUP), ('media.role', 'DSP')))]
    result['filter_request'] = {'match_count': len(filters), 'numerator_frames': None, 'denominator_rate_hz': None}
    if len(filters) == 1:
        request = filters[0]['info']['props'].get('node.latency')
        fraction = re.fullmatch(r'([0-9]{1,7})/([0-9]{1,6})', request) if isinstance(request, str) else None
        if fraction and 1 <= int(fraction[1]) <= 1048576 and 1 <= int(fraction[2]) <= 768000:
            result['filter_request'].update(numerator_frames=int(fraction[1]), denominator_rate_hz=int(fraction[2]))
    result['monitor_status'] = capture['monitor'].get('status') if capture['monitor'].get('status') in inventory.STATUSES else 'parse-error'
    result['samples'] = []
    result['error_deltas'] = []
    if result['monitor_status'] == 'ok':
        try:
            frames = parse_top(capture['monitor']['stdout'])
            if not result['core_identity_consistent']:
                raise ValueError('graph session changed or unknown')
            if len(frames) != capture['sample_count_requested']:
                raise ValueError('incomplete monitor samples')
            for number, rows in enumerate(frames):
                # Driver must exist with the same serial in both snapshots;
                # absent/reused IDs cannot turn a request into a driver receipt.
                relevant = {r['driver_id'] for r in rows if r['node_id'] in first and
                            first.get(r['node_id']) is not None and first.get(r['node_id']) == last.get(r['node_id']) and
                            any(n.get('id') == r['node_id'] and n.get('info', {}).get('props', {}).get('node.name') == binding['node_name'] for n in before)}
                sample = []
                for row in rows:
                    if row['driver_id'] not in relevant or first.get(row['node_id']) is None or first.get(row['node_id']) != last.get(row['node_id']):
                        continue
                    sample.append({'node_index': node_indexes[row['node_id']], **{k: row[k] for k in ('role', 'async', 'state', 'quantum_frames', 'rate_hz', 'period_ms', 'wait_ms', 'busy_ms', 'wait_ratio', 'busy_ratio', 'errors')}})
                result['samples'].append({'sample_index': number, 'nodes': sample})
            for index in sorted({r['node_index'] for s in result['samples'] for r in s['nodes']}):
                rows = [r for s in result['samples'] for r in s['nodes'] if r['node_index'] == index and r['state'] in ('R', 't', 'T') and r['wait_ms'] is not None and r['busy_ms'] is not None]
                counts = [r['errors'] for r in rows]
                continuous = len(rows) == len(frames)
                monotone = all(a <= b for a, b in zip(counts, counts[1:]))
                result['error_deltas'].append({'node_index': index,
                                               'errors_delta': counts[-1]-counts[0] if continuous and monotone else None,
                                               'status': 'observed' if continuous and monotone else 'incomplete-or-reset'})
        except (ValueError, KeyError, TypeError):
            result['monitor_status'] = 'parse-error'; result['samples'] = []
    result['pulse_status'] = capture['pulse_inputs'].get('status') if capture['pulse_inputs'].get('status') in inventory.STATUSES else 'parse-error'
    result['pulse_queues'] = []
    if result['pulse_status'] == 'ok':
        try:
            if capture.get('pulse_sinks', {}).get('status') != 'ok':
                raise ValueError('pulse sink mapping unavailable')
            sinks = json_text(capture['pulse_sinks']['stdout'])
            if not isinstance(sinks, list) or len(sinks) > 1024:
                raise ValueError('invalid pulse sinks')
            selected = {}
            for sink in sinks:
                if not isinstance(sink, dict):
                    raise ValueError('invalid pulse sink')
                if sink.get('name') in (binding['node_name'], 'rog_audio_speaker_sink') and type(sink.get('index')) is int:
                    if sink['index'] in selected:
                        raise ValueError('duplicate pulse sink mapping')
                    selected[sink['index']] = 'candidate' if sink['name'] == 'rog_audio_speaker_sink' else 'physical'
            values = json_text(capture['pulse_inputs']['stdout'])
            if not isinstance(values, list) or len(values) > 1024:
                raise ValueError('invalid pulse list')
            for value in values:
                if not isinstance(value, dict):
                    raise ValueError('invalid pulse item')
                if type(value.get('sink')) is not int or value['sink'] not in selected:
                    continue
                result['pulse_queues'].append({'route_role': selected[value['sink']],
                                              'buffer_latency_usec': finite(value.get('buffer_latency_usec')),
                                              'sink_latency_usec': finite(value.get('sink_latency_usec')),
                                              'corked': value.get('corked') if type(value.get('corked')) is bool else None})
        except (ValueError, TypeError, KeyError):
            result['pulse_status'] = 'parse-error'; result['pulse_queues'] = []
    result['status'] = 'summarised'
    result['running_driver_observed'] = any(r['role'] == 'driver' and r['state'] in ('R', 't', 'T') and r['quantum_frames'] > 0 and r['rate_hz'] > 0 for s in result['samples'] for r in s['nodes'])
    return result


def main():
    parser = PrivateArgumentParser(description=__doc__)
    parser.add_argument('--from-capture'); parser.add_argument('--public-summary')
    parser.add_argument('--kit'); parser.add_argument('--runtime'); parser.add_argument('--output')
    parser.add_argument('--samples', type=int, default=3)
    args = parser.parse_args()
    try:
        if args.from_capture:
            if not args.public_summary or args.output or args.kit or args.runtime:
                raise ValueError('argument combination')
            capture, sha = load_json(args.from_capture)
            write_private(args.public_summary, summary(capture, sha))
        else:
            if not args.kit or not args.runtime or not args.output or args.public_summary:
                raise ValueError('argument combination')
            os.environ['LC_ALL'] = 'C'
            write_private(args.output, collect(args.kit, args.runtime, args.samples))
        return 0
    except (OSError, ValueError, TypeError, KeyError, RecursionError, configparser.Error,
            speaker.InstallError, speaker.speaker.ProfileError):
        parser.exit(2, 'audio path unavailable: invalid input, capability or destination\n')


if __name__ == '__main__':
    raise SystemExit(main())
