#!/usr/bin/env python3
"""Prepare adjustable programme leveling alongside the original speaker voicing.

Offline only: no package install, service change, playback or recording.
"""
import hashlib
import json
from pathlib import Path
import sys

import prepare_speaker_profile as speaker
import programme_loudness as programme
from audio_common import PrivateArgumentParser


def build(bundle,output,target=-20.0,maximum=None,history=15,silence=-50.0):
    bundle=speaker.no_symlinks(Path(bundle));speaker.verify(bundle)
    manifest_bytes=speaker.read_file(bundle/'manifest.json')
    preset_bytes=speaker.read_file(bundle/'preset.json')
    report_bytes=speaker.read_file(bundle/'field-mapping.json')
    manifest=speaker.json_load(manifest_bytes);preset=speaker.json_load(preset_bytes)
    report=speaker.json_load(report_bytes);out=preset['output']
    budget=programme.number(report['signal_checks']['fir_attenuation_db'],0,120)
    maximum=min(budget,36.0) if maximum is None else programme.number(maximum,0,36)
    settings={'contract':programme.CONTRACT,'target_lufs':programme.number(target,-100,0),
              'maximum_gain_db':maximum,'history_seconds':history,
              'silence_threshold_lufs':programme.number(silence,-100,0),
              'source_fir_normalization_db':budget,'above_source_budget':maximum>budget,
              'parent_bundle_manifest_sha256':hashlib.sha256(manifest_bytes).hexdigest(),
              'parent_preset_sha256':hashlib.sha256(preset_bytes).hexdigest(),
              'parent_report_sha256':hashlib.sha256(report_bytes).hexdigest(),
              'preserved_stage_sha256':{n:programme.digest(out[n]) for n in out['plugins_order'] if n!='autogain#0'}}
    out['plugins_order']=[n for n in out['plugins_order'] if n!='autogain#0']
    out['plugins_order'].insert(len(out['plugins_order'])-1,'autogain#0')
    out['autogain#0']=programme.stage(settings)
    # The generic leveler replaces the old bypassed approximation. It is not
    # a newly qualified implementation of the original Dolby volume leveler.
    for field in report['fields']:
        if field['output_stage']=='autogain#0':
            field['output_stage']=None;field['status']='not-emitted'
            field['approximation']='OEM leveler is not implemented; this bundle uses independent bounded EBU programme leveling.'
    if 'dynamics_emitted' in report.get('interpreted_selection',{}):
        report['interpreted_selection']['dynamics_emitted']=[n for n in report['interpreted_selection']['dynamics_emitted'] if n!='autogain#0']
    report['stages']=[{'name':n,'bypassed':out[n]['bypass']} for n in out['plugins_order']]
    report['programme_loudness']=settings;manifest['programme_loudness']=settings
    report['limits'].append('Independent programme makeup has an adjustable DSP cap; FIR normalization is an engineering budget, not an acoustic or amplifier safety bound.')
    programme.validate(settings,out,report)
    files={'preset.json':speaker.json_bytes(preset),'field-mapping.json':speaker.json_bytes(report),
           manifest['impulse']:speaker.read_file(bundle/manifest['impulse'])}
    manifest['outputs']={n:speaker.digest(b) for n,b in files.items()}
    files['manifest.json']=speaker.json_bytes(manifest)
    output=speaker.no_symlinks(Path(output));speaker.require(not output.exists() and output.parent.is_dir(),'output_exists_or_parent_missing')
    with speaker.parent_fd(output) as (parent,name):
        import os
        os.mkdir(name,0o700,dir_fd=parent)
    # Retain partial output on failure. This public pathname may have been
    # renamed/replaced since creation; deleting by pathname could erase an
    # unrelated replacement directory. Recovery is an explicit operator step.
    (output/'irs').mkdir(mode=0o700)
    for name,data in files.items():speaker.new_file(output/name,data)
    speaker.verify(output)
    return {'result':'prepared','activation_state':'not-installed',
            'qualification':'offline-candidate-unqualified','programme_loudness_contract':programme.CONTRACT,
            'target_lufs':settings['target_lufs'],'maximum_gain_db':maximum,
            'source_fir_normalization_db':budget,'above_source_budget_advisory':maximum>budget,
            'manifest_sha256':speaker.digest(files['manifest.json'])}


def main(argv=None):
    p=PrivateArgumentParser(description=__doc__)
    p.add_argument('--bundle',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--target-lufs',type=float,default=-20.0)
    p.add_argument('--maximum-gain-db',type=float)
    p.add_argument('--history-seconds',type=int,default=15)
    p.add_argument('--silence-threshold-lufs',type=float,default=-50.0)
    a=p.parse_args(argv)
    try:
        result=build(a.bundle,a.output,a.target_lufs,a.maximum_gain_db,a.history_seconds,a.silence_threshold_lufs)
        print(json.dumps(result,sort_keys=True,allow_nan=False));return 0
    except (speaker.ProfileError,ValueError,KeyError,TypeError,OSError,AttributeError,IndexError,OverflowError):
        print(json.dumps({'result':'failed','reason':'invalid_loudness_bundle_or_controls'}),file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
