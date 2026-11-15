# Parth's LabelLens CV and Synthetic Label Work

**For:** Paridhi  
**Branch:** [parth-gen](https://github.com/paridhik11/labellens/tree/parth-gen)
**Base work:** CV and template work from `parth-cv`, reviewed and merged to `main`.

## Project goal

Build a reproducible synthetic medical-device label workflow and a computer-vision baseline for reading fields and GS1 barcodes, locating symbols, and preserving positions through distortion. Generated labels remain test drafts, use supplied identifiers, and are evaluated separately by condition.

## Work completed

### Synthetic labels and augmentation

- Aligned augmentation tests with the augmentation API and tested coordinate transforms for label, text and symbol positions.
- Added fixed-seed label generation with varied product, manufacturer, address, model, lot, expiry and serial values. Each base label has clean, moderate and hard variants with matching ground-truth JSON and a manifest.
- Ground truth includes transformed corners, homography, GS1 data, change log and self-check. Failed samples remain in evaluation.
- Added harder synthetic conditions including glare and occlusion. These are controlled synthetic stress cases, not real capture conditions.

### Computer vision and barcode handling

- Added label-boundary detection, perspective correction, OCR, GS1 parsing, template and blind extraction paths, and coordinates mapped to the original image.
- Barcode decoding supports blind image search and template-assisted recovery. The template-assisted path uses known barcode-slot information, so its scores should not be presented as blind decoding.
- Blind symbol search scans the label at multiple scales. Detection still uses references derived from the same synthetic symbol drawing code, so these results do not establish performance on independently drawn or real-world symbols.
- Added negative cases for absent or incorrect symbols and barcode/text mismatches.

### Draft rendering and verification

- Added deterministic SVG, physical-size PDF and preview rendering for the test-device template.
- Draft output carries DRAFT marking, a change log, artifact hashes and self-check results. Barcode content is retained when unchanged and regenerated only for confirmed changes.
- Print comparison is bound to an approval record and artifact hash. The verification code does not create approvals or publish artwork.

## Fresh-seed results

The following results are from seeds 100, 101 and 102 in `results/cv_final_eval.md`: 51 synthetic labels per condition and 102 expected symbol instances per condition. All use one synthetic template family.

| Condition | Exact GS1, blind | Exact GS1, template-assisted | Blind symbol matches | Template symbol matches | Corners within 10 px |
| --- | ---: | ---: | ---: | ---: | ---: |
| Clean | 51/51 | 51/51 | 102/102 | 102/102 | 51/51 |
| Moderate | 51/51 | 51/51 | 102/102 | 102/102 | 51/51 |
| Hard | 51/51 | 51/51 | 102/102 | 102/102 | 51/51 |
| Original hard | 51/51 | 50/51 | 102/102 | 102/102 | 51/51 |
| Very hard | 43/51 | 44/51 | 93/102 | 93/102 | 51/51 |

“Very hard” includes synthetic glare and occlusion. On that condition, OCR character error rate was 9.35% in blind mode and 3.85% in template mode after format post-correction. Clean, moderate, hard and original-hard post-corrected OCR error rates were 0.00% for both modes. In the variation cases, absent symbols produced 0 false positive detections; the exact counts and confidence intervals are in the evaluation report.

The older “15/17 hard” figure only applied to an easier, reduced blur/noise setting and is not the result to use for the original hard benchmark. The old “4/17 baseline” comparison mixed settings; the same-image fresh-seed comparisons are reported in `results/cv_final_eval.md`. No seed-42 or seed-43 figures are used here.

## Limits and remaining work

- These results use synthetic artwork from one template family. No real product photo has been evaluated yet.
- The very-hard barcode result is lower than the other conditions. OCR naming in blind mode is heuristic and performs worse than template mapping under very hard glare and occlusion.
- Symbol detection is not validated on independent artwork: the references come from the same code as the synthetic symbols, and independently drawn variants were not detected in the fresh evaluation.
- The test GTIN is an all-zero placeholder, not an allocated GTIN or UDI-DI. No real identifier is fabricated.
- Pictograms are simplified test artwork, not certified ISO symbols. No reviewer approval was issued and no artwork was published.
- Cross-platform output bytes are not identical, even though the reported evaluation metrics matched. On Windows without Poppler's `pdftoppm`, one render test fails.
- The shared schemas and retrieval modules were not changed in the CV work.

## Verification

The prior scoped Mac run used the Conda Python 3.12 environment:

```bash
/opt/anaconda3/envs/labellens-cv/bin/python -m pytest -q src/gen src/cv
/opt/anaconda3/envs/labellens-cv/bin/python -m ruff check src/gen src/cv
```

Output from this handoff update:

```text
233 passed in 123.86s (0:02:03)
All checks passed!
```

The Windows caveat above is recorded in `docs/CV_STATUS.md`. Reproduction commands and all fresh-seed tables are in [`results/cv_final_eval.md`](../results/cv_final_eval.md).

## Key implementation files

- [`src/gen/generate_dataset.py`](../src/gen/generate_dataset.py): fixed-seed synthetic labels and matching ground truth.
- [`src/gen/augment.py`](../src/gen/augment.py): image effects and coordinate transforms.
- [`src/cv/barcode.py`](../src/cv/barcode.py) and [`src/cv/barcode_blind.py`](../src/cv/barcode_blind.py): template-assisted and blind barcode paths.
- [`src/cv/extract.py`](../src/cv/extract.py), [`src/cv/fields.py`](../src/cv/fields.py), and [`src/cv/symbols.py`](../src/cv/symbols.py): extraction, field naming and symbol detection.
- [`src/gen/render.py`](../src/gen/render.py) and [`src/cv/verify.py`](../src/cv/verify.py): draft rendering and approval-bound print comparison.

