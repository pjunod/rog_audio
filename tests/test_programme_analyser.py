"""Threaded lifecycle regressions on the actual source-bound native slot."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

CASES = ('history-during-reconstruction', 'stale-generation-refused',
         'processing-lease-serializes-history-and-swap', 'failed-candidate-never-ready')


class AnalyserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        source = os.environ.get('ROG_EASYEFFECTS_SOURCE')
        if not source:
            raise unittest.SkipTest('ROG_EASYEFFECTS_SOURCE selects patched source')
        header = Path(source)/'src/programme_analyser_state.hpp'
        pins = json.loads((root/'patches/easyeffects/source.json').read_text())
        if hashlib.sha256(header.read_bytes()).hexdigest() != pins['programme_analyser_header_sha256']:
            raise AssertionError('Native analyser header does not match its patch pin')
        compiler = shutil.which('c++')
        if not compiler:
            raise unittest.SkipTest('C++20 compiler unavailable')
        cls.directory = tempfile.TemporaryDirectory(prefix='rog-analyser-cases-')
        cls.addClassCleanup(cls.directory.cleanup)
        cls.binary = Path(cls.directory.name)/'programme-analyser-cases'
        subprocess.run([compiler, '-std=c++20', '-O2', '-Wall', '-Wextra', '-Werror', '-pthread',
                        '-I', str(Path(source)/'src'),
                        str(root/'probes/speaker/programme_analyser_cases.cpp'),
                        '-o', str(cls.binary)], check=True, capture_output=True, text=True)


def case(name):
    def run(self):
        result = subprocess.run([str(self.binary), name], capture_output=True,
                                text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
    return run


for name in CASES:
    setattr(AnalyserTests, 'test_'+name.replace('-', '_'), case(name))
