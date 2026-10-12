#!/usr/bin/env python3
"""Read-only compatibility inventory for a delivered Ubuntu speaker runtime."""
import json
from pathlib import Path
import re
import subprocess
from audio_common import PrivateArgumentParser
import prepare_speaker_profile as files

DEPENDENCY=re.compile(r'^([a-z0-9][a-z0-9+.-]*)(?::([a-z0-9-]+))?(?:\s*\((>=|<=|=|>>|<<)\s*([^()\s]+)\))?$')

def parse_dependency(text):
    match=DEPENDENCY.fullmatch(text.strip())
    if not match:raise ValueError('unsupported dependency expression')
    return match.groups()

def compare(version,operator,required):
    if not operator:return True
    return subprocess.run(['dpkg','--compare-versions',version,operator,required],capture_output=True).returncode==0

def inspect(manifest):
    result=subprocess.run(['dpkg-query','-W','-f=${binary:Package}\t${Architecture}\t${Version}\t${Status}\t${Provides}\n'],capture_output=True,text=True,timeout=20)
    if result.returncode:raise ValueError('dpkg inventory unavailable')
    available={}
    for line in result.stdout.splitlines():
        parts=line.split('\t')
        if len(parts)!=5 or parts[3]!='install ok installed':continue
        name=parts[0].split(':')[0]
        candidate={'version':parts[2],'provider':parts[0],'architecture':parts[1]}
        available.setdefault(name,[]).append(candidate)
        for provided in filter(None,parts[4].split(',')):
            alias,_,operator,version=parse_dependency(provided)
            available.setdefault(alias,[]).append({**candidate,'version':version if operator=='=' else None})
    dependencies=[]
    for group in manifest['dependencies'].split(','):
        alternatives=[]
        for text in group.split('|'):
            name,qualifier,operator,minimum=parse_dependency(text)
            candidates=[]
            for candidate in available.get(name,[]):
                architecture_matches=(candidate['architecture'] in (manifest['architecture'],'all')
                                      and qualifier in (None,'any','native',manifest['architecture']))
                satisfied=(architecture_matches and
                           (not operator or candidate['version'] is not None and
                            compare(candidate['version'],operator,minimum)))
                candidates.append({**candidate,'architecture_matches':architecture_matches,'satisfied':satisfied})
            actual=next((x for x in candidates if x['satisfied']),
                        next((x for x in candidates if x['architecture_matches']),None))
            alternatives.append({'name':name,'required_architecture':qualifier or manifest['architecture'],
                                 'operator':operator,'required_version':minimum,
                                 'installed_version':actual['version'] if actual else None,
                                 'installed_provider':actual['provider'] if actual else None,
                                 'installed_architecture':actual['architecture'] if actual else None,
                                 'installed_candidates':candidates,'satisfied':any(x['satisfied'] for x in candidates)})
        dependencies.append({'alternatives':alternatives,'satisfied':any(x['satisfied'] for x in alternatives)})
    os_info={}
    for line in Path('/etc/os-release').read_text().splitlines():
        key,sep,value=line.partition('=')
        if sep and key in ('ID','VERSION_ID'):os_info[key]=value.strip('"')
    architecture=subprocess.check_output(['dpkg','--print-architecture'],text=True,timeout=5).strip()
    platform=os_info=={'ID':'ubuntu','VERSION_ID':'26.10'} and architecture==manifest['architecture']
    status='incompatible-platform' if not platform else ('compatible' if all(x['satisfied'] for x in dependencies) else 'prerequisites-missing')
    return {'schema_version':1,'kind':'speaker-runtime-compatibility','evidence_kind':'live-read-only',
            'status':status,'distribution_id':os_info.get('ID'),'distribution_version':os_info.get('VERSION_ID'),
            'architecture':architecture,'binary_sha256':manifest['binary_sha256'],'package_sha256':manifest['package_sha256'],
            'dependencies':dependencies,'settings_or_services_changed':False}

def main(argv=None):
    p=PrivateArgumentParser(description=__doc__);p.add_argument('--manifest',required=True);p.add_argument('--output',required=True);a=p.parse_args(argv)
    try:
        manifest=json.loads(files.read_file(Path(a.manifest),limit=1024*1024))
        result=inspect(manifest);files.new_file(Path(a.output),(json.dumps(result,indent=2,sort_keys=True)+'\n').encode())
        print(json.dumps({'status':result['status'],'satisfied_dependency_groups':sum(x['satisfied'] for x in result['dependencies']),
                          'dependency_groups':len(result['dependencies']),'settings_or_services_changed':False}));return 0
    except (OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError,files.ProfileError):
        print(json.dumps({'status':'error','reason':'runtime_inventory_capability_unavailable'}));return 3

if __name__=='__main__':raise SystemExit(main())
