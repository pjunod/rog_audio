"""Check runtime dependencies against synthetic multi-architecture inventories."""
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import inspect_speaker_runtime as runtime


def package(name, architecture, version='1.0', provides='', status='install ok installed'):
    return '\t'.join((name, architecture, version, status, provides))


class RuntimeInventoryTests(unittest.TestCase):
    def inspect(self, dependencies, rows, version_results=None):
        manifest = {'architecture': 'amd64', 'dependencies': dependencies,
                    'binary_sha256': 'a' * 64, 'package_sha256': 'b' * 64}
        inventory = subprocess.CompletedProcess([], 0, '\n'.join(rows), '')
        version_results = version_results or {}
        with mock.patch.object(runtime.subprocess, 'run', return_value=inventory) as query, \
                mock.patch.object(runtime.subprocess, 'check_output', return_value='amd64\n'), \
                mock.patch.object(runtime.Path, 'read_text', return_value='ID=ubuntu\nVERSION_ID="26.10"\n'), \
                mock.patch.object(runtime, 'compare', side_effect=lambda v, op, required: version_results[(v, op, required)]) as compare:
            report = runtime.inspect(manifest)
        self.assertIn('${Architecture}', query.call_args.args[0][2])
        self.assertFalse(report['settings_or_services_changed'])
        return report, compare

    def test_i386_package_and_virtual_provider_do_not_satisfy_amd64(self):
        report, compare = self.inspect('libaudio (>= 1.0), virtual-audio (>= 1.0)', [
            package('libaudio:i386', 'i386', provides='virtual-audio (= 2.0)')])
        self.assertEqual(report['status'], 'prerequisites-missing')
        for group in report['dependencies']:
            alternative = group['alternatives'][0]
            self.assertFalse(group['satisfied'])
            self.assertIsNone(alternative['installed_provider'])
            self.assertEqual(alternative['installed_candidates'][0]['architecture'], 'i386')
            self.assertFalse(alternative['installed_candidates'][0]['architecture_matches'])
        compare.assert_not_called()

    def test_amd64_and_architecture_independent_packages_match(self):
        report, _ = self.inspect('libaudio (>= 1.0), audio-data', [
            package('libaudio:amd64', 'amd64', '2.0'), package('audio-data', 'all')],
            {('2.0', '>=', '1.0'): True})
        self.assertEqual(report['status'], 'compatible')
        self.assertEqual([g['alternatives'][0]['installed_architecture'] for g in report['dependencies']],
                         ['amd64', 'all'])

    def test_later_foreign_architecture_cannot_shadow_matching_package(self):
        report, compare = self.inspect('libaudio (>= 2.0)', [
            package('libaudio:amd64', 'amd64', '2.0'), package('libaudio:i386', 'i386', '3.0')],
            {('2.0', '>=', '2.0'): True})
        alternative = report['dependencies'][0]['alternatives'][0]
        self.assertEqual(report['status'], 'compatible')
        self.assertEqual(alternative['installed_provider'], 'libaudio:amd64')
        self.assertEqual(len(alternative['installed_candidates']), 2)
        compare.assert_called_once_with('2.0', '>=', '2.0')

    def test_versioned_and_unversioned_providers_preserved_in_either_order(self):
        rows = [package('older', 'amd64', provides='virtual-audio (= 1.0)'),
                package('matching', 'amd64', provides='virtual-audio (= 2.0)'),
                package('unversioned', 'all', provides='virtual-audio')]
        for ordered in (rows, list(reversed(rows))):
            with self.subTest(order=[row.split('\t')[0] for row in ordered]):
                report, compare = self.inspect('virtual-audio (>= 2.0)', ordered,
                    {('1.0', '>=', '2.0'): False, ('2.0', '>=', '2.0'): True})
                alternative = report['dependencies'][0]['alternatives'][0]
                self.assertEqual(report['status'], 'compatible')
                self.assertEqual(alternative['installed_provider'], 'matching')
                self.assertEqual(alternative['installed_version'], '2.0')
                self.assertEqual(len(alternative['installed_candidates']), 3)
                self.assertEqual(compare.call_count, 2)

    def test_unversioned_and_foreign_providers_cannot_supply_required_version(self):
        report, compare = self.inspect('virtual-audio (>= 2.0)', [
            package('unversioned', 'all', provides='virtual-audio'),
            package('foreign:i386', 'i386', provides='virtual-audio (= 3.0)')])
        self.assertEqual(report['status'], 'prerequisites-missing')
        compare.assert_not_called()

    def test_versioned_alternative_uses_matching_provider(self):
        report, compare = self.inspect('absent (= 1.0) | virtual-audio (= 2.0)', [
            package('matching', 'all', provides='virtual-audio (= 2.0)')],
            {('2.0', '=', '2.0'): True})
        alternatives = report['dependencies'][0]['alternatives']
        self.assertEqual(report['status'], 'compatible')
        self.assertFalse(alternatives[0]['satisfied'])
        self.assertTrue(alternatives[1]['satisfied'])
        compare.assert_called_once_with('2.0', '=', '2.0')

    def test_unversioned_dependency_accepts_unversioned_native_provider(self):
        report, compare = self.inspect('virtual-audio', [package('provider', 'amd64', provides='virtual-audio')])
        self.assertEqual(report['status'], 'compatible')
        self.assertIsNone(report['dependencies'][0]['alternatives'][0]['installed_version'])
        compare.assert_not_called()

    def test_architecture_qualifier_cannot_bypass_runtime_architecture(self):
        report, _ = self.inspect('libaudio:amd64, libaudio:i386', [
            package('libaudio:amd64', 'amd64'), package('libaudio:i386', 'i386')])
        self.assertTrue(report['dependencies'][0]['satisfied'])
        self.assertFalse(report['dependencies'][1]['satisfied'])

    def test_noninstalled_provider_is_not_available(self):
        report, _ = self.inspect('virtual-audio', [
            package('removed', 'amd64', provides='virtual-audio', status='deinstall ok config-files')])
        self.assertEqual(report['status'], 'prerequisites-missing')
        self.assertEqual(report['dependencies'][0]['alternatives'][0]['installed_candidates'], [])


if __name__ == '__main__':
    unittest.main()
