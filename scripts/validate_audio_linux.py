#!/usr/bin/env python3
"""Package synthetic lane tests into a disposable matching-version container.

No hardware, host configuration or desktop socket mounts. Logs remain private.
This is an explicit build/test command, never called by repository checks.
"""
import io
import json
import re
import os
from pathlib import Path
import shlex
import subprocess
import tarfile
import uuid
from audio_common import PrivateArgumentParser

IMAGE = 'ubuntu@sha256:ee126c2fa0249079a7e24ae3a3d29b04783ef93ab33c868751c9a1289d3fffff'
CHECKS = ('all', 'unit', 'unit-inspector', 'unit-analyser', 'unit-candidate', 'config',
          'compile', 'native-match', 'native-other-app', 'native-other-target')
UNIT_MODULES = {'unit-inspector':'test_inspect_audio', 'unit-analyser':'test_analyse_audio_latency',
                'unit-candidate':'test_prepare_audio_latency'}
FILES = ('scripts/audio_common.py', 'scripts/inspect_audio.py',
         'scripts/analyse_audio_latency.py', 'scripts/prepare_audio_latency.py',
         'tests/test_inspect_audio.py', 'tests/test_analyse_audio_latency.py',
         'tests/test_prepare_audio_latency.py', 'tests/audio/validate_client.c',
         'tests/audio/linux-validation.sh', 'tests/audio/synthetic-trials.json',
         'tests/audio/synthetic-candidate.conf',
         'evidence/audio-latency-synthetic-analysis.json')


def archive(root):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream,mode='w') as tar:
        for name in FILES:
            path=root/name
            if path.is_symlink() or not path.is_file():
                raise ValueError('required synthetic lane source missing')
            tar.add(path,arcname='candidate.conf' if name.endswith('synthetic-candidate.conf') else name)
    return stream.getvalue()


def main():
    parser=PrivateArgumentParser(description=__doc__)
    parser.add_argument('--ssh-target',help='Optional private SSH alias; otherwise use local Docker')
    parser.add_argument('--identity-file',help='Optional private SSH key path')
    parser.add_argument('--stage','--check',dest='stage',choices=CHECKS,default='all')
    parser.add_argument('--test-id',action='append',default=[],help='Failed unittest method ID; repeat within selected unit suite')
    parser.add_argument('--output',required=True,help='New private validation-log JSON')
    args=parser.parse_args()
    if args.identity_file and not args.ssh_target:
        parser.error('identity requires ssh')
    module=UNIT_MODULES.get(args.stage)
    pattern=(re.escape(module) if module else r'(?:test_inspect_audio|test_analyse_audio_latency|test_prepare_audio_latency)')+r'\.[A-Za-z][A-Za-z0-9_]*\.test_[A-Za-z0-9_]+'
    if args.test_id and (args.stage not in ('unit', *UNIT_MODULES) or len(args.test_id)>128 or len(set(args.test_id)) != len(args.test_id) or any(not re.fullmatch(pattern,x) for x in args.test_id)):
        parser.error('invalid method selection')
    root=Path(__file__).resolve().parents[1]
    name='audio-latency-'+uuid.uuid4().hex[:12]
    docker=['docker','run','--rm','--pull=never','-i','--name',name,'-e','AUDIO_STAGE='+args.stage,'-e','AUDIO_TEST_IDS='+json.dumps(args.test_id),IMAGE,'bash','-c',
            'mkdir /case; tar -x -C /case; bash /case/tests/audio/linux-validation.sh']
    cleanup=['docker','rm','-f',name]
    if args.ssh_target:
        if args.ssh_target.startswith('-') or any(c.isspace() for c in args.ssh_target):
            parser.error('invalid target')
        ssh=['ssh','-o','BatchMode=yes']
        if args.identity_file:
            ssh.extend(['-i',str(Path(args.identity_file).resolve())])
        command=ssh+[args.ssh_target,shlex.join(docker)]
        cleanup=ssh+[args.ssh_target,shlex.join(cleanup)]
    else:
        command=docker
    try:
        # Reserve output exclusively before dispatching any build.
        fd=os.open(args.output,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        output_stream=os.fdopen(fd,'w',encoding='utf-8')
        data=archive(root)
        try:
            process=subprocess.run(command,input=data,capture_output=True,timeout=600)
            result={'returncode':process.returncode,
                    'stdout':process.stdout.decode('utf-8','replace'),
                    'stderr':process.stderr.decode('utf-8','replace')}
        except subprocess.TimeoutExpired:
            subprocess.run(cleanup,capture_output=True,timeout=30)
            result={'returncode':None,'status':'timeout'}
        result['report']=None
        for line in result.get('stdout','').splitlines():
            if line.startswith('audio_validation_report='):
                try:
                    result['report']=json.loads(line.split('=',1)[1])
                except ValueError:
                    pass
        # Write only to the exclusively reserved file, with no private console text.
        with output_stream as stream:
            json.dump({'schema_version':1,'kind':'private-linux-validation',
                       'image':IMAGE,'container':name,'stage':args.stage,'test_ids':args.test_id,'result':result},stream,indent=2)
            stream.write('\n')
        print('Linux validation passed' if result.get('returncode')==0 else 'Linux validation failed; inspect private log')
        return 0 if result.get('returncode')==0 else 1
    except (OSError,ValueError,subprocess.TimeoutExpired):
        parser.exit(2,'Linux validation unavailable or output creation failed\n')


if __name__ == '__main__':
    raise SystemExit(main())
