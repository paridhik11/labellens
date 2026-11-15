# Symbols, phase 0: baseline

**What I did.** I rebuilt the evaluation so the symbol detector can be tested alone on whole labels. The harness
(`src/cv/symbol_eval.py`) finds the label boundary, straightens the photo exactly as `extract_label` does, runs a
detector over the whole label, maps boxes back to the photo and scores IoU >= 0.5. I regenerated the fresh seeds 100 to
102 (and their negative sets) in this branch and ran `detect_symbols_blind` on them.

**Result.** The published numbers reproduce exactly.

| Set | Result (Wilson 95%) |
| --- | --- |
| clean / moderate / hard, symbols found | 102/102 each (96.4 to 100.0) |
| very hard, symbols found | 93/102 (91.2%; 84.1 to 95.3) |
| independent drawings (alt_style) found | **0/204** (0.0 to 1.8) |
| absent symbols reported (false positives) | **0/306** (0.0 to 1.2) |

So the detector works on the one drawing it was built from and on nothing else. Its zero false positives are
cheap: it accepts almost nothing it has not seen.

**Files.** `src/cv/symbol_eval.py` (harness, truth reader, scoring, Wilson tables), `scripts/symbols/baseline.py`,
`scripts/symbols/gen_baseline.sh`, `results/symbols_experiments.md` (experiments table, started),
`.gitignore` (keep the symbols reports, ignore images and caches).

**Check yourself.** The harness reuses `find_label_corners`, `rectify_label` and `project_box` from the extractor, so it
sees the same straightened label; it does not run OCR. Truth boxes for the old datasets are the slot boxes, as in
`eval_v2`.

**Unsure.** I did not re-run the full `eval_v2` (OCR plus barcodes) for this baseline; the symbol-only numbers match the
recorded full-pipeline numbers cell for cell, which is the check.
