# CV status after the cv-fixes work

Branch `cv-fixes`, not merged to main. Numbers live in `results/cv_final_eval.md` (fresh seeds 100 to 102),
`results/cv_experiments.md` (dev seeds 42 and 43) and `results/cv_diagnosis.md` (what was wrong at the start).
Everything here is measured on synthetic labels from one template family. No real photo has been evaluated.

## Solid (measured, re-runnable, and not tied to the known template)

- Label boundary and rectification. The strict contour finder works on clean to hard. A fallback rebuilds the
  outline when an occluder crosses the edge, using the outer edge pixels and a robust line fit per side.
- OCR reading. The root cause of the old clean-image errors (tight line crops) is fixed: each line is
  re-cropped with a 30 percent margin on weakly dithered pixels after CLAHE contrast equalisation. The same
  steps run for every image, whatever its condition.
- Blind barcode decoding. Candidate regions are located in the pixels, levelled, deblurred with a Wiener
  filter at several strengths, upscaled and thresholded several ways. Only complete GS1 decodes are
  accepted from enhanced views, so noise cannot produce a barcode (tested).
- Blind symbol search over the whole label at 14 sizes. Finds the pictograms at 0.6 and 1.25 of the normal
  size, where the old slot-window search found none at 0.6.
- Negative cases. Missing and wrong symbols are reported as missing, with no false positive on the dev sets or
  on the fresh sets (0 of 306 absent symbols reported); a printed lot or expiry that disagrees with the barcode is flagged.
- Output contract. `extract_label` returns a valid `LabelExtraction`, and `src.cv.integration` passes it to
  `ProductRecord` and `Flag` without changing `schemas.py`. The UDI-DI is only ever copied from a decoded
  barcode, never generated.
- Tests. `tests/test_cv_vision.py` skips cleanly without OpenCV, Pillow and zxing-cpp, and the OCR model
  tests are marked slow, so the root CI command passes in the main environment (109 passed, 1 skipped).

## Synthetic-only (works here, unproven anywhere else)

