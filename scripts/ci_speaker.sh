#!/usr/bin/env bash
# Explicit post-review acceptance; test selectors avoid repeating passing cases.
set -euo pipefail
stage=${1:-all}
test_ids=${2:-}
case "$stage" in all|unit|music|dynamic|off) ;; *) echo 'invalid speaker stage' >&2; exit 2;; esac
if [[ -n "$test_ids" && "$stage" != unit ]]; then
  echo 'test IDs require the unit stage' >&2; exit 2
fi
root=$(cd -- "$(dirname -- "$0")/.." && pwd)
case_dir=$(mktemp -d)
image="rog-audio-speaker-$(basename "$case_dir" | tr '[:upper:]' '[:lower:]'):ci"
cleanup() { docker image rm "$image" >/dev/null 2>&1 || true; rm -rf "$case_dir"; }
trap cleanup EXIT
git clone --quiet https://github.com/antoinecellerier/speaker-tuning-to-easyeffects "$case_dir/converter"
git -C "$case_dir/converter" checkout --quiet 430e3a501e21bf8fdb615b133d2e8130b17973c1
docker build --tag "$image" - < "$root/scripts/speaker-build.Dockerfile"
mkdir "$case_dir/output"
docker run --rm -i --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --user "$(id -u):$(id -g)" \
  --tmpfs /tmp:rw,nosuid,nodev,size=256m \
  --mount "type=bind,src=$root,dst=/repo,readonly" \
  --mount "type=bind,src=$case_dir/converter,dst=/converter,readonly" \
  --mount "type=bind,src=$case_dir/output,dst=/output" \
  --env ROG_SPEAKER_CONVERTER=/converter --env "TEST_IDS=$test_ids" \
  --env "TEST_STAGE=$stage" "$image" python - <<'PYRUN'
import os, subprocess, sys, unittest
sys.path.insert(0, '/repo/tests')
stage = os.environ['TEST_STAGE']
failed = False
if stage in ('all', 'unit'):
    ids = os.environ['TEST_IDS'].split()
    suite = (unittest.defaultTestLoader.loadTestsFromNames(ids) if ids else
             unittest.defaultTestLoader.discover('tests', pattern='test_prepare_speaker_profile.py'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    failed = not result.wasSuccessful() or bool(result.skipped)
profiles = ['music', 'dynamic', 'off'] if stage == 'all' else ([stage] if stage != 'unit' else [])
for profile in profiles:
    command = [sys.executable, 'scripts/prepare_speaker_profile.py', 'build',
        '--xml', 'profiles/asus/gu605mz/DEV_0285_SUBSYS_10431C63_PCI_SUBSYS_1C631043.xml',
        '--inf', 'profiles/asus/gu605mz/dax3_ext_rtk.inf', '--codec', '10ec0285',
        '--subsystem', '10431c63', '--endpoint', 'internal_speaker', '--mode', 'normal',
        '--profile', profile, '--converter', '/converter', '--output', '/output/' + profile]
    built = subprocess.run(command).returncode == 0
    verified = built and subprocess.run([sys.executable, 'scripts/prepare_speaker_profile.py',
        'verify', '--bundle', '/output/' + profile]).returncode == 0
    print('ASUS profile', profile, 'PASS' if verified else 'FAIL', flush=True)
    failed |= not verified
raise SystemExit(1 if failed else 0)
PYRUN
