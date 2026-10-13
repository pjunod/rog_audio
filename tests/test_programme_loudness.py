"""Invented model-bound bundles; no host install, playback or recording."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import prepare_programme_loudness as prepare
import programme_loudness as programme
import speaker_install as kit
from test_speaker_install import synthetic_bundle, inventory


def document(path):
    return json.loads(path.read_bytes())


def rewrite(bundle, preset=None, report=None, manifest=None):
    manifest = document(bundle/'manifest.json') if manifest is None else manifest
    for name, value in (('preset.json', preset), ('field-mapping.json', report)):
        if value is not None:
            (bundle/name).write_bytes(kit.encoded(value))
    manifest['outputs'] = {name: kit.sha((bundle/name).read_bytes())
                           for name in manifest['outputs']}
    (bundle/'manifest.json').write_bytes(kit.encoded(manifest))


def source(root, thinkpad=False):
    bundle = synthetic_bundle(root)
    preset = document(bundle/'preset.json')
    preset['output']['limiter#0'].update({'threshold': -1.0, 'gain-boost': False})
    report = document(bundle/'field-mapping.json')
    report['signal_checks'] = {'fir_attenuation_db': 10.1375 if thinkpad else 2.6475}
    report['limits'] = ['Invented fixture; not acoustic qualification.']
    manifest = document(bundle/'manifest.json')
    if thinkpad:
        manifest['hardware'] = copy.deepcopy(kit.speaker.DEVICE_CONTRACTS['10ec0285', '17aa2276']['bundle_hardware'])
        manifest['inputs']['source_manifest_sha256'] = '0'*64
        preset['output']['plugins_order'].insert(1, 'autogain#0')
        preset['output']['autogain#0'] = {'bypass': True, 'input-gain': 0, 'output-gain': 0}
        report['fields'].append({'output_stage': 'autogain#0', 'status': 'approximation-bypassed'})
        report['interpreted_selection'] = {'dynamics_emitted': ['autogain#0']}
    report['stages'] = [{'name': n, 'bypassed': preset['output'][n]['bypass']}
                        for n in preset['output']['plugins_order']]
    rewrite(bundle, preset, report, manifest)
    return bundle


class ProgrammeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='rog-programme-cases-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = source(self.root/'source')
        self.output = self.root/'derived'
        self.runtime = self.root/'runtime.json'
        self.runtime.write_bytes(kit.encoded({
            'schema_version': 1, 'source_commit': '6d9b1220d3dcebb154ba759a05600662bc0af549',
            'routing_contract': 'exact-device-route-v1', 'binary_sha256': '0'*64,
            'programme_loudness_contract': programme.CONTRACT}))

    def test_model_defaults_preserve_ir_voicing_and_parent_bindings(self):
        for model, budget in ((False, 2.6475), (True, 10.1375)):
            parent = self.source if not model else source(self.root/'lenovo', True)
            output = self.root/('asus-derived' if not model else 'lenovo-derived')
            before = document(parent/'preset.json')['output']
            result = prepare.build(parent, output)
            derived = document(output/'preset.json')['output']
            manifest = document(output/'manifest.json')
            settings = manifest['programme_loudness']
            self.assertEqual(settings['target_lufs'], -20.0)
            self.assertEqual(settings['maximum_gain_db'], budget)
            self.assertFalse(settings['above_source_budget'])
            self.assertEqual(derived['plugins_order'][-2:], ['autogain#0', 'limiter#0'])
            for name in before['plugins_order']:
                if name != 'autogain#0':
                    self.assertEqual(before[name], derived[name])
            self.assertEqual((parent/manifest['impulse']).read_bytes(), (output/manifest['impulse']).read_bytes())
            self.assertEqual(settings['parent_bundle_manifest_sha256'], kit.sha((parent/'manifest.json').read_bytes()))
            self.assertEqual(settings['parent_preset_sha256'], kit.sha((parent/'preset.json').read_bytes()))
            self.assertEqual(settings['parent_report_sha256'], kit.sha((parent/'field-mapping.json').read_bytes()))
            self.assertEqual(result['activation_state'], 'not-installed')
            self.assertEqual(kit.speaker.verify(output)['result'], 'verified')

    def test_independent_stage_does_not_claim_oem_leveler_equivalence(self):
        parent = source(self.root/'lenovo', True)
        prepare.build(parent, self.output)
        report = document(self.output/'field-mapping.json')
        field = report['fields'][-1]
        self.assertIsNone(field['output_stage'])
        self.assertEqual(field['status'], 'not-emitted')
        self.assertIn('OEM leveler is not implemented', field['approximation'])
        self.assertEqual(report['interpreted_selection']['dynamics_emitted'], [])
        self.assertIs(report['complete_equivalence'], False)

    def test_above_source_budget_is_advisory_and_full_control_range_works(self):
        for cap in (0, 6, 36):
            output = self.root/('cap-'+str(cap))
            result = prepare.build(self.source, output, target=-18, maximum=cap)
            settings = document(output/'manifest.json')['programme_loudness']
            self.assertEqual(settings['maximum_gain_db'], cap)
            self.assertEqual(settings['above_source_budget'], cap > 2.6475)
            self.assertEqual(result['above_source_budget_advisory'], cap > 2.6475)
            self.assertEqual(kit.speaker.verify(output)['result'], 'verified')

    def test_invalid_finite_numeric_and_history_controls_leave_no_output(self):
        cases = ({'target': float('nan')}, {'target': float('inf')}, {'target': True},
                 {'target': .1}, {'target': -101}, {'maximum': float('inf')},
                 {'maximum': float('nan')}, {'maximum': True}, {'maximum': -1},
                 {'maximum': 36.1}, {'silence': float('nan')}, {'silence': False},
                 {'silence': 1}, {'history': True}, {'history': 5},
                 {'history': 3601}, {'history': 15.0})
        for controls in cases:
            with self.subTest(controls=controls):
                with self.assertRaises(ValueError):
                    prepare.build(self.source, self.output, **controls)
                self.assertFalse(self.output.exists())

    def test_post_creation_replacement_survives_write_failure(self):
        retained = self.root/'renamed-partial'
        def replace_then_fail(path, data):
            self.output.rename(retained)
            self.output.mkdir()
            (self.output/'owner-file').write_bytes(b'keep replacement contents')
            raise OSError('injected write failure after public path replacement')
        with mock.patch.object(prepare.speaker, 'new_file', side_effect=replace_then_fail):
            with self.assertRaises(OSError):
                prepare.build(self.source, self.output)
        self.assertEqual((self.output/'owner-file').read_bytes(), b'keep replacement contents')
        self.assertTrue((retained/'irs').is_dir())

    def test_existing_destination_and_symlink_are_preserved(self):
        self.output.mkdir(); marker = self.output/'owner-file'; marker.write_bytes(b'keep')
        with self.assertRaises(kit.speaker.ProfileError):
            prepare.build(self.source, self.output)
        self.assertEqual(marker.read_bytes(), b'keep')
        alias = self.root/'alias'; alias.symlink_to(self.source)
        with self.assertRaises(kit.speaker.ProfileError):
            prepare.build(alias, self.root/'new-output')
        self.assertFalse((self.root/'new-output').exists())

    def test_preserved_voicing_tamper_fails_even_with_rehashed_inventory(self):
        prepare.build(self.source, self.output)
        preset = document(self.output/'preset.json')
        preset['output']['convolver#0']['output-gain'] = -3.0
        rewrite(self.output, preset=preset)
        with self.assertRaisesRegex(ValueError, 'voicing_stage_changed'):
            kit.speaker.verify(self.output)

    def test_leveler_cap_tamper_and_boolean_controls_are_refused(self):
        prepare.build(self.source, self.output)
        original = document(self.output/'preset.json')
        for key, value in (('maximum-gain', 36), ('maximum-gain', True),
                           ('input-gain', False), ('bypass', 0),
                           ('maximum-history', 15.0), ('force-silence', 0)):
            preset = copy.deepcopy(original); preset['output']['autogain#0'][key] = value
            rewrite(self.output, preset=preset)
            with self.subTest(key=key), self.assertRaises(ValueError):
                kit.speaker.verify(self.output)

    def test_unsafe_or_missing_final_limiter_refused_before_output(self):
        original = document(self.source/'preset.json')
        for key, value in (('threshold', 0), ('gain-boost', True), ('bypass', True),
                           ('input-gain', 1), ('output-gain', -1)):
            preset = copy.deepcopy(original); preset['output']['limiter#0'][key] = value
            report = document(self.source/'field-mapping.json')
            report['stages'] = [{'name': n, 'bypassed': preset['output'][n]['bypass']}
                                for n in preset['output']['plugins_order']]
            rewrite(self.source, preset=preset, report=report)
            with self.subTest(key=key), self.assertRaises((ValueError, kit.speaker.ProfileError)):
                prepare.build(self.source, self.output)
            self.assertFalse(self.output.exists())

    def test_old_runtime_rejected_before_kit_creation(self):
        prepare.build(self.source, self.output)
        runtime = document(self.runtime); runtime.pop('programme_loudness_contract')
        self.runtime.write_bytes(kit.encoded(runtime))
        destination = self.root/'kit'
        with self.assertRaises(kit.InstallError) as error:
            kit.prepare(self.output, inventory(), destination, self.runtime)
        self.assertEqual(error.exception.reason, 'runtime_lacks_bounded_programme_makeup')
        self.assertFalse(destination.exists())

    def test_derived_kit_capability_is_checked_again_on_load(self):
        prepare.build(self.source, self.output)
        destination = self.root/'kit'
        kit.prepare(self.output, inventory(), destination, self.runtime)
        self.assertEqual(kit.load_kit(destination)[1]['runtime']['programme_loudness_contract'], programme.CONTRACT)
        original = document(destination/'kit.json')
        for runtime in ({k: v for k, v in original['runtime'].items() if k != 'programme_loudness_contract'}, None):
            changed = copy.deepcopy(original); changed['runtime'] = runtime
            (destination/'kit.json').write_bytes(kit.encoded(changed))
            with self.assertRaises(kit.InstallError) as error:
                kit.load_kit(destination)
            self.assertEqual(error.exception.reason, 'runtime_lacks_bounded_programme_makeup')

    def test_legacy_bundle_keeps_bypassed_autogain_without_new_capability(self):
        parent = source(self.root/'lenovo', True)
        runtime = document(self.runtime); runtime.pop('programme_loudness_contract')
        self.runtime.write_bytes(kit.encoded(runtime))
        destination = self.root/'legacy-kit'
        self.assertEqual(kit.speaker.verify(parent)['result'], 'verified')
        kit.prepare(parent, inventory('17aa2276'), destination, self.runtime)
        kit.load_kit(destination)
        self.assertIs(document(destination/'speaker-source/preset.json')['output']['autogain#0']['bypass'], True)
