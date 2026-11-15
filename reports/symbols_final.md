# Symbols (branch `cv-symbols`): combined report

Phases 0 to 7 are done, one commit each, all on `cv-symbols`; nothing is merged. Everything is synthetic except the
two real checks, which are small. Numbers and per-phase detail: `results/symbols_experiments.md` and `reports/symbols_phase*.md`.

## Did it reach the targets?

**No.** Targets were recall >= 0.90 on held-out styles and false positives <= 2%. On held-out styles (384 symbols, 640 absent):

| Detector | Recall (Wilson 95%) | False positives |
| --- | --- | --- |
| v1 (before) | 16/384 (4.2%; 2.6 to 6.7) | 0/640 |
| v2 silhouette bank | 190/384 (49.5%; 44.5 to 54.5) | 16/640 (2.5%) |
| v2 CNN | 244/384 (63.5%; 58.6 to 68.2) | 55/640 (8.6%) |
| v2 zero-shot CLIP | **308/384 (80.2%; 75.9 to 83.9)** | 27/640 (4.2%) |

On the dev styles (tuned on) the silhouette and CNN reach 94.1% (241/256) with 0 to 1 false positives in 480; the 45-point
drop on held-out styles is the real measure of generalisation. The dev set was not hard enough: its "novel" geometry (a tank and a
two-ball hourglass) was easier than the held-out tower, gable, triangle, framed-glass and white-on-black badge styles.

## What worked and what did not

* **Independent artwork, the original goal:** v1 found 0/204 independent drawings. v2 silhouette and CNN find 204/204, with
  0/306 false positives and the same 100% as v1 on clean, moderate and hard original labels (seeds 100 to 102, never tuned on).
* **Held-out styles:** only CLIP handles the white-on-black badge (59/64, others 0/64). Silhouette and CNN fail on new shape
  families (tower factory plus framed glass: 30 to 50%). Keypoints (SIFT, ORB) are useless on flat pictograms (7% and 1%).
* **Real artwork on labels (336):** v1 0; silhouette 20.2%; CNN 46.4%; CLIP 61.3% (generic factory icons 83%, ISO manufacturer 44%,
  **ISO use-by hourglass 12.5% at best**).
* **Real label photos: 0 of 3 symbols found by every detector**, and 3 symbols is not a measurement. They are 1.0% to 2.3% of the
  image's short side (the proposer's minimum is 4.5%) and one is rotated 90 degrees. I labelled those boxes myself (not a human);
  please check them.
* **Text anchors (phase 5):** at most +1 symbol when the symbol sits beside its text, up to 16% false positives, and a collapse
  to 1.6% recall when the layout differs. Not used.
* **Phase 7 (lot and expiry format check):** a clear win. New seeds 103 to 105, run once: very hard false `barcode_mismatch`
  alarms 7/44 to 1/44 (blind) and 8/45 to 1/45 (template); real wrong barcodes still flagged 102/102; 0/612 alarms elsewhere.
  About 14 to 18% of very hard labels still reach a reviewer as `needs_human_review` instead of a critical mismatch.

## Evidence on flipping `symbol_detector` to "v2" (your decision)

`extract_label(..., symbol_detector="v2")` is available; the default stays `"v1"`. Evidence from the symbol harness on seeds 100 to 102
(same straightening as the extractor, not run through OCR):

| | v1 | v2 silhouette | v2 CNN |
| --- | --- | --- | --- |
| clean, moderate, hard original labels | 100% | 100% | 100% |
| very hard original labels | 91.2% (93/102) | 76.5% (78/102) | 80.4% (82/102) |
| independent drawing (alt_style) | 0/204 | 204/204 | 204/204 |
| absent symbols reported | 0/306 | 0/306 | 0/306 |
| held-out styles | 4.2% | 49.5% | 63.5% |

For: v2 loses nothing on clean to hard labels and fixes the generalisation failure. Against: it costs 11 to 15 points on very hard
photos of our own artwork, the CNN weights are not in git (they rebuild with one command), and neither detector works on real carton
photos yet. A middle option I did not test: accept a symbol when either detector finds it (v1 or v2), which should keep v1's very-hard
recall. I would flip only after that option is measured and a human has checked real-label boxes.

## Method notes

* Held-out styles and real data were scored once per frozen variant; the freeze commits (7767100, 2e3f3cb) precede the runs and
  `results/heldout_log.jsonl` lists every use. The CLIP step ran only because the CNN missed 0.90, as agreed.
* All styles are one author's drawings; "held out" means unseen, not independent. The real artwork is the independent evidence.
* A first dev run scored against square slots and understated narrow hourglasses; truth is now the glyph's tight box (fix to the
  measurement, noted in the experiments file).
* The stopping rule fired after phase 2 (SIFT, ORB and fusion gained under 2 points); phases 3 to 5 were run because you asked
  for them, not because they were expected to help.
* `eval_v2` for seeds 103 to 105 crashed twice with a Windows process-pool error under load; re-run one at a time.

## Not done

* Rotated and small-symbol proposals (the real-carton failure), the ISO hourglass, and a human check of the real-label boxes.
* Parth's `data/real/` DailyMed set was not in this checkout, so real labels are my own small sample (6 labels, 2 with symbols).
* Nothing merged to main; CLAUDE.md "Current state" and `docs/CV_STATUS.md` have a short note.

## Reproduce

`scripts/symbols/gen_baseline.sh`, `generate_styled` / `generate_real_artwork` (seeds in `results/symbols_frozen_config.json`),
`python -m src.cv.symbols_v2.cnn train --mined data/synthetic/styled_train`, `scripts/symbols/run_final.sh`, `run_final_clip.sh`, `ext_eval.py`,
`phase7_report.py`. Environment: CV venv plus `torch==2.15.0` (CPU) and, for CLIP, `transformers`.
