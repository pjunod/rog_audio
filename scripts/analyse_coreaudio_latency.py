#!/usr/bin/env python3
"""Summarise read-only HAL output properties; no playback or physical measurement."""
import json
import math
import os
from pathlib import Path
import re
import stat

from audio_common import LIMIT, PrivateArgumentParser, digest, unique, write_private

STATES = {'ok', 'unavailable', 'error', 'invalid-data'}
BUILTIN = int.from_bytes(b'bltn', 'big')
TRANSPORTS = {BUILTIN: 'built-in', int.from_bytes(b'usb ', 'big'): 'usb',
              int.from_bytes(b'blue', 'big'): 'bluetooth', int.from_bytes(b'blte', 'big'): 'bluetooth-le',
              int.from_bytes(b'hdmi', 'big'): 'hdmi', int.from_bytes(b'dprt', 'big'): 'displayport',
              int.from_bytes(b'grup', 'big'): 'aggregate', int.from_bytes(b'virt', 'big'): 'virtual'}
FORMAT_KEYS = ('rate_hz', 'channels', 'format_id', 'format_flags', 'bytes_per_packet',
               'frames_per_packet', 'bytes_per_frame', 'bits_per_channel')


def number(value, minimum, maximum, integer=False):
    if type(value) not in ((int,) if integer else (int, float)):
        raise ValueError('invalid numeric property')
    if not minimum <= value <= maximum or not math.isfinite(value):
        raise ValueError('invalid numeric property')
    return value


def uint(value):
    return number(value, 0, 2**32 - 1, integer=True)


def rate(value):
    return number(value, 1, 768000)


def prop(value, validator):
    if not isinstance(value, dict) or set(value) != {'status', 'os_status', 'value'}:
        raise ValueError('invalid property envelope')
    state = value['status']
    if not isinstance(state, str) or state not in STATES:
        raise ValueError('invalid property state')
    code = number(value['os_status'], -(2**31), 2**31 - 1, integer=True)
    if state == 'ok':
        if code != 0:
            raise ValueError('invalid success state')
        data = validator(value['value'])
    else:
        if value['value'] is not None:
            raise ValueError('invalid failed property')
        data = None
    return {'status': state, 'os_status': code, 'value': data}


def array(value):
    if not isinstance(value, list) or len(value) > 128:
        raise ValueError('invalid object list')
    return value


def format_value(value):
    if not isinstance(value, dict) or set(value) != set(FORMAT_KEYS):
        raise ValueError('invalid stream format')
    result = {key: (rate(value[key]) if key == 'rate_hz' else uint(value[key])) for key in FORMAT_KEYS}
    number(result['channels'], 1, 128, integer=True)
    return result


def range_value(value):
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError('invalid buffer range')
    lower = number(value[0], 1, 2**32 - 1)
    upper = number(value[1], lower, 2**32 - 1)
    return [lower, upper]


def frames_ms(frames, nominal_rate):
    return frames * 1000 / nominal_rate if frames is not None and nominal_rate is not None else None


def public_format(property_value):
    result = {'status': property_value['status'], 'os_status': property_value['os_status'], 'value': None}
    value = property_value['value']
    if value is not None:
        result['value'] = {key: value[key] for key in ('rate_hz', 'channels', 'bits_per_channel')}
        result['value']['encoding'] = 'linear-pcm' if value['format_id'] == int.from_bytes(b'lpcm', 'big') else 'other'
    return result


