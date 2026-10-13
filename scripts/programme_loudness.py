"""Schema for independent programme leveling; no host or DSP side effects."""
import hashlib
import json
import math
import re

CONTRACT = 'bounded-programme-makeup-v1'
DIGEST = re.compile(r'[0-9a-f]{64}\Z')

def canonical(value):
    return (json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()

def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()

def number(value,minimum,maximum):
    if type(value) not in (int,float) or not math.isfinite(value) or not minimum<=value<=maximum:
        raise ValueError('invalid_programme_loudness_number')
    return float(value)

def stage(settings):
    return {'bypass':False,'input-gain':0.0,'output-gain':0.0,
            'target':settings['target_lufs'],'maximum-gain':settings['maximum_gain_db'],
            'silence-threshold':settings['silence_threshold_lufs'],
            'maximum-history':settings['history_seconds'],'reference':'Integrated',
            'force-silence':False}

def validate(settings,output,report):
    expected={'contract','target_lufs','maximum_gain_db','history_seconds',
              'silence_threshold_lufs','source_fir_normalization_db',
              'above_source_budget','parent_bundle_manifest_sha256',
              'parent_preset_sha256','parent_report_sha256','preserved_stage_sha256'}
    if not isinstance(settings,dict) or set(settings)!=expected or settings['contract']!=CONTRACT:
        raise ValueError('unsupported_programme_loudness_contract')
    number(settings['target_lufs'],-100,0);number(settings['maximum_gain_db'],0,36)
    number(settings['silence_threshold_lufs'],-100,0)
    if type(settings['history_seconds']) is not int or not 6<=settings['history_seconds']<=3600:
        raise ValueError('invalid_programme_loudness_history')
    budget=number(settings['source_fir_normalization_db'],0,120)
    if budget!=report['signal_checks']['fir_attenuation_db']:
        raise ValueError('source_gain_budget_mismatch')
    above=settings['maximum_gain_db']>budget
    if type(settings['above_source_budget']) is not bool or settings['above_source_budget']!=above:
        raise ValueError('invalid_gain_budget_advisory')
    for name in ('parent_bundle_manifest_sha256','parent_preset_sha256','parent_report_sha256'):
        if not isinstance(settings[name],str) or not DIGEST.fullmatch(settings[name]):
            raise ValueError('invalid_programme_parent_hash')
    order=output['plugins_order']
    selected=output['autogain#0']
    if not isinstance(selected,dict) or set(selected)!=set(stage(settings)):
        raise ValueError('invalid_programme_leveler_stage')
    for key in ('input-gain','output-gain','target','maximum-gain','silence-threshold'):
        if type(selected[key]) not in (int,float) or not math.isfinite(selected[key]):
            raise ValueError('invalid_programme_leveler_number')
    if type(selected['maximum-history']) is not int or type(selected['bypass']) is not bool or type(selected['force-silence']) is not bool:
        raise ValueError('invalid_programme_leveler_controls')
    if order[-2:]!=['autogain#0','limiter#0'] or selected!=stage(settings):
        raise ValueError('invalid_programme_leveler_stage')
    limiter=output['limiter#0']
    if limiter.get('bypass') is not False or limiter.get('gain-boost') is not False or limiter.get('threshold')!=-1 or limiter.get('input-gain')!=0 or limiter.get('output-gain')!=0:
        raise ValueError('programme_requires_original_minus_one_db_limiter')
    preserved=settings['preserved_stage_sha256']
    if not isinstance(preserved,dict) or set(preserved)!=set(order)-{'autogain#0'}:
        raise ValueError('invalid_preserved_stage_inventory')
    for name in preserved:
        if preserved[name]!=digest(output[name]):raise ValueError('voicing_stage_changed')
    if report.get('programme_loudness')!=settings:
        raise ValueError('programme_report_mismatch')
