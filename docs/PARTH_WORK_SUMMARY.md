# Parth's LabelLens CV and Synthetic Label Work

**For:** Paridhi  
**Branch:** [parth-gen](https://github.com/paridhik11/labellens/tree/parth-gen)
**Base work:** CV and template work from `parth-cv`, reviewed and merged to `main`.

## Required status note for future summaries and handoffs

Updated 2026-11-16 at Parth's request. Carry this unresolved item into every
future progress summary, README or handoff Markdown prepared for Parth, Paridhi
or anyone else. Do not describe photo extraction or Task 4 as fully solved.

- **Photo-extraction fixes are deferred at Parth's request.** Ten clear online
  device-package photos are now collected, with product name, lot/batch and
  expiry readable in each image according to AI inspection. All 30 reference
  readings are LLM-labelled, not human-validated truth.
- The unchanged extraction pipeline still performs poorly on this clear set:
  exact product name **1/10**, lot **0/10**, expiry **0/10**. Source:
  [clear-photo results](../results/cv_real_photos_clear.md). No 80% real-photo
  accuracy claim is supported. Do not present dataset selection as a model fix.
- The three-photo human spot-check is **NOT_RUN**, not zero errors. Images stay
  local under `data/real_photos/clear_online/`; source URLs and fingerprints are
  in [SOURCES.md](../data/real/SOURCES.md).
- The earlier 12-photo convenience set and its separate baseline are preserved
  in [cv_real_photos.md](../results/cv_real_photos.md). Do not blend either set
  with synthetic results or with medicine evaluation.
- Task 3's newer device-symbol collection contains 20 images and 44 visually
  assigned LLM-labelled crops. Human symbol validation and real-symbol/blind-mode
  accuracy remain unmeasured. The legacy medicine artworks are separate.

When this deferred work is actually fixed and reviewed, update this status using
new executed results and real human feedback. Until then, include the limitation
explicitly even when describing completed generator/export work.

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

### Structured revisions (Task 6)

- Added a local revision engine that copies the old template and ProductRecord,
  increments their versions, binds updated text into a new export snapshot and
  records the actor, reason and change ID. Original inputs remain unchanged.
- Reuses the exact existing barcode for KEEP, regenerates and decode-checks
  confirmed encoded changes, and returns no artwork for NEEDS_INPUT. Missing
  allocated identifiers are never supplied by the engine. A sterilization
  method change updates its bound synthetic symbol without changing the barcode.
- New PDF/SVG outputs remain drafts with the named groups. Layout and barcode
  checks run; OCR and symbol detection for revisions are NOT_RUN. Application
  storage, trusted confirmation/authorization and publication remain separate.

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

- The results table above uses synthetic artwork from one template family. Separate real-photo evaluations now exist and remain poor, as recorded in the required status note above.
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

