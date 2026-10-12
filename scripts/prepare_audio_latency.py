#!/usr/bin/env python3
"""Generate a private application/endpoint latency request, without activation."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from audio_common import digest, load_json, schema, write_private, write_text, PrivateArgumentParser
from inspect_audio import graph, integer, version, validate_inventory


CONFIG_FILE = '90-audio-latency-trial.conf'


def prepare(inventory, source_hash, quantum, node_name, route_name, client_binary):
    validate_inventory(inventory)
    if type(quantum) is not int or quantum not in (64,128,256):
        raise ValueError('supported requests are 64, 128 or 256 frames')
    versions = {x: version(inventory,x) for x in ('pipewire','wireplumber')}
    # These configuration interfaces are bounded to the inspected major/minor series.
    if not versions['pipewire'] or not re.fullmatch(r'1\.[4-6]\.\d+', versions['pipewire']) or not versions['wireplumber'] or not re.fullmatch(r'0\.5\.\d+',versions['wireplumber']):
        raise ValueError('unsupported or unknown installed config versions')
    if not isinstance(client_binary,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',client_binary):
        raise ValueError('client binary must be an explicit basename')
    if not isinstance(node_name,str) or not re.fullmatch(r'alsa_output\.[A-Za-z0-9_.:-]{1,200}',node_name):
        raise ValueError('target must be an exact ALSA output name')
    data = graph(inventory)
    nodes = [x for x in data if x.get('type') == 'PipeWire:Interface:Node' and x.get('info',{}).get('props',{}).get('node.name') == node_name]
    if len(nodes) != 1:
        raise ValueError('ambiguous or absent target node')
    props = nodes[0]['info']['props']
    if props.get('media.class') != 'Audio/Sink' or props.get('device.api') != 'alsa':
        raise ValueError('target is not an ALSA sink')
    device_id = props.get('device.id')
    profile_device = props.get('card.profile.device')
    if integer(device_id,0,2147483647) is None or integer(profile_device,0,2147483647) is None:
        raise ValueError('missing target identifiers')
    device = [x for x in data if type(x.get('id')) is int and x.get('id') == device_id and x.get('type') == 'PipeWire:Interface:Device']
    if len(device) != 1:
        raise ValueError('target device unavailable')
    routes = device[0].get('info',{}).get('params',{}).get('Route',[])
    if not isinstance(routes,list):
        raise ValueError('invalid routes')
    active = [x for x in routes if isinstance(x,dict) and x.get('direction') == 'Output' and type(x.get('device')) is int and x.get('device') == profile_device]
    if len(active) != 1 or active[0].get('name') != route_name:
        raise ValueError('target route is ambiguous or changed')
    cores = [x for x in data if x.get('type') == 'PipeWire:Interface:Core']
    if len(cores) != 1:
        raise ValueError('ambiguous graph core')
    core = cores[0]['info'].get('props',{})
    rate = integer(core.get('default.clock.rate'))
    previous_quantum = integer(core.get('default.clock.quantum'))
    if rate != 48000 or previous_quantum is None:
        raise ValueError('candidate requires observed 48 kHz default')
    configs = inventory.get('user_config',{})
    if configs.get('status') != 'ok' or not isinstance(configs.get('files'),list):
        raise ValueError('previous user configuration unavailable')
    previous = []
    for entry in configs['files']:
        if not isinstance(entry,dict) or entry.get('status') != 'ok' or not isinstance(entry.get('text'),str) or digest(entry['text'].encode()) != entry.get('sha256'):
            raise ValueError('invalid prior user configuration')
        path = entry.get('path')
        if not isinstance(path,str) or Path(path).is_absolute() or '..' in Path(path).parts:
            raise ValueError('invalid previous config path')
        if Path(path).name == CONFIG_FILE:
            raise ValueError('candidate filename already exists in previous configuration')
        previous.append({'path':path,'sha256':entry['sha256']})
    # target.object AND binary AND output stream prevent blanket graph forcing.
    config = ('# Candidate only: suggested latency, graph negotiation must be observed.\n'
              'stream.rules = [\n  {\n    matches = [ {\n'
              f'      application.process.binary = {json.dumps(client_binary)}\n'
              f'      target.object = {json.dumps(node_name)}\n'
              '      media.class = "Stream/Output/Audio"\n'
              '    } ]\n    actions = { update-props = {\n'
              f'      node.latency = "{quantum}/{rate}"\n'
              '    } }\n  }\n]\n')
    manifest = {'schema_version':1, 'kind':'audio-latency-candidate', 'activation_state':'not-installed',
                'inventory_sha256':source_hash, 'versions':versions, 'previous_config_root':inventory.get('config_root'),
                'config_sha256':digest(config.encode()), 'validation_state':'unvalidated',
                'target':{'node_name':node_name,'route_name':route_name,'client_binary':client_binary},
                'observed':{'default_quantum_frames':previous_quantum,'default_rate_hz':rate,
                            'graph_period_ms':1000*previous_quantum/rate,
                            'node_latency':props.get('node.latency'), 'previous_user_config':previous},
                'proposed':{'node_latency':f'{quantum}/{rate}', 'requested_period_ms':1000*quantum/rate},
                'unknowns':['negotiated quantum','physical latency','PulseAudio client buffering','DSP delay'],
                'limits':['native PipeWire client rule only; PulseAudio clients are outside this experiment',
                          'shared endpoint routes can change; re-inspect route before activation',
                          'no global quantum, scheduling, ALSA batch, mixer, default-route or protection changes']}
    return config,manifest


def write_bundle(output, config, manifest, inventory):
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise FileExistsError('bundle exists')
    # Stage entirely in the same parent and publish using an exclusive directory.
    temp = Path(tempfile.mkdtemp(prefix='.audio-trial-',dir=output.parent))
    try:
        write_text(temp/CONFIG_FILE,config)
        write_private(temp/'manifest.json',manifest)
        write_private(temp/'previous-user-config.json',inventory['user_config'])
        write_text(temp/'RESTORE.txt',
                   'NOT INSTALLED. This bundle makes no live changes.\n'
                   'Before an authorised test: verify inventory hashes and target route; snapshot routing, mixer,\n'
                   'PipeWire metadata and configs again. Preserve stock packages/firmware and previous defaults.\n'
                   'Only in the coordinated test window, place this fragment in the user PipeWire\n'
                   'client.conf.d directory after checking it is absent. Restart only the named test client.\n'
                   'Request the exact target endpoint in that native client; inspect negotiated graph timing.\n'
                   'Rollback: stop that test client, remove only the trial fragment if its hash matches the\n'
                   'manifest, then relaunch the prior client. Re-inspect defaults and graph. No service restart\n'
                   'is required by this application-scoped experiment. Do not overwrite prior configuration.\n')
        os.mkdir(output,0o700)  # Fails on concurrent creation; never replaces a destination.
        for path in temp.iterdir():
            os.rename(path,output/path.name)
    finally:
        shutil.rmtree(temp)


def main():
    parser = PrivateArgumentParser(description=__doc__)
    parser.add_argument('--inventory',required=True)
    parser.add_argument('--quantum',required=True,type=int,choices=(64,128,256))
    parser.add_argument('--node-name',required=True)
    parser.add_argument('--route-name',required=True)
    parser.add_argument('--client-binary',required=True)
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    try:
        inventory,sha=load_json(args.inventory)
        config,manifest=prepare(inventory,sha,args.quantum,args.node_name,args.route_name,args.client_binary)
        write_bundle(args.output,config,manifest,inventory)
        return 0
    except (ValueError,OSError,TypeError,KeyError,RecursionError):
        parser.exit(2,'candidate refused: invalid inventory/target, unavailable prior config, or destination exists\n')


if __name__ == '__main__':
    raise SystemExit(main())
