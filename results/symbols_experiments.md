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

CNN detail (idea 4): 3 classes (manufacturer, expiry, other), input two 48 by 48 channels from the candidate's ink map
(ink and hole-filled silhouette), 3 conv blocks and a dense head (about 60 thousand weights), trained on 12,019 crops: 4,000 per
class of procedurally drawn pictograms from the seen geometry families (jittered, outline, filled or duo, never badge)
pushed through the candidate finder, plus crops mined from the train-split label set. CPU only, at most 4 torch threads, seed 0.
A procedural-only first model (no mined crops) also scored 241/256 on dev.

## Phase 5: text-anchor rule (OCR lines as a presence signal)

Anchor lines come from OCR only: the line with the EXP key, and the line above a street-address line (or one starting
"manufacturer"). A candidate is "near" its anchor when within 3 line heights. Two uses: **boost** (accept a weaker candidate,
silhouette >= 0.6 or CNN p >= 0.2, when it is near its anchor) and **gate** (accept only candidates near their anchor).
Relaxed thresholds were fixed before the run, not tuned. OCR found the EXP line in 222/224 and the manufacturer line in
218/224 anchored images, and 362/368 and 357/368 in random-layout images.

| Dev set | Variant | Recall, all conditions | Recall, very hard | False positives |
| --- | --- | --- | --- | --- |
| anchored layout (symbol beside its text; 128 symbols, 320 absent) | silhouette | 122/128 (95.3%; 90.2 to 97.8) | 26/32 (81.2%) | 0/320 (0.0%) |
| | silhouette + boost | 123/128 (96.1%) | 27/32 (84.4%) | 52/320 (16.2%; 12.6 to 20.7) |
| | silhouette + gate | 121/128 (94.5%) | 25/32 (78.1%) | 0/320 (0.0%) |
| | CNN | 123/128 (96.1%; 91.2 to 98.3) | 27/32 (84.4%) | 0/320 (0.0%) |
| | CNN + boost | 123/128 (96.1%) | 27/32 (84.4%) | 0/320 (0.0%) |
| | CNN + gate | 122/128 (95.3%) | 26/32 (81.2%) | 0/320 (0.0%) |
| random layout (256 symbols, 480 absent) | silhouette + boost | 241/256 (94.1%) | 51/64 | 120/480 (25.0%) |
| | silhouette + gate | **4/256 (1.6%)** | 4/64 | 0/480 |
| | CNN + gate | **4/256 (1.6%)** | 4/64 | 0/480 |

Reading: when the symbol sits beside its text (the ISO practice), the anchor rule gains at most one symbol (123 against 122
or 123) and the boost lets text-like blobs through (16% false positives with the silhouette scorer). Used as a gate it does
not help and collapses when the layout is not as assumed. Every label here carries the EXP and manufacturer lines
whether or not a symbol is printed, so the text does not say whether a symbol is present; only position can. Verdict: report
the signal, do not use it in the detector.

## Final run: frozen detectors on held-out styles, real artwork and real labels (scored once)

Settings were frozen in `results/symbols_frozen_config.json` (commit 7767100) and `results/symbols_frozen_clip.json`
(commit 2e3f3cb) before any held-out data was scored. Each dataset was scored in one invocation per detector family;
`results/heldout_log.jsonl` lists every use (plus one diagnostic on the real labels, proposer recall only).
Targets: recall >= 0.90 and false positives <= 2%. **No detector meets both on held-out styles.**

### Held-out styles h1 to h6, random placement (384 symbols, 640 absent symbols, four conditions)

