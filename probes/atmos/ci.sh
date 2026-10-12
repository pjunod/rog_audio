#!/bin/sh
# Hosted/offline fast lane: explicit source fetch, then no-network build/test.
set -eu
if [ "$#" -lt 2 ] || [ "$1" != --report ]; then
    echo 'usage: ci.sh --report NEW_REPORT [--test METHOD ...]' >&2
    exit 2
fi
report=$2
shift 2
[ ! -e "$report" ] && [ ! -L "$report" ] || { echo 'report collision' >&2; exit 2; }
probe=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
scratch=$(mktemp -d /tmp/atmos-ci.XXXXXXXX)
tag="rog-atmos-ci:$(basename "$scratch")"
cleanup() {
    docker image rm "$tag" >/dev/null 2>&1 || true
    rm -rf "$scratch"
}
trap cleanup EXIT HUP INT TERM
cp -R "$probe" "$scratch/probe"
git init -q "$scratch/Cavern"
git -C "$scratch/Cavern" fetch --depth 1 https://github.com/VoidXH/Cavern.git 7d85d1880666ca5ea323848cff47ce7f50b29f7d
git -C "$scratch/Cavern" checkout --detach -q FETCH_HEAD
docker build --platform linux/amd64 --target ci -t "$tag" "$probe"
code=0
docker run --rm --name "rog-atmos-$(basename "$scratch")" --network none \
    --memory 1g --pids-limit 128 -v "$scratch:/work" -w /work "$tag" \
    sh -c 'set -eu
        sh probe/build.sh --source /work/Cavern --output build
        ffmpeg -hide_banner -loglevel error -f lavfi -i sine=frequency=997:sample_rate=48000:duration=0.16 -c:a eac3 -b:a 768k -ac 6 -f eac3 /work/bed.eac3
        ffmpeg -hide_banner -loglevel error -f lavfi -i sine=frequency=997:sample_rate=48000:duration=0.16 -c:a eac3 -b:a 192k -ac 2 -f eac3 /work/stereo.eac3
        python3 probe/test_probe.py --probe /work/build/atmos-probe --bed-fixture /work/bed.eac3 --stereo-fixture /work/stereo.eac3 --report /work/regression.json "$@"
    ' sh "$@" || code=$?
if [ -f "$scratch/regression.json" ]; then
    # noclobber is an exclusive create, including a raced output collision.
    (set -C; cat "$scratch/regression.json" > "$report") || exit 2
fi
exit "$code"
