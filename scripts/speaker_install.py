#!/usr/bin/env python3
"""Prepare, snapshot, install and remove an exact-route EasyEffects speaker kit.

No package installs, daemon starts, default-sink changes or amplifier controls.
Install/remove are explicit later operator actions; prepare/status are offline.
"""
import argparse
import configparser
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import stat

import inspect_audio
import prepare_speaker_profile as speaker
from audio_common import PrivateArgumentParser

SCHEMA = 1
STATES = {"snapshot-complete", "installing", "installed", "install-incomplete", "removed"}
MAX_FILES = 1024
MAX_FILE = 4 * 1024 * 1024
MAX_TOTAL = 64 * 1024 * 1024
NAME = re.compile(r'[a-zA-Z0-9_.:-]{1,200}\Z')
DIGEST = re.compile(r'[0-9a-f]{64}\Z')
RC_FILES = {'convolver':'convolverrc','equalizer':'equalizerrc','autogain':'autogainrc',
            'multiband_compressor':'multibandcompressorrc','limiter':'limiterrc'}


class InstallError(Exception):
    def __init__(self,reason,code=2):
        self.reason,self.code=reason,code


def require(condition,reason,code=2):
    if not condition:raise InstallError(reason,code)


def sha(data):return hashlib.sha256(data).hexdigest()


def encoded(value):return (json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()


def read(path):
    try:return speaker.read_file(Path(path),limit=MAX_FILE)
    except speaker.ProfileError:raise InstallError('unsafe_or_unreadable_file') from None


def document(path):
    try:return speaker.json_load(read(path))
    except (speaker.ProfileError,ValueError,TypeError):raise InstallError('invalid_json') from None


def safe(path):
    try:return speaker.no_symlinks(Path(path))
    except speaker.ProfileError:raise InstallError('unsafe_path') from None


def relative(name):
    require(isinstance(name,str) and name and not Path(name).is_absolute() and
            str(Path(name))==name and name!='.' and not any(x in ('.','..') for x in Path(name).parts),'invalid_relative_path')
    return name


def replace(path,data,mode=0o600):
    """No-follow parent descriptor; same-directory temporary file and fsync."""
    path=safe(path)
    with speaker.parent_fd(path) as (parent,name):
        temporary='.'+name+'.rog-'+os.urandom(8).hex()
        fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL,mode,dir_fd=parent)
        try:
            with os.fdopen(fd,'wb') as stream:
                os.fchmod(stream.fileno(),mode)
                stream.write(data);stream.flush();os.fsync(stream.fileno())
            os.rename(temporary,name,src_dir_fd=parent,dst_dir_fd=parent)
            os.fsync(parent)
        finally:
            try:os.unlink(temporary,dir_fd=parent)
            except FileNotFoundError:pass


def durable_new_file(path,data):
    path=safe(path)
    with speaker.parent_fd(path) as (parent,name):
        flags=os.O_WRONLY|os.O_CREAT|os.O_EXCL|getattr(os,'O_NOFOLLOW',0)
        fd=os.open(name,flags,0o600,dir_fd=parent)
        with os.fdopen(fd,'wb') as stream:
            os.fchmod(stream.fileno(),0o600)
            stream.write(data);stream.flush();os.fsync(stream.fileno())
        os.fsync(parent)


def sync_directory(parent,name):
    fd=os.open(name,os.O_RDONLY|os.O_DIRECTORY|getattr(os,'O_NOFOLLOW',0),dir_fd=parent)
    try:os.fsync(fd)
    finally:os.close(fd)
    os.fsync(parent)


def mkdir(path):
    path=safe(path)
    if path.exists():
        require(path.is_dir(),'not_directory');return
    mkdir(path.parent)
    with speaker.parent_fd(path) as (parent,name):
        try:
            os.mkdir(name,0o700,dir_fd=parent)
            sync_directory(parent,name)
        except FileExistsError:require(path.is_dir() and not path.is_symlink(),'directory_race')