| Detector | Recall | False positives |
| --- | --- | --- |
| v1 blind template matching | 16/384 (4.2%; 2.6 to 6.7) | 0/640 (0.0%; 0.0 to 0.6) |
| v2 silhouette bank | 190/384 (49.5%; 44.5 to 54.5) | 16/640 (2.5%; 1.5 to 4.0) |
| v2 CNN | 244/384 (63.5%; 58.6 to 68.2) | 55/640 (8.6%; 6.7 to 11.0) |
| v2 silhouette AND CNN | 157/384 (40.9%; 36.1 to 45.9) | 1/640 (0.2%; 0.0 to 0.9) |
| v2 SIFT | 27/384 (7.0%; 4.9 to 10.0) | 20/640 (3.1%; 2.0 to 4.8) |
| v2 ORB | 3/384 (0.8%; 0.3 to 2.3) | 211/640 (33.0%; 29.4 to 36.7) |
| **v2 zero-shot CLIP (threshold 0.4 from dev)** | **308/384 (80.2%; 75.9 to 83.9)** | 27/640 (4.2%; 2.9 to 6.1) |

Recall per held-out style (64 symbols each):

| Style | What is new | silhouette | CNN | CLIP |
| --- | --- | --- | --- | --- |
| h1 | gable factory, triangle hourglass, filled | 31 (48.4%) | 61 (95.3%) | 32 (50.0%) |
| h2 | same shapes, thin outline | 61 (95.3%) | 61 (95.3%) | 63 (98.4%) |
| h3 | tower factory, framed hourglass, rounded outline | 19 (29.7%) | 29 (45.3%) | 34 (53.1%) |
| h4 | same shapes, filled | 18 (28.1%) | 32 (50.0%) | 63 (98.4%) |
| h5 | white-on-black badge | 0 (0.0%) | 0 (0.0%) | 59 (92.2%) |
| h6 | very heavy rounded strokes | 61 (95.3%) | 61 (95.3%) | 57 (89.1%) |

By condition (96 symbols per condition): silhouette 50, 49, 49, 42; CNN 64, 64, 64, 52; CLIP 80, 80, 77, 71 (clean,
moderate, hard, very hard). False positives per condition (160 absent each): silhouette 5, 5, 3, 3; CNN 14, 15, 16, 10;
CLIP 8, 7, 7, 5.

### Held-out styles, symbols beside their text (192 symbols, 320 absent)

v1 5/192 (2.6%), FP 0/320; silhouette 87/192 (45.3%; 38.4 to 52.4), FP 11/320 (3.4%); CNN 124/192 (64.6%; 57.6 to 71.0), FP 23/320
(7.2%); silhouette AND CNN 83/192, FP 0/320; SIFT 10/192, FP 10/320; ORB 6/192, FP 101/320; **CLIP 148/192 (77.1%; 70.6 to 82.5), FP 16/320 (5.0%; 3.1 to 8.0)**.

### Real artwork (14 Wikimedia Commons drawings) printed on synthetic labels (336 symbols)

| Detector | all | ISO manufacturer (48) | ISO hourglass (48) | generic factory (120) | generic hourglass (120) |
| --- | --- | --- | --- | --- | --- |
| v1 | 0/336 (0.0%) | 0 | 0 | 0 | 0 |
| silhouette | 68 (20.2%; 16.3 to 24.9) | 3 (6.2%) | 3 (6.2%) | 8 (6.7%) | 54 (45.0%) |
| CNN | 156 (46.4%; 41.2 to 51.8) | 23 (47.9%) | 0 (0.0%) | 61 (50.8%) | 72 (60.0%) |
| CLIP | 206 (61.3%; 56.0 to 66.4) | 21 (43.8%) | 6 (12.5%) | 100 (83.3%) | 79 (65.8%) |

The ISO use-by hourglass (thin walls, solid sand, no caps) is the hard case for every detector.

### Real label photos (DailyMed; 3 symbols and 4 symbol-free boxes; boxes labelled by the assistant, not a human)

All detectors found 0/3 symbols. The proposer never produced a box near them: the symbols are 8 to 36 px, 1.0% to 2.3% of the
image short side, below the proposer minimum of 4.5%, and the pregnancy-test manufacturer pictogram is turned 90 degrees.
False positives on the 4 symbol-free boxes (8 absent slots): v1 0, silhouette 0, CNN 2 (25%), CLIP 0, ORB 7. This is a
sample of 3, not a measurement of recall.

### External check: original artwork, seeds 100 to 102 (not used for any tuning)

