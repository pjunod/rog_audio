#!/usr/bin/env python3
"""Prepare/install/remove one private candidate filter latency request.

File changes are explicit subcommands. No audio/service/session operation is run.
"""
import argparse
import ctypes
import errno
import json
import os
from pathlib import Path
import stat
import sys

from audio_common import PrivateArgumentParser, load_json, schema
import inspect_audio as inventory
import inspect_audio_path as path
import speaker_install as speaker

FILE = 'client.conf.d/90-rog-audio-latency-trial.conf'
STATES = {'snapshot-complete', 'installing', 'installed', 'install-incomplete', 'removed'}


class RemovalConflict(ValueError):
    def __init__(self, recovery):
        self.recovery = recovery
        super().__init__('removal ownership changed; recovery evidence retained')


def rule(quantum):
    if type(quantum) is not int or quantum not in (128, 256):
        raise ValueError('unsupported period request')
    return ('# One private output filter; a suggestion, never a forced graph period.\n'
            'filter.rules = [\n  { matches = [ {\n'
            f'      application.id = "{path.APP}"\n'
            f'      node.name = "{path.FILTER}"\n'
            f'      node.group = "{path.GROUP}"\n'
            '      media.role = "DSP"\n'
            '    } ]\n    actions = { update-props = {\n'
            f'      node.latency = "{quantum}/48000"\n'
            '    } }\n  }\n]\n').encode()


def clean_environment(value):
    return isinstance(value, dict) and value.get('status') == 'ok' and value.get('values') == {}


override_context = path.override_context


def no_overrides(context):
    return context.get('status') == 'ok' and all(context.get(k) == {} for k in ('current', 'manager', 'unit'))


def prepare(capture, capture_sha, quantum, output):
    schema(capture, 'audio-path-capture')
    report = path.summary(capture, capture_sha)
    if not report.get('route_consistent') or not report.get('speaker_state_consistent') or not report.get('core_identity_consistent'):
        raise ValueError('baseline path conflict')
    if not clean_environment(capture.get('process_environment')) or not clean_environment(capture.get('process_environment_after')):
        raise ValueError('unknown or overridden candidate environment')
    if not all(no_overrides(capture.get(k, {})) for k in ('restart_environment', 'restart_environment_after')):
        raise ValueError('unknown or overridden future restart environment')
    if report['versions'] != {'pipewire': '1.6.8', 'wireplumber': '0.5.17'}:
        raise ValueError('unsupported configuration source versions')
    graph = inventory.graph(capture['inventory'])
    cores = [x['info'].get('props', {}) for x in graph if x.get('type') == 'PipeWire:Interface:Core']
    if len(cores) != 1 or inventory.integer(cores[0].get('default.clock.rate')) != 48000:
        raise ValueError('observed graph rate is not 48 kHz')
    settings = inventory.public_summary(capture['inventory'], capture_sha).get('graph_settings', {})
    if settings.get('force_quantum') != 0 or settings.get('force_rate') != 0:
        raise ValueError('forced graph timing is outside this trial')
    before = capture['speaker_before']
    if FILE in before['pipewire_config'].get('files', {}):
        raise ValueError('existing trial file')
    content = rule(quantum)
    manifest = {'schema_version': 1, 'kind': 'audio-path-trial',
                'evidence_kind': capture['evidence_kind'],
                'activation_state': 'not-installed', 'quantum_frames': quantum,
                'rate_hz': 48000, 'requested_period_ms': quantum*1000/48000,
                'config_sha256': speaker.sha(content), 'capture_sha256': capture_sha,
                'baseline': before, 'baseline_summary': report,
                'baseline_copy_sha256': speaker.sha(speaker.encoded(capture)),
                'variable': 'one output filter node.latency suggestion',
                'validation_state': 'source-derived-not-yet-native-validated',
                'limits': ['the linked driver may affect other clients sharing that graph',
                           'follower request is not a negotiated driver period',
                           'DSP declarations/client queues are not physical latency']}
    root = speaker.exclusive_directory(output)
    speaker.durable_new_file(root/'candidate.conf', content)
    speaker.durable_new_file(root/'manifest.json', speaker.encoded(manifest))
    speaker.durable_new_file(root/'baseline-capture.json', speaker.encoded(capture))
    speaker.durable_new_file(root/'RESTORE.txt', (
        'INACTIVE BUNDLE. Prepare has changed no running process or live config.\n'
        'Only in the coordinated window: stop the active speaker candidate with controlled quit.\n'
        'Do not restart PipeWire/WirePlumber, alter presets/IR, routes, volume or amplifier controls.\n'
        'Use audio_path_trial.py install with this bundle, exact kit/runtime and a NEW private snapshot.\n'
        'Installation creates only the private candidate config/pipewire/'+FILE+'; it starts nothing.\n'
        'Restart only the existing speaker candidate through its established service owner.\n'
        'Observe an already authorised stream using inspect_audio_path.py. Compare running DRIVER\n'
        'periods, error deltas and identical tuning hashes; follower requests alone prove no change.\n'
        'Rollback: controlled stop candidate, audio_path_trial.py remove with snapshot and NEW archive,\n'
        'then restart only candidate using the prior service. Verify baseline timing and tuning again.\n'
        'Remove refuses an edited owned fragment; it preserves all unrelated config and all DSP files.\n'
    ).encode())
    return {'status': 'prepared', 'activation_state': 'not-installed',
            'config_sha256': speaker.sha(content)}


