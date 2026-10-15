#!/bin/sh
# Add only the native live backend to an existing private Atmos build.
set -eu
if [ "$#" != 2 ] || [ "$1" != --output ]; then
    echo 'usage: build-native.sh --output EXISTING_PRIVATE_BUILD' >&2
    exit 2
fi
probe=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
out=$(cd "$2" && pwd)
[ "$(uname -s)" = Linux ] && [ "$(uname -m)" = x86_64 ] || { echo 'Linux x86_64 build required' >&2; exit 2; }
[ "$(cc -dumpfullversion)" = 15.3.0 ] || { echo 'native compiler pin mismatch' >&2; exit 2; }
[ "$(pkg-config --modversion libpipewire-0.3)" = 1.6.8 ] || { echo 'PipeWire header pin mismatch' >&2; exit 2; }
[ "$(pkg-config --modversion libspa-0.2)" = 0.2 ] || { echo 'SPA header pin mismatch' >&2; exit 2; }
for name in atmos-pw-playback native-tests native-io-tests native-build.json native-source.tar PIPEWIRE-EXAMPLE-LICENSE native_playback.py; do
    [ ! -e "$out/$name" ] && [ ! -L "$out/$name" ] || { echo 'native output collision' >&2; exit 2; }
done
scratch=$(mktemp -d "$out/.native-build.XXXXXXXX")
trap 'rm -rf "$scratch"' EXIT HUP INT TERM
# pkg-config emits compiler tokens for the pinned local headers, never user input.
# shellcheck disable=SC2046
cc -std=c11 -O2 -Wall -Wextra -Werror -pthread $(pkg-config --cflags libpipewire-0.3) \
    "$probe/native/playback.c" "$probe/native/playback_core.c" \
    $(pkg-config --libs libpipewire-0.3) -o "$scratch/atmos-pw-playback"
cc -std=c11 -O2 -Wall -Wextra -Werror -pthread \
    "$probe/native/test_core.c" "$probe/native/playback_core.c" -o "$scratch/native-tests"
# shellcheck disable=SC2046
cc -std=c11 -O2 -Wall -Wextra -Werror -pthread $(pkg-config --cflags libpipewire-0.3) \
    "$probe/native/test_io.c" "$probe/native/playback_core.c" \
    $(pkg-config --libs libpipewire-0.3) \
    -Wl,--wrap=pw_stream_dequeue_buffer,--wrap=pw_stream_queue_buffer,--wrap=pw_stream_flush -o "$scratch/native-io-tests"
cp "$probe/native/PIPEWIRE-EXAMPLE-LICENSE" "$scratch/PIPEWIRE-EXAMPLE-LICENSE"
cp "$probe/native_playback.py" "$scratch/native_playback.py"
tar --sort=name --mtime=@0 --owner=0 --group=0 --numeric-owner -cf "$scratch/native-source.tar" -C "$probe" \
    native/playback.c native/playback_core.c native/playback_core.h \
    native/test_core.c native/test_io.c native/PIPEWIRE-EXAMPLE-LICENSE \
    native/compiler-packages.json native_playback.py build-native.sh
# Record actual linked ABI rather than claiming general Linux portability.
python3 - "$probe" "$scratch" <<'PY'
import hashlib,json,re,subprocess,sys
from pathlib import Path
probe,out=map(Path,sys.argv[1:])
def run(*args):
    return subprocess.check_output(args,text=True)
linked=run('readelf','--dynamic',str(out/'atmos-pw-playback'))
needed=re.findall(r'Shared library: \[(.*?)\]',linked)
versions=re.findall(r'Name: (GLIBC_[0-9.]+)',run('readelf','--version-info',str(out/'atmos-pw-playback')))
floor=max(versions,key=lambda x:tuple(map(int,x[6:].split('.'))))
if 'libpipewire-0.3.so.0' not in needed:
    raise SystemExit('unexpected native PipeWire linkage')
receipt={'protocol':'rog-atmos-pw-v1','architecture':'x86_64','compiler':run('cc','--version').splitlines()[0],
    'compiler_version':run('cc','-dumpfullversion').strip(),
    'pipewire_headers':run('pkg-config','--modversion','libpipewire-0.3').strip(),
    'spa_headers':run('pkg-config','--modversion','libspa-0.2').strip(),
    'flags':['-std=c11','-O2','-Wall','-Wextra','-Werror','-pthread'],
    'needed_sonames':needed,'maximum_required_glibc_version':floor,
    'source_sha256':{name:hashlib.sha256((probe/name).read_bytes()).hexdigest() for name in
        ('native/playback.c','native/playback_core.c','native/playback_core.h','native/test_core.c','native/test_io.c',
         'native/PIPEWIRE-EXAMPLE-LICENSE','native/compiler-packages.json',
         'native_playback.py','build-native.sh')},
    'artifact_sha256':{name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in
        ('atmos-pw-playback','native-tests','native-io-tests','native-source.tar','PIPEWIRE-EXAMPLE-LICENSE','native_playback.py')},
    'qualification':'Compile/link receipt only; software acceptance and physical limits are separate.'}
(out/'native-build.json').write_text(json.dumps(receipt,indent=2)+'\n')
PY
python3 - "$scratch" "$out" <<'PY'
import os,sys
from pathlib import Path
source,destination=map(Path,sys.argv[1:])
for path in source.iterdir():
    os.link(path,destination/path.name)
PY
