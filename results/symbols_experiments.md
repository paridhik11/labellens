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

## Phase 1: style library (what the detectors are tested on)

16 styles in `src/gen/symbol_styles.py`: 8 train (t1 to t8), 4 dev (d1 to d4, used for tuning; d3 and d4 use a factory and
hourglass geometry, F5 and H5, that no other split uses), 6 held-out (h1 to h6: gable, tower, triangle and framed families
and a white-on-black "badge" render mode that no train or dev style has). Written without reading the old artwork code.
Truth boxes of styled symbols are the glyph's tight ink box (the square slot overstated narrow hourglasses).

| Set | Detector | Recall, symbols found | False positives (absent symbols reported) |
| --- | --- | --- | --- |
| dev styles d1 to d4, all four conditions (256 symbols) | v1 `detect_symbols_blind` | 4/256 (1.6%; 0.6 to 3.9) | 0/480 (0.0%; 0.0 to 0.8) |

Per dev style v1 finds 4/64, 0/64, 0/64, 0/64. It finds essentially nothing it was not built from.
Real artwork for the real held-out check: 14 Wikimedia Commons files (4 ISO pictograms, 10 generic icons of the same concept),
sources and licenses in `scripts/symbols/real_symbol_sources.json`; 12 DailyMed label images in
`scripts/symbols/real_label_sources.json`. Images are not committed.

## Phases 2 and 3: detector ideas on the dev styles

Dev set `styled_dev`: styles d1 to d4, 32 labels per condition, 256 symbols (64 per condition) for recall and 480 absent
symbols (empty and distractor labels) for false positives. Each idea's setting is the best on dev with false positives
<= 2%; held-out styles are not used. Candidates are found by the same ink-blob proposer for every idea
(`src/cv/symbols_v2/candidates.py`), so recall cannot exceed what the proposer finds.

| # | Idea | Recall, all conditions | Recall, very hard | False positives |
| --- | --- | --- | --- | --- |
| 0 | v1 blind template matching (baseline) | 4/256 (1.6%; 0.6 to 3.9) | 2/64 (3.1%) | 0/480 (0.0%; 0.0 to 0.8) |
| 1 | v2 silhouette overlap with the train-style bank (hole-filled, tight crop; t=0.8, margin 0) | 241/256 (94.1%; 90.6 to 96.4) | 51/64 (79.7%; 68.3 to 87.7) | 1/480 (0.2%; 0.0 to 1.2) |
| 2 | SIFT keypoints, RANSAC inliers >= 8 | 35/256 (13.7%; 10.0 to 18.4) | 5/64 (7.8%) | 9/480 (1.9%; 1.0 to 3.5) |
| 3 | ORB keypoints, RANSAC inliers >= 6 | 39/256 (15.2%; 11.3 to 20.1) | 11/64 (17.2%) | 137/480 (28.5%; 24.7 to 32.7) |
| 4 | CNN on candidate crops (procedural train styles plus crops mined from train labels; p >= 0.5) | 241/256 (94.1%; 90.6 to 96.4) | 51/64 (79.7%; 68.3 to 87.7) | 0/480 (0.0%; 0.0 to 0.8) |
| 5 | idea 1 OR idea 2 | 235/256 (91.8%; 87.8 to 94.6) | 46/64 (71.9%) | 10/480 (2.1%; 1.1 to 3.8) |
| 6 | idea 1 OR idea 4 | 241/256 (94.1%) | 51/64 (79.7%) | 1/480 (0.2%) |
| 7 | idea 1 AND idea 4 | 241/256 (94.1%) | 51/64 (79.7%) | 0/480 (0.0%; 0.0 to 0.8) |

Recall by condition for idea 1: clean 64/64, moderate 63/64, hard 63/64, very hard 51/64.
Why the ceiling: the 15 missed symbols are in very hard images (glare and opaque bars hide the symbol) and a few hard ones.
A first run counted square slot boxes as truth and showed 86.7% with a gap on narrow hourglasses; scoring against the
glyph's tight box removed that (a measurement fix, not a detector change).

Stopping rule: ideas 2 and 3 (and the combinations 5 to 7) gained under 2 points over idea 1, so the search for new scorers
stops here. Idea 1 and idea 4 are tied on dev; the held-out styles decide between them.