def load_bundle(directory):
    root = speaker.safe(directory)
    manifest = speaker.document(root/'manifest.json')
    schema(manifest, 'audio-path-trial')
    if manifest.get('rate_hz') != 48000 or manifest.get('activation_state') != 'not-installed':
        raise ValueError('invalid trial manifest')
    expected = rule(manifest.get('quantum_frames'))
    if speaker.read(root/'candidate.conf') != expected or manifest.get('config_sha256') != speaker.sha(expected):
        raise ValueError('modified candidate rule')
    capture = speaker.speaker.json_load(speaker.speaker.read_file(root/'baseline-capture.json', limit=8*1024*1024))
    schema(capture, 'audio-path-capture')
    if speaker.sha(speaker.encoded(capture)) != manifest.get('baseline_copy_sha256') or capture.get('speaker_before') != manifest['baseline']:
        raise ValueError('baseline capture changed')
    baseline = path.hashed_state(manifest['baseline'])
    if not isinstance(baseline.get('pipewire_config'), dict):
        raise ValueError('missing config preimage')
    return root, manifest, expected


def publish_absent(target, content):
    """Durable complete inode, then exclusive atomic link; never overwrite."""
    with speaker.speaker.parent_fd(speaker.safe(target)) as (parent, name):
        temporary = '.'+name+'.trial-'+os.urandom(8).hex()
        descriptor = os.open(temporary, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600, dir_fd=parent)
        try:
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(content); stream.flush(); os.fsync(stream.fileno())
            os.link(temporary, name, src_dir_fd=parent, dst_dir_fd=parent, follow_symlinks=False)
            os.fsync(parent)
        finally:
            os.unlink(temporary, dir_fd=parent); os.fsync(parent)


def current_state(kit, runtime, environment=None):
    state = path.state_snapshot(kit, runtime, environment)
    return state, Path(state['state_root'])/'config/pipewire'


def check_observation(observed, kit, versions):
    speaker.idle(observed)
    if speaker.observed_route(observed, kit['hardware']) != kit['binding']:
        raise ValueError('speaker path drift')
    if {k: inventory.version(observed, k) for k in ('pipewire', 'wireplumber')} != versions:
        raise ValueError('installed configuration versions changed')
    settings = inventory.public_summary(observed, '0'*64).get('graph_settings', {})
    if settings.get('force_quantum') != 0 or settings.get('force_rate') != 0:
        raise ValueError('graph forcing changed')


