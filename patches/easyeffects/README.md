# EasyEffects runtime source series

**Status:** device-return fix accepted; programme-loudness candidate compiled, review and acceptance pending ·
**Updated:** 2026-10-13.

[The source manifest](source.json) pins upstream v8.2.8 and each patch hash.
[SHA256SUMS](SHA256SUMS) was generated deliberately for the new routing series
and the verbatim Ubuntu compatibility import. It was refreshed when candidate
configuration, process/socket and graph identities were isolated from stock
EasyEffects. This is a downstream series; no upstream acceptance is claimed.

Apply in this order to commit
`6d9b1220d3dcebb154ba759a05600662bc0af549`:

1. [Ubuntu compatibility](ubuntu/0001-Disable-echo-canceller.patch), verbatim from
   source package `8.2.8+ds-1build1`, authored by Sebastian Ramacher. The distro
   variant does not compile the WebRTC-2 echo canceller.
2. [Speaker scope](0001-Scope-speaker-correction-to-device-route.patch), local:
   exact device/route selectors, resolved-target interception, typed metadata
   ownership/restoration, direct route-event DSP bypass, and private candidate
   config/application/control/graph identity.
3. [Device-return autoload](0002-Retain-output-routes-for-device-return.patch),
   local: retained device/profile route state, sink-arrival hydration,
   invalidation generations, persistent late profile bindings and current-node
   validation for queued events.

4. [Bounded programme makeup](0003-Bound-programme-loudness-makeup.patch),
   local: independent 0–36 dB automatic makeup limit, retained-state clamping,
   silence/readiness resets, louder-source reduction and preset/UI controls.
   This candidate is distinct from the accepted device-return runtime.

Upstream code and the local routing and makeup headers are GPL-3.0-or-later. The original
copyright headers are retained. Ubuntu packaging attribution and CC0-1.0 terms
are in [COPYRIGHT](ubuntu/COPYRIGHT). Full corresponding upstream source with
the complete additive series is retained beside every exported binary package.

Use [the source/build tool](../../scripts/build_easyeffects_runtime.py) so patch
application cannot silently skip paths when the output sits inside another Git
checkout. See [installation](../../docs/SPEAKER_INSTALL.md) for operators and
[the pinned upstream autoload implementation](https://github.com/wwmm/easyeffects/blob/6d9b1220d3dcebb154ba759a05600662bc0af549/src/presets_autoload_manager.cpp)
for the route-description filename contract.
The [device-return contract](../../docs/SPEAKER_AUTOLOAD.md) describes the new
additive fix, bounded native build and kit metadata regeneration. The prior
accepted/imported patch bytes remain unchanged; checksums were deliberately
extended for the additive patch and route-cache header pin.

[Programme loudness](../../docs/PROGRAMME_LOUDNESS.md) describes the native
capability contract and preserved model-bundle preparation. SHA256SUMS was
deliberately extended for patch3 and the makeup header; original imported and
accepted patch hashes are unchanged. Compilation does not imply acceptance.
