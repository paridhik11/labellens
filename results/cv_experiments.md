# CV experiments on the dev seeds

Every experiment below was run on dev seeds 42 and 43 only (17 labels per condition and seed). The fresh
seeds 100 to 102 were not generated until all code was frozen (commit `c594b6d`). Rule used: keep an idea
only if it helps on both dev seeds and does not depend on the template; stop when two ideas in a row give
less than 1 point on both seeds. "1 point" here means 1 percentage point of character error rate (about 16
edits per condition and seed) or 1 label of exact GS1 matches.

The scripts are in `scripts/cv_experiments/` and run from the repo root with `PYTHONPATH=.` and the dev
datasets from `docs/CV_FIX_STATUS.md`. They import the current code, so re-running one now measures the
code at `c594b6d`, not the state it was written against. That only matters for rows marked "superseded".

## OCR (all six fields, character edits over 17 labels, template field mapping)

The baseline row is the extractor at `05869b6`. In the experiment rows, "very hard" uses only the labels
where the strict corner finder found the label (4 on seed 42, 5 on seed 43), because the fallback corner
finder did not exist yet. Script: `ocr_exp.py`.

| Experiment | Seed 42: clean, moderate, hard, hard_original, very_hard | Seed 43: same | Kept? |
| --- | --- | --- | --- |
| Baseline `05869b6` (tight crops), all 17 labels | 82, 27, 1, n/a, n/a (from `results/cv_diagnosis.md`) | see `cv_diagnosis.md` | starting point |
| Pad crops 50% of line height | 5, 0, 0, 1, 16 | 1, 0, 2, 0, 48 | superseded by the next rows |
| Pad crops 30% | 15, 0, 0, 0, 13 | 14, 1, 0, 1, 45 | no |
| Weak dither (noise sigma 4) + pad 15% | 0, 0, 1, 0, 15 | 0, 1, 6, 3, 48 | no |
| Weak dither + pad 30% | 0, 0, 0, 0, 15 | 0, 0, 0, 1, 48 | **yes** (default reader) |
| Vote of pad 50%, pad 30%, dither + pad 15% | 0, 0, 0, 0, 13 | 0, 0, 0, 1, 47 | no: under 1 point better than one pass, three times the cost |
| Vote of pad 50%, dither + pad 15%, dither + pad 30% | 0, 0, 0, 0, 15 | 0, 0, 0, 1, 48 | no gain |
| Upscale to 1800 px wide, pad 50% | 4, 0, 1, 1, 14 | 8, 0, 0, 0, 45 | no |
| Upscale to 1800 px wide, three-pass vote | 0, 0, 0, 0, 13 | 0, 0, 1, 1, 46 | no gain |

Glare handling, very hard only, all 17 labels (fallback corners in place), on top of the kept reader.
Script: `glare_exp.py`. Columns are edits on very_hard, clean and hard_original.

| Experiment | Seed 42 | Seed 43 | Kept? |
| --- | --- | --- | --- |
| Kept reader as is | 87, 0, 0 | 127, 0, 1 | reference |
| CLAHE contrast equalisation first | 76, 0, 0 | 122, 0, 0 | **yes**: better on both seeds and no harm elsewhere, though under 1 point on seed 43 |
| Field-level vote of reader and CLAHE | 74, 0, 0 | 128, 0, 0 | no: not better on both |
| Local paper flattening (morphological background division) | 83, 0, 14 | 139, 0, 7 | no: hurts hard_original |
| Vote of reader and flattening | 81, 0, 12 | 128, 0, 5 | no |

After the two vote rows and the flattening row gave less than 1 point (or harm) on both seeds, no further
OCR ideas were tried (stopping rule). A second OCR engine was not tried for this reason.

## Barcode (exact GS1 matches out of 17, hard / hard_original / very_hard)

