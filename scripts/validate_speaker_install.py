#!/usr/bin/env python3
"""Run a reviewed installation test selection once; missing capabilities fail."""
import argparse
from pathlib import Path
import sys
import unittest

MODULES = {
    'install': 'test_speaker_install',
    'inspector': 'test_inspect_speaker_runtime',
    'source': 'test_easyeffects_runtime',
    'routing': 'test_speaker_routing',
    'autoload': 'test_easyeffects_autoload',
    'build': 'test_easyeffects_build',
    'programme': 'test_programme_loudness',
    'makeup': 'test_programme_makeup',
    'analyser': 'test_programme_analyser',
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', choices=('all', *MODULES), default='all')
    parser.add_argument('--test-id', action='append', default=[])
    args = parser.parse_args()
    modules = list(MODULES.values()) if args.stage == 'all' else [MODULES[args.stage]]
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tests'))
    if any(name.split('.')[0] not in modules for name in args.test_id):
        parser.error('test IDs must belong to the selected installation stage')
    selected = list(dict.fromkeys(args.test_id)) or modules
    suite = unittest.defaultTestLoader.loadTestsFromNames(selected)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() and result.testsRun and not result.skipped else 1


if __name__ == '__main__':
    raise SystemExit(main())