| Set | v1 | v2 silhouette | v2 CNN |
| --- | --- | --- | --- |
| clean, moderate, hard (102 symbols each) | 102/102 each | 102/102 each | 102/102 each |
| very hard (102) | 93 (91.2%; 84.1 to 95.3) | 78 (76.5%; 67.4 to 83.6) | 82 (80.4%; 71.6 to 86.9) |
| alt_style, independent filled artwork (204) | 0 (0.0%; 0.0 to 1.8) | **204 (100.0%; 98.2 to 100.0)** | **204 (100.0%)** |
| absent symbols reported (306) | 0 | 0 (0.0%; 0.0 to 1.2) | 0 (0.0%; 0.0 to 1.2) |
| small (0.6) and large (1.25) symbols (204 each) | 204 each | 204 each | 204 each |

v2 keeps everything v1 gets on clean to hard labels and fixes the independent drawing (0/204 to 204/204), but loses 11 to 15
points on very hard labels (glare and opaque bars hide part of the symbol and the blob finder then misses it).

## Phase 7: lot and expiry format check (src/cv/consistency.py)

Paired comparison on the same OCR: the confidence-only checker against the checker with the format rule. Wilson 95% intervals.

### Dev seeds 42 and 43 (rule not tuned on them)

### Labels whose print agrees with the barcode: false `barcode_mismatch` alarms (lower is better)

| condition | mode | decoded labels | confidence only: false mismatch | with format check: false mismatch | with format check: needs_human_review |
| --- | --- | ---: | --- | --- | --- |
| clean | blind | 34 | 0/34 (0.0%; 0.0 to 10.2) | 0/34 (0.0%; 0.0 to 10.2) | 0/34 (0.0%; 0.0 to 10.2) |
| clean | template | 34 | 0/34 (0.0%; 0.0 to 10.2) | 0/34 (0.0%; 0.0 to 10.2) | 0/34 (0.0%; 0.0 to 10.2) |
| moderate | blind | 34 | 0/34 (0.0%; 0.0 to 10.2) | 0/34 (0.0%; 0.0 to 10.2) | 0/34 (0.0%; 0.0 to 10.2) |
| moderate | template | 34 | 0/34 (0.0%; 0.0 to 10.2) | 0/34 (0.0%; 0.0 to 10.2) | 0/34 (0.0%; 0.0 to 10.2) |
| hard | blind | 34 | 0/34 (0.0%; 0.0 to 10.2) | 0/34 (0.0%; 0.0 to 10.2) | 0/34 (0.0%; 0.0 to 10.2) |
| hard | template | 34 | 0/34 (0.0%; 0.0 to 10.2) | 0/34 (0.0%; 0.0 to 10.2) | 0/34 (0.0%; 0.0 to 10.2) |
| hard_original | blind | 33 | 0/33 (0.0%; 0.0 to 10.4) | 0/33 (0.0%; 0.0 to 10.4) | 0/33 (0.0%; 0.0 to 10.4) |
| hard_original | template | 33 | 0/33 (0.0%; 0.0 to 10.4) | 0/33 (0.0%; 0.0 to 10.4) | 0/33 (0.0%; 0.0 to 10.4) |
| very_hard | blind | 33 | 5/33 (15.2%; 6.7 to 30.9) | 1/33 (3.0%; 0.5 to 15.3) | 4/33 (12.1%; 4.8 to 27.3) |
| very_hard | template | 33 | 9/33 (27.3%; 15.1 to 44.2) | 1/33 (3.0%; 0.5 to 15.3) | 8/33 (24.2%; 12.8 to 41.0) |

### Negative sets (moderate and hard): wrong_barcode must stay flagged, other cases must stay quiet

