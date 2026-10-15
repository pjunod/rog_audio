#!/bin/sh
# Build only the isolated harness observer; production native recipe is separate.
set -eu
if [ "$#" != 2 ] || [ "$1" != --output ]; then
    echo 'usage: build-capture.sh --output EXISTING_PRIVATE_BUILD' >&2
    exit 2
fi
probe=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
out=$(cd "$2" && pwd)
[ "$(uname -s)" = Linux ] && [ "$(uname -m)" = x86_64 ] || exit 2
[ "$(cc -dumpfullversion)" = 15.3.0 ] || { echo 'native compiler pin mismatch' >&2; exit 2; }
[ "$(pkg-config --modversion libpipewire-0.3)" = 1.6.8 ] || exit 2
[ "$(pkg-config --modversion libspa-0.2)" = 0.2 ] || exit 2
for name in atmos-pw-capture native-capture-tests native_capture.py capture-build.json capture-source.tar; do
    [ ! -e "$out/$name" ] && [ ! -L "$out/$name" ] || { echo 'capture output collision' >&2; exit 2; }
done
scratch=$(mktemp -d "$out/.capture-build.XXXXXXXX")
trap 'rm -rf "$scratch"' EXIT HUP INT TERM
# shellcheck disable=SC2046
cc -std=c11 -O2 -Wall -Wextra -Werror -pthread $(pkg-config --cflags libpipewire-0.3) \
    "$probe/native/capture.c" "$probe/native/capture_core.c" \
    $(pkg-config --libs libpipewire-0.3) -o "$scratch/atmos-pw-capture"
# shellcheck disable=SC2046
cc -std=c11 -O2 -Wall -Wextra -Werror -pthread $(pkg-config --cflags libpipewire-0.3) \
    "$probe/native/test_capture.c" "$probe/native/capture_core.c" \
    $(pkg-config --libs libpipewire-0.3) \
    -Wl,--wrap=write,--wrap=pw_stream_dequeue_buffer,--wrap=pw_stream_queue_buffer,--wrap=pw_stream_get_time_n,--wrap=pw_stream_destroy \
    -o "$scratch/native-capture-tests"
cp "$probe/native_capture.py" "$scratch/native_capture.py"
tar --sort=name --mtime=@0 --owner=0 --group=0 --numeric-owner -cf "$scratch/capture-source.tar" -C "$probe" \
    native/capture.c native/capture_core.c native/capture_core.h native/test_capture.c \
    native/PIPEWIRE-EXAMPLE-LICENSE native/compiler-packages.json native_capture.py build-capture.sh
python3 - "$probe" "$scratch" <<'PY'
import hashlib,json,re,subprocess,sys
from pathlib import Path
probe,out=map(Path,sys.argv[1:])
def run(*args):
    return subprocess.check_output(args,text=True)
needed=re.findall(r'Shared library: \[(.*?)\]',run('readelf','--dynamic',str(out/'atmos-pw-capture')))
versions=re.findall(r'Name: (GLIBC_[0-9.]+)',run('readelf','--version-info',str(out/'atmos-pw-capture')))
if 'libpipewire-0.3.so.0' not in needed:
    raise SystemExit('unexpected capture linkage')
receipt={'protocol':'rog-atmos-capture-v1','role':'isolated virtual sink monitor observer only',
    'compiler_version':run('cc','-dumpfullversion').strip(),'architecture':'x86_64',
    'pipewire_headers':run('pkg-config','--modversion','libpipewire-0.3').strip(),
    'needed_sonames':needed,'maximum_required_glibc_version':max(versions,key=lambda x:tuple(map(int,x[6:].split('.')))),
    'source_sha256':{name:hashlib.sha256((probe/name).read_bytes()).hexdigest() for name in
        ('native/capture.c','native/capture_core.c','native/capture_core.h','native/test_capture.c',
         'native/PIPEWIRE-EXAMPLE-LICENSE','native/compiler-packages.json','native_capture.py','build-capture.sh')},
    'artifact_sha256':{name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in
        ('atmos-pw-capture','native-capture-tests','native_capture.py','capture-source.tar')},
    'qualification':'Compile/link only; exact captured PCM and physical acceptance are separate.'}
(out/'capture-build.json').write_text(json.dumps(receipt,indent=2)+'\n')
PY
python3 - "$scratch" "$out" <<'PY'
import os,sys
from pathlib import Path
source,destination=map(Path,sys.argv[1:])
for path in source.iterdir():
    os.link(path,destination/path.name)
PY
