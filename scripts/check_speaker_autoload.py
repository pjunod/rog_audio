#!/usr/bin/env python3
"""Focused route/sink arrival acceptance in a private, device-free graph.

Selectors are independent for failure-only retries after combined PR review.
The real candidate loads the emitted preset/IR; generated PCM stays in null sinks.
"""
import argparse
import json
import os
from pathlib import Path
import selectors
import subprocess
import sys
import uuid

from check_speaker_graph import Graph, GraphError
import speaker_install as kit

CASES=('route-before-node','node-before-route','device-return')


def acceptance(kit_path,case,output,binary,mock,player):
    output=kit.exclusive_directory(output)
    root,manifest=kit.load_kit(kit_path)
    if kit.sha(kit.speaker.read_file(Path(binary),limit=64*1024*1024))!=manifest['runtime']['binary_sha256']:
        raise GraphError('candidate binary mismatch')
    if Path('/dev/snd').exists():raise GraphError('run in a device-free container')
    state=output/'state';runtime=output/'runtime';runtime.mkdir(mode=0o700)
    env=dict(os.environ,ROG_AUDIO_STATE_DIR=str(state),XDG_RUNTIME_DIR=str(runtime),
             PIPEWIRE_RUNTIME_DIR=str(runtime),PIPEWIRE_REMOTE='rog-autoload-'+uuid.uuid4().hex[:12],
             XDG_CONFIG_HOME=str(state/'config'),XDG_DATA_HOME=str(state/'data'),
             XDG_CACHE_HOME=str(state/'cache'),XDG_STATE_HOME=str(state/'session'),
             QT_QPA_PLATFORM='offscreen',QT_QUICK_BACKEND='software',QT_LOGGING_RULES='easyeffects.debug=true')
    for key in ('PIPEWIRE_CONFIG_DIR','PIPEWIRE_CONFIG_NAME','PULSE_SINK','PULSE_SOURCE'):env.pop(key,None)
    locations=kit.roots(env)
    for name in manifest['files']:
        target=locations['data']/name.split('/',1)[1];kit.mkdir(target.parent);kit.replace(target,kit.read(root/name))
    target=locations['config']/'db/easyeffectsrc';kit.mkdir(target.parent)
    kit.replace(target,kit.settings(b'',manifest))  # Real zero-interval deployment contract.
    conf=state/'config/pipewire/pipewire.conf.d/99-private.conf';kit.mkdir(conf.parent)
    conf.write_text('context.properties = { core.name = "'+env['PIPEWIRE_REMOTE']+'" }\n')
    graph=Graph(output,env);node_name=manifest['binding']['node_name'];observations=[]
    try:
        graph.start('pipewire',['pipewire']);graph.until(lambda _:True)
        graph.start('wireplumber',['wireplumber'])
        device=graph.start('mock-device',[mock]+(['--empty-routes'] if case=='node-before-route' else []),pipe=True)
        selector=selectors.DefaultSelector();selector.register(device.stdout,selectors.EVENT_READ)
        try:
            if not selector.select(15):raise GraphError('synthetic device did not export')
            line=device.stdout.readline().decode().strip()
        finally:selector.close()
        if not line.startswith('device '):raise GraphError('synthetic device export failed')
        device_id=int(line.split()[1])
        def add_sink():
            props={'factory.name':'support.null-audio-sink','node.name':node_name,
                   'node.description':'Synthetic returned speakers','media.class':'Audio/Sink',
                   'audio.position':['FL','FR'],'object.linger':True,
                   'device.id':device_id,'card.profile.device':0,'device.api':'alsa'}
            graph.call(['pw-cli','create-node','adapter',json.dumps(props)])
            return graph.until(lambda g:graph.node(g,node_name))
        def change_route(command):
            device.stdin.write((command+'\n').encode());device.stdin.flush()
        def observed_route(description):
            log=output/'easyeffects.log'
            return log.exists() and ('output route: '+description) in log.read_text(errors='replace')
        if case=='device-return':
            physical=add_sink();graph.call(['wpctl','set-default',str(physical['id'])])
        graph.stage=case+' candidate startup'
        graph.start('easyeffects',[binary,'--hide-window','--service-mode'])
        graph.until(lambda g:graph.node(g,'rog_audio_speaker_sink'))
        if case=='route-before-node':
            graph.until(lambda _:observed_route('Speakers'))
            if graph.node(graph.dump(),node_name):raise GraphError('physical fixture sink already exists')
            graph.preset(binary)  # Service round trip while there is still no sink.
            observations.append('real Device route observed before its sink at zero autoload interval')
            physical=add_sink();graph.call(['wpctl','set-default',str(physical['id'])])
        elif case=='node-before-route':
            physical=add_sink();graph.call(['wpctl','set-default',str(physical['id'])])
            graph.until(lambda _:graph.preset(binary)==manifest['bypass_name'])
            observations.append('sink without route selected the empty fallback')
            change_route('speaker')
        graph.until(lambda _:graph.preset(binary)==manifest['preset_name'])
        if case=='device-return':
            old_serial=physical['info']['props']['object.serial']
            change_route('headphones')
            graph.until(lambda _:graph.preset(binary)==manifest['bypass_name'])
            graph.call(['pw-cli','destroy',str(physical['id'])])
            graph.until(lambda g:not graph.node(g,node_name))
            change_route('speaker')
            graph.until(lambda g:any(x['type']=='PipeWire:Interface:Device' and x['id']==device_id and
                any(r.get('device')==0 and r.get('name')=='analog-output-speaker'
                    for r in x.get('info',{}).get('params',{}).get('Route',[])) for x in g))
            # A service round trip while absent exercises the dropped-node timer
            # ordering; the returning sink must recover from the retained route.
            graph.preset(binary)
            physical=add_sink();graph.call(['wpctl','set-default',str(physical['id'])])
            if physical['info']['props']['object.serial']==old_serial:raise GraphError('fixture sink did not return as a new instance')
            graph.until(lambda _:graph.preset(binary)==manifest['preset_name'])
            observations.append('headphone fallback followed by speaker route while sink absent recovered on new serial')
        observations.append('exact bound speaker preset selected by native IPC')
        graph.stage=case+' actual correction pipeline'
        graph.start('player',[player,'rog-autoload-player',node_name])
        graph.until(lambda g:graph.linked(g,'rog-autoload-player','rog_audio_speaker_sink'))
        graph.until(lambda _: 'kernel correctly loaded' in (output/'easyeffects.log').read_text(errors='replace'))
        expected={p.split('#')[0] for p in json.loads(kit.read(root/'speaker-source/preset.json'))['output']['plugins_order']}
        def plugins_present(g):
            actual={x.get('info',{}).get('props',{}).get('node.name','').removeprefix('rog_audio_soe_')
                    for x in g if x['type']=='PipeWire:Interface:Node'}
            return expected<=actual
        graph.until(plugins_present)
        observations.append('actual bound IR, plugins and speaker interception loaded')
        change_route('headphones')
        graph.until(lambda _:graph.preset(binary)==manifest['bypass_name'])
        graph.until(lambda g:graph.linked(g,'rog-autoload-player',node_name))
        if graph.linked(graph.dump(),'rog-autoload-player','rog_audio_speaker_sink'):
            raise GraphError('headphone route retained speaker interception')
        observations.append('headphones selected empty fallback and released correction ownership')
        for name,digest in manifest['files'].items():
            if kit.sha(kit.read(locations['data']/name.split('/',1)[1]))!=digest:
                raise GraphError('runtime changed preset, IR or autoload bytes')
        observations.append('all kit payload bytes retained')
        receipt={'schema_version':1,'case':case,'status':'passed','evidence_kind':'isolated-synthetic-runtime',
                 'binary_sha256':manifest['runtime']['binary_sha256'],'source_commit':manifest['runtime']['source_commit'],
                 'speaker_bundle_manifest_sha256':manifest['speaker_bundle_manifest_sha256'],
                 'autoload_interval_ms':0,'assertions':observations,'physical_device_or_session_access':False,
                 'acoustic_or_physical_latency_measurement':False}
        kit.replace(output/'receipt.json',kit.encoded(receipt));return receipt
    finally:
        if sys.exc_info()[0] is not None:
            try:kit.replace(output/'failure-graph.json',kit.encoded(graph.dump()))
            except (GraphError,ValueError,subprocess.TimeoutExpired):pass
        graph.close()


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',choices=CASES,required=True)
    parser.add_argument('--kit',required=True);parser.add_argument('--output',required=True)
    parser.add_argument('--binary',default='/opt/rog-audio/easyeffects/bin/easyeffects')
    parser.add_argument('--mock-device',default='/opt/rog-audio/mock-device')
    parser.add_argument('--player',default='/opt/rog-audio/synthetic-player')
    parser.add_argument('--private-dbus',action='store_true',help=argparse.SUPPRESS);args=parser.parse_args(argv)
    if not args.private_dbus:
        return subprocess.run(['dbus-run-session','--',sys.executable,str(Path(__file__).resolve()),
            *(sys.argv[1:] if argv is None else argv),'--private-dbus']).returncode
    try:
        result=acceptance(args.kit,args.case,args.output,args.binary,args.mock_device,args.player)
        print(json.dumps({'case':args.case,'status':result['status'],'assertion_count':len(result['assertions'])}));return 0
    except (GraphError,kit.InstallError,OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as error:
        if kit.safe(args.output).is_dir():
            kit.replace(Path(args.output)/'failure.json',kit.encoded({'case':args.case,'exception':type(error).__name__,'detail':str(error)}))
        print(json.dumps({'case':args.case,'status':'failed','reason':'synthetic_autoload_acceptance_failed'}));return 1

if __name__=='__main__':raise SystemExit(main())
