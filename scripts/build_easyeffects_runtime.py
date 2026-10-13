#!/usr/bin/env python3
"""Build/export the pinned speaker-scoped EasyEffects runtime in isolated Docker or Podman.

Source preparation reads Git objects at the pin, never ignored owner data.
This tool neither installs packages on the host nor mounts its audio/session.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import uuid

from audio_common import PrivateArgumentParser
import prepare_speaker_profile as files
import package_easyeffects_runtime as package

ROOT=Path(__file__).resolve().parents[1]
PIN='6d9b1220d3dcebb154ba759a05600662bc0af549'
SERIES=('ubuntu/0001-Disable-echo-canceller.patch',
        '0001-Scope-speaker-correction-to-device-route.patch',
        '0002-Retain-output-routes-for-device-return.patch')
MAX_ARCHIVE=128*1024*1024

class BuildError(Exception):pass

def sha(data):return hashlib.sha256(data).hexdigest()

def run(argv,**kwargs):
    result=subprocess.run(argv,capture_output=True,**kwargs)
    if result.returncode:raise BuildError('external_build_command_failed')
    return result.stdout


def source_snapshot(source,output):
    output=files.no_symlinks(Path(output));source=files.no_symlinks(Path(source))
    if output.exists() or not output.parent.is_dir():raise BuildError('source_output_conflict')
    environment=dict(os.environ,GIT_NO_REPLACE_OBJECTS='1')
    resolved=run(['git','-C',str(source),'rev-parse',PIN+'^{commit}'],env=environment).decode().strip()
    if resolved!=PIN:raise BuildError('upstream_source_pin_mismatch')
    archive=run(['git','-C',str(source),'archive','--format=tar',PIN],env=environment)
    if len(archive)>MAX_ARCHIVE:raise BuildError('upstream_archive_limit')
    output.mkdir(mode=0o700)
    try:
        with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
            # Python's data filter prevents traversal, escaping links and devices.
            tar.extractall(output,filter='data')
        checksums=json.loads((ROOT/'patches/easyeffects/source.json').read_text())['files']
        for name in SERIES:
            patch=ROOT/'patches/easyeffects'/name
            if sha(files.read_file(patch,limit=4*1024*1024))!=checksums[name]:raise BuildError('patch_hash_mismatch')
            patch_environment=dict(os.environ,GIT_CEILING_DIRECTORIES=str(output.parent))
            for key in ('GIT_DIR','GIT_WORK_TREE','GIT_INDEX_FILE'):patch_environment.pop(key,None)
            run(['git','apply','--check',str(patch)],cwd=output,env=patch_environment)
            run(['git','apply',str(patch)],cwd=output,env=patch_environment)
        if not (output/'src/speaker_routing.hpp').is_file():raise BuildError('routing_patch_not_applied')
        pins=json.loads((ROOT/'patches/easyeffects/source.json').read_text())
        if sha((output/'src/speaker_routing.hpp').read_bytes())!=pins['routing_header_sha256']:raise BuildError('routing_header_pin_mismatch')
        if sha((output/'src/output_route_cache.hpp').read_bytes())!=pins['output_route_header_sha256']:raise BuildError('output_route_header_pin_mismatch')
        if 'org.rog_audio.SpeakerEffects' not in (output/'src/tags_app.hpp').read_text():raise BuildError('candidate_namespace_not_applied')
    except BaseException:
        shutil.rmtree(output);raise
    return output


def build_command(engine,image,context):
    command=[engine,'build','--cpu-period','100000','--cpu-quota','200000',
             '--memory','6g','--memory-swap','6g']
    if engine=='podman':command+=['--jobs','1']
    return command+['--tag',image,str(context)]


def runtime_command(engine,action):
    return [engine,action,'--network','none','--cpus','2','--memory','6g','--pids-limit','2048']


def build(source,output,image_tag=None,engine='docker'):
    output=files.no_symlinks(Path(output))
    if output.exists() or not output.parent.is_dir():raise BuildError('runtime_output_conflict')
    if engine not in ('docker','podman'):raise BuildError('unsupported_container_engine')
    image=image_tag or 'rog-audio-ee:'+uuid.uuid4().hex[:12]
    if subprocess.run([engine,'image','inspect',image],capture_output=True).returncode==0:raise BuildError('image_tag_exists')
    output.mkdir(mode=0o700)
    container=None
    try:
        with tempfile.TemporaryDirectory(prefix='rog-ee-context-',dir=output) as temporary:
            context=Path(temporary)
            # Only pinned public sources and two explicit synthetic support files.
            staged=source_snapshot(source,context/'patched')
            # Keep the full patched source with the artifact for GPL source access.
            shutil.copytree(staged,output/'source',symlinks=True)
            shutil.move(str(staged),context/'easyeffects')
            (context/'probes').mkdir()
            for name in ('mock_device.cpp','synthetic_player.c'):
                shutil.copy2(ROOT/'probes/speaker'/name,context/'probes'/name)
            shutil.copy2(ROOT/'patches/easyeffects/source.json',context/'source.json')
            (context/'Dockerfile').write_bytes((ROOT/'scripts/easyeffects-build.Dockerfile').read_bytes())
            try:
                result=subprocess.run(build_command(engine,image,context),capture_output=True,timeout=1800)
            except subprocess.TimeoutExpired as error:
                (output/'build.log').write_bytes((error.stdout or b'')+(error.stderr or b''))
                raise BuildError('compiler_build_timed_out') from None
            (output/'build.log').write_bytes(result.stdout+result.stderr)
            if result.returncode:raise BuildError('compiler_build_failed')
        container=run(runtime_command(engine,'create')+['--name','rog-audio-ee-export-'+uuid.uuid4().hex[:12],image,'true']).decode().strip()
        run([engine,'cp',container+':/opt/rog-audio/easyeffects',str(output/'runtime')])
        binary=output/'runtime/bin/easyeffects'
        package_stream=run(runtime_command(engine,'run')+['--rm','-i',image,'python3','-'],
                           input=(ROOT/'scripts/package_easyeffects_runtime.py').read_bytes(),timeout=120)
        with tarfile.open(fileobj=io.BytesIO(package_stream)) as tar:tar.extractall(output,filter='data')
        manifest=json.loads((output/'runtime.json').read_text())
        if sha(binary.read_bytes())!=manifest['binary_sha256']:raise BuildError('exported_binary_mismatch')
        expected_package=package.PACKAGE+'_'+package.VERSION+'_amd64.deb'
        if manifest.get('package_version')!=package.VERSION or manifest.get('package')!=expected_package:raise BuildError('exported_package_version_mismatch')
        if sha((output/expected_package).read_bytes())!=manifest['package_sha256']:raise BuildError('exported_package_mismatch')
        if sha((ROOT/'patches/easyeffects/source.json').read_bytes())!=manifest['source_manifest_sha256']:raise BuildError('exported_source_manifest_mismatch')
        manifest['image']=image
        (output/'runtime.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
        # Full upstream source and copyright travel with the built artifact.
        shutil.copytree(ROOT/'patches/easyeffects',output/'patches')
        shutil.copy2(ROOT/'patches/easyeffects/source.json',output/'source-manifest.json')
        shutil.copy2(ROOT/'patches/easyeffects/ubuntu/COPYRIGHT',output/'UBUNTU-COPYRIGHT')
        return {'status':'runtime-built','binary_sha256':manifest['binary_sha256'],'image':image,'activation_state':'not-installed'}
    finally:
        if container:subprocess.run([engine,'rm',container],capture_output=True)
        # Keep the named image for review-bound graph acceptance; remove it once
        # receipts and deliverable files are retained. Never prune shared caches.


def main(argv=None):
    parser=PrivateArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    for command in ('source','build'):
        sub=commands.add_parser(command);sub.add_argument('--source',required=True);sub.add_argument('--output',required=True)
    commands.choices['build'].add_argument('--image-tag')
    commands.choices['build'].add_argument('--container-engine',choices=('docker','podman'),default='docker')
    args=parser.parse_args(argv)
    try:
        if args.command=='source':source_snapshot(args.source,args.output);result={'status':'source-prepared','source_commit':PIN}
        else:result=build(args.source,args.output,args.image_tag,args.container_engine)
        print(json.dumps(result,sort_keys=True));return 0
    except (BuildError,OSError,ValueError,KeyError,TypeError,files.ProfileError,tarfile.TarError,subprocess.SubprocessError):
        print(json.dumps({'status':'error','reason':'invalid_source_or_build_capability'}));return 3

if __name__=='__main__':raise SystemExit(main())
