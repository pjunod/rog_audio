#!/bin/sh
# Only inside a device-free isolated container; no host sessions or sound mounts.
set -eu
stage=${1:?explicit stage required}
cd /repo
case "$stage" in
  unit-path|unit-trial)
    shift
    PYTHONPATH=/repo/scripts:/repo/tests python3 tests/audio/run_path_units.py "$stage" "$@"
    exit
    ;;
  compile|config|filter-match|filter-other-app|filter-other-node|filter-other-group|filter-other-role|filter-env-latency|filter-env-quantum) ;;
  *) exit 2;;
esac
[ "$#" -eq 1 ] || exit 2
[ ! -e /dev/snd ] || exit 2
export LC_ALL=C
unset PIPEWIRE_LATENCY PIPEWIRE_QUANTUM PIPEWIRE_PROPS PIPEWIRE_RATE PIPEWIRE_CONFIG_DIR PIPEWIRE_CONFIG_NAME
task_dir=$(mktemp -d /tmp/rog-path-XXXXXXXX)
server_pid=
cleanup() {
  if [ -n "$server_pid" ]; then kill "$server_pid" 2>/dev/null || :; wait "$server_pid" 2>/dev/null || :; fi
  rm -rf "$task_dir"
}
trap cleanup EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
export XDG_CONFIG_HOME="$task_dir/config" XDG_RUNTIME_DIR="$task_dir/runtime"
export XDG_STATE_HOME="$task_dir/state" PIPEWIRE_RUNTIME_DIR="$task_dir/runtime"
export PIPEWIRE_REMOTE=rog-latency-fixture
mkdir -p "$XDG_CONFIG_HOME/pipewire/client.conf.d" "$XDG_CONFIG_HOME/pipewire/pipewire.conf.d" "$XDG_RUNTIME_DIR"
chmod 700 "$XDG_RUNTIME_DIR"
PYTHONPATH=/repo/scripts python3 - "$XDG_CONFIG_HOME/pipewire/client.conf.d/trial.conf" <<'PY'
import sys
from pathlib import Path
from audio_path_trial import rule
Path(sys.argv[1]).write_bytes(rule(256))
PY
if [ "$stage" = config ]; then
  pw-config -n client.conf merge filter.rules > "$task_dir/merged.conf"
  python3 - "$task_dir/merged.conf" <<'PY'
import sys
from pathlib import Path
text=Path(sys.argv[1]).read_text()
assert all(value in text for value in ('org.rog_audio.SpeakerEffects',
    'rog_audio_soe_output_level', 'rog_audio_speaker_sink_group', 'DSP', '256/48000'))
print('config: passed')
PY
  exit
fi
cc -std=c11 -Wall -Wextra -Werror /repo/tests/audio/validate_filter_latency.c \
  $(pkg-config --cflags --libs libpipewire-0.3) -o "$task_dir/filter-probe"
if [ "$stage" = compile ]; then echo 'compile: passed'; exit; fi
printf 'context.properties = { core.name = "%s" }\n' "$PIPEWIRE_REMOTE" > "$XDG_CONFIG_HOME/pipewire/pipewire.conf.d/private.conf"
pipewire > "$task_dir/pipewire.log" 2>&1 & server_pid=$!
ready=0
for attempt in 1 2 3 4 5 6 7 8 9 10; do
  if [ -S "$XDG_RUNTIME_DIR/$PIPEWIRE_REMOTE" ]; then ready=1; break; fi
  sleep .1
done
[ "$ready" -eq 1 ] || { cat "$task_dir/pipewire.log"; exit 1; }
case "$stage" in
  filter-match) argument=match; expected=256/48000; forced=absent;;
  filter-env-latency) export PIPEWIRE_LATENCY=128/48000; argument=match; expected=128/48000; forced=absent;;
  filter-env-quantum) export PIPEWIRE_QUANTUM=64/48000; argument=match; expected=256/48000; forced=64;;
  *) argument=${stage#filter-}; expected=absent; forced=absent;;
esac
"$task_dir/filter-probe" "$argument" > "$task_dir/properties.txt"
python3 - "$task_dir/properties.txt" "$expected" "$forced" "$stage" <<'PY'
import sys
from pathlib import Path
values=dict(line.split('=',1) for line in Path(sys.argv[1]).read_text().splitlines())
assert values['latency']==sys.argv[2], values
assert values['force_quantum']==sys.argv[3], values
assert values['force_rate']==('48000' if sys.argv[3]!='absent' else 'absent'), values
print(sys.argv[4]+': passed; inactive properties only')
PY