def install(bundle, kit_path, runtime, snapshot, observed, overrides, environment=None,
            refresh_inventory=None, refresh_overrides=None):
    root, manifest, content = load_bundle(bundle)
    _, kit = speaker.load_kit(kit_path)
    check_observation(observed, kit, manifest['baseline_summary']['versions'])
    if not no_overrides(overrides):
        raise ValueError('unknown or overridden restart environment')
    current, config = current_state(kit_path, runtime, environment)
    if current != manifest['baseline']:
        raise ValueError('baseline settings or configuration changed')
    target = config/FILE
    if target.exists() or target.is_symlink():
        raise ValueError('trial path occupied')
    directory, journal = speaker.snapshot(snapshot, {'pipewire': config}, observed, kit)
    journal.update({'kind': 'audio-path-trial-snapshot', 'quantum_frames': manifest['quantum_frames'],
                    'config_sha256': speaker.sha(content), 'baseline': current})
    speaker.replace(directory/'snapshot.json', speaker.encoded(journal))
    # Recheck preimage after copying; fsync failures leave live bytes untouched.
    fresh, _ = current_state(kit_path, runtime, environment)
    if fresh != current:
        raise ValueError('snapshot preimage changed')
    journal['state'] = 'installing'; speaker.replace(directory/'snapshot.json', speaker.encoded(journal))
    try:
        speaker.mkdir(target.parent)
        # Snapshotting and persistence may take time. Do not reuse the earlier
        # manager/unit state or graph when deciding whether to publish.
        refreshed_overrides = (refresh_overrides or (lambda: override_context(environment=environment)))()
        if not no_overrides(refreshed_overrides):
            raise ValueError('restart environment changed during snapshot')
        refreshed_inventory = (refresh_inventory or inventory.collect)()
        check_observation(refreshed_inventory, kit, manifest['baseline_summary']['versions'])
        publish_absent(target, content)
        journal['state'] = 'installed'; speaker.replace(directory/'snapshot.json', speaker.encoded(journal))
    except BaseException:
        journal['state'] = 'install-incomplete'
        speaker.replace(directory/'snapshot.json', speaker.encoded(journal)); raise
    return {'status': 'installed-files', 'runtime_started': False,
            'snapshot_sha256': speaker.sha(speaker.encoded(journal))}


def load_snapshot(directory, environment=None):
    directory = speaker.safe(directory)
    journal = speaker.document(directory/'snapshot.json')
    schema(journal, 'audio-path-trial-snapshot')
    if not isinstance(journal.get('state'), str) or journal['state'] not in STATES:
        raise ValueError('invalid snapshot state')
    state = speaker.roots(environment)['config'].parent.parent
    config = state/'config/pipewire'
    if type(journal.get('uid')) is not int or journal['uid'] != os.geteuid() or journal.get('roots') != {'pipewire': str(config)}:
        raise ValueError('snapshot ownership/root mismatch')
    expected = rule(journal.get('quantum_frames'))
    if journal.get('config_sha256') != speaker.sha(expected):
        raise ValueError('invalid snapshot rule')
    # Restoration is one fixed owned addition; arbitrary journal paths cannot
    # direct writes/removal, and all prior files are only checked/read here.
    before = journal.get('before', {}).get('pipewire')
    if not isinstance(before, dict) or type(before.get('exists')) is not bool or not isinstance(before.get('files'), dict) or not isinstance(before.get('directories'), dict) or len(before['files'])+len(before['directories']) > speaker.MAX_FILES or FILE in before['files']:
        raise ValueError('invalid absent preimage')
    for name, mode in before['directories'].items():
        speaker.relative(name)
        if type(mode) is not int or not 0 <= mode <= 0o777:
            raise ValueError('invalid backup directory')
    for name, record in before['files'].items():
        speaker.relative(name)
        if not isinstance(record, dict) or not isinstance(record.get('sha256'), str) or not speaker.DIGEST.fullmatch(record['sha256']):
            raise ValueError('invalid backup record')
        if speaker.sha(speaker.read(directory/'before/pipewire'/name)) != record.get('sha256'):
            raise ValueError('snapshot backup changed')
    speaker.outside_locations(directory, {'pipewire': config})
    return directory, journal, config, expected


