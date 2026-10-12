#!/usr/bin/env python3
"""Actual candidate loader/plugin/routing acceptance in a private synthetic graph.

Run in the pinned build container with no host devices/session mounts. Each
--case selector is independent for failure-only retries after batch review.
"""
import argparse
import array
import json
import math
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import uuid

import speaker_install as kit

class GraphError(Exception):pass

class Graph:
    def __init__(self,root,environment):
        self.root=root;self.env=environment;self.processes=[];self.handles=[]
    def start(self,name,argv,pipe=False,environment=None):
        log=(self.root/(name+'.log')).open('wb');self.handles.append(log)
        child=subprocess.Popen(argv,env=environment or self.env,stdin=subprocess.PIPE if pipe else subprocess.DEVNULL,
                               stdout=subprocess.PIPE if pipe else log,stderr=log,start_new_session=True)
        self.processes.append(child);return child
    def call(self,argv):
        result=subprocess.run(argv,env=self.env,capture_output=True,text=True,timeout=15)
        if result.returncode:raise GraphError('graph command failed: '+argv[0])
        return result.stdout
    def dump(self):return json.loads(self.call(['pw-dump']))
    def until(self,predicate,seconds=15):
        deadline=time.monotonic()+seconds
        while time.monotonic()<deadline:
            try:
                result=predicate(self.dump())
                if result:return result
            except (ValueError,GraphError):pass
            if any(p.poll() is not None for p in self.processes):raise GraphError('graph process exited')
            time.sleep(.05)
        raise GraphError('graph observation timed out')
    def node(self,graph,name):
        return next((x for x in graph if x['type']=='PipeWire:Interface:Node' and
                     x.get('info',{}).get('props',{}).get('node.name')==name),None)
    def linked(self,graph,output,input):
        a=self.node(graph,output);b=self.node(graph,input)
        if not a or not b:return False
        return any(x['type']=='PipeWire:Interface:Link' and x.get('info',{}).get('output-node-id')==a['id'] and
                   x.get('info',{}).get('input-node-id')==b['id'] and x.get('info',{}).get('state') in ('active','paused') for x in graph)
    def targets(self,graph,subject):
        result={}
        for item in graph:
            if item['type']!='PipeWire:Interface:Metadata' or item.get('props',{}).get('metadata.name')!='default':continue
            for entry in item.get('metadata',[]):
                if entry.get('subject')==subject and entry.get('key') in ('target.node','target.object'):
                    value=entry.get('value')
                    wire=value if isinstance(value,str) else json.dumps(value,separators=(',',':'))
                    result[entry['key']]={'type':entry.get('type'),'value':wire}
        return result
    def preset(self,binary):
        return self.call([binary,'--last-loaded-preset','output']).strip()
    def stop(self,child):
        if child.poll() is None:
            os.killpg(child.pid,signal.SIGTERM)
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=5)
        if child in self.processes:self.processes.remove(child)
    def close(self):
        for child in list(reversed(self.processes)):self.stop(child)
        for handle in self.handles:handle.close()


def rms(path):
    values=array.array('f');values.frombytes(path.read_bytes())
    # Ignore graph startup; measure the final 100 ms of generated stereo samples.
    data=values[-9600:]
    if len(data)<4800:raise GraphError('insufficient synthetic capture')
    if any(not math.isfinite(v) for v in data):raise GraphError('nonfinite synthetic output')
    return math.sqrt(sum(v*v for v in data)/len(data))


