#!/usr/bin/env python3
"""Build/export the pinned speaker-scoped EasyEffects runtime in isolated Docker.

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

ROOT=Path(__file__).resolve().parents[1]
PIN='6d9b1220d3dcebb154ba759a05600662bc0af549'
SERIES=('ubuntu/0001-Disable-echo-canceller.patch',
        '0001-Scope-speaker-correction-to-device-route.patch')
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
        if 'org.rog_audio.SpeakerEffects' not in (output/'src/tags_app.hpp').read_text():raise BuildError('candidate_namespace_not_applied')
    except BaseException:
        shutil.rmtree(output);raise
    return output


def build(source,output,image_tag=None):
    output=files.no_symlinks(Path(output))
    if output.exists() or not output.parent.is_dir():raise BuildError('runtime_output_conflict')
    output.mkdir(mode=0o700)
    image=image_tag or 'rog-audio-ee:'+uuid.uuid4().hex[:12]
    if subprocess.run(['docker','image','inspect',image],capture_output=True).returncode==0:raise BuildError('image_tag_exists')
    container=None
    try:
        with tempfile.TemporaryDirectory(prefix='rog-ee-context-') as temporary:
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
            result=subprocess.run(['docker','build','--tag',image,str(context)],capture_output=True,timeout=1800)
            (output/'build.log').write_bytes(result.stdout+result.stderr)
            if result.returncode:raise BuildError('compiler_build_failed')
        container=run(['docker','create','--network','none',image,'true']).decode().strip()
        run(['docker','cp',container+':/opt/rog-audio/easyeffects',str(output/'runtime')])
        binary=output/'runtime/bin/easyeffects'
        package_stream=run(['docker','run','--rm','-i','--network','none',image,'python3','-'],
                           input=(ROOT/'scripts/package_easyeffects_runtime.py').read_bytes(),timeout=120)
        with tarfile.open(fileobj=io.BytesIO(package_stream)) as tar:tar.extractall(output,filter='data')
        manifest=json.loads((output/'runtime.json').read_text())
        if sha(binary.read_bytes())!=manifest['binary_sha256']:raise BuildError('exported_binary_mismatch')
        manifest['image']=image
        (output/'runtime.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
        # Full upstream source and copyright travel with the built artifact.
        shutil.copytree(ROOT/'patches/easyeffects',output/'patches')
        shutil.copy2(ROOT/'patches/easyeffects/source.json',output/'source-manifest.json')
        shutil.copy2(ROOT/'patches/easyeffects/ubuntu/COPYRIGHT',output/'UBUNTU-COPYRIGHT')
        return {'status':'runtime-built','binary_sha256':manifest['binary_sha256'],'image':image,'activation_state':'not-installed'}
    finally:
        if container:subprocess.run(['docker','rm',container],capture_output=True)
        # Keep the named image for review-bound graph acceptance; remove it once
        # receipts and deliverable files are retained. Never prune shared caches.


def main(argv=None):
    parser=PrivateArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    for command in ('source','build'):
        sub=commands.add_parser(command);sub.add_argument('--source',required=True);sub.add_argument('--output',required=True)
    commands.choices['build'].add_argument('--image-tag')
    args=parser.parse_args(argv)
    try:
        if args.command=='source':source_snapshot(args.source,args.output);result={'status':'source-prepared','source_commit':PIN}
        else:result=build(args.source,args.output,args.image_tag)
        print(json.dumps(result,sort_keys=True));return 0
    except (BuildError,OSError,ValueError,KeyError,TypeError,files.ProfileError,tarfile.TarError,subprocess.SubprocessError):
        print(json.dumps({'status':'error','reason':'invalid_source_or_build_capability'}));return 3

if __name__=='__main__':raise SystemExit(main())
