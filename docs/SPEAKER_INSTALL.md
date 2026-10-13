# Speaker installation — exact route, reversible files

**Status:** v0.2.2 published; +rog3 programme implementation accepted; live loudness/hours open ·
**Updated:** 2026-10-13 · **Executes:** internal-speaker installation from
[status](STATUS.md).

[Both current laptops](../evidence/programme-service-autoload-and-current-settings-v2-2026-10-13.json)
now run +rog3 with the separately backported reviewed stop helper and user
unit. Native/helper stops returned 0, settings serialized correctly, two
automatic preset starts and fresh IR/full-stereo checks passed. ROG uses
1024/48000 at −20 LUFS/cap 2.6475 dB; ThinkPad uses 256/48000 at −16
LUFS/cap 14.1375 dB. Original IR/non-AutoGain settings, final limiters, owner
gains/routes, stock services/firmware and exact rollback remain preserved.
New hours are active, not complete; current owner listening, new reboot,
hotplug/resume and physical/acoustic acceptance remain separate. The old
ThinkPad hour, ROG 256/512 failures and earlier recovered updates are dated
history in [status](STATUS.md). No +rog4 package was installed by the backport.

The original [ROG](../evidence/rog-speaker-deployment-2026-10-12.json) and
[ThinkPad](../evidence/thinkpad-speaker-deployment-2026-10-12.json) deployment
receipts retain initial 20% volume, private recovery snapshots and startup
history. Later owner-selected levels are test conditions, not installation
instructions. The owner reports positive demo clarity but ordinary movies/shows
remain too quiet on both; everyday loudness and physical quality acceptance
are unresolved. Both persistent login services remain enabled. Keep the
original filters, limiter and stock amplifier protection intact.