def summarise(capture, source_sha256):
    if not isinstance(source_sha256, str) or not re.fullmatch(r'[0-9a-f]{64}', source_sha256):
        raise ValueError('invalid source hash')
    if not isinstance(capture, dict) or type(capture.get('schema_version')) is not int or capture['schema_version'] != 1:
        raise ValueError('unsupported inventory schema')
    if capture.get('kind') != 'coreaudio-output-inventory' or capture.get('evidence_kind') != 'live-read-only':
        raise ValueError('unsupported inventory kind')
    defaults = {key: prop(capture[key], uint) for key in ('default_output_before', 'default_output_after',
                                                       'system_output_before', 'system_output_after')}
    defaults_available = all(item['status'] == 'ok' and item['value'] != 0 for item in defaults.values())
    stable = (defaults['default_output_before']['value'] == defaults['default_output_after']['value'] and
              defaults['system_output_before']['value'] == defaults['system_output_after']['value']) if defaults_available else None
    device_list = prop(capture['devices'], array)
    public_devices, seen_devices, seen_streams = [], set(), set()
    for index, raw in enumerate(device_list['value'] or []):
        if not isinstance(raw, dict):
            raise ValueError('invalid device object')
        object_id = uint(raw['object_id'])
        if object_id == 0 or object_id in seen_devices:
            raise ValueError('duplicate or unknown device object')
        seen_devices.add(object_id)
        integers = {key: prop(raw[key], uint) for key in ('transport_type', 'buffer_frames',
                    'output_device_latency_frames', 'output_safety_offset_frames', 'is_running', 'is_alive')}
        if integers['buffer_frames']['value'] == 0:
            raise ValueError('invalid buffer size')
        rates = {key: prop(raw[key], rate) for key in ('nominal_rate_hz', 'actual_rate_hz')}
        nominal = rates['nominal_rate_hz']['value']
        stream_list = prop(raw['output_streams'], array)
        streams = []
        for stream_index, stream in enumerate(stream_list['value'] or []):
            if not isinstance(stream, dict):
                raise ValueError('invalid stream object')
            stream_id = uint(stream['object_id'])
            if stream_id == 0 or stream_id in seen_streams:
                raise ValueError('duplicate or unknown stream object')
            seen_streams.add(stream_id)
            latency = prop(stream['latency_frames'], uint)
            active = prop(stream['is_active'], uint)
            terminal = prop(stream['terminal_type'], uint)
            virtual = prop(stream['virtual_format'], format_value)
            physical = prop(stream['physical_format'], format_value)
            formats_available = nominal is not None and virtual['value'] is not None and physical['value'] is not None
            aligned = (nominal == virtual['value']['rate_hz'] == physical['value']['rate_hz']) if formats_available else None
            device_frames = integers['output_device_latency_frames']['value']
            stream_frames = latency['value']
            combined = device_frames + stream_frames if device_frames is not None and stream_frames is not None else None
            streams.append({'alias': 'stream-' + str(stream_index + 1), 'latency_frames': latency,
                            'is_active': active, 'terminal_type': {'status': terminal['status'],
                                'os_status': terminal['os_status'], 'kind': {
                                    int.from_bytes(b'spkr', 'big'): 'speaker',
                                    int.from_bytes(b'hdph', 'big'): 'headphones'}.get(terminal['value'], 'unclassified')},
                            'virtual_format': public_format(virtual), 'physical_format': public_format(physical),
                            'formats_match_device_nominal_rate': aligned,
                            'reported_stream_latency_ms': frames_ms(stream_frames, nominal) if aligned else None,
                            'reported_device_plus_stream_latency_ms': frames_ms(combined, nominal) if aligned else None})
        properties = {**rates, **{key: value for key, value in integers.items() if key != 'transport_type'},
                      'buffer_range_frames': prop(raw['buffer_range_frames'], range_value)}
        public_devices.append({'alias': 'output-' + str(index + 1),
                               'transport': TRANSPORTS.get(integers['transport_type']['value'], 'unknown'),
                               'transport_status': integers['transport_type']['status'],
                               'transport_os_status': integers['transport_type']['os_status'],
                               'is_default_output': object_id == defaults['default_output_before']['value'] if defaults_available else None,
                               'is_system_output': object_id == defaults['system_output_before']['value'] if defaults_available else None,
                               'reported_properties': properties, 'output_streams_status': stream_list['status'],
                               'output_streams_os_status': stream_list['os_status'], 'streams': streams,
                               'buffer_period_ms': frames_ms(integers['buffer_frames']['value'], nominal),
                               'reported_device_latency_ms': frames_ms(integers['output_device_latency_frames']['value'], nominal),
                               'safety_offset_ms': frames_ms(integers['output_safety_offset_frames']['value'], nominal)})
    defaults_listed = all(value['value'] in seen_devices for value in defaults.values()
                          if value['status'] == 'ok' and value['value'] != 0)
    partial = device_list['status'] != 'ok' or stable is not True or not defaults_listed or any(
        device['output_streams_status'] != 'ok' or device['transport_status'] != 'ok' or
        device['reported_properties']['is_alive']['value'] == 0 or
        any(value['status'] != 'ok' for value in device['reported_properties'].values()) or
        any(stream['latency_frames']['status'] != 'ok' or stream['is_active']['status'] != 'ok' or
            stream['terminal_type']['status'] != 'ok' or stream['virtual_format']['status'] != 'ok' or
            stream['physical_format']['status'] != 'ok' for stream in device['streams']) for device in public_devices)
    return {'schema_version': 1, 'kind': 'coreaudio-output-timing-summary', 'evidence_kind': 'reported-software-parameters',
            'source_sha256': source_sha256, 'collection_status': 'partial' if partial else 'ok',
            'device_inventory_status': device_list['status'], 'device_inventory_os_status': device_list['os_status'],
            'default_route_stable_during_snapshot': stable,
            'default_property_statuses': {key: {'status': value['status'], 'os_status': value['os_status']} for key, value in defaults.items()},
            'devices': public_devices, 'physical_latency_ms': None, 'settings_or_services_changed': False,
            'limits': ['Sequential HAL getters are a snapshot, not an atomic or active-client timing measurement.',
                       'Buffer period and safety offset remain separate from reported device/stream latency.',
                       'Device-plus-stream latency is driver-reported with aligned format rates; it is not an acoustic delay.',
                       'No application queue, callback scheduling, arbitrary plugin or event-to-sound measurement is included.',
                       'Idle/running and enabled-stream states differ; nominal/actual rates are API reports, not clock calibration.']}


def read_capture(path):
    fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
    try:
        if not stat.S_ISREG(os.fstat(fd).st_mode):
            raise ValueError('invalid capture file')
        with os.fdopen(fd, 'rb', closefd=False) as stream:
            data = stream.read(LIMIT + 1)
        if len(data) > LIMIT:
            raise ValueError('capture exceeds size limit')
    finally:
        os.close(fd)
    parsed = json.loads(data, object_pairs_hook=unique,
                        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('invalid JSON constant')))
    return parsed, digest(data)


def main(argv=None):
    parser = PrivateArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    try:
        capture, source_hash = read_capture(Path(args.input))
        summary = summarise(capture, source_hash)
        write_private(Path(args.output), summary)
        print(json.dumps({'status': summary['collection_status'], 'outputs': len(summary['devices']),
                          'physical_latency_ms': None, 'settings_or_services_changed': False}))
        return 0
    except (OSError, ValueError, KeyError, TypeError, RecursionError, OverflowError):
        print(json.dumps({'status': 'error', 'reason': 'coreaudio_inventory_unavailable_or_invalid'}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
