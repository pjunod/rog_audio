#!/usr/bin/env python3
"""Package the built private-prefix runtime; stdout is a tar artifact stream.

Run inside the pinned Ubuntu build image. No host package is installed.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

PREFIX=Path('/opt/rog-audio/easyeffects')
PIN='6d9b1220d3dcebb154ba759a05600662bc0af549'
PACKAGE='rog-audio-easyeffects'
VERSION='8.2.8+rog4'
SCRATCH=Path('/build/rog-audio-package')

def command(argv):return subprocess.check_output(argv,text=True).strip()

def main():
    if (not isinstance(globals().get('STOP_HELPER_BYTES'), bytes) or
            not isinstance(globals().get('STOP_HELPER_LICENSE_BYTES'), bytes)):
        raise RuntimeError('exact stop helper bytes must accompany packaging input')
    SCRATCH.mkdir(mode=0o700,parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='rog-ee-package-',dir=SCRATCH) as temporary:
        base=Path(temporary);package=base/'root';control=package/'DEBIAN';control.mkdir(parents=True)
        dependencies=command(['dpkg-query','-W','-f=${Depends}','easyeffects'])+', lsp-plugins-lv2 (>= 1.2.10), python3'
        shutil.copytree(PREFIX,package/'opt/rog-audio/easyeffects',symlinks=True)
        (control/'control').write_text('Package: '+PACKAGE+'\nVersion: '+VERSION+'\nArchitecture: amd64\n'
            'Maintainer: rog_audio contributors <agent@example.invalid>\n'
            'Section: sound\nPriority: optional\nDepends: '+dependencies+'\n'
            'Description: Exact-route internal-speaker EasyEffects runtime\n'
            ' Private-prefix build with target ownership and route-event DSP bypass.\n')
        launcher=package/'usr/bin/rog-speaker-effects';launcher.parent.mkdir(parents=True)
        launcher.write_text('#!/bin/sh\nexec /opt/rog-audio/easyeffects/bin/easyeffects "$@"\n');launcher.chmod(0o755)
        stop=package/'usr/lib/rog-audio/stop-speaker-effects';stop.parent.mkdir(parents=True)
        stop.write_bytes(STOP_HELPER_BYTES);stop.chmod(0o755)
        desktop=package/'usr/share/applications/org.rog_audio.SpeakerEffects.desktop';desktop.parent.mkdir(parents=True)
        desktop.write_text('[Desktop Entry]\nType=Application\nName=ROG Audio Speaker Effects\n'
                           'Comment=Private internal-speaker correction candidate\nExec=rog-speaker-effects\n'
                           'Terminal=false\nCategories=AudioVideo;Audio;\n')
        notices=package/'usr/share/doc'/PACKAGE;notices.mkdir(parents=True)
        (notices/'STOP-HELPER-MIT-LICENSE').write_bytes(STOP_HELPER_LICENSE_BYTES)
        shutil.copy2('/src/easyeffects/LICENSE',notices/'UPSTREAM-LICENSE')
        shutil.copy2('/usr/share/doc/easyeffects/copyright',notices/'copyright')
        source_bytes=Path('/opt/rog-audio/easyeffects-source.json').read_bytes()
        shutil.copy2('/opt/rog-audio/easyeffects-source.json',notices/'source.json')
        artifact=base/(PACKAGE+'_'+VERSION+'_amd64.deb')
        subprocess.run(['dpkg-deb','--root-owner-group','--build',str(package),str(artifact)],check=True,stdout=subprocess.DEVNULL)
        ldd=command(['ldd',str(PREFIX/'bin/easyeffects')])
        libraries=[]
        for line in ldd.splitlines():
            if '=> not found' in line:raise RuntimeError('Unresolved built runtime library')
            name=line.strip().split()[0]
            if name.endswith('.so') or '.so.' in name:libraries.append(name)
        packages=command(['dpkg-query','-W','-f=${binary:Package}\t${Version}\t${Status}\n']).splitlines()
        versions={parts[0]:parts[1] for line in packages if len(parts:=line.split('\t'))==3 and parts[2]=='install ok installed'}
        manifest={'schema_version':1,'source_commit':PIN,'routing_contract':'exact-device-route-v1',
                  'source_manifest_sha256':hashlib.sha256(source_bytes).hexdigest(),
                  'patches_sha256':json.loads(source_bytes)['files'],
                  'programme_loudness_contract':json.loads(source_bytes)['programme_loudness_contract'],
                  'stop_contract':'owned-synchronous-exit-v1',
                  'stop_helper_sha256':hashlib.sha256(STOP_HELPER_BYTES).hexdigest(),
                  'stop_helper_license_sha256':hashlib.sha256(STOP_HELPER_LICENSE_BYTES).hexdigest(),
                  'binary_sha256':hashlib.sha256((PREFIX/'bin/easyeffects').read_bytes()).hexdigest(),
                  'package':artifact.name,'package_version':VERSION,'package_sha256':hashlib.sha256(artifact.read_bytes()).hexdigest(),
                  'runtime_prefix':str(PREFIX),'distribution':'Ubuntu 26.10','architecture':'amd64',
                  'dependencies':dependencies,'build_package_versions':versions,'elf_libraries':sorted(libraries),
                  'activation_state':'not-installed','qualification':'isolated-build; physical/acoustic acceptance pending'}
        (base/'runtime.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
        with tarfile.open(fileobj=sys.stdout.buffer,mode='w|') as tar:
            tar.add(artifact,arcname=artifact.name);tar.add(base/'runtime.json',arcname='runtime.json')

if __name__=='__main__':main()
