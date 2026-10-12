# ASUS GU605MZ recovered speaker tuning

The laptop owner requested these recovered files be available directly in
this public repository. The XML targets Realtek ALC285 subsystem `10431c63`;
the matching INF identifies driver `9.117.611.44` dated 2024-01-16.

- [Tuning XML](DEV_0285_SUBSYS_10431C63_PCI_SUBSYS_1C631043.xml) — original DAX3 coefficients and profiles.
- [Matching INF](dax3_ext_rtk.inf) — original hardware mappings and vendor notices.
- [Manifest](manifest.json) — byte counts, SHA-256 digests and extraction provenance.

Original file bytes and notices are retained. These vendor artifacts are
not relicensed by this repository. The INF references other driver-package
files that are not included here; this is not a complete Windows installer.

The extraction reader reported an incorrect-reference-count warning, retained
in the manifest. Hashes identify the recovered files, not vendor-signature
authentication. Linux conversion and physical speaker qualification are
separate from publication. See the [speaker build](../../../docs/AUDIO_SPEAKER_BUILD.md).
