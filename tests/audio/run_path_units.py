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


class RetryResult(unittest.TextTestResult):
    """Keep subtest details in logs, but return a runnable parent method ID."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.failed_ids = set()

    def addFailure(self, test, error):
        self.failed_ids.add(test.id())
        super().addFailure(test, error)

    def addError(self, test, error):
        self.failed_ids.add(test.id())
        super().addError(test, error)

    def addSubTest(self, test, subtest, error):
        if error is not None:
            self.failed_ids.add(test.id())
        super().addSubTest(test, subtest, error)

    def addSkip(self, test, reason):
        self.failed_ids.add(getattr(test, 'test_case', test).id())
        super().addSkip(test, reason)

    def addUnexpectedSuccess(self, test):
        self.failed_ids.add(test.id())
        super().addUnexpectedSuccess(test)


def main(argv):
    try:
        selected = suite(argv[0], argv[1:])
    except (IndexError, ValueError, AttributeError):
        print('path unit selector refused', file=sys.stderr); return 2
    result = unittest.TextTestRunner(verbosity=2, resultclass=RetryResult).run(selected)
    print(json.dumps({'tests_run': result.testsRun, 'skipped_count': len(result.skipped),
                      'successful': accepted(result), 'failed_test_ids': sorted(result.failed_ids)}))
    return 0 if accepted(result) else 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
