#!/usr/bin/env python3
"""Run only reviewed manual-annotation methods; bind source before code loading."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ('scripts/analyse_manual_annotations.py',
           'scripts/validate_manual_annotations.py',
           'tests/test_analyse_manual_annotations.py',
           'tests/audio/synthetic-manual-annotations.json')
PATTERN = re.compile(r'test_analyse_manual_annotations\.AnnotationTests\.test_[A-Za-z0-9_]+\Z')


class PrivateParser(argparse.ArgumentParser):
    def error(self, _message):
        self.print_usage(sys.stderr)
        self.exit(2, 'Annotation acceptance error: invalid_arguments\n')


def snapshot_sources():
    """Bound reads of fixed project files before any project module is imported."""
    result = {}
    for name in SOURCES:
        fd = os.open(ROOT / name, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW)
        try:
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode) or before.st_size > 8 * 1024 * 1024:
                raise ValueError('source_snapshot_failed')
            digest, length = hashlib.sha256(), 0
            while True:
                chunk = os.read(fd, min(65536, 8 * 1024 * 1024 + 1 - length))
                if not chunk:
                    break
                length += len(chunk)
                if length > 8 * 1024 * 1024:
                    raise ValueError('source_snapshot_failed')
                digest.update(chunk)
            after = os.fstat(fd)
            if (length != before.st_size or length != after.st_size or
                    before.st_mtime_ns != after.st_mtime_ns or
                    before.st_ctime_ns != after.st_ctime_ns):
                raise ValueError('source_snapshot_failed')
            result[name] = digest.hexdigest()
        finally:
            os.close(fd)
    return result


def main(argv=None):
    parser = PrivateParser(description=__doc__)
    parser.add_argument('--report', required=True)
    parser.add_argument('--test-id', action='append', default=[])
    args = parser.parse_args(argv)
    ids = args.test_id
    if len(ids) > 64 or len(ids) != len(set(ids)) or any(not PATTERN.fullmatch(item) for item in ids):
        print('Annotation acceptance error: invalid_selection', file=sys.stderr)
        return 2
    # No project imports above this point. Snapshot before loader imports tests/analyser.
    try:
        initial_hashes = snapshot_sources()
    except (OSError, ValueError):
        print('Annotation acceptance error: source_snapshot_failed', file=sys.stderr)
        return 2
    # Reserve the result before running anything: a collision must not repeat tests.
    try:
        fd = os.open(args.report, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                     os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    except OSError:
        print('Annotation acceptance error: report_create_failed', file=sys.stderr)
        return 2
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as report:
            os.fchmod(report.fileno(), 0o600)
            sys.path.insert(0, str(ROOT / 'tests'))
            suite = unittest.defaultTestLoader.loadTestsFromNames(ids or ['test_analyse_manual_annotations'])
            start = time.monotonic()
            result = unittest.TextTestRunner(verbosity=2).run(suite)
            try:
                final_hashes = snapshot_sources()
            except (OSError, ValueError):
                final_hashes = None
            unchanged = initial_hashes == final_hashes
            receipt = {'schema_version': 1, 'kind': 'synthetic-selected-unit-acceptance',
                       'test_ids': ids or ['test_analyse_manual_annotations'],
                       'tests_run': result.testsRun, 'failures': len(result.failures),
                       'errors': len(result.errors), 'skips': len(result.skipped),
                       'elapsed_seconds': time.monotonic() - start,
                       'passed': result.wasSuccessful() and bool(result.testsRun) and
                                 not result.skipped and unchanged,
                       'physical_measurements': False,
                       'source_sha256': initial_hashes,
                       'source_sha256_after': final_hashes,
                       'source_unchanged': unchanged,
                       'source_failure_reason': None if unchanged else 'source_changed_during_acceptance'}
            json.dump(receipt, report, indent=2, sort_keys=True, allow_nan=False)
            report.write('\n'); report.flush(); os.fsync(report.fileno())
    except (OSError, ValueError):
        print('Annotation acceptance error: report_write_failed', file=sys.stderr)
        return 1
    if not unchanged:
        print('Annotation acceptance error: source_changed_during_acceptance', file=sys.stderr)
    return 0 if receipt['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