- Every number. One 100 by 60 mm layout, one font (Pillow's default), black on white, printed at 300 DPI,
  with synthetic blur, noise, glare and occlusion. Real ink spread, paper texture, curved packaging, phone
  JPEG compression and motion blur are not modelled.
- Blind field naming. The rules (printed keys REF, LOT and EXP, a street-address pattern, the line above
  the address is the manufacturer, the line with the widest characters is the product name) were written
  for and only tested on this one layout. Under glare and occlusion they are clearly worse than the
  template mapping.
- Symbols. Detection is template matching against the reference drawings, which come from the same code
  that draws the symbols on the labels. A second, independently drawn version of the same two pictograms
  was found 0 times. Real ISO 7000 artwork would almost certainly also be missed.
- Barcode. The test symbol is a rectangular 8 by 96 module DataMatrix at 3 pixels per module, and the AI
  01 value is the all-zero test placeholder. Other symbologies and sizes were not tested.
- The very hard condition is my own design (1 or 2 opaque bars from the edges, 1 or 2 glare blobs). It is a
  stress test, not a model of any real capture.

## Needs Parth's review

- `src/gen/augment.py`: the new `hard_original` (the setting before commit `3c98598`) and `very_hard`
  conditions. Clean, moderate and hard are byte-identical to before (checked on seed 42, 103 files).
- `src/gen/smoke_label.py`: new optional arguments for negative cases (`symbol_overrides`,
  `allow_print_barcode_mismatch`). Without them the output is unchanged.
- `src/cv/extract.py`: now has a template mode (the old behaviour, plus the new OCR, the enhanced slot
  decode and the fallback corners) and a blind mode. The old `eval_extract.py` still runs, in template
  mode, so `results/cv_extract.md` would change if regenerated. It was left as the historical baseline.
- The claims in `docs/PARTH_WORK_SUMMARY.md` listed below.
- `src/gen/test_render.py::test_render_reuse_and_confirmed_change` fails on Windows without the Poppler
  `pdftoppm` program. That is unrelated to this work.
- Whether the real-photo check (`data/real_photos/README.md`, `python -m src.cv.eval_real`) should use
  printed synthetic labels or real product labels.

## Claims in `docs/PARTH_WORK_SUMMARY.md` that are no longer true or need a caveat

1. "Hard 15/17 (88.24%)" exact GS1 and the "above 80 percent" goal: reproduces, but only on the reduced hard
   setting introduced in the same commit. On the original setting the same decoder got 12/17 (seed 42),
   25/34 on both dev seeds and 37/51 (72.5%) on fresh seeds 100 to 102.
2. "The original whole-image-only baseline decoded 4/17 hard barcodes on seed 42": true, but it was measured
   on the original hard setting while the 15/17 is on the reduced one, so 4 to 15 mixes two changes. On the
   same reduced images the old decoder gets 5/17.
3. "An independent seed-43 dataset also decoded ... 16/17 hard": true on the reduced setting; 13/17 on the
   original setting.
4. The barcode improvement is described as decoding; 10 of the 15 seed-42 hard matches came from the
   template-slot crop, which does not exist for an unknown layout. The new blind decoder gets 51/51 on the
   fresh hard sets without it.
5. OCR CER table (clean 15.15% product name, hard 0.00%): reproduces, but the clean errors were an artefact
   of tight line crops in the recogniser (dropped spaces, 0 read as O), and hard being 0% was the same
   sensitivity, not robust OCR. After the fix every field is 0.00% on clean, moderate and hard (fresh
   seeds, template mode).
6. "Symbol matches 34/34" and "Mean symbol IoU 0.988": true, but the search only looks in a window around
   the known slot at 0.8 to 1.2 times the slot size, and the references are drawn by the same code as the
   labels. That detector finds 0/204 symbols at 0.6 size and 0/204 of an independently drawn version.
7. "all evaluation images contain both symbols" and "cannot measure false-positive behavior": no longer the
   case. Negative sets now exist; 0 of 306 absent symbols were reported on the fresh seeds.
8. "It does not include glare or occlusion": a `very_hard` condition with both now exists (fresh-seed
   numbers in `results/cv_fixes.md`).
9. "Repeating seed-42 generation produced 103 byte-identical files": confirmed on one machine, but the
   dataset hash on Windows differs from the published macOS hash, so generation is not byte-identical across
   platforms (the metrics were identical).
10. "233 passed": on Windows without the Poppler `pdftoppm` program one render test fails (232 passed).
11. "locate and read fields": field names come from template slot positions in the original extractor. Blind
    naming without the template now exists but is clearly worse under glare and occlusion.
12. Key files: blind barcode decoding is now in `src/cv/barcode_blind.py`, field rules in `src/cv/fields.py`;
    `src/cv/barcode.py` is no longer the whole barcode story.

## Symbols after the cv-symbols branch (not merged)

See `reports/symbols_final.md`. The old detector found 0/204 independently drawn pictograms. Detector v2 (`src/cv/symbols_v2`,
`extract_label(symbol_detector="v2")`, default still `"v1"`) finds 204/204 of them and keeps 100% on clean to hard original labels, but
loses 11 to 15 points on very hard original labels (76.5% and 80.4% against 91.2%). On held-out styles written by us it reaches 49.5%
(silhouette), 63.5% (CNN) and 80.2% (zero-shot CLIP, 4.2% false positives); the 90% and 2% targets were not met. On real carton
photos every detector found 0 of 3 symbols (they are 1 to 2% of the image and one is rotated); real-label boxes were labelled by
the assistant, not a human. The lot and expiry format check (`src/cv/consistency.py`) cut false critical mismatches on very hard labels from
7/44 to 1/44 (blind) and 8/45 to 1/45 (template) on new seeds 103 to 105, with real wrong barcodes still flagged 102/102.
