"""Generated probe WAV contracts; no Dolby payload or sound-device access."""
import importlib.util
import json
import math
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('atmos_energy', ROOT/'scripts/analyse_atmos_render.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def wave(values, channels=2):
    pcm = struct.pack('<' + 'f' * len(values), *values)
    return (b'RIFF' + struct.pack('<I', len(pcm)+60) + b'WAVEfmt ' + struct.pack('<I',40)
            + struct.pack('<HHIIHHHHI',0xfffe,channels,48000,48000*channels*4,channels*4,32,22,32,3 if channels==2 else 0x2d63f)
            + MODULE.FLOAT_GUID + b'data' + struct.pack('<I',len(pcm)) + pcm)


class AnalyseAtmosTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='atmos-energy-')
        self.root = Path(self.tmp.name)
        self.path = self.root/'render.wav'

    def tearDown(self):
        self.tmp.cleanup()

    def test_channel_windows_and_partial_length(self):
        values = [0.25,0] * 960 + [0,0.125] * 5
        self.path.write_bytes(wave(values))
        report = MODULE.analyse(self.path,20)
        self.assertEqual(report['samples_per_channel'],965)
        self.assertEqual([item['dominant_channel'] for item in report['windows']],['FL','FR'])
        self.assertEqual(report['windows'][-1]['samples_per_channel'],5)
        self.assertAlmostEqual(report['rms'][0],math.sqrt(960*0.25**2/965))
        self.assertEqual(report['peak'],[0.25,0.125])
        self.assertFalse(report['reference_fidelity_compared'])
        self.assertFalse(report['physical_measurement'])

    def test_height_and_silence_have_distinct_observations(self):
        self.path.write_bytes(wave([0]*11+[0.5],12))
        report = MODULE.analyse(self.path)
        self.assertEqual(report['windows'][0]['dominant_channel'],'TBR')
        self.path.write_bytes(wave([0,0]))
        self.assertIsNone(MODULE.analyse(self.path)['windows'][0]['dominant_channel'])

    def test_invalid_pcm_headers_and_window_rejected(self):
        for payload in [wave([float('nan'),0]),wave([float('inf'),0]),wave([1.01,0]),wave([0,0])[:-1],b'no WAV']:
            with self.subTest(payload_length=len(payload)):
                self.path.write_bytes(payload)
                with self.assertRaises(ValueError):MODULE.analyse(self.path)
        self.path.write_bytes(wave([0,0]))
        for window in [0,19,1001,20.5,True]:
            with self.assertRaises(ValueError):MODULE.analyse(self.path,window)
        payload=bytearray(wave([0,0]));payload[24:28]=struct.pack('<I',44100)
        self.path.write_bytes(payload)
        with self.assertRaises(ValueError):MODULE.analyse(self.path)

    def test_duration_bound_and_report_collision(self):
        self.path.write_bytes(wave([0,0]))
        with self.path.open('r+b') as source:source.truncate(90*48000*12*4+69)
        with self.assertRaises(ValueError):MODULE.analyse(self.path)
        self.path.write_bytes(wave([0,0]))
        output=self.root/'report.json';output.write_text('owner data')
        result=subprocess.run([sys.executable,str(ROOT/'scripts/analyse_atmos_render.py'),'--input',str(self.path),'--report',str(output)],capture_output=True)
        self.assertEqual(result.returncode,2)
        self.assertEqual(output.read_text(),'owner data')
        output.unlink();output.symlink_to(self.root/'missing')
        result=subprocess.run([sys.executable,str(ROOT/'scripts/analyse_atmos_render.py'),'--input',str(self.path),'--report',str(output)],capture_output=True)
        self.assertEqual(result.returncode,2)
        self.assertTrue(output.is_symlink())
        self.assertFalse((self.root/'missing').exists())


if __name__ == '__main__':unittest.main()
