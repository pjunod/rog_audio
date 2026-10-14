#!/usr/bin/env python3
"""Run only reviewed offline Atmos-energy methods, with exact selective retries."""
import argparse
import importlib
import json
import os
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = 'test_analyse_atmos_render'
CLASS = 'AnalyseAtmosTests'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--test-id', action='append', default=[])
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    ids = args.test_id
    pattern = re.escape(MODULE + '.' + CLASS) + r'\.test_[A-Za-z0-9_]+'
    if len(ids) > 128 or len(set(ids)) != len(ids) or any(not re.fullmatch(pattern,item) for item in ids):
        parser.error('invalid Atmos-energy test selection')
    sys.path.insert(0,str(ROOT/'tests'))
    module = importlib.import_module(MODULE)
    case = getattr(module,CLASS)
    available = {MODULE+'.'+CLASS+'.'+name for name in unittest.defaultTestLoader.getTestCaseNames(case)}
    if any(item not in available for item in ids):
        parser.error('unknown Atmos-energy test method')
    suite = unittest.TestSuite(case(item.rsplit('.',1)[-1]) for item in ids) if ids else unittest.defaultTestLoader.loadTestsFromTestCase(case)
    report_file = None
    if args.report:
        try:
            descriptor = os.open(args.report,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
            report_file = os.fdopen(descriptor,'w')
        except OSError:
            parser.error('report unavailable or collision')
    try:
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        receipt = {'schema_version':1,'evidence_class':'synthetic-test','tests_run':result.testsRun,
                   'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),
                   'selected_test_ids':ids or sorted(available)}
        if report_file:
            json.dump(receipt,report_file,indent=2,allow_nan=False);report_file.write('\n')
        return 0 if result.wasSuccessful() and result.testsRun and not result.skipped else 1
    finally:
        if report_file:report_file.close()


if __name__ == '__main__':raise SystemExit(main())
