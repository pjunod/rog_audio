# Provenance — source, migration and evidence boundaries

Read [hardware](AUDIO_HARDWARE.md) for observed device facts and
[implementation](AUDIO_IMPLEMENTATION.md) for dependency pins.

## Audio was separated from the display project

These audio contracts and the sanitized inventory were originally published
in [rog_hdr_dv PR 18](https://github.com/pjunod/rog_hdr_dv/pull/18), merged as
`69dcec96fd72a4f1ee7c529555dd1250cbd799d6` on 2026-10-12. The owner then requested
a separate GitHub repository. This repository imports only audio documents
and evidence, with implementation built independently by GPT-6.1 Sol agents.
Display patches and unrelated history were not imported. Raw diagnostic
captures remain private; the recovered ASUS XML and INF are published at the
owner’s explicit request in profiles/asus/gu605mz.

## Source claims and measurements have different meanings

`source-review` describes code or documentation. `synthetic-test` describes
generated data. `private-offline` processes explicitly supplied private
artifacts. `live-read-only` describes observed configuration. Physical
latency/acoustics and owner listening reports require their own receipts.
The initial inventory is read-only, and firmware calibration messages are
not an acoustic measurement. OEM extraction had a retained reader warning.

## Licences belong to each component

The speaker converter reference is MIT-licensed by Antoine Cellerier and
contributors; source remains separately pinned with retained attribution.
Cavern has its own licence and restrictions; consult the exact copied licence
and source manifest in the Atmos lane before redistribution or commercial use.
Dolby public wrappers do not supply proprietary runtime libraries. This repo
claims no Dolby certification. Recovered ASUS XML/INF retain their original
notices and are published at the owner’s request. No blanket project licence
overrides third-party terms.
