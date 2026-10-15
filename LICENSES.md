# Licensing and attribution

The [MIT licence](LICENSE) applies to original rog_audio code and documentation.
It does not relicense recovered vendor artifacts or separately fetched
third-party dependencies.

| Component | Terms and attribution |
|---|---|
| Original rog_audio tools/docs | MIT, rog_audio contributors |
| Recovered ASUS XML and Dolby driver INF | Original vendor notices retained under profiles/asus/gu605mz; published at laptop owner's request, not relicensed as MIT |
| Downloaded Lenovo speaker XML, Dolby extension INF and official README | Unmodified selected vendor files under profiles/lenovo/x1-extreme-gen1; original notices and source hashes retained, not relicensed as MIT |
| speaker-tuning-to-easyeffects | MIT, Antoine Cellerier and contributors; fetched at the source manifest's exact revision |
| EasyEffects and local runtime patch | GPL-3.0-or-later, Wellington Wallace/upstream contributors; local routing header uses the same terms; corresponding patched source travels with binary artifacts |
| Ubuntu EasyEffects packaging compatibility patch | Original Sebastian Ramacher attribution retained; packaging CC0-1.0 terms and full notice in patches/easyeffects/ubuntu/COPYRIGHT |
| PipeWire native playback and isolated capture helpers | Original rog_audio code under MIT; callback/stream setup adapted from PipeWire 1.6.8 audio-src-ring.c, copyright 2024 Wim Taymans, MIT; full notice in probes/atmos/native/PIPEWIRE-EXAMPLE-LICENSE |
| Native PipeWire shared library/headers | External system dependency, PipeWire upstream MIT and component notices; pinned package/source identity and actual linked ABI recorded separately, library not bundled here |
| Cavern | Bence Sgánetz (VoidX); upstream component-specific licence, retained with built artifacts; see pinned source and Atmos contract |
| Dolby gst-home-audio | Upstream wrapper terms; proprietary runtime libraries are separate and are not supplied here |

See [provenance](docs/PROVENANCE.md) for the repository split and evidence
classes. Build artifacts that include upstream components must retain their
actual notices and satisfy those components' terms.
