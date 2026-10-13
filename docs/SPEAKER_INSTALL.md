# Speaker installation — exact route, reversible files

**Status:** reviewed compiler, 33 lane unit cases and both device graph cases passed ·
**Updated:** 2026-10-13 · **Executes:** internal-speaker installation from
[status](STATUS.md).

Both laptops now run their separate authorized v0.2.0 candidates. The ROG's
live preset, IR, plugins and physical output checks are recorded in
[the deployment receipt](../evidence/rog-speaker-deployment-2026-10-12.json).
The owner reports substantial audible improvement and requested automatic
startup, enabled for user login after reboot. Initial enablement preserved
the listening process; actual post-reboot startup is pending observation. Initial
deployment volume was 20%, and the prior volume, private snapshot and versioned
recovery tools are retained. Physical hotplug/measurement acceptance is pending.
The ThinkPad's separate Lenovo candidate has also passed its live loading and
speaker output checks, with login startup enabled and rollback retained; see
[its deployment receipt](../evidence/thinkpad-speaker-deployment-2026-10-12.json).
Owner listening feedback on the ThinkPad remains pending. Both candidates
use the persistent service. ThinkPad retains the 256-frame request; ROG now
uses the 2048-frame baseline after reviewed removal of its failed request.
Their [paired latency trials and rollback](LATENCY_COMPARISON.md#7-paired-256-frame-trials--both-tuned-paths-preserved)
preserved tuning, physical defaults and the volume observed in that paired
window: 86% on the ROG, 20% on the ThinkPad. Those values are historical,
distinct from initial installation and later owner adjustments. The current
normal-use attempt starts at 94% on ROG and 100% on ThinkPad; tests preserve the
chosen level and record later adjustments.

Read [speaker preparation](AUDIO_SPEAKER_BUILD.md) before using
[the installation tool](../scripts/speaker_install.py). The input is an
integrity-checked offline tuning bundle and a fresh read-only inventory.
The kit installs files only. It does not start EasyEffects, install packages,
change the physical default sink, set amplifier controls, restart services,
play audio or record sound. Coordinate the later runtime start and audible
acceptance window separately.

## Download v0.2.0 and select your kit

The [v0.2.0 release](https://github.com/pjunod/rog_audio/releases/tag/v0.2.0)
contains the reviewed runtime package with corresponding source, two kits and
SHA256 checksums. Use an owned directory outside any existing checkout.

```bash
# Obtain versioned tools and matching assets; requires GitHub CLI.
git clone --branch v0.2.0 https://github.com/pjunod/rog_audio.git rog-audio-0.2.0
cd rog-audio-0.2.0
mkdir delivery
gh release download v0.2.0 --repo pjunod/rog_audio --dir delivery \
  --pattern 'rog-audio-speaker-*.tar.gz' --pattern SHA256SUMS
(cd delivery && sha256sum --check SHA256SUMS)
tar -xzf delivery/rog-audio-speaker-runtime-0.2.0.tar.gz -C delivery
tar -xzf delivery/rog-audio-speaker-kits-0.2.0.tar.gz -C delivery
```

Both checksum entries must report `OK`. The runtime directory is
`delivery/runtime`. Choose `delivery/kits/asus` for the GU605MZ or
`delivery/kits/thinkpad` for the first-generation X1 Extreme. These are separate
music/balanced candidates bound to the inspected device and route. Use those
paths in place of `RUNTIME_ARTIFACT` and `KIT` below. The `.deb` SHA256 is
`089ae964c8e1b75281d589a6cd52a3a25d358f9443112162fea616b69b5904d7`.

Run the read-only prerequisite inspection in §5 and retain the fresh inventory
from §2 before the coordinated install. The kits and package do not start audio
automatically. Read §3–4 before installation so the private snapshot and removal
commands are ready. Keep the corresponding source and notices with the package.

## 1. Bind the hardware and runtime

The kit binds the Realtek codec `10ec0285` to ASUS subsystem `10431c63` or
Lenovo subsystem `17aa2276`, the codec's ALSA card, one exact ALSA output node
name and the selected `analog-output-speaker` route. The Lenovo preparer adds
its own first-generation ThinkPad identity checks. Neither a generic stereo
sink nor a transient PipeWire node ID is a hardware selector.

EasyEffects autoload uses the route **description** in the filename and
`device-profile` JSON key. The routing correction uses the ALSA route **name**.
Both are retained so translated descriptions do not replace the ALSA selector.
Headphones must not inherit speaker EQ from delayed preset loading.

The runtime is built from upstream EasyEffects v8.2.8 commit
`6d9b1220d3dcebb154ba759a05600662bc0af549` with attributed Ubuntu compatibility
and a local routing correction. A runtime manifest binds its binary hash and
`exact-device-route-v1` contract. A self-supplied manifest proves byte binding,
not external authentication or acoustic acceptance.

## 2. Prepare an inactive kit

Use new output paths. Runtime artifacts are built in isolation. The reviewed
ASUS and ThinkPad graph cases passed separately with their own tuning bytes;
coordinated installation and physical acceptance remain pending.

```bash
# Read-only graph, codec and route inventory.
python3 scripts/inspect_audio.py --output INVENTORY.json

# Compose the verified candidate and exact runtime identity.
python3 scripts/speaker_install.py prepare \
  --bundle BUNDLE --inventory INVENTORY.json \
  --runtime-manifest RUNTIME.json --output KIT
```

Exit 0 means files were prepared. Exit 2 means invalid input or a filesystem
conflict; exit 3 means missing supported hardware/runtime capability. Public
output reports status and hashes, without private paths or device captures.
The command does not activate the candidate.

The kit contains the original verified bundle, a uniquely named output preset,
its IR, an empty fallback preset and exact device/route autoload JSON. It
composes the existing importer rather than duplicating the tuning converter.

## 3. Snapshot and install files

Close the candidate before explicit filesystem changes so concurrent writers
cannot silently overwrite the snapshot or candidate. The installer detects
its graph clients or live candidate lock and returns a normal resource-conflict error. It never quits
an application for you. Candidate files live under
`${XDG_STATE_HOME:-$HOME/.local/state}/rog-audio/easyeffects/`, with separate
`config`, `data` and `cache` subdirectories. `ROG_AUDIO_STATE_DIR` selects
another absolute candidate state root. The raw binary enforces this layout,
including when launched directly. Stock EasyEffects XDG trees are untouched.
The application identity, PipeWire nodes/groups, runtime lock and local
control socket are distinct. Stock app presence is not a file-install conflict;
close it during the audible acceptance window to avoid two processors.
Do not repurpose HOME or use an unknown Flatpak configuration layout.

```bash
# Explicit later installation; does not start the runtime.
python3 scripts/speaker_install.py install \
  --kit KIT --runtime EXACT_BINARY --snapshot PRIVATE_SNAPSHOT

# Read snapshot state and owned-file differences.
python3 scripts/speaker_install.py status --snapshot PRIVATE_SNAPSHOT
```

The snapshot is a new mode-0700 directory containing all prior EasyEffects
candidate config/data files, byte hashes, modes, empty directory inventory and private
hardware collection. Each root has at most 1,024 entries, each file at most
4 MiB, and both roots together at most 64 MiB. Symlinks and special files fail.
A durable planned-write journal precedes installation; an interrupted write
can therefore be restored even if its completion journal entry was not saved.
Copied backup files, each new backup directory and publication parents are
synced before managed bytes can be replaced. Removal uses the same durable
archive path before restoring anything. Settings are derived from the verified
snapshot backup, so an edit before snapshotting is retained and an edit after
snapshotting causes a preimage conflict. Snapshot states are a fixed lifecycle
enum; arbitrary corrupt diagnostics never become public status values.
Snapshots cannot overlap the target XDG trees.

Settings select only the exact physical output for EasyEffects, keep automatic
output processing, disable input processing, and select an empty autoload
fallback. The physical default remains as configured by the user. Existing app blocklists
are retained when presets load (`ignorePresetBlocklist=true`).
The new runtime's target-aware policy is required for these settings.

## 4. Remove and retain post-install state

If login startup was enabled, first disable it and stop the managed service.
The final controlled quit also handles a still-running initial deployment
process. This prevents a later login from relaunching a removed candidate.

```bash
systemctl --user disable --now rog-audio-speaker.service
QT_QPA_PLATFORM=offscreen rog-speaker-effects --quit
rm -- "$HOME/.config/systemd/user/rog-audio-speaker.service"
systemctl --user daemon-reload
```

On both inspected laptops the prior unit was absent. If replacing an existing unit
elsewhere, retain and restore its original bytes and enablement instead.

```bash
# Explicit later removal; EasyEffects must be closed.
python3 scripts/speaker_install.py remove \
  --snapshot PRIVATE_SNAPSHOT --archive PRIVATE_POST_INSTALL_ARCHIVE
```

Removal first snapshots the complete post-install state. It restores managed
config files and owned data bytes, preserves unrelated new files, and removes
only empty new directories. Edited owned preset/IR/autoload files are a conflict
because deleting them would lose user work. Prior plugin settings are restored
byte for byte, including their recorded modes. Incomplete installs are
recoverable through the same interface.

Keep both private snapshots until removal and the coordinated runtime check
are accepted. They contain personal application settings and must not enter
Git. No package or boot rollback is needed for these filesystem operations.
Controlled `--quit` restores owned per-stream targets before disconnecting.
Original target metadata is held in memory; forced termination does not provide
that controlled restoration. The session manager handles disappearing virtual
nodes. Physical restart/resume and forced-termination behaviour remain acceptance
work, and the file journal is a filesystem recovery receipt.

### Automatic startup after login

[The user unit](../systemd/rog-audio-speaker.service) starts the installed
runtime when the user manager reaches `default.target`, including login after
reboot. It orders startup after PipeWire and WirePlumber and uses the installed
candidate's private state under `$HOME/.local/state/rog-audio/easyeffects`.
`QT_QPA_PLATFORM=offscreen` supports background processing without opening a
window. A custom candidate state location requires changing the unit's
`ROG_AUDIO_STATE_DIR` to that same absolute location before validation.

```bash
# Validate the unit on the target host; retain any prior unit before replacement.
systemd-analyze --user verify systemd/rog-audio-speaker.service
install -D -m 0644 systemd/rog-audio-speaker.service \
  "$HOME/.config/systemd/user/rog-audio-speaker.service"
systemctl --user daemon-reload
# Enable future login startup without interrupting an existing listening run.
systemctl --user enable rog-audio-speaker.service
systemctl --user is-enabled rog-audio-speaker.service
```

Both laptops' unit validation, manager properties and resolved login-target
links passed. Their current deployment-session processes stayed unchanged.
The persistent service takes over at the next normal user-manager startup;
no reboot was performed for this configuration change. See
[the startup receipt](../evidence/rog-speaker-startup-2026-10-12.json).
The same checks are retained in the ThinkPad deployment receipt above.
Immediate bypass remains `rog-speaker-effects --quit`; permanent startup
rollback uses the disable/stop procedure above. Stock amplifier controls,
physical default selection and operator volume are not set by this unit.

**Later session observation — 2026-10-13:** the authorized ROG logout/handoff
exposed autoload bypass when device-route availability preceded node handling.
The operator reported consistent tuning/route files and restored the exact
native tuned preset, retaining physical volume. The full ASUS chain then
passed bounded zero-PCM checks and entered a fresh hour. This demonstrates
restoration, not reliable automatic startup. The native runtime correction is implemented; candidate compilation and
focused acceptance remain pending. It is not installed during the active hour.
[Speaker autoload](SPEAKER_AUTOLOAD.md) owns the exact `+rog2` package contract,
unchanged-tuning kit regeneration, retained rollback and coordinated upgrade
steps. Use that procedure after review and affected acceptance; do not relax
runtime/kit identity checks or duplicate a new migration path.
[Progress and retained attempts](STATUS.md#startup-and-sustained-check-progress--2026-10-13)
remain separate from this installation procedure and prior acceptance.

## 5. Build and deliver the usable runtime

```bash
# Read public Git objects only; working-tree/private data never enter Docker.
git clone https://github.com/wwmm/easyeffects.git PUBLIC_EASYEFFECTS_GIT
python3 scripts/build_easyeffects_runtime.py build \
  --source PUBLIC_EASYEFFECTS_GIT --output RUNTIME_ARTIFACT \
  --image-tag rog-audio-ee:acceptance

# Read-only prerequisite report on EACH actual laptop.
python3 scripts/inspect_speaker_runtime.py \
  --manifest RUNTIME_ARTIFACT/runtime.json --output PRIVATE_COMPATIBILITY.json
```

The delivered `rog-audio-easyeffects_8.2.8+rog1_amd64.deb` installs only its
private prefix, launcher, desktop entry and licence/source notices. It has no
service scripts or autostart activation. Dependencies derive from Ubuntu's
EasyEffects `8.2.8+ds-1build1` package plus required LSP LV2 plugins. The runtime
supports Ubuntu 26.10 amd64 and its Qt 6.11.2 private ABI; other versions need
an appropriate rebuild. GCC 15.3.0 compiled Release with `-O3 -DNDEBUG
-std=gnu++20`; the actual compiler defaults were `-march=x86-64` and
`-mtune=generic`, with no native CPU tuning. That application baseline supports
both laptops' amd64 processors. Shared libraries retain Ubuntu's package ABI.
[The compiler receipt](../evidence/speaker-runtime-build-2026-10-12.json) binds
all 22 modified compiled source files to the retained review source.
The report lists installed versions/providers and
missing prerequisites without installing anything.

`runtime.json` records binary/package SHA256, exact source/patch manifest,
dependency expression, build package versions and ELF library names. Retain
`source/`, `patches/`, `source-manifest.json` and `UBUNTU-COPYRIGHT` beside the
package; these provide corresponding GPL source and original notices. The
compiled prefix is `/opt/rog-audio/easyeffects`; install the Debian package
at that path rather than inventing a relocation procedure.

The following commands are for the later coordinated installation window.
Use the delivered per-device kit and a new private snapshot directory.

```bash
# Coordinated package/dependency installation on the selected laptop.
sudo apt install ./RUNTIME_ARTIFACT/rog-audio-easyeffects_8.2.8+rog1_amd64.deb
mkdir -p "${XDG_STATE_HOME:-$HOME/.local/state}/rog-audio/snapshots"
python3 scripts/speaker_install.py install \
  --kit KIT --runtime /opt/rog-audio/easyeffects/bin/easyeffects \
  --snapshot "${XDG_STATE_HOME:-$HOME/.local/state}/rog-audio/snapshots/PRE_INSTALL"

# Explicit candidate start/stop; these address only its private control socket.
rog-speaker-effects --hide-window --service-mode
rog-speaker-effects --quit

# Restore files, retain later settings, then remove only the candidate package.
python3 scripts/speaker_install.py remove \
  --snapshot "${XDG_STATE_HOME:-$HOME/.local/state}/rog-audio/snapshots/PRE_INSTALL" \
  --archive "${XDG_STATE_HOME:-$HOME/.local/state}/rog-audio/snapshots/POST_INSTALL"
sudo apt remove rog-audio-easyeffects
```

Do not use `apt autoremove`: prerequisites may be shared with existing desktop
software. Stock routing, configuration, amplifier firmware and protection are
preserved. No display or session restart belongs to this procedure.

## 6. Review-bound isolated acceptance

Run these tests only after independent adversarial review and fixes.
[The unit receipt](../evidence/speaker-installation-unit-validation-2026-10-12.json)
records one source, 12 installer and 20 native routing cases passing against
integrated `155d003`, with zero skips. The initial 20 native launches failed
on a noexec Docker temporary mount; only those failed cases were retried with
an executable private mount. Source/installer passes were retained.
[The graph receipt](../evidence/speaker-runtime-graph-validation-2026-10-12.json)
records both device cases passing all 10 assertions against integrated
`ca0e755`, with their separate verified tuning bundles. Only the failed ASUS
case was retried after focused fixture review; the ThinkPad case passed on its
first run. The graph helper was rebuilt separately, and both image IDs and
helper hashes are recorded. The production package remained
`089ae964c8e1b75281d589a6cd52a3a25d358f9443112162fea616b69b5904d7`.
Each selector can be retried independently.

```bash
# Prepare actual patched source for native policy compilation.
python3 scripts/build_easyeffects_runtime.py source \
  --source PUBLIC_EASYEFFECTS_GIT --output PATCHED_SOURCE
ROG_EASYEFFECTS_GIT=PUBLIC_EASYEFFECTS_GIT \
  python3 -m unittest discover -s tests -p test_easyeffects_runtime.py -v
python3 -m unittest discover -s tests -p test_speaker_install.py -v
ROG_EASYEFFECTS_SOURCE=PATCHED_SOURCE \
  python3 -m unittest discover -s tests -p test_speaker_routing.py -v

# Compose CI-only bindings from public/synthetic inventory and converted bytes.
python3 scripts/prepare_speaker_graph_kit.py --device asus \
  --bundle ASUS_BUNDLE --runtime-manifest RUNTIME_ARTIFACT/runtime.json \
  --output SYNTHETIC_ASUS_KIT
python3 scripts/prepare_speaker_graph_kit.py --device thinkpad \
  --bundle LENOVO_BUNDLE --runtime-manifest RUNTIME_ARTIFACT/runtime.json \
  --output SYNTHETIC_LENOVO_KIT

# Run INSIDE the retained image, with no /dev/snd or host session mounts.
python3 scripts/check_speaker_graph.py --case asus-loader-route \
  --kit ASUS_KIT --output NEW_PRIVATE_ASUS_RECEIPT
python3 scripts/check_speaker_graph.py --case lenovo-loader-route \
  --kit LENOVO_KIT --output NEW_PRIVATE_LENOVO_RECEIPT

# Example failed-case retry; passing cases are not repeated.
ROG_EASYEFFECTS_SOURCE=PATCHED_SOURCE PYTHONPATH=tests \
  python3 -m unittest -v \
  test_speaker_routing.SpeakerRoutingTests.test_external_target_wins
```

Graph inputs are source-verified converted bundles, runtime manifest, kit and a
new writable output directory in durable owned storage. CI builds ASUS/Lenovo bundles from the public
profile files and sanitized inventories described in
[speaker preparation](AUDIO_SPEAKER_BUILD.md) and
[ThinkPad preparation](THINKPAD_AUDIO.md). The fixture preparer invents node and
route observations; it does not need private host captures.

```bash
# Clean container invocation; KIT_DIR holds the synthetic per-device kit.
mkdir -m 700 NEW_OUTPUT  # Retained output beneath the durable owned workspace.
docker run --rm --network none --read-only --cap-drop ALL \
  --security-opt no-new-privileges --user "$(id -u):$(id -g)" \
  --env TMPDIR=/output \
  --mount "type=bind,src=$(pwd),dst=/repo,readonly" \
  --mount "type=bind,src=ABSOLUTE_KIT_DIR,dst=/kit,readonly" \
  --mount "type=bind,src=ABSOLUTE_NEW_OUTPUT,dst=/output" \
  rog-audio-ee:acceptance python3 /repo/scripts/check_speaker_graph.py \
  --case asus-loader-route --kit /kit --output /output/case
```

The fixture stores its runtime/configuration under the retained output;
`TMPDIR` also points there rather than temporary project storage.

The real EasyEffects loader and plugins process generated audio through an
exported synthetic SPA Device Route and null sinks. PipeWire's
[client-device module](https://github.com/PipeWire/pipewire/blob/1.6.8/src/modules/module-client-device.c)
exports `SPA_TYPE_INTERFACE_Device` locally and exposes a PipeWire Device to
remote observers; the fixture implements SPA info/result/sync methods. The pinned
client and server configurations already load that module, so the fixture uses
them without duplicate registration. Each laptop's emitted preset/IR
gets a separate receipt. Failures retain the last private graph snapshot and
name the observation stage; session-manager state stays in the writable private
output tree. The runner observes ordinary app interception,
HDMI/USB choices, automatic loading with two route profile-device indices,
default changes, route bypass before delayed autoload,
stock/candidate isolation and exact typed target restoration. The latter sets
real metadata before interception, observes the owned effects pair, then
requires the original types and values after controlled quit. Its RMS comparison
is a synthetic signal check, not an acoustic or physical latency measurement.
Remove the exact owned Docker image only after receipts and deliverables are
retained; do not prune shared images or caches.

## 7. Evidence still required

Compiler success, synthetic graphs, preset load, plugin discovery and reversible
file installation establish separate capabilities. None establishes calibrated
sound quality, physical speaker protection, host Atmos rendering, or physical
latency. Hardware headphone hotplug timing, resume, calls, CPU/power and audible
comparison remain coordinated acceptance work. Preserve stock amplifier
firmware, calibration and protection throughout those tests.
