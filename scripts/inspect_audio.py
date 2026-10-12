#!/usr/bin/env python3
"""Read-only Linux audio inventory; raw output stays in a private capture."""
import argparse
import json
import os
from pathlib import Path
import platform
import re
import selectors
import stat
import subprocess
import time
from audio_common import LIMIT, digest, load_json, read_bytes, schema, write_private, PrivateArgumentParser

STATUSES = {'ok', 'unavailable', 'permission-denied', 'timeout', 'parse-error'}
PROBES = {
    'graph': ['pw-dump'],
    'settings': ['pw-metadata', '-n', 'settings'],
    'pipewire_version': ['pipewire', '--version'],
    'wireplumber_version': ['wireplumber', '--version'],
    'packages': ['dpkg-query', '-W', '-f=${binary:Package}\t${Version}\n', 'pipewire', 'wireplumber', 'libasound2t64', 'alsa-ucm-conf'],
    'playback': ['aplay', '-l'], 'capture': ['arecord', '-l'],
    'kernel': ['journalctl', '-k', '-b', '--no-pager', '-n', '2000'],
    'audio_log': ['journalctl', '--user', '-b', '--no-pager', '-u', 'pipewire', '-u', 'pipewire-pulse', '-u', 'wireplumber', '-n', '1000'],
    'threads': ['ps', '-eLo', 'pid,tid,cls,rtprio,comm'],
}


def problem(status):
    return {'status': status}


def run_command(argv, timeout=5):
    """No shell; bounded output and time; never expose stderr in public output."""
    try:
        proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        return problem('unavailable')
    except PermissionError:
        return problem('permission-denied')
    except OSError:
        return problem('unavailable')
    buffers = [bytearray(), bytearray()]
    deadline = time.monotonic() + timeout
    status = 'ok'
    with selectors.DefaultSelector() as selector:
        selector.register(proc.stdout, selectors.EVENT_READ, 0)
        selector.register(proc.stderr, selectors.EVENT_READ, 1)
        try:
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    status = 'timeout'
                    break
                for key, _ in selector.select(remaining):
                    chunk = os.read(key.fileobj.fileno(), 65536)
                    if not chunk:
                        selector.unregister(key.fileobj)
                    else:
                        buffers[key.data].extend(chunk)
                    if sum(map(len, buffers)) > 4 * 1024 * 1024:
                        status = 'parse-error'
                        break
                if status != 'ok':
                    break
            if status != 'ok':
                proc.kill()
            try:
                proc.wait(timeout=max(.01, deadline-time.monotonic()))
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
                status = 'timeout'
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait()
            proc.stdout.close()
            proc.stderr.close()
    if status != 'ok':
        return problem(status)
    if proc.returncode:
        status = 'permission-denied' if b'Permission denied' in buffers[1] or b'Operation not permitted' in buffers[1] else 'unavailable'
    return {'status': status, 'returncode': proc.returncode,
            'stdout': buffers[0].decode('utf-8', 'replace'),
            'stderr': buffers[1].decode('utf-8', 'replace')}


def file_probe(path):
    try:
        data = read_bytes(path)
        if len(data) > 65536:
            return problem('parse-error')
        return {'status': 'ok', 'sha256': digest(data), 'text': data.decode('utf-8', 'replace')}
    except PermissionError:
        return problem('permission-denied')
    except OSError:
        return problem('unavailable')
    except ValueError:
        return problem('parse-error')


def configs(config_root):
    """Bounded private prior configuration; unknown is never treated as empty."""
    result, visited, byte_count = [], 0, 0
    try:
        if config_root.is_symlink():
            return problem('parse-error')
        for component in ('pipewire', 'wireplumber'):
            root = config_root / component
            if root.is_symlink():
                return problem('parse-error')
            if not root.exists():
                continue
            pending = [root]
            while pending:
                directory = pending.pop()
                with os.scandir(directory) as entries:
                    for entry in entries:
                        visited += 1
                        if visited > 1024 or entry.is_symlink():
                            return problem('parse-error')
                        path = Path(entry.path)
                        if entry.is_dir(follow_symlinks=False):
                            pending.append(path)
                            continue
                        if len(result) >= 256 or entry.stat(follow_symlinks=False).st_size > 65536:
                            return problem('parse-error')
                        probe = file_probe(path)
                        if probe['status'] != 'ok':
                            return probe
                        if probe['sha256'] != digest(probe['text'].encode('utf-8')):
                            return problem('parse-error')
                        byte_count += len(probe['text'].encode('utf-8'))
                        if byte_count > 1024 * 1024:
                            return problem('parse-error')
                        result.append({'path': str(path.relative_to(config_root)), **probe})
        return {'status': 'ok', 'files': sorted(result, key=lambda x:x['path'])}
    except PermissionError:
        return problem('permission-denied')
    except OSError:
        return problem('unavailable')