def exclusive_directory(path):
    path=safe(path);require(path.parent.is_dir(),'output_parent_missing')
    with speaker.parent_fd(path) as (parent,name):
        os.mkdir(name,0o700,dir_fd=parent)
        sync_directory(parent,name)
    return path


def file_record(path):
    path=safe(path)
    if not path.exists():return {'exists':False}
    data=read(path)
    return {'exists':True,'sha256':sha(data),'mode':stat.S_IMODE(path.stat().st_mode),'size_bytes':len(data)}


def tree(root):
    """Snapshot bounded files; absent roots and empty directories are explicit."""
    root=safe(root);result={'exists':root.exists(),'files':{},'directories':{}}
    if not root.exists():return result
    require(root.is_dir(),'not_directory')
    result['mode']=stat.S_IMODE(root.stat().st_mode)
    pending=[root];count,total=0,0
    while pending:
        parent=pending.pop()
        with os.scandir(parent) as entries:
            for entry in entries:
                count+=1;require(count<=MAX_FILES,'snapshot_entry_limit')
                require(not entry.is_symlink(),'snapshot_symlink')
                path=Path(entry.path);name=str(path.relative_to(root))
                if entry.is_dir(follow_symlinks=False):
                    result['directories'][name]=stat.S_IMODE(entry.stat(follow_symlinks=False).st_mode)
                    pending.append(path)
                else:
                    record=file_record(path);total+=record['size_bytes'];require(total<=MAX_TOTAL,'snapshot_byte_limit')
                    result['files'][name]=record
    return result


def roots(environment=None):
    env=os.environ if environment is None else environment
    state=Path(env.get('ROG_AUDIO_STATE_DIR',str(Path(env.get('XDG_STATE_HOME',str(Path.home()/'.local/state')))/'rog-audio/easyeffects')))
    require(state.is_absolute(),'candidate_state_must_be_absolute')
    return {'data':safe(state/'data/easyeffects'),'config':safe(state/'config/easyeffects')}


def observed_route(inventory,hardware=None):
    hardware=hardware or {'codec':'10ec0285','subsystem':'10431c63'}
    codec=hardware.get('codec');subsystem=hardware.get('subsystem')
    require(codec=='10ec0285' and subsystem in ('10431c63','17aa2276'),'unsupported_speaker_identity',3)
    require(isinstance(inventory,dict),'invalid_inventory')
    graph=inspect_audio.graph(inventory)
    candidates=[]
    for node in graph:
        props=node.get('info',{}).get('props',{})
        if node.get('type')!='PipeWire:Interface:Node' or props.get('media.class')!='Audio/Sink' or props.get('device.api')!='alsa':continue
        card=props.get('api.alsa.pcm.card')
        if isinstance(card,str) and card.isdigit():card=int(card)
        if type(card) is not int or not 0<=card<=255:continue
        codec_prefix='/proc/asound/card'+str(card)+'/codec#'
        codec_match=False
        for name,probe in inventory.get('files',{}).items():
            if not name.startswith(codec_prefix) or probe.get('status')!='ok':continue
            text=probe.get('text','')
            if re.search(r'^Vendor Id: 0x'+re.escape(codec)+r'\s*$',text,re.M) and re.search(r'^Subsystem Id: 0x'+re.escape(subsystem)+r'\s*$',text,re.M):codec_match=True
        if not codec_match:continue
        require(type(props.get('device.id')) is int and type(props.get('card.profile.device')) is int,'missing_route_identifiers')
        devices=[x for x in graph if x.get('type')=='PipeWire:Interface:Device' and type(x.get('id')) is int and x['id']==props['device.id']]
        require(len(devices)==1,'ambiguous_device')
        params=devices[0].get('info',{}).get('params',{});routes=params.get('Route',[])
        require(isinstance(routes,list),'invalid_route_list')
        selected=[x for x in routes if isinstance(x,dict) and x.get('direction')=='Output' and type(x.get('device')) is int and x['device']==props['card.profile.device']]
        require(len(selected)==1,'ambiguous_active_route')
        route=selected[0];require(route.get('name')=='analog-output-speaker','internal_speaker_not_selected',3)
        node_name=props.get('node.name');description=route.get('description',route['name'])
        require(isinstance(node_name,str) and NAME.fullmatch(node_name) and node_name.startswith('alsa_output.'),'invalid_node_identity')
        require(isinstance(description,str) and 0<len(description)<=128 and all(ord(c)>=32 for c in description) and ':' not in description,'invalid_route_description')
        candidates.append({'node_name':node_name,'route_name':route['name'],'route_description':description,
                           'codec':codec,'subsystem':subsystem})
    require(len(candidates)==1,'ambiguous_or_missing_supported_speaker',3)
    return candidates[0]


