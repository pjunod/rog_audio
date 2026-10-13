"""Compile the actual pinned controller once; execute each reviewed case once."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

CASES = ('requested-cap', 'retained-cap-reduction', 'silence-reset',
         'invalid-request-reset', 'invalid-cap-and-smoothing',
         'louder-source-reduces', 'smoothing-no-overshoot',
         'zero-request-and-reset')


class MakeupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        source = os.environ.get('ROG_EASYEFFECTS_SOURCE')
        if not source:
            raise unittest.SkipTest('ROG_EASYEFFECTS_SOURCE selects patched source')
        header = Path(source)/'src/programme_makeup_gain.hpp'
        pins = json.loads((root/'patches/easyeffects/source.json').read_text())
        if hashlib.sha256(header.read_bytes()).hexdigest() != pins['programme_makeup_header_sha256']:
            raise AssertionError('Native makeup header does not match its patch pin')
        compiler = shutil.which('c++')
        if not compiler:
            raise unittest.SkipTest('C++20 compiler unavailable')
        cls.directory = tempfile.TemporaryDirectory(prefix='rog-makeup-cases-')
        cls.addClassCleanup(cls.directory.cleanup)
        cls.binary = Path(cls.directory.name)/'programme-makeup-cases'
        subprocess.run([compiler, '-std=c++20', '-O2', '-Wall', '-Wextra', '-Werror',
                        '-I', str(Path(source)/'src'),
                        str(root/'probes/speaker/programme_makeup_cases.cpp'),
                        '-o', str(cls.binary)], check=True, capture_output=True, text=True)


def case(name):
    def run(self):
        result = subprocess.run([str(self.binary), name], capture_output=True,
                                text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
    return run


for name in CASES:
    setattr(MakeupTests, 'test_'+name.replace('-', '_'), case(name))
