# Speaker autoload — recover the preset when the output device returns

**Status:** native implementation complete; compiler, independent review and
focused acceptance pending · **Updated:** 2026-10-13.

Companion to [speaker installation](SPEAKER_INSTALL.md), which owns installation
and rollback. This document describes the native device-return fix and its
isolated build contract. Physical session-return acceptance remains separate.

## Retain routes before their sink exists

EasyEffects v8.2.8 receives Device Route and sink-node events independently.
Its original delayed route callback returned when the sink was absent. A later
`sinkAdded` therefore carried an empty route description into autoload, selecting
the configured empty fallback even when the physical route was speakers.

The additive [source patch](../patches/easyeffects/0002-Retain-output-routes-for-device-return.patch)
retains the current output route by PipeWire device ID and ALSA profile-device
index. Sink arrival replays that route before preset notification. A single queued
initialization reconciles a sink already discovered by Manager's registry sync
before the effects object connected its signal handlers. A route
arriving after the sink updates the same state. Device removal or route
invalidation clears the cache and node route fields; a generation identifies
scheduled work so older callbacks cannot replay superseded route descriptions.
Notification history is keyed by sink ID/serial and device/profile binding. It
survives route re-enumeration, so an identical route does not reload a preset;
actual device/node removal clears that history. Pending work is recorded only
when a notification is emitted, so invalidation before delivery still rearms
the fresh route notification. Queued autoload events resolve the current node under the PipeWire lock and
require its original serial. Ordinary volume/port updates do not reload a preset.

The existing direct route-event DSP bypass remains active during delayed preset
loading. Speaker DSP remains scoped to the exact bound device and
`analog-output-speaker`; headphones and other output profiles use their current
route descriptions and the empty fallback. There is no added retry delay:
`presetsAutoloadInterval=0` remains the deployed contract. A nonzero configured
interval still controls route-triggered preset notifications.

The original speaker-scope and attributed Ubuntu compatibility patches retain
their accepted bytes. [The source manifest](../patches/easyeffects/source.json)
pins the additive patch and actual route-cache header separately. New compiler
and synthetic acceptance receipts do not imply physical resume, calibrated
sound quality or measured latency.

## Build with bounded native Docker or Podman

Use an owned durable directory outside the owner's checkout. The build context
contains pinned public source, the patch manifest and two synthetic support
probes. It excludes Git metadata, credentials and raw captures.

```bash
# Fetch the exact public upstream source objects into durable owned storage.
git clone --no-checkout --depth 1 --branch v8.2.8 \
  https://github.com/wwmm/easyeffects.git PUBLIC_EASYEFFECTS_GIT

# Compile/package without exposing host audio devices or a session socket.
python3 scripts/build_easyeffects_runtime.py build \
  --source PUBLIC_EASYEFFECTS_GIT --output NEW_RUNTIME_ARTIFACT \
  --image-tag localhost/rog-audio-ee:OWNED_UNIQUE_TAG \
  --container-engine podman
```

`--container-engine docker` selects Docker with the same resource bounds.
Podman builds use one job, a 100,000 µs CPU period and 200,000 µs quota,
6 GiB memory and a 6 GiB total memory/swap limit. CMake compiles with one worker.
Export/package containers use two CPUs, 6 GiB memory, at most 2,048 PIDs and
no network. Dependencies install only in the owned container. Source and build
logs survive failures; disposable contexts live under the durable artifact
output. Packaging scratch lives under `/build/rog-audio-package` inside the
owned container. Cleanup removes only owned contexts/export containers.

The artifact is `rog-audio-easyeffects_8.2.8+rog2_amd64.deb`, with
`runtime.json`, full corresponding `source/`, `patches/`, source manifest and
original licences. The exporter checks binary/package hashes, package version
and source-manifest binding before reporting `runtime-built`. Retain the named
image for focused acceptance; remove only that image after artifacts and
receipts are safely retained. The package has no activation scripts.

Ubuntu 26.10 amd64, Qt 6.11.2 and the original upstream commit
`6d9b1220d3dcebb154ba759a05600662bc0af549` remain the build contract. Compare
actual package/compiler versions with the inherited
[compiler receipt](../evidence/speaker-runtime-build-2026-10-12.json); a new
build receipt must record the versions actually used.

## Regenerate kit metadata without changing tuning bytes