| Experiment | Seed 42 | Seed 43 | Kept? |
| --- | --- | --- | --- |
| Starting point `05869b6`: photo, rectified label, thresholded template slot (generator self-check) | 15 / 12 / 6 | 16 / 13 / 8 | starting point |
| Whole photo with blur, median, downscale or adaptive threshold before zxing-cpp (`bc_filters_probe.py`) | no extra decode from any filter | no extra decode | no |
| Wiener deblur and 2x upscale of the whole rectified label (`bc_wiener_probe.py`) | both seeds together: 34 / 31 / 8 of 34 (very hard: label found on 9 only) | (combined) | idea kept, reshaped below |
| Blind decoder v1: candidate regions (outer contours only) then whole-photo fallback (`bc_exp.py`, superseded) | 17 / 16 / 17, but 0 candidates found: all came from the whole-photo fallback | 17 / 16 / 16 | superseded |
| Blind decoder v2: candidates also inside the label border, upright crop, Wiener at 5 strengths, 2x and 3x, none / Otsu / adaptive threshold, then whole photo | 17 / 16 / 17 | 17 / 17 / 16 | **yes** |
| Same decode attempts on the template slot crop (template-assisted mode) | same as blind in the final extractor | same | **yes**, reported separately |
| pylibdmtx as a second DataMatrix decoder | could not load on Windows (missing `libdmtx-64.dll`) | | not tried |
| OpenCV barcode module | this build only has `cv2.barcode.BarcodeDetector`; I found no DataMatrix decoder and did not test it | | not tried |

Final extractor on the dev seeds, both modes (`python -m src.cv.eval_v2 summary --records
results/cv_records/dev42.json` and `dev43.json`): seed 42 17 / 16 / 17, seed 43 17 / 17 / 16, identical for
blind and template-assisted. Clean and moderate stay 17/17.

## Label corners (very hard, labels with every corner within 10 px of truth, out of 17)

Script: `corner_exp.py` (the fallback alone; the extractor tries the strict finder first).

| Experiment | Seed 42 | Seed 43 | Kept? |
| --- | --- | --- | --- |
| Strict contour finder only (starting point) | 4 found, 4 within 10 px | 5 found, 5 within 10 px | starting point |
| Fallback v1: convex hull of the bright region, four longest edges | 10 (in the first extractor run) | not measured | superseded |
| Fallback v2: pick sides by angle (two parallel pairs) | 8 | 9 | superseded |
| Fallback v3: hull of edge pixels around the bright region (finds the outer border, not the inner one) | 13 | 10 | superseded |
| Fallback v4: v3 plus robust (Huber) refit of each side from its outermost edge pixels | 16 | 16 (16 found) | **yes** |

Final extractor: 17/17 within 10 px on both seeds (strict finder first, fallback used on 13 and 12 labels).

## Field naming without the template (blind mode, character error rate over all six fields)

| Experiment | Both dev seeds | Kept? |
| --- | --- | --- |
| Keys (REF, LOT, EXP), address pattern, line above the address, tallest other line = product name | seed 42 only: 0% on clean to hard_original, 14.02% very hard | superseded |
| Plus "product name must be 12% taller than the median line" | clean 8.55%: product name dropped on 19 of 34 labels | no |
| Plus "product name must have 15% wider characters than the median line" | clean, moderate, hard 0%; hard_original 0% / 0.87% (seed 42 / 43); very hard 9.37% / 17.40% | **yes** |

The size rule exists so that an unreadable product name gives "missing" instead of a wrong line; a unit test
covers that case. Template mapping on very hard is 4.78% / 7.61%, so blind field naming is clearly worse
under glare and occlusion.

## Symbols (dev negative and variation sets, moderate and hard, both seeds)

`python -m src.cv.eval_v2 summary --records results/cv_records/neg42.json results/cv_records/neg43.json`

| Experiment | Result | Kept? |
| --- | --- | --- |
| Template windows at 0.8 to 1.2 of slot size (starting point) | small symbols (0.6 size): 0/136 found; second artwork: 0/136; missing and wrong symbols: 0 false positives (seed 42 only) | starting point |
| Blind whole-label search, 14 sizes from 0.06 to 0.26 of the label height | small and large symbols 136/136 each; second artwork 0/136; missing and wrong symbols: 0 of 204 absent symbols reported, all 204 absences flagged | **yes** |
| Add reference images of the second artwork (`alt_ref_exp.py`) | second artwork 68/68 per seed, but a missing manufacturer symbol was reported on 23/34 and 20/34 labels | no: false positives, and it would use knowledge of the test artwork |
| Trained detector (tiny CNN or YOLO) | not tried | the only training data would be the same synthetic artwork, which is exactly what the second-artwork test shows does not transfer |

Rotation tries were not added for symbols because the label is rectified before the search.
