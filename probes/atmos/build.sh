#!/bin/sh
# Run in a disposable Linux SDK container. No dependency fetch is implicit.
set -eu
if [ "$#" != 4 ] || [ "$1" != --source ] || [ "$3" != --output ]; then
    echo 'usage: build.sh --source PINNED_CAVERN_CHECKOUT --output NEW_BUILD' >&2
    exit 2
fi
src=$(cd "$2" && pwd)
probe=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
# Resolve only the parent, preserving a final broken symlink as a collision.
out=$(python3 - "$4" <<'PY'
from pathlib import Path
import sys
p=Path(sys.argv[1])
print(p.parent.resolve(strict=True)/p.name)
PY
)
[ "$(uname -s)" = Linux ] || { echo 'Linux build required' >&2; exit 2; }
[ "$(git -c safe.directory="$src" -C "$src" rev-parse HEAD)" = 7d85d1880666ca5ea323848cff47ce7f50b29f7d ] || { echo 'source pin mismatch' >&2; exit 2; }
[ -z "$(git -c safe.directory="$src" -C "$src" status --porcelain --untracked-files=normal)" ] || { echo 'source checkout must be clean' >&2; exit 2; }
[ ! -e "$out" ] && [ ! -L "$out" ] || { echo 'output collision' >&2; exit 2; }
cd "$probe"
[ "$(dotnet --version)" = 8.0.414 ] || { echo 'SDK pin mismatch' >&2; exit 2; }
sha256sum -c SHA256SUMS
mkdir "$out"
out=$(cd "$out" && pwd)
dep=$(mktemp -d /tmp/atmos-cavern.XXXXXXXX)
trap 'rm -rf "$dep"' EXIT HUP INT TERM
# Archive the verified commit, excluding ignored builds and all local extras.
git -c safe.directory="$src" -C "$src" archive HEAD | tar -x -C "$dep"
python3 - "$probe" "$dep" <<'PY'
import hashlib,json,subprocess,sys
from pathlib import Path
probe,dep=map(Path,sys.argv[1:])
patches=json.loads((probe/'source_manifest.json').read_text())['cavern']['patches']
for patch in patches:
    if hashlib.sha256((probe/patch['path']).read_bytes()).hexdigest()!=patch['sha256']:
        raise SystemExit('patch digest mismatch')
    if hashlib.sha256((dep/patch['source_file']).read_bytes()).hexdigest()!=patch['original_file_sha256']:
        raise SystemExit('original source digest mismatch')
    subprocess.run(['git','-C',str(dep),'apply','--check',str(probe/patch['path'])],check=True)
    subprocess.run(['git','-C',str(dep),'apply',str(probe/patch['path'])],check=True)
    if hashlib.sha256((dep/patch['source_file']).read_bytes()).hexdigest()!=patch['patched_file_sha256']:
        raise SystemExit('patched source digest mismatch')
PY
# Both library projects have no PackageReference; restore needs no network.
dotnet build "$dep/Cavern.Format/Cavern.Format.csproj" -c Release --ignore-failed-sources
dotnet publish "$probe/AtmosProbe.csproj" -c Release --self-contained false -o "$out" -p:CavernPath="$dep" --ignore-failed-sources
dotnet publish "$probe/regressions/BlockBufferRegression.csproj" -c Release --self-contained false -o "$out/regressions" -p:CavernPath="$dep" --ignore-failed-sources
cp "$probe/atmos-probe" "$out/atmos-probe"
cp "$probe/source_manifest.json" "$out/source_manifest.json"
cp "$dep/LICENSE.md" "$out/CAVERN-LICENSE.md"
