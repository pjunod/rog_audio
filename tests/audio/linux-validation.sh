#!/bin/bash
# Run ONLY inside the disposable validation container, with /case populated.
set -euo pipefail
# Refuse accidental execution on the live host before any package operation.
[ -f /.dockerenv ] && [ -d /case ] && [ ! -e /dev/snd ] || {
  echo 'requires disposable Docker container, /case and no sound hardware' >&2
  exit 2
}
if [ -n "${XDG_RUNTIME_DIR:-}" ] && [ -e "$XDG_RUNTIME_DIR/pipewire-0" ]; then
  echo 'refusing inherited PipeWire runtime' >&2
  exit 2
fi
export DEBIAN_FRONTEND=noninteractive
apt-get update >/tmp/apt-output 2>&1
apt-get install -y --no-install-recommends pipewire=1.6.8-1ubuntu4 wireplumber=0.5.17-1ubuntu1 python3 gcc libc6-dev libpipewire-0.3-dev=1.6.8-1ubuntu4 pkg-config >>/tmp/apt-output 2>&1
uname -m
python3 --version
cc --version | head -1
pipewire --version
wireplumber --version
dpkg-query -W -f='${Package}=${Version}\n' pipewire wireplumber libpipewire-0.3-dev gcc
cd /case
python3 -m unittest discover -s tests -p 'test_*audio*.py'
# Disposable home/runtime; no host mounts, no /dev/snd.
export HOME=/tmp/latency-home XDG_CONFIG_HOME=/tmp/latency-home/.config XDG_RUNTIME_DIR=/tmp/latency-runtime
mkdir -m 700 -p "$HOME" "$XDG_RUNTIME_DIR" "$XDG_CONFIG_HOME/pipewire/client.conf.d"
cp /case/candidate.conf "$XDG_CONFIG_HOME/pipewire/client.conf.d/90-audio-latency-trial.conf"
pw-config -n client.conf merge stream.rules >/tmp/merged-rules
python3 - <<'PY'
from pathlib import Path
s=Path('/tmp/merged-rules').read_text()
assert '256/48000' in s and 'alsa_output.test.analog-stereo' in s and 'pw-play' in s
print('native_config_merge=PASS')
PY
cc -std=c11 -D_GNU_SOURCE -Wall -Wextra -Werror tests/audio/validate_client.c -o /tmp/latency-client $(pkg-config --cflags --libs libpipewire-0.3)
pipewire >/tmp/pipewire-output 2>&1 &
pw_pid=$!
trap 'kill "$pw_pid" 2>/dev/null || true' EXIT
for i in $(seq 1 100); do [ -S "$XDG_RUNTIME_DIR/pipewire-0" ] && break; sleep .05; done
timeout 10 /tmp/latency-client pw-play alsa_output.test.analog-stereo 256/48000
timeout 10 /tmp/latency-client other-app alsa_output.test.analog-stereo absent
timeout 10 /tmp/latency-client pw-play alsa_output.other.analog-stereo absent
printf 'isolated_native_client_validation=PASS\n'
