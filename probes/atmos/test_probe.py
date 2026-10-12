#!/usr/bin/env python3
"""Synthetic offline regressions; requires an explicitly supplied Linux build."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import runpy
from unittest import mock
import unittest

PROBE = None
BED = None
STEREO_FIXTURE = None
RESULTS = []


def scene(position=(-1, 0, 1), samples=4096, amplitude=0.125, keys=None):
    return {'schema_version': 1, 'sample_rate': 48000, 'samples': samples, 'objects': [
        {'amplitude': amplitude, 'frequency_hz': 997, 'keyframes': keys or [
            {'sample': 0, 'position': list(position)}]}]}


def wave(path):
    data = path.read_bytes()
    assert data[:4] == b'RIFF' and data[8:16] == b'WAVEfmt '
    assert len(data) == struct.unpack_from('<I', data, 4)[0] + 8
    channels = struct.unpack_from('<H', data, 22)[0]
    assert struct.unpack_from('<H', data, 20)[0] == 0xfffe
    assert data[60:64] == b'data'
    count = struct.unpack_from('<I', data, 64)[0] // 4
    values = struct.unpack_from('<' + 'f' * count, data, 68)
    return channels, values


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='atmos-regression-')
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def run_probe(self, data, *, layout='stereo-speakers', inspect=False, suffix='.json'):
        source = self.root / ('input' + suffix)
        source.write_bytes(json.dumps(data).encode() if suffix == '.json' else data)
        report, output = self.root / 'report.json', self.root / 'output.wav'
        command = [str(PROBE), 'inspect' if inspect else 'render', '--input', str(source),
                   '--report', str(report), '--layout', layout]
        if not inspect:
            command += ['--output', str(output)]
        result = subprocess.run(command, capture_output=True, timeout=100)
        receipt = json.loads(report.read_text()) if report.exists() else None
        return result, receipt, output

    def test_channel_order_and_height(self):
        positions = {0: (-1, 0, 1), 1: (1, 0, 1), 2: (0, 0, 1),
                     4: (-1, 0, -1), 5: (1, 0, -1), 6: (-1, 0, 0), 7: (1, 0, 0),
                     8: (-1, 1, 1), 9: (1, 1, 1), 10: (-1, 1, -1), 11: (1, 1, -1)}
        for channel, position in positions.items():
            with self.subTest(channel=channel):
                result, receipt, output = self.run_probe(scene(position), layout='7.1.4')
                self.assertEqual(result.returncode, 0, receipt)
                self.assertEqual(receipt['output']['channels'], ['FL', 'FR', 'FC', 'LFE', 'BL', 'BR', 'SL', 'SR', 'TFL', 'TFR', 'TBL', 'TBR'])
                energies = receipt['output']['rms']
                self.assertEqual(max(range(12), key=lambda i: energies[i]), channel, energies)
                self.assertLess(receipt['output']['peak'], 0.126)
                self.assertEqual(wave(output)[0], 12)
                output.unlink(); (self.root / 'report.json').unlink()

    def test_stereo_and_exact_partial_block(self):
        result, receipt, output = self.run_probe(scene(samples=4101))
        self.assertEqual(result.returncode, 0, receipt)
        channels, values = wave(output)
        self.assertEqual(channels, 2)
        self.assertEqual(len(values), 4101 * 2)
        self.assertGreater(receipt['output']['rms'][0], receipt['output']['rms'][1] * 2)
        self.assertEqual(receipt['output']['layout'], 'stereo-speakers')
        self.assertIsNone(receipt['atmos_signalling'])

    def test_moving_object_and_repeatability(self):
        keys = [{'sample': 0, 'position': [-1, 0, 1]}, {'sample': 8191, 'position': [1, 1, -1]}]
        data = scene(samples=8192, keys=keys)
        result, receipt, output = self.run_probe(data, layout='7.1.4')
        self.assertEqual(result.returncode, 0, receipt)
        channels, values = wave(output)
        def energy(start, stop, channel):
            return sum(x*x for x in values[start*channels+channel:stop*channels:channels])
        self.assertGreater(energy(0, 1024, 0), energy(0, 1024, 11) * 4)
        self.assertGreater(energy(7168, 8192, 11), energy(7168, 8192, 0) * 4)
        digest = hashlib.sha256(output.read_bytes()).hexdigest()
        output.unlink(); (self.root / 'report.json').unlink()
        result, receipt, output = self.run_probe(data, layout='7.1.4')
        self.assertEqual(result.returncode, 0, receipt)
        self.assertEqual(hashlib.sha256(output.read_bytes()).hexdigest(), digest)
        RESULTS.append({'moving_scene_wav_sha256': digest})

    def test_silence(self):
        result, receipt, output = self.run_probe(scene(amplitude=0))
        self.assertEqual(result.returncode, 0, receipt)
        self.assertTrue(all(x == 0 for x in wave(output)[1]))

    def test_scene_inspect(self):
        result, receipt, output = self.run_probe(scene(), inspect=True)
        self.assertEqual(result.returncode, 0, receipt)
        self.assertEqual(receipt['status'], 'synthetic-inspected')
        self.assertFalse(receipt['object_metadata_consumed'])
        self.assertFalse(output.exists())

    def test_invalid_scene_and_limits(self):
        bad = [scene(position=(2, 0, 1)), scene(samples=480001), scene(keys=[{'sample': 1, 'position': [0,0,1]}]),
               scene(keys=[{'sample': 0, 'position': [0,0,1]}, {'sample': 0, 'position': [1,0,1]}])]
        for data in bad:
            result, receipt, output = self.run_probe(data)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(receipt['status'], 'invalid-input')
            self.assertFalse(output.exists())
            (self.root / 'report.json').unlink()
        source = self.root / 'huge.eac3'
        with source.open('wb') as f:
            f.truncate(67108865)
        result = subprocess.run([str(PROBE), 'inspect', '--input', str(source), '--report', str(self.root/'size.json')], capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(json.loads((self.root/'size.json').read_text())['error'], 'input_size_limit')

    def test_collision_and_symlink(self):
        result, receipt, output = self.run_probe(scene())
        self.assertEqual(result.returncode, 0, receipt)
        original = output.read_bytes()
        result, _, _ = self.run_probe(scene(amplitude=0))
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(output.read_bytes(), original)
        (self.root/'report.json').unlink(); output.unlink()
        output.symlink_to(self.root/'missing')
        result, receipt, output = self.run_probe(scene())
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(output.is_symlink())
        self.assertFalse((self.root/'missing').exists())

    def test_unsupported_and_truncated(self):
        for data in [b'not an audio container', b'\x0b\x77\x07\xff\x30\x80']:
            result, receipt, output = self.run_probe(data, suffix='.eac3')
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(receipt['status'], ['unsupported', 'invalid-input'])
            self.assertFalse(output.exists())
            (self.root/'report.json').unlink()

    def test_unsupported_stereo_eac3(self):
        if STEREO_FIXTURE is None:
            self.skipTest('explicit generated stereo E-AC-3 fixture not supplied')
        result, receipt, output = self.run_probe(STEREO_FIXTURE.read_bytes(), suffix='.eac3', inspect=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(receipt['status'], 'unsupported')
        self.assertEqual(receipt['error'], 'upstream_feature_stereo')
        self.assertFalse(output.exists())

    def regression(self, name):
        result = subprocess.run(['dotnet', str(PROBE.parent/'regressions'/'BlockBufferRegression.dll'), name],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(name + ': pass', result.stdout)

    def test_block_buffer_metadata_boundary(self):
        self.regression('block-buffer')

    def test_joc_timeslot_frame_boundary(self):
        self.regression('joc-timeslots')

    def test_late_sparse_detection(self):
        self.regression('late-sparse')

    def test_oamd_freshness_and_stable_configuration(self):
        self.regression('metadata-state')

    def test_publication_racer_preserved(self):
        launcher = runpy.run_path(str(PROBE))
        source = self.root/'scene.json'; source.write_text('{}')
        report, output = self.root/'report.json', self.root/'output.wav'
        original_link = __import__('os').link
        def decoder(command, **kwargs):
            Path(command[command.index('--report')+1]).write_text('{"status":"synthetic-rendered"}')
            Path(command[command.index('--output')+1]).write_bytes(b'generated')
            return subprocess.CompletedProcess(command,0)
        def raced_link(src,dest):
            if Path(dest) == output:
                original_link(src,dest)
                output.unlink()  # A competing writer replaces the published inode.
                output.write_bytes(b'racer-owned')
            else:
                raise FileExistsError('competing report publication')
        with mock.patch('sys.argv',[str(PROBE),'render','--input',str(source),'--report',str(report),'--output',str(output)]), \
             mock.patch('subprocess.run',side_effect=decoder), mock.patch('os.link',side_effect=raced_link):
            self.assertEqual(launcher['main'](),2)
        self.assertEqual(output.read_bytes(),b'racer-owned')
        self.assertFalse(report.exists())

    def test_generated_eac3_bed(self):
        if BED is None:
            self.skipTest('explicit generated E-AC-3 fixture not supplied')
        data = BED.read_bytes()
        result, receipt, output = self.run_probe(data, suffix='.eac3', inspect=True)
        self.assertEqual(result.returncode, 0, receipt)
        self.assertEqual(receipt['status'], 'bed-only')
        self.assertEqual(receipt['object_frames'], 0)
        self.assertFalse(receipt['object_metadata_consumed'])
        (self.root/'report.json').unlink()
        result, receipt, output = self.run_probe(data, suffix='.eac3')
        self.assertEqual(result.returncode, 0, receipt)
        self.assertEqual(receipt['status'], 'bed-fallback-rendered')
        self.assertEqual(len(wave(output)[1]), receipt['input_samples'] * 2)
        self.assertGreater(receipt['output']['peak'], 0.01)
        self.assertFalse(receipt['object_metadata_consumed'])
        RESULTS.append({'generated_eac3_sha256': hashlib.sha256(data).hexdigest(), 'bed_report': receipt})


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--probe', required=True, type=Path)
    parser.add_argument('--bed-fixture', type=Path, help='generated 5.1 E-AC-3; stereo is unsupported upstream')
    parser.add_argument('--stereo-fixture', type=Path)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--test', action='append', metavar='METHOD', help='repeat to run selected test method IDs only')
    args = parser.parse_args()
    PROBE = args.probe.resolve(strict=True)
    BED = args.bed_fixture.resolve(strict=True) if args.bed_fixture else None
    STEREO_FIXTURE = args.stereo_fixture.resolve(strict=True) if args.stereo_fixture else None
    if args.test:
        selected = [name.removeprefix('ProbeTests.') for name in args.test]
        available = unittest.defaultTestLoader.getTestCaseNames(ProbeTests)
        if any(name not in available for name in selected):
            parser.error('unknown test method ID')
        suite = unittest.TestSuite(ProbeTests(name) for name in selected)
    else:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(ProbeTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if args.report:
        with args.report.open('x') as f:
            json.dump({'schema_version': 1, 'evidence_class': 'synthetic-test', 'tests_run': result.testsRun,
                       'failures': len(result.failures), 'errors': len(result.errors), 'skips': len(result.skipped),
                       'results': RESULTS}, f, indent=2)
            f.write('\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
