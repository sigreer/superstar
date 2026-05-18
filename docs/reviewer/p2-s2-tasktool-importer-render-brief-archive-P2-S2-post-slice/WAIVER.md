# Waiver — P2.S2 post-slice chain parser artifact

The post-slice chain for P2.S2 (`p2-s2-tasktool-importer-render-brief-archive-P2-S2-post-slice`) reached an unambiguous **`ready`** verdict on round 3 (see `r3-*-response.md`). However, `chain.json` records `verdict: null` / `verdict_valid: false` because the codex reviewer wrapper duplicated its body on stdout and stderr, confusing the verdict parser. P2.S3's plan reviewer hit the same artifact at round 5 with the same outcome.

**Resolution.** P2.S2 was closed via `tasktool close P2.S2 --skip-review-gate`, with the bypass and its reason recorded in the slice's `notes` per spec §8.2. The substantive verdict is `ready`; the failure is purely a parser limitation against this specific reviewer wrapper's stdout layout.

This file is a durable acknowledgement of the bypass so future readers of the chain folder don't have to reconstruct the situation from `chain.json` + the slice notes.

**No further action.** Do not re-run the chain; do not change `chain.json`. The reviewer wrapper / parser pairing is the upstream fix.
