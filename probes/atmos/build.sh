#!/bin/sh
# Run in a disposable Linux SDK container. No dependency fetch is implicit.
set -eu
if [ "$#" != 4 ] || [ "$1" != --source ] || [ "$3" != --output ]; then
    echo 'usage: build.sh --source PINNED_CAVERN_CHECKOUT --output NEW_BUILD' >&2
    exit 2
fi
src=$(cd "$2" && pwd)
probe=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
out=$4
[ "$(uname -s)" = Linux ] || { echo 'Linux build required' >&2; exit 2; }
[ "$(git -c safe.directory="$src" -C "$src" rev-parse HEAD)" = 7d85d1880666ca5ea323848cff47ce7f50b29f7d ] || { echo 'source pin mismatch' >&2; exit 2; }
[ -z "$(git -c safe.directory="$src" -C "$src" status --porcelain --untracked-files=normal)" ] || { echo 'source checkout must be clean' >&2; exit 2; }
[ ! -e "$out" ] || { echo 'output collision' >&2; exit 2; }
cd "$probe"
[ "$(dotnet --version)" = 8.0.414 ] || { echo 'SDK pin mismatch' >&2; exit 2; }
mkdir "$out"
out=$(cd "$out" && pwd)
# Both library projects have no PackageReference; restore needs no network.
dotnet build "$src/Cavern.Format/Cavern.Format.csproj" -c Release --ignore-failed-sources
dotnet publish "$probe/AtmosProbe.csproj" -c Release --self-contained false -o "$out" -p:CavernPath="$src" --ignore-failed-sources
cp "$probe/atmos-probe" "$out/atmos-probe"
cp "$probe/source_manifest.json" "$out/source_manifest.json"
cp "$src/LICENSE.md" "$out/CAVERN-LICENSE.md"