def collect(runner=run_command, system=None, environment=None, home=None):
    report = {'schema_version': 1, 'kind': 'audio-inventory', 'evidence_kind': 'live-read-only',
              'probes': {}, 'files': {}, 'user_config': {'status': 'unavailable'}}
    if (system or platform.system()) != 'Linux':
        report['collection_status'] = 'unsupported-platform'
        return report
    env = os.environ if environment is None else environment
    runtime = env.get('XDG_RUNTIME_DIR')
    session = False
    try:
        info = Path(runtime).stat() if runtime else None
        session = bool(info and stat.S_ISDIR(info.st_mode) and info.st_uid == os.geteuid() and (Path(runtime)/'pipewire-0').is_socket())
    except OSError:
        pass
    report['collection_status'] = 'ok'
    for name, argv in PROBES.items():
        report['probes'][name] = runner(argv, 5) if name not in ('graph', 'settings') or session else problem('unavailable')
    for path in [Path('/proc/asound/cards'), *sorted(Path('/proc/asound').glob('card*/codec#*'))[:32]]:
        report['files'][str(path)] = file_probe(path)
    config_root = Path(env['XDG_CONFIG_HOME']) if env.get('XDG_CONFIG_HOME') else (Path(home) if home else Path.home()) / '.config'
    report['user_config'] = configs(config_root)
    report['config_root'] = str(config_root)
    return bound_report(report)


def bound_report(report):
    if len((json.dumps(report, indent=2, sort_keys=True) + '\n').encode()) > LIMIT:
        report['collection_status'] = 'partial'
        report['probes'] = {k:problem('parse-error') for k in report['probes']}
        report['files'] = {}
        report['user_config'] = problem('parse-error')
        if 'kernel_log' in report:
            report['kernel_log'] = problem('parse-error')
    return report


def validate_inventory(report):
    schema(report, 'audio-inventory')
    probes = report.get('probes')
    if not isinstance(probes,dict) or not isinstance(report.get('user_config',{}),dict):
        raise ValueError('invalid inventory containers')
    for name in PROBES:
        probe = probes.get(name,{})
        if not isinstance(probe,dict) or not isinstance(probe.get('stdout',''),str):
            raise ValueError('invalid probe')


def graph(report):
    validate_inventory(report)
    probe = report.get('probes', {}).get('graph', {})
    if probe.get('status') != 'ok':
        raise ValueError('graph unavailable')
    data = json.loads(probe['stdout'])
    if not isinstance(data, list) or len(data) > 10000 or not all(isinstance(x, dict) and isinstance(x.get('info', {}), dict) for x in data):
        raise ValueError('invalid graph')
    for item in data:
        info = item.get('info', {})
        if not isinstance(info.get('props', {}), dict) or not isinstance(info.get('params', {}), dict):
            raise ValueError('invalid graph properties')
    return data


def version(report, component):
    validate_inventory(report)
    probe = report.get('probes', {}).get(component + '_version', {})
    if probe.get('status') != 'ok':
        return None
    match = re.search(r'(?:Compiled with lib'+component+r'|Linked with lib'+component+r'|'+component+r')\s+(\d+\.\d+\.\d+)\b', probe.get('stdout', ''))
    return match[1] if match else None


def integer(value, minimum=1, maximum=384000):
    return value if type(value) is int and minimum <= value <= maximum else None


