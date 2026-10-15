"""Generated annotations and owned files only; no physical measurements."""
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import analyse_manual_annotations as annotations


def trial(index=0, delay=10, **changes):
    click = 1000 + index * 100
    chirp = click + delay
    result = {'trial_id': 'press-' + str(index), 'recording_id': 'synthetic-track',
              'condition_id': 'lab5-pilot', 'block_id': 'block-a',
              'click': {'sample': click, 'lower': click - 2, 'upper': click + 2},
              'chirp': {'sample': chirp, 'lower': chirp - 3, 'upper': chirp + 3},
              'valid': True, 'rejection_reasons': []}
    result.update(changes)
    return result


def document(trials=None):
    return {'schema_version': 1, 'evidence_class': 'synthetic',
            'recordings': [{'recording_id': 'synthetic-track', 'sha256': '0' * 64,
                'sample_rate_hz': 1000, 'frame_count': 100000,
                'timebase_scale_bound_ppm': 1000, 'preprocessing': 'generated-fixture',
                'unquantified_biases': ['keyboard-actuation-offset', 'recorder-processing']}],
            'conditions': [{'condition_id': 'lab5-pilot', 'setup_id': 'lab5',
                'route': 'internal-speakers', 'settings_id': 'synthetic-settings',
                'method_id': 'manual-onsets-v1', 'keyboard_id': 'common-usb-key',
                'geometry_id': 'marked-position', 'signal_id': 'chirp-v1',
                'power_state': 'ac', 'load_state': 'idle', 'phase': 'pilot'}],
            'trials': [trial()] if trials is None else trials}


