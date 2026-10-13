"""Synthetic parser/privacy and bounded read-only collection regressions."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import inspect_audio_path as path
from audio_path_fixture import setup, top_frame


class PathTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.kit, self.binary, self.env, self.inv, self.capture = setup(self.root)

    def test_driver_period_and_follower_suggestion_remain_separate(self):
        report = path.summary(self.capture, '0'*64)
        nodes = report['samples'][0]['nodes']
        self.assertAlmostEqual(nodes[0]['period_ms'], 5.333333333333333)
        self.assertEqual(nodes[0]['role'], 'driver')
        self.assertEqual(nodes[1]['role'], 'follower')
        self.assertAlmostEqual(nodes[1]['period_ms'], 21.333333333333332)
        self.assertIsNone(report['physical_latency_ms'])
        self.assertIsNone(report['end_to_end_latency_ms'])
        self.assertEqual(report['reported_process_latency'][0]['constant_ms'], 1)
        self.assertEqual(report['pulse_queues'][0]['buffer_latency_usec'], 12000)
        self.assertEqual(report['error_deltas'][0]['errors_delta'], 1)

    def test_idle_monitor_is_not_running_driver_evidence(self):
        self.capture['monitor']['stdout'] = top_frame(0, state='S')*2
        result = path.summary(self.capture, '0'*64)
        self.assertFalse(result['running_driver_observed'])
        self.assertIsNone(result['samples'][0]['nodes'][0]['period_ms'])
        self.assertIsNone(result['error_deltas'][0]['errors_delta'])

    def test_counter_reset_and_missing_samples_are_not_zero_errors(self):
        self.capture['monitor']['stdout'] = top_frame(errors=5)+top_frame(errors=1)
        result = path.summary(self.capture, '0'*64)
        self.assertIsNone(result['error_deltas'][0]['errors_delta'])
        self.capture['monitor']['stdout'] = top_frame()
        self.assertEqual(path.summary(self.capture, '0'*64)['monitor_status'], 'parse-error')

    def test_reused_ids_or_restarted_core_cannot_establish_driver(self):
        graph = json.loads(self.capture['after']['graph']['stdout'])
        graph[0]['info']['props']['object.serial'] += 1
        self.capture['after']['graph']['stdout'] = json.dumps(graph)
        self.assertFalse(path.summary(self.capture, '0'*64)['running_driver_observed'])
        graph[-2]['info']['cookie'] += 1
        self.capture['after']['graph']['stdout'] = json.dumps(graph)
        self.assertEqual(path.summary(self.capture, '0'*64)['monitor_status'], 'parse-error')

    def test_four_channel_route_drift_is_reported_without_rebinding(self):
        graph = json.loads(self.capture['after']['graph']['stdout'])
        graph[0]['info']['props']['node.name'] = 'alsa_output.test.analog-surround-40'
        self.capture['after']['graph']['stdout'] = json.dumps(graph)
        report = path.summary(self.capture, '0'*64)
        self.assertFalse(report['route_consistent'])
        self.assertEqual(self.capture['speaker_before']['binding']['node_name'], 'alsa_output.test.analog-stereo')

    def test_allowlist_excludes_names_errors_and_rejects_hostile_hashes(self):
        marker = 'private-secret-client-path'
        self.capture['pulse_inputs']['stdout'] = json.dumps([{'sink': 5, 'properties': {'secret': marker}, 'buffer_latency_usec': 2}, {'sink': 99, 'buffer_latency_usec': 999}])
        self.capture['monitor']['stderr'] = marker
        self.capture['monitor']['stdout'] = self.capture['monitor']['stdout'].replace('rog_audio_soe_output_level', marker)
        self.assertNotIn(marker, json.dumps(path.summary(self.capture, '0'*64)))
        self.assertEqual(len(path.summary(self.capture, '0'*64)['pulse_queues']), 1)
        self.capture['speaker_before']['binary_sha256'] = marker
        with self.assertRaises(ValueError): path.summary(self.capture, '0'*64)

    def test_malformed_profiler_and_nonfinite_components_do_not_become_numbers(self):
        for text in ('garbage secret', top_frame().replace('25.0us', 'NaNus'), top_frame().replace('256', '99999999')):
            with self.subTest(text=text):
                with self.assertRaises(ValueError): path.parse_top(text)
        graph = json.loads(self.capture['after']['graph']['stdout'])
        graph[-1]['info']['params']['ProcessLatency'][0]['ns'] = True
        self.capture['after']['graph']['stdout'] = json.dumps(graph)
        self.assertIsNone(path.summary(self.capture, '0'*64)['reported_process_latency'][0]['ns'])

    def test_collection_uses_only_readers_and_unsupported_platform_does_nothing(self):
        calls = []
        def runner(argv, timeout):
            calls.append((argv, timeout))
            if argv[0] == 'pw-top': return {'status': 'ok', 'stdout': top_frame()*3}
            if argv[0] == 'pw-dump': return self.inv['probes']['graph']
            if argv[0] == 'pw-metadata': return self.inv['probes']['settings']
            return {'status': 'unavailable'}
        with mock.patch.object(path.inventory, 'collect', return_value=self.inv), mock.patch.object(path, 'process_environment', return_value={'status': 'ok', 'values': {}}):
            captured = path.collect(self.kit, self.binary, runner=runner, system='Linux', environment=self.env)
        self.assertEqual(captured['speaker_before'], captured['speaker_after'])
        self.assertTrue(all(argv[0] in ('pw-top', 'pw-dump', 'pw-metadata', 'pactl', 'systemctl', 'busctl') for argv, _ in calls))
        self.assertTrue(all('restart' not in argv and 'set-param' not in argv for argv, _ in calls))
        calls.clear()
        self.assertEqual(path.collect(None, None, runner=runner, system='Darwin')['status'], 'unsupported-platform')
        self.assertEqual(calls, [])

    def test_runtime_payload_and_symlink_mismatches_fail_before_collection(self):
        self.binary.write_bytes(b'changed')
        with self.assertRaises(ValueError): path.state_snapshot(self.kit, self.binary, self.env)
        self.binary.unlink(); self.binary.symlink_to(self.root/'runtime.json')
        with self.assertRaises(path.speaker.speaker.ProfileError): path.state_snapshot(self.kit, self.binary, self.env)

    def test_main_settings_preimage_is_private_and_hash_bound(self):
        rc = self.root/'state/config/easyeffects/db/easyeffectsrc'
        marker = 'private-main-settings-preimage'
        rc.write_bytes(rc.read_bytes()+b'\n# '+marker.encode()+b'\n')
        state = path.state_snapshot(self.kit, self.binary, self.env)
        self.assertIn(marker, state['main_rc_text'])
        self.assertEqual(path.speaker.sha(state['main_rc_text'].encode()), state['rc']['db/easyeffectsrc']['sha256'])
        self.capture['speaker_before'] = state; self.capture['speaker_after'] = copy.deepcopy(state)
        self.assertNotIn(marker, json.dumps(path.summary(self.capture, '0'*64)))
        real = path.speaker.read; count = [0]
        def racing_read(filename):
            data = real(filename)
            if Path(filename) == rc:
                count[0] += 1
                if count[0] == 2: return data+b'# changed-between-reads\n'
            return data
        with mock.patch.object(path.speaker, 'read', side_effect=racing_read):
            with self.assertRaisesRegex(ValueError, 'changed while reading'):
                path.state_snapshot(self.kit, self.binary, self.env)

    def test_restart_environment_reads_selected_variables_only(self):
        def runner(argv, timeout):
            if argv[0] == 'busctl': return {'status': 'ok', 'stdout': 'a(sb) 0\n'}
            return {'status': 'ok', 'stdout': 'SECRET=private-value\nPIPEWIRE_LATENCY=128/48000\n' if argv[-1] == 'show-environment' else 'Environment=SECRET=other-value\n'}
        result = path.override_context(runner, {})
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['manager'], {'PIPEWIRE_LATENCY': '128/48000'})
        self.assertNotIn('private-value', json.dumps(result))
        self.assertNotIn('other-value', json.dumps(result))

    def test_restart_environment_requires_positive_typed_empty_array(self):
        calls = []
        def runner(argv, timeout):
            calls.append((argv, timeout))
            if argv[0] == 'busctl': return {'status': 'ok', 'stdout': 'a(sb) 0\n'}
            return {'status': 'ok', 'stdout': 'Environment=\n' if 'show' in argv else ''}
        self.assertEqual(path.override_context(runner, {}), {'status': 'ok', 'current': {}, 'manager': {}, 'unit': {}})
        self.assertIn((['systemctl', '--user', 'show', 'rog-audio-speaker.service', '--all', '--property=Environment'], 5), calls)
        self.assertIn((['busctl', '--user', 'get-property', 'org.freedesktop.systemd1',
                        '/org/freedesktop/systemd1/unit/rog_2daudio_2dspeaker_2eservice',
                        'org.freedesktop.systemd1.Service', 'EnvironmentFiles'], 5), calls)

    def test_restart_environment_nonempty_missing_wrong_type_or_error_refuses(self):
        probes = [{'status': 'ok', 'stdout': text} for text in (
            'a(sb) 1 "private-env-file" false\n', '', 'as 0\n', 'a(sb)\n',
            'a(sb) 0\nprivate-secret', 'a(sb) 00\n', 'a(sb) 0 garbage\n')]
        probes.extend({'status': status, 'stdout': 'a(sb) 0\n', 'stderr': 'private-secret'}
                      for status in ('unavailable', 'nonzero', 'timeout'))
        for probe in probes:
            with self.subTest(probe=probe):
                def runner(argv, timeout):
                    if argv[0] == 'busctl': return probe
                    return {'status': 'ok', 'stdout': 'Environment=\n' if 'show' in argv else ''}
                result = path.override_context(runner, {})
                self.assertEqual(result['status'], 'unavailable')
                self.assertNotIn('private-', json.dumps(result))

    def test_restart_environment_missing_duplicate_or_malformed_environment_refuses(self):
        for text in ('', 'Environment=\nEnvironment=\n', 'Environment="unclosed\n'):
            with self.subTest(text=text):
                def runner(argv, timeout):
                    if argv[0] == 'busctl': return {'status': 'ok', 'stdout': 'a(sb) 0\n'}
                    return {'status': 'ok', 'stdout': text if 'show' in argv else ''}
                self.assertIn(path.override_context(runner, {})['status'], ('parse-error', 'unavailable'))

    def test_procfs_zero_size_environment_is_bounded_and_selected(self):
        info = type('Info', (), {'st_mode': 0o100600, 'st_uid': path.os.geteuid(), 'st_size': 0})()
        with mock.patch.object(path.speaker, 'read', return_value=b'123\n'), mock.patch.object(path.os, 'readlink', return_value=str(self.binary)), mock.patch.object(path.os, 'open', return_value=99), mock.patch.object(path.os, 'fstat', return_value=info), mock.patch.object(path.os, 'close'), mock.patch.object(path.os, 'read', side_effect=[b'SECRET=never-copy\0PIPEWIRE_LATENCY=128/48000\0', b'']):
            result = path.process_environment(self.binary, {'XDG_RUNTIME_DIR': str(self.root)})
        self.assertEqual(result, {'status': 'ok', 'values': {'PIPEWIRE_LATENCY': '128/48000'}})


if __name__ == '__main__': unittest.main()
