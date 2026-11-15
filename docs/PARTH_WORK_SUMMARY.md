# Parth's LabelLens CV and Synthetic Label Work

**For:** Paridhi  
**Branch:** [`parth-cv`](https://github.com/paridhik11/labellens/tree/parth-cv)  
**Latest commit:** [`3c98598`](https://github.com/paridhik11/labellens/commit/3c985984d7cf1df290ac770be16562351157e8e3)

## Project goal

Build a reproducible synthetic medical-device label workflow and a computer-vision baseline that can locate and read fields, decode the GS1 barcode, detect the two template pictograms, and preserve correct positions through distortion. The output must remain clearly marked test draft artwork, must use supplied identifiers rather than invented ones, and must keep results separate for clean, moderate and hard conditions.

## Work completed

### Synthetic label generation

- Aligned augmentation tests with the actual API: `augment_label` returns the image, source-to-photo transform and label corners; `transform_box` maps slot rectangles into photo coordinates.
- Extended the test-label builder with varied product, manufacturer, address, model, lot, expiry and serial values. Each base label shares its values across the clean, moderate and hard variants.
- Added a fixed-seed dataset generator. The default creates 17 base labels across three conditions, for 51 PNGs and matching ground-truth JSON files. The manifest records seeds, paths and self-check counts.
- Ground truth includes transformed label, text-slot and symbol corners, the homography, GS1 data, change log and self-check. Failed images remain in the dataset for evaluation.
- Reduced only the hard-condition blur and noise to keep barcode modules readable. Hard rotation, perspective and uneven lighting remain enabled.

### Computer vision and barcode recovery

- Added label-boundary detection and perspective correction, OCR with RapidOCR, GS1 AI parsing, template field mapping and an integrated extraction path.
- Preserved image-coordinate correctness: detected text and barcode positions are mapped back to the original photograph. Symbol positions are likewise mapped back after rectification.
- Added synthetic template matching for the manufacturer and expiry pictograms. The symbols are generated deterministically from the existing drawing code.
- Improved hard-condition barcode decoding. The pipeline tries the original image first, then the rectified label, then a locally thresholded crop of the known barcode slot. The recovery is restricted to the current test-device template.
- Added an automated check that requires at least 14 of the 17 seed-42 hard labels to have an exact GS1 match.

### Draft rendering and print comparison

- Added deterministic SVG, physical-size PDF and 300-DPI preview rendering for the test-device template.
- Draft packages carry a DRAFT watermark, change log, artifact hashes and OCR/barcode/symbol self-check. Barcode matrices are reused when encoded data is unchanged; changed barcode data requires explicit confirmation.
- Added print comparison against a reference manifest. Verification requires an authorized approval record bound to that exact manifest and checks artifact hashes. It does not create approvals or publish artwork.

## Measured results

Seed 42 uses 17 images per condition. The score for symbols is the number of expected pictograms with the right name and a bounding-box intersection-over-union (IoU) of at least 0.50. IoU is overlap area divided by the combined area of the expected and predicted boxes.

| Condition | Exact GS1 matches | Label corners within 10 px | Symbol matches | Mean symbol IoU |
| --- | ---: | ---: | ---: | ---: |
| Clean | 17/17 (100%) | 17/17 | 34/34 | 0.988 |
| Moderate | 17/17 (100%) | 17/17 | 34/34 | 0.988 |
| Hard | 15/17 (88.24%) | 17/17 | 34/34 | 0.990 |

An independent seed-43 dataset also decoded 17/17 clean, 17/17 moderate and 16/17 hard barcodes (94.12%). The original whole-image-only baseline decoded 4/17 hard barcodes on seed 42. Repeating seed-42 generation produced 103 byte-identical files.

OCR character error rate (CER) on seed 42, by field:

| Condition | Product name | Manufacturer | Address | Model | Lot | Expiry |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Clean | 15.15% | 0.00% | 0.00% | 7.14% | 5.26% | 5.10% |
| Moderate | 1.73% | 0.00% | 0.00% | 6.30% | 2.48% | 0.00% |
| Hard | 0.00% | 0.00% | 0.00% | 0.42% | 0.00% | 0.00% |

All six fields were present in all 17 images per condition. CER counts character insertions, deletions and substitutions without normalizing spaces, punctuation or case.

The exact seed-42 extraction report is in [`results/cv_extract.md`](../results/cv_extract.md). The separate generator self-check and decoder evaluation count a barcode as successful only when exactly one decoded symbol has the expected GS1 fields and values.

## Verification

Commands were run with the Conda environment's Python 3.12 executable:

```bash
/opt/anaconda3/envs/labellens-cv/bin/python -m pytest -q src/gen src/cv
/opt/anaconda3/envs/labellens-cv/bin/python -m ruff check src/gen src/cv
/opt/anaconda3/envs/labellens-cv/bin/python -m pip check
```

Actual output:

```text
233 passed in 61.48s (0:01:01)
All checks passed!
No broken requirements found.
```

The full evaluation command is:

```bash
/opt/anaconda3/envs/labellens-cv/bin/python -m src.gen.generate_dataset --output-dir data/synthetic/task1 --seed 42
/opt/anaconda3/envs/labellens-cv/bin/python -m src.cv.eval_extract --dataset data/synthetic/task1 --output results/cv_extract.md
```

The generated 51-image dataset is not committed because it is large. The two-seed barcode evaluation used temporary directories; rerun the generator with `--seed 43` for the independent-seed check.

## Important limits and remaining work

- The measured data comes from one synthetic 100 mm by 60 mm test-device template, not real product photographs. It does not include glare or occlusion.
- Two hard barcodes on seed 42 and one on seed 43 still fail and remain flagged for human review.
- Both pictograms are simplified synthetic artwork. They are not certified ISO symbols, and all evaluation images contain both symbols.
- AI 01 uses the existing all-zero test placeholder. It is not an allocated GTIN or UDI-DI.
- Draft rendering and comparison are local project functionality. No reviewer approval was issued, no artwork was published, and no medical or regulatory compliance claim is made.
- The repository's shared schemas and retrieval code were not changed in this work.

## Key implementation files

- [`src/gen/generate_dataset.py`](../src/gen/generate_dataset.py): fixed-seed generation and matching ground truth.
- [`src/gen/augment.py`](../src/gen/augment.py): clean, moderate and hard image effects plus coordinate transforms.
- [`src/cv/barcode.py`](../src/cv/barcode.py): GS1 parsing and barcode-slot recovery.
- [`src/cv/extract.py`](../src/cv/extract.py): integrated OCR, barcode, field and symbol extraction.
- [`src/cv/eval_extract.py`](../src/cv/eval_extract.py): condition-separated evaluation and report generation.
- [`src/gen/render.py`](../src/gen/render.py) and [`src/cv/verify.py`](../src/cv/verify.py): draft artifact generation and approval-bound comparison.