def prepare(bundle,inventory,output,runtime_manifest):
    bundle=safe(bundle)
    try:speaker.verify(bundle)
    except (speaker.ProfileError,ValueError,KeyError,TypeError):raise InstallError('speaker_bundle_invalid') from None
    manifest=document(bundle/'manifest.json')
    binding=observed_route(inventory,manifest['hardware'])
    runtime=document(runtime_manifest)
    require(isinstance(runtime,dict) and runtime.get('schema_version')==1 and
            runtime.get('source_commit')=='6d9b1220d3dcebb154ba759a05600662bc0af549' and
            runtime.get('routing_contract')=='exact-device-route-v1' and
            isinstance(runtime.get('binary_sha256'),str) and DIGEST.fullmatch(runtime['binary_sha256']),
            'unsupported_runtime_contract',3)
    manifest=document(bundle/'manifest.json');preset=read(bundle/'preset.json')
    stem='rog-speaker-'+sha(preset)[:16]
    bypass=stem+'-bypass'
    autoload=binding['node_name'].replace('/','_')+':'+binding['route_description'].replace('/','_')+'.json'
    files={'data/output/'+stem+'.json':preset,
           'data/output/'+bypass+'.json':encoded({'output':{'blocklist':[],'plugins_order':[]}}),
           'data/'+manifest['impulse']:read(bundle/manifest['impulse']),
           'data/autoload/output/'+autoload:encoded({'device':binding['node_name'],
                   'device-description':'Internal speakers','device-profile':binding['route_description'],
                   'preset-name':stem})}
    kit={'schema_version':1,'kind':'speaker-install-kit','activation_state':'not-installed',
         'hardware':manifest['hardware'],'selection':manifest['selection'],'binding':binding,
         'speaker_bundle_manifest_sha256':sha(read(bundle/'manifest.json')),'runtime':runtime,
         'preset_name':stem,'bypass_name':bypass,'files':{n:sha(b) for n,b in files.items()},
         'rc_files':sorted({'db/easyeffectsrc'}|{'db/'+RC_FILES[n.split('#')[0]] for n in json.loads(preset)['output']['plugins_order']}),
         'limits':['physical/acoustic qualification pending','no host package/service/default-sink/amp changes performed by this kit']}
    output=exclusive_directory(output)
    try:
        for name,data in files.items():mkdir((output/name).parent);speaker.new_file(output/name,data)
        mkdir(output/'speaker-source')
        for parent,dirs,names in os.walk(bundle):
            for name in names:
                source=Path(parent)/name;destination=output/'speaker-source'/source.relative_to(bundle)
                mkdir(destination.parent);speaker.new_file(destination,read(source))
        speaker.new_file(output/'kit.json',encoded(kit))
    except BaseException:
        shutil.rmtree(output);raise
    return {'status':'prepared','activation_state':'not-installed','kit_sha256':sha(encoded(kit))}


