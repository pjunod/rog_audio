#!/usr/bin/env python3
"""Compose a per-device graph-test kit from a real converted tuning bundle.

The route inventory is invented; these bindings never describe a laptop.
Actual per-host install kits use fresh read-only inventories instead.
"""
import json
from pathlib import Path
from audio_common import PrivateArgumentParser
import speaker_install as kit


def prepare(bundle,runtime,device,output):
    manifest=kit.document(Path(bundle)/'manifest.json')
    subsystem={'asus':'10431c63','thinkpad':'17aa2276'}[device]
    kit.require(manifest['hardware']['codec']=='10ec0285' and manifest['hardware']['subsystem']==subsystem,
                'graph_fixture_device_mismatch')
    node='alsa_output.rog_fixture.'+device
    graph=[{'type':'PipeWire:Interface:Node','info':{'props':{
        'node.name':node,'media.class':'Audio/Sink','device.api':'alsa','api.alsa.pcm.card':3,
        'device.id':42,'card.profile.device':0}}},
        {'id':42,'type':'PipeWire:Interface:Device','info':{'params':{'Route':[
          {'device':0,'direction':'Output','name':'analog-output-speaker','description':'Speakers'}]}}}]
    inventory={'schema_version':1,'kind':'audio-inventory','evidence_kind':'invented-synthetic-inventory',
               'probes':{'graph':{'status':'ok','stdout':json.dumps(graph)}},
               'files':{'/proc/asound/card3/codec#0':{'status':'ok','text':
                        'Vendor Id: 0x10ec0285\nSubsystem Id: 0x'+subsystem+'\n'}}}
    return kit.prepare(bundle,inventory,output,runtime)


def main(argv=None):
    parser=PrivateArgumentParser(description=__doc__);parser.add_argument('--bundle',required=True)
    parser.add_argument('--runtime-manifest',required=True);parser.add_argument('--device',choices=('asus','thinkpad'),required=True)
    parser.add_argument('--output',required=True);args=parser.parse_args(argv)
    try:
        result=prepare(args.bundle,args.runtime_manifest,args.device,args.output)
        result['evidence_kind']='isolated-synthetic-preparation';print(json.dumps(result,sort_keys=True));return 0
    except (kit.InstallError,OSError,ValueError,KeyError,TypeError):
        print(json.dumps({'status':'error','reason':'invalid_graph_fixture_input'}));return 2

if __name__=='__main__':raise SystemExit(main())