def rename_absent(source_parent, source_name, destination_parent, destination_name):
    """Linux atomic rename with no destination replacement, on one filesystem."""
    library = ctypes.CDLL(None, use_errno=True)
    rename = getattr(library, 'renameat2', None)
    if rename is None:
        raise ValueError('atomic quarantine requires Linux renameat2')
    rename.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint)
    rename.restype = ctypes.c_int
    if rename(source_parent, os.fsencode(source_name), destination_parent,
              os.fsencode(destination_name), 1) != 0:  # RENAME_NOREPLACE
        code = ctypes.get_errno()
        if code in (errno.ENOSYS, errno.EINVAL, errno.EOPNOTSUPP, errno.EXDEV):
            raise ValueError('filesystem lacks atomic quarantine capability')
        raise OSError(code, os.strerror(code))


def descriptor_record(descriptor):
    before = os.fstat(descriptor)
    if not stat.S_ISREG(before.st_mode) or before.st_size > speaker.MAX_FILE:
        raise ValueError('owned object is not a bounded regular file')
    os.lseek(descriptor, 0, os.SEEK_SET)
    data = bytearray()
    while len(data) <= speaker.MAX_FILE:
        chunk = os.read(descriptor, min(65536, speaker.MAX_FILE+1-len(data)))
        if not chunk: break
        data.extend(chunk)
    after = os.fstat(descriptor)
    if len(data) > speaker.MAX_FILE or before.st_size != after.st_size or len(data) != after.st_size or before.st_mtime_ns != after.st_mtime_ns or before.st_ctime_ns != after.st_ctime_ns:
        raise ValueError('owned inode changed while reading')
    return {'exists': True, 'sha256': speaker.sha(data),
            'mode': stat.S_IMODE(after.st_mode), 'size_bytes': len(data)}


def quarantine_rule(target, retained, original_descriptor, original_record):
    """Retain the actual moved inode, including any later writes through open FDs.

    Unexpected moved objects are restored only to an absent original name.
    A concurrent new destination always wins; the moved object stays archived.
    """
    quarantine = speaker.exclusive_directory(retained/'quarantine')
    with speaker.speaker.parent_fd(target) as (parent, name):
        destination = os.open(quarantine, os.O_RDONLY|os.O_DIRECTORY|getattr(os, 'O_NOFOLLOW', 0))
        try:
            if os.fstat(parent).st_dev != os.fstat(destination).st_dev:
                raise ValueError('removal archive must share the configuration filesystem')
            info = os.fstat(original_descriptor)
            receipt = {'schema_version': 1, 'kind': 'audio-path-removal-inode',
                       'state': 'planned', 'device': info.st_dev, 'inode': info.st_ino,
                       'relative_path': 'quarantine/removed-rule.conf',
                       'expected': original_record}
            speaker.durable_new_file(retained/'removal.json', speaker.encoded(receipt))
            rename_absent(parent, name, destination, 'removed-rule.conf')
            # Persist both directory entries before ownership verification.
            os.fsync(destination); os.fsync(parent)
            moved = os.stat('removed-rule.conf', dir_fd=destination, follow_symlinks=False)
            matches = (moved.st_dev, moved.st_ino) == (info.st_dev, info.st_ino)
            if matches:
                try:
                    matches = descriptor_record(original_descriptor) == original_record
                    os.fsync(original_descriptor)
                except (ValueError, OSError): matches = False
            if not matches:
                # Persist the unexpected inode when it is a readable regular
                # file/directory. Symlinks are retained without following them.
                receipt['inode_sync_status'] = 'directory-entry-retained'
                if not stat.S_ISLNK(moved.st_mode):
                    try:
                        fd = os.open('removed-rule.conf', os.O_RDONLY|os.O_NONBLOCK|getattr(os, 'O_NOFOLLOW', 0), dir_fd=destination)
                        try: os.fsync(fd)
                        finally: os.close(fd)
                        receipt['inode_sync_status'] = 'synced'
                    except OSError:
                        # A permission change must not prevent no-overwrite
                        # restoration of the actual object that was moved.
                        receipt['inode_sync_status'] = 'unavailable'
                try:
                    rename_absent(destination, 'removed-rule.conf', parent, name)
                except FileExistsError:
                    recovery = 'retained-in-archive'
                else:
                    recovery = 'restored-original-path'
                os.fsync(destination); os.fsync(parent)
                receipt['state'] = recovery
                speaker.replace(retained/'removal.json', speaker.encoded(receipt))
                raise RemovalConflict(recovery)
            receipt['state'] = 'retained-owned-inode'
            speaker.replace(retained/'removal.json', speaker.encoded(receipt))
        finally: os.close(destination)