def public_summary(report, source_hash):
    validate_inventory(report)
    result = {'schema_version': 1, 'kind': 'audio-public-summary', 'source_sha256': source_hash,
              'evidence_kind': 'private-offline', 'physical_latency_ms': None,
              'limits': ['snapshot may span hotplug or state transitions', 'graph period is not physical latency',
                         'no audio playback, recording, or configuration activation'],
              'probes': {}, 'versions': {k: version(report,k) for k in ('pipewire','wireplumber')}}
    for name in PROBES:
        status = report.get('probes', {}).get(name, {}).get('status')
        result['probes'][name] = status if status in STATUSES else 'parse-error'
    config = report.get('user_config', {})
    result['user_config'] = {'status': config.get('status') if config.get('status') in STATUSES else 'parse-error'}
    if config.get('status') == 'ok' and isinstance(config.get('files'), list):
        result['user_config']['file_count'] = len(config['files'])
        result['user_config']['sha256'] = sorted(x['sha256'] for x in config['files'] if isinstance(x,dict) and isinstance(x.get('sha256'),str) and re.fullmatch(r'[0-9a-f]{64}', x['sha256']))
    settings = report.get('probes',{}).get('settings',{})
    if settings.get('status') == 'ok':
        result['graph_settings'] = {}
        for key in ('rate','quantum','min-quantum','max-quantum','force-quantum','force-rate'):
            matches = re.findall(r"key:'clock\."+key+r"' value:'(\d+)'",settings.get('stdout',''))
            if len(matches) == 1:
                result['graph_settings'][key.replace('-','_')] = integer(int(matches[0]),0)
    threads = report.get('probes',{}).get('threads',{})
    if threads.get('status') == 'ok':
        result['data_loop_scheduling'] = []
        for line in threads.get('stdout','').splitlines():
            parts = line.split()
            if len(parts) == 5 and re.fullmatch(r'data-loop(?:\.\d+)?',parts[4]) and parts[2] in ('RR','FF','TS','OTHER','DL','B'):
                result['data_loop_scheduling'].append({'class':parts[2], 'rt_priority':int(parts[3]) if parts[3].isdigit() and 0 <= int(parts[3]) <= 99 else None})
    try:
        data = graph(report)
        cores = [x for x in data if x.get('type') == 'PipeWire:Interface:Core']
        if len(cores) == 1:
            props = cores[0].get('info', {}).get('props', {})
            rate = integer(props.get('default.clock.rate'))
            quantum = integer(props.get('default.clock.quantum'))
            result['graph_default'] = {'rate_hz': rate, 'quantum_frames': quantum,
                                      'graph_period_ms': quantum*1000/rate if rate and quantum else None}
        result['endpoints'] = []
        for item in data:
            if item.get('type') != 'PipeWire:Interface:Node':
                continue
            props = item.get('info', {}).get('props', {})
            media = props.get('media.class')
            if media not in ('Audio/Sink', 'Audio/Source', 'Audio/Duplex'):
                continue
            state = item['info'].get('state')
            result['endpoints'].append({'media_class': media, 'channels': integer(props.get('audio.channels'),1,64),
                                        'state': state if state in ('error','creating','suspended','idle','running') else None,
                                        'device_api': props.get('device.api') if props.get('device.api') in ('alsa','bluez5') else None})
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        result['probes']['graph'] = 'parse-error'
    return result


def import_legacy(value):
    """Explicit adapter for the coordinator's private 2026-10-12 snapshot."""
    if not isinstance(value, dict) or not isinstance(value.get('commands'), dict) or 'captured_at' not in value:
        raise ValueError('unsupported legacy capture')
    probes = {}
    for name in PROBES:
        old = value['commands'].get(name, {})
        if not isinstance(old,dict) or not isinstance(old.get('stdout',''),str):
            raise ValueError('invalid legacy probe')
        probes[name] = {'status': 'ok' if old.get('returncode') == 0 else 'unavailable',
                        'stdout': old.get('stdout', '')}
    return {'schema_version': 1, 'kind': 'audio-inventory', 'evidence_kind': 'live-read-only',
            'probes': probes, 'user_config': {'status': 'unavailable'}, 'files': {}}


def main():
    parser = PrivateArgumentParser(description=__doc__)
    parser.add_argument('--output')
    parser.add_argument('--from-capture')
    parser.add_argument('--public-summary')
    parser.add_argument('--legacy-capture', action='store_true')
    parser.add_argument('--kernel-log', help='Optional private pre-captured log; no privilege escalation')
    args = parser.parse_args()
    try:
        if args.from_capture:
            if not args.public_summary or args.output or args.kernel_log:
                raise ValueError('capture mode requires only a summary destination')
            report, sha = load_json(args.from_capture)
            if args.legacy_capture:
                report = import_legacy(report)
            write_private(args.public_summary, public_summary(report, sha))
        else:
            if not args.output or args.public_summary or args.legacy_capture:
                raise ValueError('collection requires a private output')
            report = collect()
            if args.kernel_log:
                report['kernel_log'] = file_probe(args.kernel_log)
            write_private(args.output, bound_report(report))
        return 0
    except (OSError, ValueError, TypeError, KeyError, RecursionError):
        parser.exit(2, 'audio inspection failed: invalid input, unavailable data, or output exists\n')


if __name__ == '__main__':
    raise SystemExit(main())
