# CV fix status (branch cv-fixes)

Work stopped here because the usage limit was reached. Nothing below is merged to main.

## Finished

Phase 0 (setup and reproduction):
- Python 3.12 venv `.venv-cv`, exact pins from `requirements-cv.txt` install on Windows.
- `results/cv_extract.md` seed-42 numbers reproduce exactly (51 images). Only the provenance block differs
  (platform, CRLF source hashes, dataset hash). Model hashes match.
- `pytest -q src/gen src/cv`: 232 passed, 1 failed (`test_render_reuse_and_confirmed_change` needs Poppler
  `pdftoppm`, not installed here).
- `pylibdmtx` does not load on Windows with Python 3.12 (missing `libdmtx-64.dll`); dropped.

## Phase 1: measured, report not yet generated

Code is written (`src/cv/baseline_ref.py`, `src/cv/diagnose.py`) but `results/cv_diagnosis.md` has NOT been
generated and `diagnose.py` has not been run end to end. Next command:

    python -m src.cv.diagnose --datasets data/synthetic/dev42 data/synthetic/dev43

Dev datasets (not committed) are made with:

    python -m src.gen.generate_dataset --output-dir data/synthetic/dev42 --seed 42 --conditions clean moderate hard hard_original very_hard
    python -m src.gen.generate_dataset --output-dir data/synthetic/dev43 --seed 43 --conditions clean moderate hard hard_original very_hard

Findings so far (dev seeds 42 and 43, 17 labels per condition, from scratch runs that the script repeats):

- (a) Barcode 2x2, exact GS1 matches. Commit `3c98598` reduced hard blur (1.0 to 1.8 became 1.0 to 1.6) and
  noise (8 became 6) and added slot recovery. Old decoder is `ecc9869`, new is `05869b6`.

  | Seed | Decoder | Original hard | Reduced hard |
  | ---: | --- | --- | --- |
  | 42 | old | 4/17 | 5/17 |
  | 42 | new | 12/17 | 15/17 |
  | 43 | old | 3/17 | 9/17 |
  | 43 | new | 13/17 | 16/17 |

- (b) OCR root cause: the PP-OCRv4 recogniser, given text lines cropped tightly at the ink, drops spaces and
  swaps 0 and O on pixel-perfect rendered text. Not a special character, not a different preprocessing path,
  not detector box size (median box heights are about equal across conditions), not an evaluation bug.
  Evidence on 6 seed-42 labels: clean 28 edits as is, 1 edit after adding sigma 4 noise; padding the crop by
  10 px before recognition gives the correct text. Hard reaches 0% because the text is large (30 to 45 px
  glyphs) against a blur of at most 1.6 px, and its noise tips the recogniser the right way. The full
  17-label table is produced by `diagnose.py`.
- New finding: the test barcode is an 8 by 96 module rectangular DataMatrix at 3 px per module, not a square
  symbol. That is why modest blur breaks decoding.
- Blind barcode decoding (no template slot) looks very promising: Wiener deblurring of the whole rectified
  label or whole photo, then 2x upscaling, then zxing-cpp. Scratch result on 34 labels per condition (both
  dev seeds): clean 34, moderate 34, hard 34, original hard 32, very hard 33 (whole photo). Not yet in
  `src/cv`, no tests yet.
- Label boundary detection fails on very hard (found on 9 of 34 labels) because occluders cross the edge.

## Generator changes already made

- `src/gen/augment.py`: new conditions `hard_original` (old blur and noise) and `very_hard` (hard plus glare
  and occlusion). Clean, moderate and hard are byte-identical to before (checked on seed 42, 103 files).
- `src/gen/generate_dataset.py`: `--conditions` option. Extra conditions reuse the hard seed.
- No tests yet for these two changes.

## Next

1. Run `diagnose.py`, review and commit `results/cv_diagnosis.md` (sections c and d are in the script).
2. Phase 2 fixes 1 to 7, one commit each with tests: padded OCR crops, blind barcode mode
   (Wiener plus upscale), symbol negatives and style variation, tests that skip without CV libraries,
   integration script, `data/real_photos/README.md`.
3. `results/cv_experiments.md` table.
4. Phase 3: seeds 100, 101, 102 generated once. They have NOT been generated or looked at.
5. Phase 4 documents and the list of outdated claims in `docs/PARTH_WORK_SUMMARY.md`.