def load_kit(path):
    root=safe(path);kit=document(root/'kit.json')
    require(isinstance(kit,dict) and kit.get('schema_version')==1 and kit.get('kind')=='speaker-install-kit','unsupported_kit')
    try:speaker.verify(root/'speaker-source')
    except (speaker.ProfileError,ValueError,KeyError,TypeError):raise InstallError('source_bundle_invalid') from None
    require(sha(read(root/'speaker-source/manifest.json'))==kit['speaker_bundle_manifest_sha256'],'source_bundle_changed')
    require(isinstance(kit.get('files'),dict) and len(kit['files'])==4,'invalid_kit_inventory')
    binding=kit.get('binding',{})
    require(isinstance(binding,dict) and binding.get('codec')=='10ec0285' and binding.get('subsystem') in ('10431c63','17aa2276') and binding.get('route_name')=='analog-output-speaker','invalid_kit_binding')
    source_manifest=document(root/'speaker-source/manifest.json')
    require(kit.get('hardware')==source_manifest['hardware'] and kit.get('selection')==source_manifest['selection'] and binding.get('codec')==source_manifest['hardware']['codec'] and binding.get('subsystem')==source_manifest['hardware']['subsystem'],'kit_hardware_or_selection_mismatch')
    source_preset=read(root/'speaker-source/preset.json')
    stem='rog-speaker-'+sha(source_preset)[:16]
    require(kit.get('preset_name')==stem and kit.get('bypass_name')==stem+'-bypass','invalid_preset_identity')
    require(isinstance(binding.get('node_name'),str) and NAME.fullmatch(binding['node_name']) and isinstance(binding.get('route_description'),str) and ':' not in binding['route_description'],'invalid_route_description')
    autoload=binding['node_name'].replace('/','_')+':'+binding['route_description'].replace('/','_')+'.json'
    expected={'data/output/'+stem+'.json':source_preset,
              'data/output/'+stem+'-bypass.json':encoded({'output':{'blocklist':[],'plugins_order':[]}}),
              'data/'+source_manifest['impulse']:read(root/'speaker-source'/source_manifest['impulse']),
              'data/autoload/output/'+autoload:encoded({'device':binding['node_name'],'device-description':'Internal speakers','device-profile':binding['route_description'],'preset-name':stem})}
    require(kit['files']=={n:sha(v) for n,v in expected.items()},'kit_payload_scope_mismatch')
    require(kit.get('rc_files')==sorted({'db/easyeffectsrc'}|{'db/'+RC_FILES[n.split('#')[0]] for n in json.loads(source_preset)['output']['plugins_order']}),'invalid_runtime_rc_scope')
    for name,digest in kit['files'].items():
        relative(name);require(name.startswith('data/') and isinstance(digest,str) and DIGEST.fullmatch(digest),'invalid_kit_path')
        require(sha(read(root/name))==digest,'kit_payload_changed')
    return root,kit


def idle(inventory):
    runtime=os.environ.get('XDG_RUNTIME_DIR')
    if runtime:
        lock=Path(runtime)/'rog-audio-speaker-effects.lock'
        if lock.exists():
            try:
                lines=read(lock).splitlines();require(bool(lines),'invalid_candidate_lock',3)
                first=lines[0]
                require(first.isdigit() and int(first)>0,'invalid_candidate_lock',3)
                os.kill(int(first),0)
            except ProcessLookupError:pass
            else:raise InstallError('candidate_running_close_it_before_filesystem_change',3)
    # Refuse concurrent app writers; quitting/starting it is an operator step.
    for item in inspect_audio.graph(inventory):
        props=item.get('info',{}).get('props',{})
        if props.get('application.id')=='org.rog_audio.SpeakerEffects':
            raise InstallError('candidate_running_close_it_before_filesystem_change',3)


def settings(before,kit):
    parser=configparser.ConfigParser(interpolation=None,strict=True);parser.optionxform=str
    if before:
        try:parser.read_string(before.decode('utf-8'))
        except (UnicodeError,configparser.Error):raise InstallError('unsupported_prior_settings') from None
    updates={'Presets':{'ignorePresetBlocklist':'true'},'Window':{'outputAutoloadingUsesFallback':'true','outputAutoloadingFallbackPreset':kit['bypass_name'],
                       'presetsAutoloadInterval':'0'},
             'EffectsPipelines':{'processAllInputs':'false','processAllOutputs':'true'},
             'StreamOutputs':{'useDefaultOutputDevice':'false','outputDevice':kit['binding']['node_name'],'speakerCorrectionDevice':kit['binding']['node_name'],
                              'speakerCorrectionRoute':kit['binding']['route_name']}}
    for group,values in updates.items():
        if not parser.has_section(group):parser.add_section(group)
        for key,value in values.items():parser.set(group,key,value)
    stream=io.StringIO();parser.write(stream,space_around_delimiters=False)
    return stream.getvalue().encode()