def acceptance(kit_path,case,output,binary,mock,player):
    output=kit.exclusive_directory(output)
    root,manifest=kit.load_kit(kit_path)
    if manifest['hardware']['subsystem']!={'asus-loader-route':'10431c63','lenovo-loader-route':'17aa2276'}[case]:raise GraphError('wrong per-device kit')
    if kit.sha(kit.speaker.read_file(Path(binary),limit=64*1024*1024))!=manifest['runtime']['binary_sha256']:
        raise GraphError('candidate binary mismatch')
    if (Path('/dev/snd')).exists():raise GraphError('run in a device-free container')
    state=output/'state';runtime=output/'runtime';runtime.mkdir(mode=0o700)
    environment=dict(os.environ,ROG_AUDIO_STATE_DIR=str(state),XDG_RUNTIME_DIR=str(runtime),
                     PIPEWIRE_RUNTIME_DIR=str(runtime),PIPEWIRE_REMOTE='rog-graph-'+uuid.uuid4().hex[:12],
                     XDG_CONFIG_HOME=str(state/'config'),XDG_DATA_HOME=str(state/'data'),
                     XDG_CACHE_HOME=str(state/'cache'),QT_QPA_PLATFORM='offscreen',QT_QUICK_BACKEND='software',
                     QT_LOGGING_RULES='easyeffects.debug=true')
    for key in ('PIPEWIRE_CONFIG_DIR','PIPEWIRE_CONFIG_NAME','PULSE_SINK','PULSE_SOURCE'):environment.pop(key,None)
    locations=kit.roots(environment)
    for name in manifest['files']:
        relative=name.split('/',1)[1];target=locations['data']/relative;kit.mkdir(target.parent);kit.replace(target,kit.read(root/name))
    settings=kit.settings(b'',manifest).replace(b'presetsAutoloadInterval=0',b'presetsAutoloadInterval=1000')
    target=locations['config']/'db/easyeffectsrc';kit.mkdir(target.parent);kit.replace(target,settings)
    conf=state/'config/pipewire/pipewire.conf.d/99-private.conf';kit.mkdir(conf.parent)
    conf.write_text('context.properties = { core.name = "'+environment['PIPEWIRE_REMOTE']+'" }\n'
                    'context.modules = [ { name = libpipewire-module-client-device } ]\n')
    graph=Graph(output,environment);node_name=manifest['binding']['node_name'];observations=[]
    try:
        graph.start('pipewire',['pipewire']);graph.until(lambda _:True)
        graph.start('wireplumber',['wireplumber'])
        device=graph.start('mock-device',[mock],pipe=True)
        # The exporter announces its real global ID, without a hardware backend.
        import selectors
        selector=selectors.DefaultSelector();selector.register(device.stdout,selectors.EVENT_READ)
        if not selector.select(15):raise GraphError('synthetic device did not export')
        line=device.stdout.readline().decode().strip();selector.close()
        if not line.startswith('device '):raise GraphError('synthetic SPA device export failed before bound ID')
        device_id=int(line.split()[1])
        for name in (node_name,'rog-hdmi','rog-usb'):
            properties={'factory.name':'support.null-audio-sink','node.name':name,'node.description':'Synthetic graph sink',
                        'media.class':'Audio/Sink','audio.position':['FL','FR'],'object.linger':True}
            if name in (node_name,'rog-hdmi'):
                properties.update({'device.id':device_id,'card.profile.device':0 if name==node_name else 1,'device.api':'alsa'})
            graph.call(['pw-cli','create-node','adapter',json.dumps(properties)])
        physical=graph.until(lambda g:graph.node(g,node_name));graph.call(['wpctl','set-default',str(physical['id'])])
        graph.start('easyeffects',[binary,'--hide-window','--service-mode'])
        graph.until(lambda g:graph.node(g,'rog_audio_speaker_sink'))
        graph.until(lambda _:graph.preset(binary)==manifest['preset_name'])
        # Both sinks share one exported Device; only profile-device index1 changes.
        device.stdin.write(b'other-route\n');device.stdin.flush()
        graph.until(lambda g:any(x['type']=='PipeWire:Interface:Device' and x['id']==device_id and
                                 any(r.get('device')==1 and r.get('name')=='hdmi-output-1'
                                     for r in x.get('info',{}).get('params',{}).get('Route',[])) for x in g))
        deadline=time.monotonic()+2.2
        while time.monotonic()<deadline:
            if graph.preset(binary)!=manifest['preset_name']:
                raise GraphError('unrelated profile-device route changed automatic speaker preset')
            time.sleep(.1)
        observations.append('automatic preset selected; unrelated route index preserved it')
        for uri in ('http://lsp-plug.in/plugins/lv2/para_equalizer_x32_lr',
                    'http://lsp-plug.in/plugins/lv2/sc_limiter_stereo'):graph.call(['lv2info',uri])
        default=graph.start('default-player',[player,'rog-default'])
        graph.until(lambda g:graph.linked(g,'rog-default','rog_audio_speaker_sink'))
        for name,target in (('rog-hdmi-player','rog-hdmi'),('rog-usb-player','rog-usb')):
            graph.start(name,[player,name,target]);graph.until(lambda g:graph.linked(g,name,target))
            if graph.linked(graph.dump(),name,'rog_audio_speaker_sink'):raise GraphError('explicit target intercepted')
        observations.extend(['ordinary app processed','explicit HDMI preserved','explicit USB preserved'])
        log=output/'easyeffects.log'
        deadline=time.monotonic()+15
        while time.monotonic()<deadline and 'kernel correctly loaded' not in log.read_text(errors='replace'):time.sleep(.05)
        if 'kernel correctly loaded' not in log.read_text(errors='replace'):raise GraphError('actual IR loader did not confirm kernel')
        expected={x.split('#')[0] for x in json.loads(kit.read(root/'speaker-source/preset.json'))['output']['plugins_order']}
        actual={x.get('info',{}).get('props',{}).get('node.name','').removeprefix('rog_audio_soe_') for x in graph.dump() if x['type']=='PipeWire:Interface:Node'}
        if not expected<=actual:raise GraphError('emitted plugin nodes missing')
        observations.append('actual preset/IR/plugins loaded')
        # Default change returns ordinary streams to the user's selected sink.
        usb=graph.node(graph.dump(),'rog-usb');graph.call(['wpctl','set-default',str(usb['id'])])
        graph.until(lambda g:graph.linked(g,'rog-default','rog-usb'))
        graph.stop(default)
        direct=graph.start('direct-effects-player',[player,'rog-direct','rog_audio_speaker_sink'])
        graph.until(lambda g:graph.linked(g,'rog-direct','rog_audio_speaker_sink'))
        capture=graph.start('capture-corrected',[player,'--capture',node_name,str(output/'corrected.raw')])
        time.sleep(.5);graph.stop(capture);corrected=rms(output/'corrected.raw')
        capture=graph.start('capture-bypass',[player,'--capture',node_name,str(output/'bypass.raw')])
        time.sleep(.2);device.stdin.write(b'headphones\n');device.stdin.flush();time.sleep(.3);graph.stop(capture)
        bypass=rms(output/'bypass.raw');expected_rms=.1/math.sqrt(2)
        if abs(bypass-expected_rms)>expected_rms*.05:raise GraphError('route-event output bypass failed before delayed autoload')
        if abs(corrected-bypass)<bypass*.05:raise GraphError('loaded correction did not change generated signal')
        observations.extend(['default change preserved','route-event DSP bypass before 1000 ms autoload'])
        graph.stop(direct)
        for child in list(graph.processes):
            if child.args[0]==player:graph.stop(child)
        stock_root=output/'stock';stock_root.mkdir()
        stock_env=dict(environment,XDG_CONFIG_HOME=str(stock_root/'config'),
                       XDG_DATA_HOME=str(stock_root/'data'),XDG_CACHE_HOME=str(stock_root/'cache'))
        stock=graph.start('stock-easyeffects',['/usr/bin/easyeffects','--hide-window','--service-mode'],environment=stock_env)
        graph.until(lambda g:graph.node(g,'easyeffects_sink'))
        result=subprocess.run(['/usr/bin/easyeffects','--quit'],env=stock_env,capture_output=True,timeout=15)
        if result.returncode:raise GraphError('stock app control failed')
        graph.processes.remove(stock);stock.wait(timeout=5)
        if not graph.node(graph.dump(),'rog_audio_speaker_sink'):raise GraphError('stock quit reached candidate')
        for name,digest in manifest['files'].items():
            if kit.sha(kit.read(locations['data']/name.split('/',1)[1]))!=digest:
                raise GraphError('stock app changed candidate payload')
        if (stock_root/'data/easyeffects/output'/ (manifest['preset_name']+'.json')).exists():
            raise GraphError('stock consumed candidate preset')
        observations.append('stock startup/config/control isolated')
        # The analog route is still headphones, so interception is inactive while
        # the real default metadata receives a deliberately typed original pair.
        explicit=graph.start('explicit-speaker',[player,'rog-explicit-speaker',node_name])
        graph.until(lambda g:graph.linked(g,'rog-explicit-speaker',node_name))
        current=graph.dump();stream_id=graph.node(current,'rog-explicit-speaker')['id']
        physical_id=graph.node(current,node_name)['id']
        original_targets={'target.node':{'type':'Spa:Id','value':str(physical_id)},
                          'target.object':{'type':'Spa:String','value':node_name}}
        for key,property in original_targets.items():
            graph.call(['pw-metadata','-n','default',str(stream_id),key,property['value'],property['type']])
        graph.until(lambda g:graph.targets(g,stream_id)==original_targets)
        effects=graph.node(graph.dump(),'rog_audio_speaker_sink')
        owned_targets={'target.node':{'type':'Spa:Id','value':str(effects['id'])},
                       'target.object':{'type':'Spa:Id','value':str(effects['info']['props']['object.serial'])}}
        device.stdin.write(b'speaker\n');device.stdin.flush()
        graph.until(lambda g:graph.linked(g,'rog-explicit-speaker','rog_audio_speaker_sink') and
                             graph.targets(g,stream_id)==owned_targets)
        graph.call([binary,'--quit'])
        # Stop watching primary lifetime once it is intentionally quitting.
        app=next(p for p in graph.processes if p.args[0]==binary)
        graph.processes.remove(app)
        try:app.wait(timeout=5)
        except subprocess.TimeoutExpired:graph.processes.append(app);raise GraphError('candidate did not quit')
        graph.until(lambda g:graph.linked(g,'rog-explicit-speaker',node_name) and
                             graph.targets(g,stream_id)==original_targets)
        if 'rog-usb' not in graph.call(['pw-metadata','-n','default','0','default.audio.sink']):
            raise GraphError('runtime changed physical default')
        observations.extend(['graceful quit restored exact typed metadata pair','physical default remains USB'])
        graph.stop(explicit)
        receipt={'schema_version':1,'case':case,'status':'passed','evidence_kind':'isolated-synthetic-runtime',
                 'hardware':manifest['hardware'],'binary_sha256':manifest['runtime']['binary_sha256'],
                 'speaker_bundle_manifest_sha256':manifest['speaker_bundle_manifest_sha256'],
                 'assertions':observations,'corrected_rms':corrected,'bypass_rms':bypass,
                 'physical_device_or_session_access':False,'acoustic_or_physical_latency_measurement':False}
        kit.replace(output/'receipt.json',kit.encoded(receipt));return receipt
    finally:graph.close()


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--case',choices=('asus-loader-route','lenovo-loader-route'),required=True)
    parser.add_argument('--kit',required=True);parser.add_argument('--output',required=True)
    parser.add_argument('--binary',default='/opt/rog-audio/easyeffects/bin/easyeffects')
    parser.add_argument('--mock-device',default='/opt/rog-audio/mock-device');parser.add_argument('--player',default='/opt/rog-audio/synthetic-player')
    parser.add_argument('--private-dbus',action='store_true',help=argparse.SUPPRESS);args=parser.parse_args(argv)
    if not args.private_dbus:
        return subprocess.run(['dbus-run-session','--',sys.executable,str(Path(__file__).resolve()),
                               *(sys.argv[1:] if argv is None else argv),'--private-dbus']).returncode
    try:
        result=acceptance(args.kit,args.case,args.output,args.binary,args.mock_device,args.player)
        print(json.dumps({'case':args.case,'status':result['status'],'assertion_count':len(result['assertions'])}));return 0
    except (GraphError,kit.InstallError,OSError,ValueError,KeyError,TypeError,subprocess.SubprocessError) as error:
        try:
            if kit.safe(args.output).is_dir():kit.replace(Path(args.output)/'failure.json',kit.encoded({'case':args.case,'exception':type(error).__name__,'detail':str(error)}))
        except (kit.InstallError,OSError):pass
        print(json.dumps({'case':args.case,'status':'failed','reason':'synthetic_graph_acceptance_failed'}));return 1

if __name__=='__main__':raise SystemExit(main())
