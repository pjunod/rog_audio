"""Compile once; execute reviewed cases on the actual patched cache header."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

CASES=('route-before-node','node-before-route','node-return','profile-isolation',
       'invalidation','stale-route','device-id-reuse','missing-profile',
       'binding-change','volume-update','queued-node-removal','queued-node-reuse',
       'description-change','duplicate-route-notification','invalidation-same-route',
       'pending-invalidation-same-route','notification-removal')

class OutputAutoloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=Path(__file__).resolve().parents[1]
        source=os.environ.get('ROG_EASYEFFECTS_SOURCE')
        if not source:raise unittest.SkipTest('ROG_EASYEFFECTS_SOURCE selects patched source')
        pins=json.loads((root/'patches/easyeffects/source.json').read_text())
        header=Path(source)/'src/output_route_cache.hpp'
        if hashlib.sha256(header.read_bytes()).hexdigest()!=pins['output_route_header_sha256']:
            raise AssertionError('Native output route header does not match its patch pin')
        compiler=shutil.which('c++')
        if not compiler:raise unittest.SkipTest('C++20 compiler unavailable')
        cls.directory=tempfile.TemporaryDirectory(prefix='rog-autoload-cases-')
        cls.addClassCleanup(cls.directory.cleanup)
        cls.binary=Path(cls.directory.name)/'output-route-cases'
        subprocess.run([compiler,'-std=c++20','-O2','-Wall','-Wextra','-Werror',
                        '-I',str(Path(source)/'src'),str(root/'probes/speaker/output_route_cases.cpp'),
                        '-o',str(cls.binary)],check=True,capture_output=True,text=True)

def case(name):
    def run(self):
        result=subprocess.run([str(self.binary),name],capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
    return run

for name in CASES:setattr(OutputAutoloadTests,'test_'+name.replace('-','_'),case(name))
