# Symbol detection experiments (branch `cv-symbols`)

Goal: a pictogram detector that generalises beyond our own artwork. Targets: recall >= 0.90 on held-out styles,
false positives <= 2% on negatives, Wilson 95% intervals. Everything is synthetic unless a row says "real".
Stopping rule: stop after two ideas in a row that gain under 2 recall points on dev without raising false positives.
Held-out styles are scored once per frozen variant (`results/heldout_log.jsonl`).

## Phase 0: baseline (blind template matching, `detect_symbols_blind`)

Reproduced on freshly generated seeds 100, 101, 102 (17 labels per condition and seed, 51 per condition). The images were
regenerated in this branch with `scripts/symbols/gen_baseline.sh`; the symbol-only harness (`src/cv/symbol_eval.py`) does the
same boundary finding and straightening as `extract_label` and then calls the detector, so OCR and barcodes are not run.
The numbers match `results/cv_final_eval.md` exactly (very hard 93/102).

| Set | What is counted | Result (Wilson 95% interval) |
| --- | --- | --- |
| main, clean | symbols found | 102/102 (100.0%; 96.4 to 100.0) |
| main, moderate | symbols found | 102/102 (100.0%; 96.4 to 100.0) |
| main, hard | symbols found | 102/102 (100.0%; 96.4 to 100.0) |
| main, very hard | symbols found | 93/102 (91.2%; 84.1 to 95.3) |
| alt_style (independent filled artwork) | symbols found | **0/204 (0.0%; 0.0 to 1.8)** |
| missing_manufacturer, missing_expiry, wrong_symbol | absent symbols reported (false positives) | **0/306 (0.0%; 0.0 to 1.2)** |
| small_symbols, large_symbols | symbols found | 204/204 and 204/204 |

The detector is only right on the one drawing it was built from: 0 of 204 independent drawings found, and the zero false
positives are partly because it accepts almost nothing it has not seen.
