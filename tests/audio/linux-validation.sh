#!/bin/bash
# Explicit checks inside the disposable validation container, with /case populated.
set -euo pipefail
[ -f /.dockerenv ] && [ -d /case ] && [ ! -e /dev/snd ] || {
  echo 'requires disposable Docker container, /case and no sound hardware' >&2
  exit 2
}
if [ -n "${XDG_RUNTIME_DIR:-}" ] && [ -e "$XDG_RUNTIME_DIR/pipewire-0" ]; then
  echo 'refusing inherited PipeWire runtime' >&2
  exit 2
fi
stage=${AUDIO_STAGE:-all}
case "$stage" in
  all|unit|unit-inspector|unit-analyser|unit-candidate|unit-validator|config|compile|native-match|native-other-app|native-other-target) ;;
  *) echo 'unknown audio validation stage' >&2; exit 2 ;;
esac
export DEBIAN_FRONTEND=noninteractive
if apt-get update >/tmp/apt-output 2>&1 && apt-get install -y --no-install-recommends pipewire=1.6.8-1ubuntu4 wireplumber=0.5.17-1ubuntu1 python3 gcc libc6-dev libpipewire-0.3-dev=1.6.8-1ubuntu4 pkg-config >>/tmp/apt-output 2>&1; then
  :
else
  tail -n 80 /tmp/apt-output >&2
  echo 'audio_validation_report={"stage_outcomes":{"setup":"failed"},"failed_test_ids":[]}'
  exit 1
fi
uname -m
python3 --version
cc --version | head -1
pipewire --version
wireplumber --version
dpkg-query -W -f='${Package}=${Version}\n' pipewire wireplumber libpipewire-0.3-dev gcc
cd /case
: >/tmp/audio-stage-outcomes
failure=0
record() {
  printf '%s\t%s\n' "$1" "$2" >>/tmp/audio-stage-outcomes
  if [[ "$2" != passed ]]; then failure=1; fi
}
run_units() {
  PYTHONPATH=/case/tests python3 - <<'PY'
import json, os, re, sys, unittest
stage = os.environ.get('AUDIO_STAGE', 'all')
ids = json.loads(os.environ.get('AUDIO_TEST_IDS', '[]'))
modules = {'unit-inspector': 'test_inspect_audio',
           'unit-analyser': 'test_analyse_audio_latency',
           'unit-candidate': 'test_prepare_audio_latency',
           'unit-validator': 'test_validate_audio_linux'}
module = modules.get(stage)
pattern = (re.escape(module) if module else r'(?:test_inspect_audio|test_analyse_audio_latency|test_prepare_audio_latency|test_validate_audio_linux)') + r'\.[A-Za-z][A-Za-z0-9_]*\.test_[A-Za-z0-9_]+'
if not isinstance(ids, list) or len(ids) > 128 or any(not isinstance(x, str) or not re.fullmatch(pattern, x) for x in ids) or len(ids) != len(set(ids)) or (stage == 'all' and ids):
    sys.exit('invalid method selection')
loader = unittest.TestLoader()
suite = loader.loadTestsFromNames(ids) if ids else loader.loadTestsFromName(module) if module else loader.discover('tests', pattern='test_*audio*.py')
class Result(unittest.TextTestResult):
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
    def addUnexpectedSuccess(self, test):
        self.failed_ids.add(test.id())
        super().addUnexpectedSuccess(test)
result = unittest.TextTestRunner(verbosity=2, resultclass=Result).run(suite)
with open('/tmp/audio-unit-result.json', 'w') as output:
    json.dump({'tests_run':result.testsRun, 'failed_test_ids':sorted(result.failed_ids),
               'skipped_count':len(result.skipped), 'successful':result.wasSuccessful()}, output)
sys.exit(0 if result.wasSuccessful() else 1)
PY
}
setup_config() {
  # Leave HOME intact. No host config or desktop socket is accessible.
  export XDG_CONFIG_HOME=/tmp/latency-config XDG_RUNTIME_DIR=/tmp/latency-runtime
  mkdir -m 700 -p "$XDG_RUNTIME_DIR" "$XDG_CONFIG_HOME/pipewire/client.conf.d" || return $?
  cp /case/candidate.conf "$XDG_CONFIG_HOME/pipewire/client.conf.d/90-audio-latency-trial.conf"
}
run_config() {
  pw-config -n client.conf merge stream.rules >/tmp/merged-rules || return $?
  python3 - <<'PY'
from pathlib import Path
s=Path('/tmp/merged-rules').read_text()
assert '256/48000' in s and 'alsa_output.test.analog-stereo' in s and 'pw-play' in s
print('native_config_merge=PASS')
PY
}
compile_native() {
  cc -std=c11 -D_GNU_SOURCE -Wall -Wextra -Werror tests/audio/validate_client.c -o /tmp/latency-client $(pkg-config --cflags --libs libpipewire-0.3)
}
if [[ "$stage" == all || "$stage" == unit* ]]; then
  if run_units; then record unit passed; else record unit failed; fi
fi
if [[ "$stage" == all || "$stage" == config || "$stage" == native-* ]]; then
  if setup_config; then config_ready=1; else config_ready=0; record config-setup failed; fi
fi
if [[ "$stage" == all || "$stage" == config ]]; then
  if [[ "$config_ready" == 1 ]] && run_config; then record config passed; else record config failed; fi
fi
if [[ "$stage" == all || "$stage" == compile || "$stage" == native-* ]]; then
  if compile_native; then native_ready=1; record compile passed; else native_ready=0; record compile failed; fi
fi
if [[ "$stage" == all || "$stage" == native-* ]]; then
  daemon_ready=0
  if [[ "$native_ready" == 1 && "$config_ready" == 1 ]]; then
    pipewire >/tmp/pipewire-output 2>&1 &
    pw_pid=$!
    trap 'kill "$pw_pid" 2>/dev/null || true' EXIT
    for i in $(seq 1 100); do
      if [ -S "$XDG_RUNTIME_DIR/pipewire-0" ]; then daemon_ready=1; break; fi
      sleep .05
    done
  fi
  for selected in native-match native-other-app native-other-target; do
    [[ "$stage" == all || "$stage" == "$selected" ]] || continue
    if [[ "$daemon_ready" != 1 ]]; then record "$selected" not-run-prerequisite-failed; continue; fi
    case "$selected" in
      native-match) argv=(pw-play alsa_output.test.analog-stereo 256/48000) ;;
      native-other-app) argv=(other-app alsa_output.test.analog-stereo absent) ;;
      native-other-target) argv=(pw-play alsa_output.other.analog-stereo absent) ;;
    esac
    if timeout 10 /tmp/latency-client "${argv[@]}"; then record "$selected" passed; else record "$selected" failed; fi
  done
fi
python3 - <<'PY'
import json
from pathlib import Path
outcomes = dict(line.split('\t') for line in Path('/tmp/audio-stage-outcomes').read_text().splitlines())
unit = Path('/tmp/audio-unit-result.json')
report = {'stage_outcomes':outcomes, 'failed_test_ids':[]}
if unit.exists():
    report.update(json.loads(unit.read_text()))
print('audio_validation_report='+json.dumps(report, sort_keys=True))
PY
exit "$failure"