def outside_locations(path,locations):
    path=safe(path)
    for root in locations.values():
        require(path!=root and root not in path.parents and path not in root.parents,
                'snapshot_overlaps_easyeffects')


def kit_scope(kit):
    require(isinstance(kit,dict) and kit.get('schema_version')==1 and kit.get('kind')=='speaker-install-kit',
            'invalid_snapshot_kit')
    binding=kit.get('binding',{});stem=kit.get('preset_name')
    require(isinstance(binding,dict) and isinstance(stem,str) and
            re.fullmatch(r'rog-speaker-[0-9a-f]{16}',stem) and kit.get('bypass_name')==stem+'-bypass',
            'invalid_snapshot_preset')
    node=binding.get('node_name');description=binding.get('route_description')
    require(isinstance(node,str) and NAME.fullmatch(node) and node.startswith('alsa_output.') and
            isinstance(description,str) and 0<len(description)<=128 and
            all(ord(x)>=32 for x in description) and ':' not in description and
            binding.get('route_name')=='analog-output-speaker','invalid_snapshot_binding')
    files=kit.get('files');require(isinstance(files,dict) and len(files)==4,'invalid_snapshot_files')
    fixed={'data/output/'+stem+'.json','data/output/'+stem+'-bypass.json',
           'data/autoload/output/'+node+':'+description.replace('/','_')+'.json'}
    remaining=set(files)-fixed
    require(fixed<=set(files) and len(remaining)==1 and
            all(re.fullmatch(r'data/irs/speaker-[0-9a-f]+\.irs',x) for x in remaining) and
            all(isinstance(v,str) and DIGEST.fullmatch(v) for v in files.values()),'invalid_snapshot_files')
    rc=kit.get('rc_files')
    require(isinstance(rc,list) and len(rc)==len(set(rc)) and 'db/easyeffectsrc' in rc and
            set(rc)<={'db/easyeffectsrc',*('db/'+v for v in RC_FILES.values())},'invalid_runtime_rc_scope')
    return set(files)|{'config/db/easyeffectsrc'}


def snapshot(directory,locations,inventory,kit):
    outside_locations(directory,locations)
    views={key:tree(root) for key,root in locations.items()}
    require(sum(r['size_bytes'] for view in views.values() for r in view['files'].values())<=MAX_TOTAL,'snapshot_byte_limit')
    directory=exclusive_directory(directory)
    try:
        for key,view in views.items():
            for name,record in view['files'].items():
                data=read(locations[key]/name);require(sha(data)==record['sha256'],'snapshot_source_changed')
                target=directory/'before'/key/name;mkdir(target.parent);durable_new_file(target,data)
        data={'schema_version':1,'kind':'speaker-install-snapshot','state':'snapshot-complete',
              'uid':os.geteuid(),'roots':{k:str(v) for k,v in locations.items()},'before':views,'kit':kit,
              'inventory_sha256':sha(encoded(inventory)),'planned':{},'installed':[]}
        durable_new_file(directory/'snapshot.json',encoded(data))
        durable_new_file(directory/'inventory.json',encoded(inventory))
    except BaseException:
        shutil.rmtree(directory);raise
    return directory,data


