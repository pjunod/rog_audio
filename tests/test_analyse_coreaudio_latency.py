"""Synthetic HAL inventories only; these tests never invoke CoreAudio or audio IO."""
import contextlib
import copy
import io
import json
from pathlib import Path
import stat
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import analyse_coreaudio_latency as coreaudio

HASH = 'a' * 64


def property_value(value, status='ok', os_status=0):
    return {'status': status, 'os_status': os_status, 'value': value}


def fixture():
    format_value = {'rate_hz': 48000, 'channels': 2, 'format_id': int.from_bytes(b'lpcm', 'big'),
                    'format_flags': 9, 'bytes_per_packet': 8, 'frames_per_packet': 1,
                    'bytes_per_frame': 8, 'bits_per_channel': 32}
    stream = {'object_id': 8, 'latency_frames': property_value(960), 'terminal_type': property_value(769),
              'is_active': property_value(1), 'virtual_format': property_value(copy.deepcopy(format_value)),
              'physical_format': property_value(copy.deepcopy(format_value))}
    device = {'object_id': 7, 'transport_type': property_value(coreaudio.BUILTIN),
              'nominal_rate_hz': property_value(48000), 'actual_rate_hz': property_value(48000),
              'buffer_frames': property_value(480), 'buffer_range_frames': property_value([16, 4096]),
              'output_device_latency_frames': property_value(48), 'output_safety_offset_frames': property_value(96),
              'is_running': property_value(0), 'is_alive': property_value(1),
              'output_streams': property_value([stream])}
    return {'schema_version': 1, 'kind': 'coreaudio-output-inventory', 'evidence_kind': 'live-read-only',
            'default_output_before': property_value(7), 'default_output_after': property_value(7),
            'system_output_before': property_value(7), 'system_output_after': property_value(7),
            'devices': property_value([device])}


