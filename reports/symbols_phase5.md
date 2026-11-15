# Symbols, phase 5: text-anchor rule

**What I did.** OCR (the project's reader, once per label, cached) gives anchor lines: the line with the EXP key, and the line
above the street address. A candidate counts as near its anchor within 3 line heights. I tried the signal two ways with
both scorers: **boost** (a weaker candidate is accepted when near its anchor) and **gate** (only candidates near their anchor
are accepted). The relaxed thresholds were fixed in advance.

**Results on dev** (symbols printed beside their text, 128 symbols, 320 absent; and the random layout, 256 and 480):

| Variant | Recall (anchored) | False positives (anchored) | Recall (random layout) |
| --- | --- | --- | --- |
| silhouette | 122/128 (95.3%) | 0/320 | 241/256 (94.1%) |
| silhouette + boost | 123/128 (96.1%) | 52/320 (16.2%) | 241/256 |
| silhouette + gate | 121/128 (94.5%) | 0/320 | 4/256 (1.6%) |
| CNN | 123/128 (96.1%) | 0/320 | 241/256 (94.1%) |
| CNN + boost | 123/128 (96.1%) | 0/320 | 241/256 |
| CNN + gate | 122/128 (95.3%) | 0/320 | 4/256 (1.6%) |

**What it means.** Anchoring gains at most one symbol on labels laid out the ISO way and costs false positives (silhouette
boost) or collapses when the layout differs (gate). The text exists on every label, symbol or not, so presence cannot be
read from it; only proximity helps, and the scorers already reach about 95% without it. I report it and do not use it.

**Files.** `src/cv/symbols_v2/anchors.py`, `make_anchor_rule` in `detector.py`, OCR cache in `experiment.py`,
`scripts/symbols/anchor_eval.py`, anchored layout in `generate_styled.py`.

**Unsure.** My anchored layout puts the symbol 25 to 45 px after the text; real labels vary more. Real-label evidence is Phase 6.