class AnnotationTests(unittest.TestCase):
    def setUp(self):
        parent = ROOT / 'private/manual-annotation-test-scratch'
        parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.temporary = tempfile.TemporaryDirectory(dir=parent, prefix='case-')
        self.addCleanup(self.temporary.cleanup)
        self.scratch = Path(self.temporary.name)

    def bad(self, value, reason=None):
        with self.assertRaises(annotations.AnnotationError) as error:
            annotations.analyse(value)
        if reason:
            self.assertEqual(str(error.exception), reason)

    def test_signed_statistics_and_asymmetric_onset_timebase_bounds(self):
        result = annotations.analyse(document([trial(i, i - 10) for i in range(20)]))
        group = result['groups'][0]
        self.assertEqual(group['statistics']['raw_signed_ms'],
                         {'min': -10, 'median': -0.5, 'p95': 8, 'max': 9})
        self.assertEqual(group['statistics']['included_count'], 20)
        self.assertEqual(group['statistics']['annotation_statistic_bounds_ms']['p95'], [3, 13])
        row = group['trials'][0]
        self.assertEqual(row['raw_signed_samples'], -10)
        self.assertEqual(row['annotation_bounds_samples'], [-15, -5])
        self.assertAlmostEqual(row['annotation_and_declared_timebase_bounds_ms'][0], -15.015)
        self.assertAlmostEqual(row['annotation_and_declared_timebase_bounds_ms'][1], -4.995)
        self.assertEqual(group['onset_count_status'], 'synthetic-only')
        self.assertEqual(result['physical_validity'], 'not-verified')
        self.assertEqual(result['qualification'], 'not-established')
        example = json.loads((ROOT / 'tests/audio/synthetic-manual-annotations.json').read_text())
        generated = annotations.analyse(example)
        self.assertEqual(generated['groups'][0]['statistics']['raw_signed_ms'],
                         {'min': -5, 'median': 0, 'p95': 12, 'max': 12})
        self.assertEqual(generated['groups'][0]['statistics']['rejected_count'], 1)
        self.assertEqual(generated['groups'][0]['onset_count_status'], 'synthetic-only')
        self.assertEqual(generated['recordings'][0]['byte_verification'], 'not-requested')

    def test_rejections_missing_onsets_and_empty_groups_remain_visible(self):
        rows = [trial(0, -10), trial(1, 15, valid=False,
                rejection_reasons=['clipping', 'ambiguous-onset']),
                trial(2, chirp=None, valid=False, rejection_reasons=['missing-chirp'])]
        group = annotations.analyse(document(rows))['groups'][0]
        self.assertEqual(group['statistics']['included_count'], 1)
        self.assertEqual(group['statistics']['rejected_count'], 2)
        self.assertIsNone(group['trials'][2]['raw_signed_samples'])
        self.assertEqual(group['trials'][1]['raw_signed_ms'], 15)
        self.assertEqual(group['statistics']['rejection_reason_counts'],
                         {'ambiguous-onset': 1, 'clipping': 1, 'missing-chirp': 1})
        all_rejected = annotations.analyse(document(rows[1:]))['groups'][0]['statistics']
        self.assertIsNone(all_rejected['raw_signed_ms'])
        empty = annotations.analyse(document([]))
        self.assertEqual(empty['groups'], [])
        self.assertEqual(empty['unused_condition_ids'], ['lab5-pilot'])
        self.assertEqual(empty['unused_recording_ids'], ['synthetic-track'])

    def test_conditions_recordings_blocks_and_declared_unknowns_do_not_pool(self):
        value = document([trial(0), trial(1, block_id='block-b')])
        other = dict(value['conditions'][0], condition_id='lab6-formal',
                     setup_id='lab6', settings_id='different-settings', phase='formal')
        value['conditions'].append(other)
        value['recordings'].append(dict(value['recordings'][0], recording_id='second-track',
                                       timebase_scale_bound_ppm=None))
        value['trials'].extend([trial(2, condition_id='lab6-formal'),
                               trial(3, recording_id='second-track')])
        result = annotations.analyse(value)
        self.assertEqual(len(result['groups']), 3)
        original = next(g for g in result['groups'] if len(g['trials']) == 2)
        self.assertEqual([b['block_id'] for b in original['blocks']], ['block-a', 'block-b'])
        self.assertEqual(original['statistics']['included_count'], 2)
        unknown = next(g for g in result['groups'] if g['recording_id'] == 'second-track')
        self.assertIsNone(unknown['statistics']['annotation_and_declared_timebase_statistic_bounds_ms'])
        self.assertIsNotNone(unknown['statistics']['annotation_statistic_bounds_ms'])
        self.assertEqual(unknown['trials'][0]['input_index'], 3)
        self.assertEqual(result['recordings'][1]['unquantified_biases'],
                         ['keyboard-actuation-offset', 'recorder-processing'])
        value['evidence_class'] = 'physical-measurement'
        physical = annotations.analyse(value)
        self.assertEqual(physical['declared_evidence_class'], 'physical-measurement')
        self.assertEqual(physical['physical_validity'], 'not-verified')
        self.assertTrue(all(r['byte_verification'] == 'not-requested' for r in physical['recordings']))

    def test_schema_bounds_integer_ranges_and_collisions_are_rejected(self):
        mutations = [lambda d: d.update(schema_version=True),
            lambda d: d.update(extra='PRIVATE'),
            lambda d: d['recordings'][0].update(frame_count=0),
            lambda d: d['recordings'][0].update(sample_rate_hz=True),
            lambda d: d['recordings'][0].update(timebase_scale_bound_ppm=float('inf')),
            lambda d: d['recordings'][0].update(timebase_scale_bound_ppm=10 ** 1000),
            lambda d: d['trials'][0]['click'].update(sample=1.5),
            lambda d: d['trials'][0]['chirp'].update(upper=100000),
            lambda d: d['trials'][0]['click'].update(lower=1001),
            lambda d: d['trials'][0].update(chirp=None),
            lambda d: d['trials'][0].update(valid=False),
            lambda d: d['trials'][0].update(rejection_reasons=['PRIVATE']),
            lambda d: d['conditions'].append(copy.deepcopy(d['conditions'][0])),
            lambda d: d['trials'].append(copy.deepcopy(d['trials'][0])),
            lambda d: d['trials'].append(dict(d['trials'][0], trial_id='other-id'))]
        for mutate in mutations:
            value = document(); mutate(value)
            with self.subTest(mutation=mutations.index(mutate)):
                self.bad(value)
        value = document(); value['trials'][0]['chirp']['sample'] = 990
        value['trials'][0]['chirp'].update(lower=987, upper=993)
        self.assertEqual(annotations.analyse(value)['groups'][0]['trials'][0]['raw_signed_samples'], -10)

    def test_strict_json_duplicate_nonfinite_nesting_and_limits(self):
        for payload in (b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":Infinity}',
                        b'[' * 33 + b'0' + b']' * 33, b'\xff', b''):
            with self.subTest(payload=payload[:15]):
                with self.assertRaises(annotations.AnnotationError):
                    annotations.parse_input(payload)
        value = document()
        value['recordings'][0]['timebase_scale_bound_ppm'] = float('nan')
        self.bad(value, 'invalid_timebase_bound')
        with mock.patch.object(annotations, 'MAX_INPUT_BYTES', 5):
            with self.assertRaises(annotations.AnnotationError):
                annotations.parse_input(b'123456')
        with mock.patch.object(annotations, 'MAX_TRIALS', 0):
            self.bad(document(), 'invalid_trial_count')

    def test_regular_file_reads_refuse_fifo_symlink_directory_and_edits(self):
        source = self.scratch / 'source.json'; source.write_bytes(b'{}')
        self.assertEqual(annotations.regular_bytes(source, 10), b'{}')
        link = self.scratch / 'link'; link.symlink_to(source)
        fifo = self.scratch / 'pipe'; os.mkfifo(fifo)
        for path in (link, fifo, self.scratch):
            with self.subTest(kind=path.name):
                with self.assertRaises(annotations.AnnotationError):
                    annotations.regular_bytes(path, 10)
        before = source.stat()
        changed = types.SimpleNamespace(st_mode=before.st_mode, st_size=before.st_size,
                    st_mtime_ns=before.st_mtime_ns + 1, st_ctime_ns=before.st_ctime_ns)
        with mock.patch.object(annotations.os, 'fstat', side_effect=[before, changed]):
            with self.assertRaisesRegex(annotations.AnnotationError, 'input_changed_during_read'):
                annotations.regular_bytes(source, 10)
        with self.assertRaisesRegex(annotations.AnnotationError, 'input_too_large'):
            annotations.regular_bytes(source, 1)

    def test_optional_byte_hashing_never_promotes_declared_physical_validity(self):
        source = self.scratch / 'synthetic-bytes'; source.write_bytes(b'SYNTHETIC-NOT-AUDIO')
        value = document(); value['evidence_class'] = 'physical-measurement'
        value['recordings'][0]['sha256'] = hashlib.sha256(source.read_bytes()).hexdigest()
        result = annotations.analyse(value)
        annotations.verify_recordings(result, ['synthetic-track=' + str(source)])
        row = result['recordings'][0]
        self.assertEqual(row['byte_verification'], 'digest-matched-explicit-file')
        self.assertEqual(row['rate_frame_count_and_onsets'], 'operator-declared')
        self.assertEqual(result['physical_validity'], 'not-verified')
        self.assertEqual(result['qualification'], 'not-established')
        for bindings in (['synthetic-track=' + str(source)] * 2,
                         ['unknown=' + str(source)], ['PRIVATE'],
                         ['synthetic-track=' + str(self.scratch)]):
            with self.assertRaises(annotations.AnnotationError):
                annotations.verify_recordings(annotations.analyse(value), bindings)
        bad = document()
        with self.assertRaisesRegex(annotations.AnnotationError, 'recording_digest_mismatch'):
            annotations.verify_recordings(annotations.analyse(bad), ['synthetic-track=' + str(source)])

    def test_cli_private_output_permissions_and_existing_target_preservation(self):
        source = self.scratch / 'annotations.json'; source.write_text(json.dumps(document()))
        output = self.scratch / 'result.json'
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            prior_umask = os.umask(0o777)
            try:
                self.assertEqual(annotations.main(['--input', str(source), '--output', str(output)]), 0)
            finally:
                os.umask(prior_umask)
            result = output.read_bytes()
            self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
            self.assertEqual(annotations.main(['--input', str(source), '--output', str(output)]), 1)
            self.assertEqual(output.read_bytes(), result)
            original = source.read_bytes()
            self.assertEqual(annotations.main(['--input', str(source), '--output', str(source)]), 1)
            self.assertEqual(source.read_bytes(), original)
            target = self.scratch / 'target'; target.write_bytes(b'keep')
            link = self.scratch / 'result-link'; link.symlink_to(target)
            self.assertEqual(annotations.main(['--input', str(source), '--output', str(link)]), 1)
            self.assertEqual(target.read_bytes(), b'keep')
        self.assertNotIn(str(self.scratch), stderr.getvalue())
        parsed = json.loads(result)
        self.assertEqual(parsed['input_sha256'], hashlib.sha256(source.read_bytes()).hexdigest())

    def test_cli_special_inputs_and_unknown_arguments_fail_without_private_paths(self):
        fifo = self.scratch / 'PRIVATE-pipe'; os.mkfifo(fifo)
        command = [sys.executable, str(ROOT / 'scripts/analyse_manual_annotations.py'),
                   '--input', str(fifo), '--output', str(self.scratch / 'result.json')]
        completed = subprocess.run(command, capture_output=True, text=True, timeout=5)
        self.assertEqual(completed.returncode, 2)
        self.assertNotIn('PRIVATE', completed.stderr)
        self.assertFalse((self.scratch / 'result.json').exists())
        command = [sys.executable, str(ROOT / 'scripts/analyse_manual_annotations.py'), '--PRIVATE', str(fifo)]
        completed = subprocess.run(command, capture_output=True, text=True, timeout=5)
        self.assertEqual(completed.returncode, 2)
        self.assertNotIn('PRIVATE', completed.stderr)
        self.assertNotIn(str(self.scratch), completed.stderr)

    def test_count_met_does_not_establish_parity_and_selectors_fail_before_execution(self):
        value = document([trial(i, i % 20 - 10) for i in range(100)])
        value['conditions'][0]['phase'] = 'formal'; value['evidence_class'] = 'physical-measurement'
        result = annotations.analyse(value)
        self.assertEqual(result['groups'][0]['onset_count_status'], 'count-met')
        self.assertEqual(result['qualification'], 'not-established')
        self.assertEqual(result['physical_validity'], 'not-verified')
        command = [sys.executable, str(ROOT / 'scripts/validate_manual_annotations.py'),
                   '--report', str(self.scratch / 'report.json'), '--test-id', 'PRIVATE.invalid']
        completed = subprocess.run(command, capture_output=True, text=True, timeout=5)
        self.assertEqual(completed.returncode, 2)
        self.assertNotIn('PRIVATE', completed.stderr)
        self.assertFalse((self.scratch / 'report.json').exists())


    def test_acceptance_source_changes_fail_without_running_a_nested_suite(self):
        import validate_manual_annotations as validation
        project = self.scratch / 'fake-project'
        initial = {}
        for name in validation.SOURCES:
            source = project / name
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(b'GENERATED-BEFORE-LOAD')
            initial[name] = hashlib.sha256(source.read_bytes()).hexdigest()
        fixture = project / 'tests/audio/synthetic-manual-annotations.json'
        sentinel = object()

        def controlled_load(_names):
            fixture.write_bytes(b'GENERATED-AFTER-LOAD')
            return sentinel

        fake_result = types.SimpleNamespace(testsRun=1, failures=[], errors=[],
                                           skipped=[], wasSuccessful=lambda: True)
        fake_runner = mock.Mock()
        fake_runner.run.return_value = fake_result
        output = self.scratch / 'provenance-report.json'
        stderr = io.StringIO()
        original_path = list(sys.path)
        try:
            with mock.patch.object(validation, 'ROOT', project), \
                 mock.patch.object(validation.unittest.defaultTestLoader,
                                   'loadTestsFromNames', side_effect=controlled_load) as loader, \
                 mock.patch.object(validation.unittest, 'TextTestRunner', return_value=fake_runner), \
                 contextlib.redirect_stderr(stderr):
                status = validation.main(['--report', str(output)])
        finally:
            sys.path[:] = original_path
        self.assertEqual(status, 1)
        loader.assert_called_once()
        fake_runner.run.assert_called_once_with(sentinel)
        result = json.loads(output.read_text())
        self.assertFalse(result['passed'])
        self.assertFalse(result['source_unchanged'])
        self.assertEqual(result['source_sha256'], initial)
        self.assertNotEqual(result['source_sha256_after'][
            'tests/audio/synthetic-manual-annotations.json'], initial[
            'tests/audio/synthetic-manual-annotations.json'])
        self.assertEqual(result['source_failure_reason'], 'source_changed_during_acceptance')
        self.assertNotIn(str(self.scratch), stderr.getvalue())
        self.assertEqual(stat.S_IMODE(output.stat().st_mode), 0o600)