| group | mode | decoded labels | confidence only: `barcode_mismatch` | with format check: `barcode_mismatch` | with format check: mismatch or review |
| --- | --- | ---: | --- | --- | --- |
| other cases | blind | 408 | 0/408 (0.0%; 0.0 to 0.9) | 0/408 (0.0%; 0.0 to 0.9) | 0/408 (0.0%; 0.0 to 0.9) |
| other cases | template | 408 | 0/408 (0.0%; 0.0 to 0.9) | 0/408 (0.0%; 0.0 to 0.9) | 0/408 (0.0%; 0.0 to 0.9) |
| wrong_barcode | blind | 68 | 68/68 (100.0%; 94.7 to 100.0) | 68/68 (100.0%; 94.7 to 100.0) | 68/68 (100.0%; 94.7 to 100.0) |
| wrong_barcode | template | 68 | 68/68 (100.0%; 94.7 to 100.0) | 68/68 (100.0%; 94.7 to 100.0) | 68/68 (100.0%; 94.7 to 100.0) |

### New seeds 103 to 105 (run once, after the code was frozen)

### Labels whose print agrees with the barcode: false `barcode_mismatch` alarms (lower is better)

| condition | mode | decoded labels | confidence only: false mismatch | with format check: false mismatch | with format check: needs_human_review |
| --- | --- | ---: | --- | --- | --- |
| clean | blind | 51 | 0/51 (0.0%; 0.0 to 7.0) | 0/51 (0.0%; 0.0 to 7.0) | 0/51 (0.0%; 0.0 to 7.0) |
| clean | template | 51 | 0/51 (0.0%; 0.0 to 7.0) | 0/51 (0.0%; 0.0 to 7.0) | 0/51 (0.0%; 0.0 to 7.0) |
| moderate | blind | 51 | 0/51 (0.0%; 0.0 to 7.0) | 0/51 (0.0%; 0.0 to 7.0) | 0/51 (0.0%; 0.0 to 7.0) |
| moderate | template | 51 | 0/51 (0.0%; 0.0 to 7.0) | 0/51 (0.0%; 0.0 to 7.0) | 0/51 (0.0%; 0.0 to 7.0) |
| hard | blind | 51 | 0/51 (0.0%; 0.0 to 7.0) | 0/51 (0.0%; 0.0 to 7.0) | 0/51 (0.0%; 0.0 to 7.0) |
| hard | template | 51 | 0/51 (0.0%; 0.0 to 7.0) | 0/51 (0.0%; 0.0 to 7.0) | 0/51 (0.0%; 0.0 to 7.0) |
| hard_original | blind | 50 | 0/50 (0.0%; 0.0 to 7.1) | 0/50 (0.0%; 0.0 to 7.1) | 0/50 (0.0%; 0.0 to 7.1) |
| hard_original | template | 49 | 0/49 (0.0%; 0.0 to 7.3) | 0/49 (0.0%; 0.0 to 7.3) | 0/49 (0.0%; 0.0 to 7.3) |
| very_hard | blind | 44 | 7/44 (15.9%; 7.9 to 29.4) | 1/44 (2.3%; 0.4 to 11.8) | 6/44 (13.6%; 6.4 to 26.7) |
| very_hard | template | 45 | 8/45 (17.8%; 9.3 to 31.3) | 1/45 (2.2%; 0.4 to 11.6) | 8/45 (17.8%; 9.3 to 31.3) |

### Negative sets (moderate and hard): wrong_barcode must stay flagged, other cases must stay quiet

| group | mode | decoded labels | confidence only: `barcode_mismatch` | with format check: `barcode_mismatch` | with format check: mismatch or review |
| --- | --- | ---: | --- | --- | --- |
| other cases | blind | 612 | 0/612 (0.0%; 0.0 to 0.6) | 0/612 (0.0%; 0.0 to 0.6) | 0/612 (0.0%; 0.0 to 0.6) |
| other cases | template | 612 | 0/612 (0.0%; 0.0 to 0.6) | 0/612 (0.0%; 0.0 to 0.6) | 0/612 (0.0%; 0.0 to 0.6) |
| wrong_barcode | blind | 102 | 102/102 (100.0%; 96.4 to 100.0) | 102/102 (100.0%; 96.4 to 100.0) | 102/102 (100.0%; 96.4 to 100.0) |
| wrong_barcode | template | 102 | 102/102 (100.0%; 96.4 to 100.0) | 102/102 (100.0%; 96.4 to 100.0) | 102/102 (100.0%; 96.4 to 100.0) |