def remove(snapshot, archive, observed, environment=None):
    directory, journal, config, content = load_snapshot(snapshot, environment)
    speaker.idle(observed)
    if journal['state'] not in ('installed', 'installing', 'install-incomplete'):
        raise ValueError('snapshot not installed')
    archive = speaker.safe(archive)
    if directory == archive or directory in archive.parents or archive in directory.parents:
        raise ValueError('archive overlaps snapshot')
    target = config/FILE
    descriptor = None
    try:
        if target.exists() or target.is_symlink():
            with speaker.speaker.parent_fd(target) as (parent, name):
                descriptor = os.open(name, os.O_RDONLY|os.O_NONBLOCK|getattr(os, 'O_NOFOLLOW', 0), dir_fd=parent)
            record = descriptor_record(descriptor)
            if record['sha256'] != speaker.sha(content):
                raise ValueError('owned file changed')
        retained, _ = speaker.snapshot(archive, {'pipewire': config}, observed, journal['kit'])
        if descriptor is not None:
            quarantine_rule(target, retained, descriptor, record)
        elif target.exists() or target.is_symlink():
            raise ValueError('file appeared while archiving')
    finally:
        if descriptor is not None: os.close(descriptor)
    # Delete only empty directories that this single addition needed.
    for parent in (target.parent, config):
        relative = str(parent.relative_to(config))
        old = journal['before']['pipewire']
        if (parent == config and old['exists']) or relative in old.get('directories', {}):
            continue
        try: parent.rmdir()
        except (FileNotFoundError, OSError): pass
        else:
            descriptor = os.open(parent.parent, os.O_RDONLY|os.O_DIRECTORY)
            try: os.fsync(descriptor)
            finally: os.close(descriptor)
    journal['state'] = 'removed'; speaker.replace(directory/'snapshot.json', speaker.encoded(journal))
    return {'status': 'removed-files', 'runtime_started': False,
            'archive_sha256': speaker.sha(speaker.read(retained/'snapshot.json'))}


def status(snapshot, environment=None):
    _, journal, config, content = load_snapshot(snapshot, environment)
    record = speaker.file_record(config/FILE)
    return {'status': journal['state'], 'owned_file': 'absent' if not record['exists'] else
            'expected' if record.get('sha256') == speaker.sha(content) else 'changed'}


def main():
    parser = PrivateArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    prepare_parser = sub.add_parser('prepare'); prepare_parser.add_argument('--capture', required=True)
    prepare_parser.add_argument('--quantum', type=int, choices=(128, 256), default=256)
    prepare_parser.add_argument('--output', required=True)
    install_parser = sub.add_parser('install')
    for name in ('bundle', 'kit', 'runtime', 'snapshot'): install_parser.add_argument('--'+name, required=True)
    remove_parser = sub.add_parser('remove')
    for name in ('snapshot', 'archive'): remove_parser.add_argument('--'+name, required=True)
    status_parser = sub.add_parser('status'); status_parser.add_argument('--snapshot', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'prepare':
            capture, sha = load_json(args.capture)
            result = prepare(capture, sha, args.quantum, args.output)
        elif args.command == 'status': result = status(args.snapshot)
        else:
            if path.platform.system() != 'Linux': raise ValueError('Linux file activation only')
            observed = inventory.collect()
            if args.command == 'install':
                result = install(args.bundle, args.kit, args.runtime, args.snapshot, observed, override_context())
            else: result = remove(args.snapshot, args.archive, observed)
        print(json.dumps(result, sort_keys=True)); return 0
    except RemovalConflict as conflict:
        print(json.dumps({'status': 'removal-conflict', 'recovery': conflict.recovery,
                          'archive_retained': True, 'runtime_started': False}), file=sys.stderr)
        return 2
    except (OSError, ValueError, TypeError, KeyError, RecursionError,
            speaker.InstallError, speaker.speaker.ProfileError, path.configparser.Error):
        parser.exit(2, 'audio trial refused: invalid input, changed preimage or missing capability\n')


if __name__ == '__main__':
    raise SystemExit(main())
