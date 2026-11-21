# Public scan protocol v4 (written before E is scored on anything)

E was designed AFTER the fresh result of D failed: D's 3 wrong identifications on the fresh set were all one decoy
(pioglitazone + metformin) shown as plain metformin (`reports/public_scan.md`). The fresh_real set and the 50 device
packs are therefore exposed to this design. Unchanged: the matcher and 0.65, configs A to D, the selection rule.

## E = D + an other-ingredient check
If the OCR text contains an ingredient word of ANY corpus or med100-list product that the accepted product does not
have (similarity at least 0.85, whole word), a matched result becomes needs_review (candidates kept). Ingredient words
are derived (`python -m src.api.public_scan --words`, list in `results/public_scan/derived_words.json`): the sourced
generic-medicine name of each of the 30 corpus products (SPL genericMedicine element in the metadata) and the
`ingredient` field of each of the 70 med100-list products (`src/api/public_scan_names.json`), letters-only words of 4+
letters, minus generic words (D's derived list, the corpus-generic words), minus words in the generic names of 3 or
more of the 100 products, minus words in the label text of 5 or more of the 30 products. 100 words result.
Design history on dev only: a first version used all name words and fired on label words ("childrens", "tabs",
"pharmacy") and turned 36 of 45 correct dev positives into review; it was replaced by the sourced ingredient names
before anything else was scored. On dev (cached OCR) E equals D: positives 45 correct, 0 wrong on all dev sets.

## Scoring
1. E scored ONCE on the 15 decoy products that no run has touched (`decoys_unused` of the seed 42 split, one image
   each, artwork, moderate and hard, 45 photos; list and sha256 in `results/public_scan/photos_v4.json`, rendered with the
   same simulator and seeds rule as v2). Gate: 0 wrong and every photo under 60 s.
2. E re-run on fresh_real (177 photos) as `final_fresh_real_exposed_E`. Labelled "exposed, not a fresh result".
3. The frozen config is committed alone before step 1. No further tuning.

## Limits stated in advance
The ingredient lexicon contains the names of all 70 med100-list products, which include these 15 unused decoys, so E
knows their ingredient words. The test shows that confusable known products are caught, not how a drug absent from both
lists behaves. All 15 are single-ingredient products (none is a combination of a reference product), so the set is
easier than the pioglitazone + metformin case. One source (DailyMed labelers), real artwork with simulated camera
conditions, software-read; real phone photos are unmeasured.
