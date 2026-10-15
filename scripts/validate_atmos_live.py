#!/usr/bin/env python3
"""Run the reviewed live-player methods once, or select exact failed methods."""
import argparse
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


def source_manifest():
    names = ['probes/atmos/Program.cs', 'probes/atmos/LiveStream.cs',
             'probes/atmos/OfflinePullRenderer.cs', 'probes/atmos/atmos-live',
             'probes/atmos/native_playback.py', 'probes/atmos/build-native.sh',
             'probes/atmos/native/playback.c', 'probes/atmos/native/playback_core.c',
             'probes/atmos/native/playback_core.h', 'probes/atmos/native/test_core.c',
             'probes/atmos/native/test_io.c', 'probes/atmos/native/compiler-packages.json',
             'probes/atmos/native/PIPEWIRE-EXAMPLE-LICENSE', 'probes/atmos/source_manifest.json',
             'probes/atmos/Dockerfile', 'probes/atmos/live-ci.sh', 'probes/atmos/live_ci_options.py', 'probes/atmos/registry_json.py', 'probes/atmos/pw_cat.py', 'probes/atmos/live_integration.py',
             'tests/test_atmos_live.py', 'scripts/validate_atmos_live.py']
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in names}


def artifact_manifest(module):
    result = {}
    if module.BUILD:
        for name in ('AtmosProbe.dll', 'Cavern.dll', 'Cavern.Format.dll', 'atmos-pw-playback',
                     'native-tests', 'native-io-tests', 'native-build.json', 'native_playback.py',
                     'native-source.tar', 'PIPEWIRE-EXAMPLE-LICENSE'):
            result[name] = hashlib.sha256((module.BUILD / name).read_bytes()).hexdigest()
    if module.BED:
        result['generated_bed_fixture'] = hashlib.sha256(module.BED.read_bytes()).hexdigest()
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path)
    parser.add_argument('--bed-fixture', type=Path)
    parser.add_argument('--test-id', action='append', default=[])
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    before = source_manifest()
    sys.path.insert(0, str(ROOT / 'tests'))
    module = importlib.import_module('test_atmos_live')
    available = {'test_atmos_live.LiveTests.' + name
                 for name in unittest.defaultTestLoader.getTestCaseNames(module.LiveTests)}
    ids = args.test_id or sorted(available)
    if len(ids) != len(set(ids)) or any(name not in available for name in ids):
        parser.error('unknown or duplicate live-player test method')
    if any('.test_producer_' in name or '.test_native_core_' in name for name in ids) and not args.build:
        parser.error('producer/native core methods require --build')
    if any(name.endswith('test_producer_generated_bed_metadata_and_exact_count') for name in ids) and not args.bed_fixture:
        parser.error('generated bed method requires --bed-fixture')
    module.BUILD = args.build.resolve(strict=True) if args.build else None
    module.BED = args.bed_fixture.resolve(strict=True) if args.bed_fixture else None
    artifacts = artifact_manifest(module)
    descriptor = os.open(args.report, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(descriptor, 'w') as output:
        suite = unittest.TestSuite(module.LiveTests(name.rsplit('.', 1)[1]) for name in ids)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        after = source_manifest()
        artifacts_after = artifact_manifest(module)
        unchanged = before == after and artifacts == artifacts_after
        receipt = {'schema_version': 1, 'evidence_class': 'synthetic-test',
                   'selected_test_ids': ids, 'tests_run': result.testsRun,
                   'failures': len(result.failures), 'errors': len(result.errors), 'skips': len(result.skipped),
                   'source_before': before, 'source_after': after, 'source_unchanged': unchanged,
                   'build_and_fixture_before': artifacts, 'build_and_fixture_after': artifacts_after,
                   'failed_test_ids': [test.id() for test, _ in result.failures],
                   'error_test_ids': [test.id() for test, _ in result.errors]}
        json.dump(receipt, output, indent=2)
        output.write('\n')
    return 0 if result.wasSuccessful() and result.testsRun and not result.skipped and unchanged else 1


if __name__ == '__main__':
    raise SystemExit(main())