A new runtime changes the exact binary hash. Existing kit and latency-trial
identity checks must continue to reject the old runtime binding. Keep the
v0.2.0 runtime, kit, preset/IR hashes and private rollback snapshots before
preparing the replacement. The runtime build does not write live settings.

```bash
# Read-only capture in the separately coordinated operator window.
python3 scripts/inspect_audio.py --output NEW_PRIVATE_INVENTORY.json

# Reuse the exact retained converted bundle; do not reconvert OEM tuning.
python3 scripts/speaker_install.py prepare \
  --bundle OLD_KIT/speaker-source --inventory NEW_PRIVATE_INVENTORY.json \
  --runtime-manifest NEW_RUNTIME_ARTIFACT/runtime.json --output NEW_KIT

# Require identical preset, IR, fallback and autoload bytes before installation.
diff -qr OLD_KIT/data NEW_KIT/data
```

`diff` must report no differences for the same bound speaker route. Stop if the
payload differs; inspect the fresh hardware/route binding and original hashes.
The kit's new runtime manifest is expected to differ. Its preset name, converted
bundle manifest, plugin order and IR remain bound to the retained source bytes.
Use [the existing install/snapshot procedure](SPEAKER_INSTALL.md#3-snapshot-and-install-files)
for a later coordinated upgrade. Preserve the old package and old kit alongside
the original snapshots so rollback can restore matching runtime and metadata.

After the operator installs and verifies the new runtime, create any new
latency-trial bundle from its fresh read-only capture and newly bound kit. Old
trial bundles remain bound to the previous binary; do not edit hashes by hand,
relax identity guards or reuse an old snapshot as a new trial baseline.

## Run focused acceptance after the combined PR review

The new native cache cases cover both arrival orders, node return, two profile
indices, invalidation/removal, stale generations, device/node ID reuse, missing
profile indices, binding changes, description changes and unchanged volume
updates, duplicate route delivery, same-route re-enumeration and invalidation
before pending notification. Tests compile the actual source-bound header; they do not access audio.
Build contract cases check resource arguments, image collisions, durable context
cleanup, retained failure logs and exported artifact/source bindings.

```bash
# First prepare source and a durable scratch parent; this does not run tests.
python3 scripts/build_easyeffects_runtime.py source \
  --source PUBLIC_EASYEFFECTS_GIT --output NEW_PATCHED_SOURCE
mkdir -p DURABLE_TEST_SCRATCH

# Run each affected unit selection once only after source review is cleared.
TMPDIR=DURABLE_TEST_SCRATCH ROG_EASYEFFECTS_GIT=PUBLIC_EASYEFFECTS_GIT \
  python3 scripts/validate_speaker_install.py --stage source
TMPDIR=DURABLE_TEST_SCRATCH ROG_EASYEFFECTS_SOURCE=NEW_PATCHED_SOURCE \
  python3 scripts/validate_speaker_install.py --stage autoload
TMPDIR=DURABLE_TEST_SCRATCH \
  python3 scripts/validate_speaker_install.py --stage build

# Run each selector inside the retained device-free image with a synthetic kit.
python3 scripts/check_speaker_autoload.py --case route-before-node \
  --kit SYNTHETIC_KIT --output NEW_PRIVATE_ROUTE_FIRST_RECEIPT
python3 scripts/check_speaker_autoload.py --case node-before-route \
  --kit SYNTHETIC_KIT --output NEW_PRIVATE_NODE_FIRST_RECEIPT
python3 scripts/check_speaker_autoload.py --case device-return \
  --kit SYNTHETIC_KIT --output NEW_PRIVATE_RETURN_RECEIPT
```

These graph cases start private PipeWire/WirePlumber and the real runtime, with
synthetic null sinks and generated PCM. They require the exact preset, actual
IR/plugin loading, headphone fallback/ownership release and unchanged kit bytes.
The returned sink has a new serial while the Device remains. Its case also
requires an identical real Route re-enumeration to leave the native autoload
log count unchanged. Each selector
writes its own receipt and retains its failing stage/graph; retry only failed
or code-invalidated cases. Select a failed unit method with `--test-id`.
The inherited ASUS/Lenovo loader-route graph selectors remain available for
focused native regression review. A synthetic pass is not a laptop handoff or
physical hotplug/measurement receipt.
