# Symbols, phase 6: real labels

**What I did.** No `data/real/` folder (Parth's DailyMed set) exists in this checkout, so I fetched real material myself (with your
approval): 14 real pictogram drawings from Wikimedia Commons (4 ISO, 10 generic icons; licenses and URLs in
`scripts/symbols/real_symbol_sources.json`) and 12 images from 6 DailyMed device-type labels
(`real_label_sources.json`). Images stay local. Two tests:

1. **Real artwork on synthetic labels** (336 symbols). v1 0/336; silhouette 68 (20.2%); CNN 156 (46.4%); **CLIP 206 (61.3%; 56.0 to 66.4)**.
   Generic factory icons: CLIP 83.3%. ISO manufacturer: 44%. ISO use-by hourglass: 12.5% at best (silhouette 6%, CNN 0%).
2. **Real label photos.** Only two of the six labels carry the pictograms: a lancet carton (two hourglasses, plus
   factory-with-date icons that are not the manufacturer symbol) and a pregnancy-test carton (one manufacturer symbol, turned
   90 degrees). I marked 3 symbols and 4 symbol-free boxes by reading zoomed crops: **LLM-labelled, not human-labelled**
   (`scripts/symbols/build_real_labels_eval.py`). Every detector found 0/3. The symbols are 1.0% to 2.3% of the image's short
   side; the proposer's minimum is 4.5%, so no box came near them. False positives on the symbol-free boxes: v1 0, silhouette 0,
   CNN 2/8, CLIP 0.

**What it means.** The detectors do not work on photographs of real cartons yet: small symbols (the proposer needs to scale the
image up), rotated symbols (it needs rotated candidates) and the thin ISO hourglass all fail. Real-label recall is unmeasured beyond
3 symbols. A human should check my boxes.

**Files.** `scripts/symbols/fetch_real_*.py`, `build_real_labels_eval.py`, `src/gen/generate_real_artwork.py`, manifest flag
`"straighten": false` in `symbol_eval.py`.