The published [v0.2.1 release](https://github.com/pjunod/rog_audio/releases/tag/v0.2.1)
contains the corrected runtime, exact corresponding source/notices and newly
runtime-bound kits retaining original preset/IR payload bytes. The original
[v0.2.0 release](https://github.com/pjunod/rog_audio/releases/tag/v0.2.0) and
private rollback remain available. See [the upgrade contract](SPEAKER_AUTOLOAD.md)
for an existing installation. Release publication does not qualify sustained
or physical behaviour.

Read [speaker preparation](AUDIO_SPEAKER_BUILD.md) before using
[the installation tool](../scripts/speaker_install.py). The input is an
integrity-checked offline tuning bundle and a fresh read-only inventory.
The kit installs files only. It does not start EasyEffects, install packages,
change the physical default sink, set amplifier controls, restart services,
play audio or record sound. Coordinate the later runtime start and audible
acceptance window separately.

## Prospective v0.2.3 — +rog4 package, paired kits and required service companion

**Prepared, not published:** v0.2.2 remains the current public release. The
commands below apply only after v0.2.3 is actually published at its verified
final merge. The prepared +rog4 package reuses the accepted native ELF/source;
it adds the shutdown helper/MIT notice. Its paired kits use the kept ROG
−20 LUFS/cap 2.6475 and ThinkPad −16 LUFS/cap 14.1375 settings. Both generated
demos are accepted; that is not calibrated acoustics or proof for every medium.
The sealed kit archive retains its preparation-era provisional metadata;
later qualification belongs in the outer release notes/manifest.

Use all five release assets together. The old `rog-audio-speaker-*` download
pattern does not select both new archives:

```bash
# Only after v0.2.3 is published; choose a new durable owned directory.
audio_release_root="$HOME/.local/state/rog-audio/work"
mkdir -p "$audio_release_root"
git clone --branch v0.2.3 https://github.com/pjunod/rog_audio.git \
  "$audio_release_root/rog-audio-0.2.3"
cd "$audio_release_root/rog-audio-0.2.3"
mkdir delivery
gh release download v0.2.3 --repo pjunod/rog_audio --dir delivery \
  --pattern 'rog-audio-packaging-only-8.2.8+rog4.tar.gz' \
  --pattern 'rog-audio-provisional-speaker-kits-8.2.8+rog4.tar.gz' \
  --pattern rog-audio-speaker.service --pattern RELEASE_NOTES.md --pattern SHA256SUMS
(cd delivery && sha256sum --check SHA256SUMS)
tar -tzf delivery/rog-audio-packaging-only-8.2.8+rog4.tar.gz
tar -tzf delivery/rog-audio-provisional-speaker-kits-8.2.8+rog4.tar.gz
tar -xzf delivery/rog-audio-packaging-only-8.2.8+rog4.tar.gz -C delivery
tar -xzf delivery/rog-audio-provisional-speaker-kits-8.2.8+rog4.tar.gz -C delivery
```

The verified layouts are `delivery/artifact` for runtime/package/source and
`delivery/speaker-kits/kits/asus` or `delivery/speaker-kits/kits/thinkpad` for
the ordinary model kit. The package is
`delivery/artifact/rog-audio-easyeffects_8.2.8+rog4_amd64.deb`; its SHA256 is
`17e8dcdd0f59461a035fa0eea8ec6c692194878ed788765a39c7de54ce732e91`.
The runtime/source archive pin is `f00fe028e3c65e669bbb9a696cf0357b67bd0c1642f4fab6ae96f30aa6c0df1c`,
kit archive `c0520d9866b0166e194b71f1c18071755d43753c2474980d2bbe006a23cf9e0f`,
and standalone service companion `65beb0fa15830f9204d9026c06e37ec14fc5bb1d33a4f9108eafce93d3a706dd`.
Match these reviewed pins as well as the downloaded checksum file. Keep source,
all notices, `runtime.json`, release notes and checksums with the delivery.

Use the fresh inventory/prerequisite inspection and the existing snapshot,
install and removal commands in §1–5 with those exact runtime/kit paths. Never
mix +rog4 metadata/kits with an older package or a different model. The deb
contains the helper but no automatic unit/profile activation scripts. Its
`delivery/rog-audio-speaker.service` companion is required separately; validate
and explicitly install it as described under automatic startup. Preserve the
actual state-directory setting if the existing deployment uses a custom path.

For an existing asynchronous `--quit` unit, apply the accepted reversible
[helper/ExecStop correction](SPEAKER_SERVICE.md#3-distinguish-package-distribution-from-the-live-backport)
before invoking `systemctl stop` for an upgrade. Do not issue quit and then
immediately terminate the still-saving primary. Retain the old package,
model-kit/config/install/latency snapshots, unit/link and helper/notice
preimages before the coordinated window. Verify real exit and saved state,
then install the matching package/kit and observe automatic original-voicing
preset/IR/full stereo loading and actual driver period on the new invocation.

Package rollback must keep a corrected helper in an explicitly retained
persistent path outside the package-owned `/usr/lib/rog-audio` path, with its
MIT notice and matching ExecStop, before downgrading to a package that lacks
that helper. Otherwise the downgrade can remove the unit's stop executable.
Restore the retained matching runtime/kit/config preimages with the existing
conflict-aware removal contract; preserve the corrected stop behavior and the
kept independent latency request. Do not restore the known asynchronous
shutdown sequence while the programme runtime is in use. Dependencies are
not automatically removed, and stock PipeWire/WirePlumber, amplifier firmware,
boot and display/session configuration remain outside this upgrade.


## Download v0.2.2 — programme kits bound to +rog3

The [v0.2.2 release](https://github.com/pjunod/rog_audio/releases/tag/v0.2.2)
contains the accepted `8.2.8+rog3` runtime/source/notices, both ordinary
programme kits and checksums. Its tag, remote asset hashes and notes were
verified after direct approval. The commands name this release consistently.

```bash
# Obtain matching v0.2.2 tools and assets.
audio_release_root="$HOME/.local/state/rog-audio/work"
mkdir -p "$audio_release_root"
git clone --branch v0.2.2 https://github.com/pjunod/rog_audio.git "$audio_release_root/rog-audio-0.2.2"
cd "$audio_release_root/rog-audio-0.2.2"
mkdir delivery
gh release download v0.2.2 --repo pjunod/rog_audio --dir delivery \
  --pattern 'rog-audio-speaker-*.tar.gz' --pattern SHA256SUMS
(cd delivery && sha256sum --check SHA256SUMS)
tar -xzf delivery/rog-audio-speaker-runtime-0.2.2.tar.gz -C delivery
tar -xzf delivery/rog-audio-speaker-kits-0.2.2.tar.gz -C delivery
```

Both checksum entries must report `OK`. Use `delivery/runtime` for
`RUNTIME_ARTIFACT` and `delivery/kits/asus` or `delivery/kits/thinkpad` for the
matching `KIT`. The new package is
`rog-audio-easyeffects_8.2.8+rog3_amd64.deb`, SHA256
`92349a51ba98c6659caabc505f57117b8db46b1c70c705d99ea3449ee16ab6a8`.
These ordinary model kits preserve the original FIR and non-AutoGain stages,
with a separate -20 LUFS programme leveler before the original final limiter.
Their adjustable maximum makeup defaults are 2.6475 dB ROG and 10.1375 dB
ThinkPad; they are engineering budgets, not accepted acoustic headroom.

Published [v0.2.1](https://github.com/pjunod/rog_audio/releases/tag/v0.2.1)
remains available with its original-filter kits and `8.2.8+rog2` runtime.
Its assets are `rog-audio-speaker-runtime-0.2.1.tar.gz` and
`rog-audio-speaker-kits-0.2.1.tar.gz`; its package SHA256 remains
`b24e9c97fa1d892c4f1eede22ab5f0bf2669f7b0d3cc5c7985cae4965bd0582a`.
For that retained release use its own tagged tools, kits and `+rog2` package,
rather than combining an old runtime with a programme kit.

Run the read-only prerequisite inspection in §5 and retain the fresh inventory
from §2 before a coordinated install. Packages/kits do not start audio
implicitly. Read §3–4 first so the private snapshot and removal commands are
ready. Keep corresponding source and notices with each package. The new
implementation's passing isolated tests do not qualify everyday loudness or
the subsequent full-hour laptop checks.

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
The updated template also requires `/usr/lib/rog-audio/stop-speaker-effects`,
provided by packaging +rog4 after review/acceptance. Existing +rog2/+rog3
packages require the explicit reversible [service-helper backport](SPEAKER_SERVICE.md)
and a corresponding ExecStop path; validate its availability before replacing
the unit. The checks below do not install that helper implicitly.

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
restoration, not reliable automatic startup. The corrected +rog2 startup
runtime subsequently passed review and 29-unit/six-graph acceptance, merged,
and was installed on the ROG with automatic original-preset loading and a
separate short 512-frame pass. That history remains distinct from a new
post-reboot or final-configuration hour.
[Speaker autoload](SPEAKER_AUTOLOAD.md) owns the exact `+rog2` package contract,
unchanged-tuning kit regeneration, retained rollback and coordinated upgrade
steps. Use that procedure after review and affected acceptance; do not relax
runtime/kit identity checks or duplicate a new migration path.
[Progress and retained attempts](STATUS.md#startup-and-sustained-check-progress--2026-10-13)
remain separate from this installation procedure and prior acceptance.

## 5. Build and deliver the usable runtime

The published v0.2.2 `8.2.8+rog3` native runtime passed the isolated
28-unit/two-graph programme batch. The current packaging follow-up emits
`8.2.8+rog4` with the same native ELF/source and an added authenticated
service-stop helper; its separate source review, eleven units and one
isolated native integration passed. The [verified +rog4 artifact](../evidence/speaker-stop-packaging-only-rog4-2026-10-13.json)
is built without a native recompile; it is not published or installed on the
laptops. Its separate corrected unit companion must be used for future
installs; the deb alone does not replace or enable the user unit. Actual laptop
listening/stability remain pending; published v0.2.1 and its `+rog2` recovery
artifacts remain unchanged. Read [programme loudness](PROGRAMME_LOUDNESS.md)
for the independent controls, preserved voicing and source/build contract.
Follow the focused
[autoload build and unchanged-tuning upgrade contract](SPEAKER_AUTOLOAD.md)
for bounded native builds, corresponding source, new runtime/kit binding and
retained rollback. The v0.2.0 `+rog1` release and its receipt remain historical
recovery assets; the commands below name the current output consistently.
Use them only after the combined review and affected acceptance are clear.

```bash
# Read public Git objects only; working-tree/private data never enter Docker.
git clone https://github.com/wwmm/easyeffects.git PUBLIC_EASYEFFECTS_GIT
python3 scripts/build_easyeffects_runtime.py build \
  --source PUBLIC_EASYEFFECTS_GIT --output RUNTIME_ARTIFACT \
  --image-tag localhost/rog-audio-ee:acceptance \
  --container-engine podman

# Read-only prerequisite report on EACH actual laptop.
python3 scripts/inspect_speaker_runtime.py \
  --manifest RUNTIME_ARTIFACT/runtime.json --output PRIVATE_COMPATIBILITY.json
```

The current `rog-audio-easyeffects_8.2.8+rog3_amd64.deb` installs only its
private prefix, launcher, desktop entry and licence/source notices. It has no
service scripts or autostart activation. Dependencies derive from Ubuntu's
EasyEffects `8.2.8+ds-1build1` package plus required LSP LV2 plugins. The runtime
supports Ubuntu 26.10 amd64 and its Qt 6.11.2 private ABI; other versions need
an appropriate rebuild. GCC 15.3.0 compiled Release with `-O3 -DNDEBUG
-std=gnu++20`; the actual compiler defaults were `-march=x86-64` and
`-mtune=generic`, with no native CPU tuning. That application baseline supports
both laptops' amd64 processors. Shared libraries retain Ubuntu's package ABI.
The historical [v0.2.0 compiler receipt](../evidence/speaker-runtime-build-2026-10-12.json)
binds its 22 modified source files and `+rog1` artifact. The
[review-fixed compiler/export receipt](../evidence/speaker-autoload-reviewed-build-2026-10-13.json)
binds corrected `b6d5f1e` source, the accepted `+rog2` artifact and all 711 corresponding
source files. The earlier [intermediate receipt](../evidence/speaker-autoload-build-2026-10-13.json)
for `135c60f` is retained unchanged as history; it is superseded for this
candidate. The separate [corrected +rog3 build receipt](../evidence/programme-loudness-reviewed-build-2026-10-13.json)
binds 713 exact files and the new package. Its [28-unit/two-graph acceptance](../evidence/programme-loudness-acceptance-2026-10-13.json)
retains the two first-attempt startup failures, reviewed raw-PCM correction and
failed-selector-only retries. Its final validation/merge and publication passed; live
acceptance remains separately recorded in [status](STATUS.md).
The prerequisite report lists installed versions/providers and missing
prerequisites without installing anything.

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
sudo apt install ./RUNTIME_ARTIFACT/rog-audio-easyeffects_8.2.8+rog3_amd64.deb
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

The receipts immediately below are inherited v0.2.0 acceptance from PR 2.
The current v0.2.1 startup runtime has a separate [29-unit/six-graph receipt](../evidence/speaker-autoload-acceptance-2026-10-13.json);
those passes do not rewrite the older package or test identities.

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
helper hashes are recorded. The historical v0.2.0 production package remained
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