def install(kit_path,snapshot_path,runtime,inventory,locations):
    root,kit=load_kit(kit_path);idle(inventory)
    require(observed_route(inventory,kit['hardware'])==kit['binding'],'route_identity_changed',3)
    require(sha(speaker.read_file(Path(runtime),limit=64*1024*1024))==kit['runtime']['binary_sha256'],'runtime_binary_mismatch',3)
    payload={name:read(root/name) for name in kit['files']}
    require({name:sha(data) for name,data in payload.items()}==kit['files'],'kit_payload_changed')
    directory,state=snapshot(snapshot_path,locations,inventory,kit)
    prior=state['before']['config']['files'].get('db/easyeffectsrc')
    before=read(directory/'before/config/db/easyeffectsrc') if prior else b''
    require(not prior or sha(before)==prior['sha256'],'snapshot_backup_changed')
    payload['config/db/easyeffectsrc']=settings(before,kit)
    state['planned']={name:sha(data) for name,data in payload.items()}
    state['state']='installing'
    replace(directory/'snapshot.json',encoded(state))
    try:
        for name,data in payload.items():
            key,relative_name=name.split('/',1);target=locations[key]/relative_name
            record=state['before'][key]['files'].get(relative_name,{'exists':False})
            require(file_record(target)==record,'concurrent_target_change')
            mkdir(target.parent);replace(target,data)
            state['installed'].append(name);replace(directory/'snapshot.json',encoded(state))
        state['state']='installed';replace(directory/'snapshot.json',encoded(state))
    except BaseException:
        # Snapshot journal remains available; restoration is explicit and verifiable.
        state['state']='install-incomplete';replace(directory/'snapshot.json',encoded(state));raise
    return {'status':'installed-files','runtime_started':False,'snapshot_sha256':sha(encoded(state))}


def load_snapshot(path,locations):
    directory=safe(path);state=document(directory/'snapshot.json')
    require(isinstance(state,dict) and state.get('schema_version')==1 and state.get('kind')=='speaker-install-snapshot','unsupported_snapshot')
    require(isinstance(state.get('state'),str) and state['state'] in STATES,'invalid_snapshot_state')
    require(state.get('uid')==os.geteuid() and state.get('roots')=={k:str(v) for k,v in locations.items()},'snapshot_target_mismatch')
    require(isinstance(state.get('kit'),dict) and isinstance(state.get('before'),dict) and set(state['before'])==set(locations) and isinstance(state.get('planned'),dict) and isinstance(state.get('installed'),list),'invalid_snapshot')
    allowed=kit_scope(state['kit'])
    require(set(state['planned'])<=allowed and set(state['installed'])<=set(state['planned']) and all(isinstance(v,str) and DIGEST.fullmatch(v) for v in state['planned'].values()),'invalid_snapshot_scope')
    require(all(isinstance(x,str) and x in {'db/easyeffectsrc',*('db/'+v for v in RC_FILES.values())} for x in state['kit'].get('rc_files',[])),'invalid_runtime_rc_scope')
    for key,view in state['before'].items():
        require(key in locations and isinstance(view,dict) and isinstance(view.get('files'),dict) and isinstance(view.get('directories'),dict) and type(view.get('exists')) is bool,'invalid_snapshot')
        require(len(view['files'])+len(view['directories'])<=MAX_FILES,'snapshot_entry_limit')
        for name in view['directories']:relative(name)
        for name,record in view['files'].items():
            relative(name);require(isinstance(record,dict) and type(record.get('mode')) is int and 0<=record['mode']<=0o777 and isinstance(record.get('sha256'),str),'invalid_snapshot_record')
            require(sha(read(directory/'before'/key/name))==record['sha256'],'snapshot_backup_changed')
    return directory,state


