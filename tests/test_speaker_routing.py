"""Compile once; execute each focused case on the actual patched source header."""
import os
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

CASES = ('ordinary-speaker','explicit-hdmi-usb','metadata-target-race',
         'headphone-bypass-restores','unknown-route-bypass','default-transition',
         'explicit-speaker-other-default','external-target-wins','typed-target-restoration','application-target-change',
         'owned-acknowledgments','stream-id-reuse','sink-removal-resume',
         'selected-device-and-input','blocklist-and-process-all','startup-barrier',
         'partial-scope-and-stock','live-ignored-restores','true-removal-no-restore-write',
         'two-route-profile-indices')

class SpeakerRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=os.environ.get('ROG_EASYEFFECTS_SOURCE')
        if not source:raise unittest.SkipTest('ROG_EASYEFFECTS_SOURCE selects patched source')
        pins=json.loads((Path(__file__).resolve().parents[1]/'patches/easyeffects/source.json').read_text())
        actual=hashlib.sha256((Path(source)/'src/speaker_routing.hpp').read_bytes()).hexdigest()
        if actual!=pins['routing_header_sha256']:raise AssertionError('Native header does not match the source-bound patch')
        compiler=shutil.which('c++')
        if not compiler:raise unittest.SkipTest('C++20 compiler unavailable')
        cls.directory=tempfile.TemporaryDirectory(prefix='rog-speaker-policy-')
        cls.addClassCleanup(cls.directory.cleanup)
        cls.binary=Path(cls.directory.name)/'routing-cases'
        root=Path(__file__).resolve().parents[1]
        subprocess.run([compiler,'-std=c++20','-O2','-Wall','-Wextra','-Werror',
                        '-I',str(Path(source)/'src'),str(root/'probes/speaker/routing_cases.cpp'),
                        '-o',str(cls.binary)],check=True,capture_output=True,text=True)

def case(name):
    def run(self):
        result=subprocess.run([str(self.binary),name],capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
    return run

for name in CASES:setattr(SpeakerRoutingTests,'test_'+name.replace('-','_'),case(name))
