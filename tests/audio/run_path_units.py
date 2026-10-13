"""Run only new path suites; skips/empty suites are acceptance failures."""
import importlib
import json
import re
import sys
import unittest

CLASSES = {'unit-path': ('test_inspect_audio_path', 'PathTests'),
           'unit-trial': ('test_audio_path_trial', 'TrialTests')}


def suite(stage, identifiers):
    if stage not in CLASSES or len(identifiers) != len(set(identifiers)):
        raise ValueError('invalid selector')
    module, name = CLASSES[stage]
    case = getattr(importlib.import_module(module), name)
    if not issubclass(case, unittest.TestCase):
        raise ValueError('invalid test class')
    if not identifiers:
        result = unittest.defaultTestLoader.loadTestsFromTestCase(case)
    else:
        result = unittest.TestSuite()
        for identifier in identifiers:
            match = re.fullmatch(re.escape(module+'.'+name)+r'\.(test_[a-z0-9_]+)', identifier)
            if not match or match[1] not in vars(case) or not callable(vars(case)[match[1]]):
                raise ValueError('invalid test method')
            result.addTest(case(match[1]))
    if result.countTestCases() == 0:
        raise ValueError('empty test suite')
    return result


def accepted(result):
    return result.testsRun > 0 and result.wasSuccessful() and not result.skipped


def main(argv):
    try:
        selected = suite(argv[0], argv[1:])
    except (IndexError, ValueError, AttributeError):
        print('path unit selector refused', file=sys.stderr); return 2
    result = unittest.TextTestRunner(verbosity=2).run(selected)
    failed = [test.id() for test, _ in result.errors+result.failures+result.skipped]
    failed.extend(test.id() for test in result.unexpectedSuccesses)
    print(json.dumps({'tests_run': result.testsRun, 'skipped_count': len(result.skipped),
                      'successful': accepted(result), 'failed_test_ids': sorted(set(failed))}))
    return 0 if accepted(result) else 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