def remove(snapshot_path,archive_path,inventory,locations):
    directory,state=load_snapshot(snapshot_path,locations);idle(inventory)
    outside_locations(archive_path,locations)
    archive_path=safe(archive_path)
    require(archive_path!=directory and directory not in archive_path.parents and archive_path not in directory.parents,'archive_overlaps_snapshot')
    require(state['state'] in ('installed','install-incomplete','installing'),'snapshot_not_installed')
    # Files outside the runtime settings must still be the exact owned payload.
    for name,digest in state['planned'].items():
        key,relative_name=name.split('/',1);relative(relative_name)
        if key=='data':
            current=file_record(locations[key]/relative_name)
            prior=state['before'][key]['files'].get(relative_name,{'exists':False})
            require(current.get('sha256')==digest or current==prior,'owned_payload_changed')
    # Retain all post-install state before restoring old settings byte for byte.
    archive,retained=snapshot(archive_path,locations,inventory,state['kit'])
    restore=list(state['planned'])
    restore.extend('config/'+relative(x) for x in state['kit']['rc_files'])
    for name in dict.fromkeys(restore):
        key,relative_name=name.split('/',1);relative(relative_name);require(key in locations,'invalid_restore_root')
        target=locations[key]/relative_name
        prior=state['before'][key]['files'].get(relative_name)
        if prior:
            mkdir(target.parent);replace(target,read(directory/'before'/key/relative_name),prior['mode'])
        elif target.exists():
            with speaker.parent_fd(target) as (parent,filename):os.unlink(filename,dir_fd=parent)
    # Remove only empty directories created since the baseline; preserve new data.
    for key,root in locations.items():
        if not root.exists():continue
        current=tree(root)
        for name in sorted(current['directories'],key=lambda x:len(Path(x).parts),reverse=True):
            if name not in state['before'][key]['directories']:
                try:
                    with speaker.parent_fd(root/name) as (parent,filename):os.rmdir(filename,dir_fd=parent)
                except OSError:pass
        if not state['before'][key]['exists']:
            try:root.rmdir()
            except OSError:pass
    state['state']='removed';state['removal_archive_sha256']=sha(encoded(retained))
    replace(directory/'snapshot.json',encoded(state))
    return {'status':'removed','prior_settings_restored':True,'post_install_state_retained':True}


def status(snapshot_path,locations):
    _,state=load_snapshot(snapshot_path,locations)
    differences=[]
    names=list(state['planned'])
    if state['state']=='removed':names.extend('config/'+x for x in state['kit']['rc_files'])
    for name in dict.fromkeys(names):
        key,relative_name=name.split('/',1)
        current=file_record(locations[key]/relative_name)
        if state['state']=='removed':
            prior=state['before'][key]['files'].get(relative_name,{'exists':False})
            if current!=prior:differences.append(name)
        elif current.get('sha256')!=state['planned'][name]:differences.append(name)
    return {'status':state['state'],'owned_file_count':len(state['installed']),
            'changed_owned_file_count':len(differences),'comparison':'prior-state' if state['state']=='removed' else 'installed-payload',
            'runtime_started_by_installer':False}


def main(argv=None):
    parser=PrivateArgumentParser(description=__doc__);commands=parser.add_subparsers(dest='command',required=True)
    prepare_parser=commands.add_parser('prepare');prepare_parser.add_argument('--bundle',required=True)
    prepare_parser.add_argument('--inventory',required=True);prepare_parser.add_argument('--runtime-manifest',required=True)
    prepare_parser.add_argument('--output',required=True)
    install_parser=commands.add_parser('install');install_parser.add_argument('--kit',required=True)
    install_parser.add_argument('--snapshot',required=True);install_parser.add_argument('--runtime',required=True)
    remove_parser=commands.add_parser('remove');remove_parser.add_argument('--snapshot',required=True)
    remove_parser.add_argument('--archive',required=True)
    status_parser=commands.add_parser('status');status_parser.add_argument('--snapshot',required=True)
    args=parser.parse_args(argv)
    try:
        if args.command=='prepare':result=prepare(args.bundle,document(args.inventory),args.output,args.runtime_manifest)
        elif args.command=='status':result=status(args.snapshot,roots())
        else:
            inventory=inspect_audio.collect()
            if args.command=='install':result=install(args.kit,args.snapshot,args.runtime,inventory,roots())
            else:result=remove(args.snapshot,args.archive,inventory,roots())
        print(json.dumps(result,sort_keys=True));return 0
    except InstallError as error:print(json.dumps({'status':'error','reason':error.reason}));return error.code
    except (OSError,ValueError,KeyError,TypeError,configparser.Error,speaker.ProfileError):
        print(json.dumps({'status':'error','reason':'invalid_input_or_filesystem_state'}));return 2


if __name__=='__main__':raise SystemExit(main())
