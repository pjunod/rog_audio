#!/usr/bin/env python3
"""Run only the reviewed manual-annotation methods; no audio/device access."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import unittest

import analyse_manual_annotations as annotations

ROOT = Path(__file__).resolve().parents[1]
PATTERN = re.compile(r'test_analyse_manual_annotations\.AnnotationTests\.test_[A-Za-z0-9_]+\Z')


def main(argv=None):
    parser = annotations.PrivateParser(description=__doc__)
    parser.add_argument('--report', required=True)
    parser.add_argument('--test-id', action='append', default=[])
    args = parser.parse_args(argv)
    ids = args.test_id
    if len(ids) > 64 or len(ids) != len(set(ids)) or any(not PATTERN.fullmatch(item) for item in ids):
        print('Annotation acceptance error: invalid_selection', file=sys.stderr)
        return 2
    # Reserve the result before running anything: a collision must not repeat tests.
    try:
        fd = os.open(args.report, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                     os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    except OSError:
        print('Annotation acceptance error: report_create_failed', file=sys.stderr)
        return 2
    with os.fdopen(fd, 'w', encoding='utf-8') as report:
        os.fchmod(report.fileno(), 0o600)
        sys.path.insert(0, str(ROOT / 'tests'))
        suite = unittest.defaultTestLoader.loadTestsFromNames(ids or ['test_analyse_manual_annotations'])
        start = time.monotonic()
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        receipt = {'schema_version': 1, 'kind': 'synthetic-selected-unit-acceptance',
                   'test_ids': ids or ['test_analyse_manual_annotations'],
                   'tests_run': result.testsRun, 'failures': len(result.failures),
                   'errors': len(result.errors), 'skips': len(result.skipped),
                   'elapsed_seconds': time.monotonic() - start,
                   'passed': result.wasSuccessful() and bool(result.testsRun) and not result.skipped,
                   'physical_measurements': False,
                   'source_sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                       for name in ['scripts/analyse_manual_annotations.py',
                                    'scripts/validate_manual_annotations.py',
                                    'tests/test_analyse_manual_annotations.py']}}
        json.dump(receipt, report, indent=2, sort_keys=True, allow_nan=False)
        report.write('\n'); report.flush(); os.fsync(report.fileno())
    return 0 if receipt['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
