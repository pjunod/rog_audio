#!/bin/sh
# Explicit review-then-run entry point; images and Cavern source are supplied.
exec python3 - "$0" "$@" <<'PY'
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile

script = Path(sys.argv[1]).resolve(strict=True)
parser = argparse.ArgumentParser(description='Selected live-player unit and virtual-PipeWire integration stages')
parser.add_argument('--image', required=True)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--report', type=Path, required=True)
parser.add_argument('--stage', choices=('units', 'integration', 'all'))
parser.add_argument('--test-id', action='append', default=[])
parser.add_argument('--case', action='append', default=[])
parser.add_argument('--joc-input', type=Path)
args = parser.parse_args(sys.argv[2:])
sys.path.insert(0, str(script.parent))
from live_ci_options import select_stage
try:
    stage = select_stage(args.stage, args.test_id, args.case, args.joc_input)
except ValueError as exc:
    parser.error(str(exc))
def interrupted(signum, frame):
    raise KeyboardInterrupt('interrupted signal ' + str(signum))
for signum in (signal.SIGTERM, signal.SIGHUP):
    signal.signal(signum, interrupted)
if sys.platform != 'linux':
    parser.error('Linux container host required')
args.report = args.report.parent.resolve(strict=True) / args.report.name
log_path = Path(str(args.report) + '.log')
if any(os.path.lexists(path) for path in (args.report, log_path)):
    parser.error('report/log collision')
engine = os.environ.get('ATMOS_CONTAINER_ENGINE', 'podman')
if engine not in ('podman', 'docker'):
    parser.error('container engine must be podman or docker')
def command(argv, **kwargs):
    return subprocess.run(argv, check=True, **kwargs)
source = args.source.resolve(strict=True)
pin = '7d85d1880666ca5ea323848cff47ce7f50b29f7d'
if subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip() != pin:
    parser.error('Cavern pin mismatch')
if subprocess.check_output(['git', '-C', str(source), 'status', '--porcelain', '--untracked-files=normal'], text=True):
    parser.error('Cavern must be clean')
image_data = json.loads(subprocess.check_output([engine, 'image', 'inspect', args.image]))[0]
source_root = subprocess.check_output(['git', '-C', str(script.parent), 'rev-parse', '--show-toplevel'], text=True).strip()
source_commit = subprocess.check_output(['git', '-C', source_root, 'rev-parse', 'HEAD'], text=True).strip()
work_root = Path(os.environ.get('XDG_STATE_HOME', str(Path.home()/'.local/state'))) / 'rog-audio/work'
work_root.mkdir(parents=True, exist_ok=True)
# No image pull, source fetch, devices, session sockets or host configuration.
container_code = r'''
import json
from pathlib import Path
import subprocess
import sys
options = json.loads(sys.argv[1])
subprocess.run(['sh', 'probes/atmos/build.sh', '--source', '/work/Cavern', '--output', '/work/build'], check=True)
codes = []
if options['stage'] in ('units', 'all'):
    subprocess.run(['ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error', '-f', 'lavfi', '-i',
        'sine=frequency=997:sample_rate=48000:duration=0.16', '-c:a', 'eac3', '-b:a', '768k',
        '-ac', '6', '-f', 'eac3', '-n', '/work/bed.eac3'], check=True)
    cmd = ['python3', 'scripts/validate_atmos_live.py', '--build', '/work/build',
           '--bed-fixture', '/work/bed.eac3', '--report', '/work/units.json']
    for name in options['test_ids']:
        cmd += ['--test-id', name]
    codes.append(subprocess.run(cmd).returncode)
if options['stage'] in ('integration', 'all') and not any(codes):
    cmd = ['python3', 'probes/atmos/live_integration.py', '--probe', '/work/build/atmos-live',
           '--config', '/work/probes/atmos/live-pipewire.conf', '--report', '/work/integration.json']
    for name in options['cases']:
        cmd += ['--case', name]
    if options['joc_input']:
        cmd += ['--joc-input', '/work/joc.eac3']
    codes.append(subprocess.run(cmd).returncode)
sys.exit(0 if codes and not any(codes) else 1)
'''
receipt = {'schema_version': 1, 'stage': stage, 'evidence_class': 'selected-live-player-software',
    'source_commit': source_commit, 'image_id': image_data.get('Id'),
    'network': 'none', 'cpus': 2, 'memory_bytes': 6442450944, 'pids_limit': 256,
    'capabilities': 'all dropped', 'host_devices_or_session_sockets': False,
    'physical_audio': False, 'units': None, 'integration': None}
with tempfile.TemporaryDirectory(prefix='live-atmos-ci.', dir=work_root) as directory:
    scratch = Path(directory)
    archive = scratch/'public-source.tar'
    command(['git', '-C', source_root, 'archive', '--format=tar', '--output', str(archive),
             'HEAD', 'probes/atmos', 'scripts/validate_atmos_live.py', 'tests/test_atmos_live.py',
             'LICENSE', 'LICENSES.md'])
    command(['tar', '-xf', str(archive), '-C', str(scratch)])
    command(['git', 'clone', '--no-hardlinks', '--no-checkout', str(source), str(scratch/'Cavern')],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    command(['git', '-C', str(scratch/'Cavern'), 'checkout', '--detach', '-q', pin])
    if args.joc_input:
        shutil.copyfile(args.joc_input.resolve(strict=True), scratch/'joc.eac3')
    name = 'rog-atmos-' + scratch.name
    options = {'stage': stage, 'test_ids': args.test_id, 'cases': args.case,
               'joc_input': args.joc_input is not None}
    argv = [engine, 'run', '--rm', '--pull', 'never', '--name', name, '--network', 'none',
        '--cpus', '2', '--memory', '6g', '--pids-limit', '256', '--cap-drop', 'all',
        '--security-opt', 'no-new-privileges', '--user', str(os.getuid())+':'+str(os.getgid()),
        '-e', 'DOTNET_CLI_HOME=/tmp/atmos-cli', '-e', 'NUGET_PACKAGES=/tmp/atmos-nuget',
        '-e', 'XDG_CONFIG_HOME=/tmp/atmos-config', '-e', 'XDG_CACHE_HOME=/tmp/atmos-cache',
        '-v', str(scratch)+':/work', '-w', '/work']
    if engine == 'podman':
        argv += ['--userns', 'keep-id']
    argv += [args.image, 'python3', '-c', container_code, json.dumps(options)]
    try:
        with (scratch/'container.log').open('xb') as log:
            result = subprocess.run(argv, stdout=log, stderr=log)
        receipt['container_exit_code'] = result.returncode
    finally:
        subprocess.run([engine, 'rm', '-f', name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for key in ('units', 'integration'):
        path = scratch/(key+'.json')
        if path.is_file():
            receipt[key] = json.loads(path.read_text())
    required = ('units', 'integration') if stage == 'all' else (stage,)
    receipt['status'] = 'passed' if receipt['container_exit_code'] == 0 and all(receipt[key] for key in required) else 'failed'
    for path, data in ((log_path, (scratch/'container.log').read_bytes()),
                       (args.report, (json.dumps(receipt, indent=2, allow_nan=False)+'\n').encode())):
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'wb') as handle:
            handle.write(data)
print(json.dumps({'status': receipt['status'], 'stage': stage}))
raise SystemExit(0 if receipt['status'] == 'passed' else 1)
PY