class SummaryTests(unittest.TestCase):
    def test_components_remain_separate_and_idle_is_not_running(self):
        result = coreaudio.summarise(fixture(), HASH)
        device = result['devices'][0]
        self.assertEqual(device['buffer_period_ms'], 10)
        self.assertEqual(device['reported_device_latency_ms'], 1)
        self.assertEqual(device['safety_offset_ms'], 2)
        self.assertEqual(device['streams'][0]['reported_stream_latency_ms'], 20)
        self.assertEqual(device['streams'][0]['reported_device_plus_stream_latency_ms'], 21)
        self.assertEqual(device['reported_properties']['is_running']['value'], 0)
        self.assertEqual(device['streams'][0]['is_active']['value'], 1)
        self.assertIsNone(result['physical_latency_ms'])
        self.assertEqual(result['evidence_kind'], 'reported-software-parameters')
        self.assertFalse(result['settings_or_services_changed'])

    def test_zero_latency_differs_from_unavailable_latency(self):
        raw = fixture()
        stream = raw['devices']['value'][0]['output_streams']['value'][0]
        stream['latency_frames'] = property_value(0)
        self.assertEqual(coreaudio.summarise(raw, HASH)['devices'][0]['streams'][0]['reported_stream_latency_ms'], 0)
        stream['latency_frames'] = property_value(None, 'unavailable', 123)
        result = coreaudio.summarise(raw, HASH)
        self.assertIsNone(result['devices'][0]['streams'][0]['reported_device_plus_stream_latency_ms'])
        self.assertEqual(result['collection_status'], 'partial')

    def test_missing_nominal_rate_keeps_frames_without_inventing_ms(self):
        raw = fixture()
        raw['devices']['value'][0]['nominal_rate_hz'] = property_value(None, 'error', -1)
        device = coreaudio.summarise(raw, HASH)['devices'][0]
        self.assertEqual(device['reported_properties']['buffer_frames']['value'], 480)
        self.assertIsNone(device['buffer_period_ms'])
        self.assertIsNone(device['streams'][0]['reported_stream_latency_ms'])

    def test_unknown_actual_rate_keeps_nominal_basis_explicit(self):
        raw = fixture()
        raw['devices']['value'][0]['actual_rate_hz'] = property_value(None, 'unavailable', 1)
        result = coreaudio.summarise(raw, HASH)
        device = result['devices'][0]
        self.assertEqual(result['collection_status'], 'partial')
        self.assertIsNone(device['reported_properties']['actual_rate_hz']['value'])
        self.assertEqual(device['reported_properties']['nominal_rate_hz']['value'], 48000)
        self.assertEqual(device['buffer_period_ms'], 10)

    def test_mismatched_stream_clock_prevents_latency_sum(self):
        raw = fixture()
        raw['devices']['value'][0]['output_streams']['value'][0]['physical_format']['value']['rate_hz'] = 44100
        stream = coreaudio.summarise(raw, HASH)['devices'][0]['streams'][0]
        self.assertFalse(stream['formats_match_device_nominal_rate'])
        self.assertEqual(stream['latency_frames']['value'], 960)
        self.assertIsNone(stream['reported_device_plus_stream_latency_ms'])

    def test_changed_default_and_unknown_default_are_distinct(self):
        raw = fixture()
        raw['default_output_after'] = property_value(9)
        result = coreaudio.summarise(raw, HASH)
        self.assertFalse(result['default_route_stable_during_snapshot'])
        self.assertEqual(result['collection_status'], 'partial')
        raw['default_output_after'] = property_value(None, 'unavailable', 1)
        result = coreaudio.summarise(raw, HASH)
        self.assertIsNone(result['default_route_stable_during_snapshot'])
        self.assertIsNone(result['devices'][0]['is_default_output'])

    def test_stable_defaults_missing_from_output_inventory_remain_partial(self):
        for missing in ('empty-inventory', 'default-output', 'system-output'):
            with self.subTest(missing=missing):
                raw = fixture()
                if missing == 'empty-inventory':
                    raw['devices']['value'] = []
                elif missing == 'default-output':
                    raw['devices']['value'][0]['object_id'] = 9
                else:
                    raw['system_output_before'] = property_value(9)
                    raw['system_output_after'] = property_value(9)
                result = coreaudio.summarise(raw, HASH)
                self.assertEqual(result['collection_status'], 'partial')
                self.assertTrue(result['default_route_stable_during_snapshot'])
                self.assertEqual(len(result['devices']), 0 if missing == 'empty-inventory' else 1)
                if result['devices']:
                    self.assertEqual(result['devices'][0]['reported_properties']['buffer_frames']['value'], 480)
                    self.assertEqual(result['devices'][0]['buffer_period_ms'], 10)

    def test_multiple_outputs_streams_and_unclassified_terminal_not_invented(self):
        raw = fixture()
        other = copy.deepcopy(raw['devices']['value'][0])
        other['object_id'] = 10
        other['transport_type'] = property_value(int.from_bytes(b'usb ', 'big'))
        other['output_streams']['value'][0]['object_id'] = 11
        additional = copy.deepcopy(other['output_streams']['value'][0])
        additional['object_id'] = 12
        additional['latency_frames'] = property_value(480)
        other['output_streams']['value'].append(additional)
        raw['devices']['value'].append(other)
        result = coreaudio.summarise(raw, HASH)
        self.assertEqual([d['transport'] for d in result['devices']], ['built-in', 'usb'])
        self.assertEqual([d['is_default_output'] for d in result['devices']], [True, False])
        self.assertEqual(len(result['devices'][1]['streams']), 2)
        self.assertEqual(result['devices'][0]['streams'][0]['terminal_type']['kind'], 'unclassified')

    def test_hostile_extra_properties_cannot_enter_public_summary(self):
        raw = fixture()
        raw['hostname'] = 'PRIVATE_HOST'
        device = raw['devices']['value'][0]
        device.update({'name': 'PRIVATE_DEVICE', 'uid': 'PRIVATE_UID', 'serial': 'PRIVATE_SERIAL'})
        device['output_streams']['value'][0]['client'] = {'owner': 'PRIVATE_USER', 'home': '/PRIVATE_HOME'}
        text = json.dumps(coreaudio.summarise(raw, HASH))
        self.assertNotIn('PRIVATE', text)
        self.assertNotIn('object_id', text)

    def test_unknown_status_and_failed_value_cannot_leak_payload(self):
        raw = fixture()
        raw['devices']['value'][0]['is_running'] = property_value('PRIVATE_PAYLOAD', 'PRIVATE_STATUS', -1)
        with self.assertRaises(ValueError):
            coreaudio.summarise(raw, HASH)
        raw['devices']['value'][0]['is_running'] = property_value('PRIVATE_PAYLOAD', 'error', -1)
        with self.assertRaises(ValueError):
            coreaudio.summarise(raw, HASH)

    def test_invalid_numeric_rates_frames_and_ranges_rejected(self):
        for field, value in [('nominal_rate_hz', True), ('actual_rate_hz', float('nan')),
                             ('nominal_rate_hz', 0), ('buffer_frames', -1), ('buffer_frames', 0),
                             ('buffer_frames', 1.5), ('buffer_range_frames', [4096, 16])]:
            with self.subTest(field=field, value=value):
                raw = fixture()
                raw['devices']['value'][0][field] = property_value(value)
                with self.assertRaises(ValueError):
                    coreaudio.summarise(raw, HASH)

    def test_failed_inventory_and_disappearing_stream_remain_partial(self):
        raw = fixture()
        raw['devices'] = property_value(None, 'error', -1)
        result = coreaudio.summarise(raw, HASH)
        self.assertEqual(result['collection_status'], 'partial')
        self.assertEqual(result['devices'], [])
        raw = fixture()
        raw['devices']['value'][0]['output_streams'] = property_value(None, 'error', -2)
        device = coreaudio.summarise(raw, HASH)['devices'][0]
        self.assertEqual(device['output_streams_status'], 'error')
        self.assertEqual(device['streams'], [])

    def test_duplicate_hal_objects_and_unsupported_schema_rejected(self):
        raw = fixture()
        raw['devices']['value'].append(copy.deepcopy(raw['devices']['value'][0]))
        with self.assertRaises(ValueError):
            coreaudio.summarise(raw, HASH)
        raw = fixture()
        raw['devices']['value'][0]['output_streams']['value'].append(copy.deepcopy(raw['devices']['value'][0]['output_streams']['value'][0]))
        with self.assertRaises(ValueError):
            coreaudio.summarise(raw, HASH)
        for schema in (True, 2):
            raw = fixture()
            raw['schema_version'] = schema
            with self.assertRaises(ValueError):
                coreaudio.summarise(raw, HASH)


class PrivateIOTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='coreaudio-fixture-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.input = self.root / 'capture.json'
        self.output = self.root / 'summary.json'
        self.input.write_text(json.dumps(fixture()))

    def invoke(self):
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            code = coreaudio.main(['--input', str(self.input), '--output', str(self.output)])
        return code, captured.getvalue()

    def test_exclusive_private_output_and_input_hash(self):
        original = self.input.read_bytes()
        code, _ = self.invoke()
        self.assertEqual(code, 0)
        summary = json.loads(self.output.read_text())
        self.assertEqual(summary['source_sha256'], coreaudio.digest(original))
        self.assertEqual(stat.S_IMODE(self.output.stat().st_mode), 0o600)
        retained = self.output.read_bytes()
        code, _ = self.invoke()
        self.assertEqual(code, 2)
        self.assertEqual(self.output.read_bytes(), retained)
        self.assertEqual(self.input.read_bytes(), original)

    def test_input_output_symlinks_and_fifo_refused_without_overwrite(self):
        original = self.input.read_bytes()
        self.output.symlink_to(self.input)
        self.assertEqual(self.invoke()[0], 2)
        self.assertEqual(self.input.read_bytes(), original)
        self.output.unlink()
        self.input.unlink()
        self.input.symlink_to(self.root / 'missing')
        self.assertEqual(self.invoke()[0], 2)
        self.input.unlink()
        coreaudio.os.mkfifo(self.input)
        self.assertEqual(self.invoke()[0], 2)

    def test_duplicate_keys_nonfinite_and_oversized_json_fail_privately(self):
        for data in ('{"schema_version":1,"schema_version":1}', '{"value":NaN}', 'PRIVATE_PAYLOAD'):
            self.input.write_text(data)
            code, text = self.invoke()
            self.assertEqual(code, 2)
            self.assertNotIn('PRIVATE', text)
            self.assertNotIn(str(self.input), text)
            self.assertFalse(self.output.exists())
        with mock.patch.object(coreaudio, 'LIMIT', 16):
            self.input.write_text(' ' * 17)
            self.assertEqual(self.invoke()[0], 2)


if __name__ == '__main__':
    unittest.main()
