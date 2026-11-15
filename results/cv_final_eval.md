# CV final evaluation on fresh seeds

Seeds 100, 101, 102 were generated once, after the pipeline code was frozen at commit `c594b6d`. No pipeline code
was changed after these images were generated. (The report was written at `cadf763`, which only added
`results/cv_experiments.md` and `scripts/cv_experiments/`; the pipeline imports neither. The first report run
crashed in the Windows process pool that runs the starting-point code and was re-run unchanged.)
17 labels per condition and seed, so 51 images per condition below. All data is synthetic, from one template family, with test identifiers.

Intervals are Wilson 95% score intervals computed from the counts in the tables (`python -m src.cv.intervals`;
nothing was re-run). They treat every label, or every symbol, as an independent trial. Labels are
independent draws, but the two symbols on one label share its photo conditions, so the symbol intervals
are somewhat too narrow.

## Starting point on the same images

Extractor at `05869b6` (the parth-cv branch as received), run from that commit.

| Condition | Images | Exact GS1 | Symbols IoU>=0.5 | Symbol false positives | Corners within 10 px | CER product_name | CER manufacturer | CER manufacturer_address | CER model | CER lot | CER expiry | CER all |
| --- | ---: | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | 51 | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 0 | 51/51 (100.0%) | 13.68% | 0.00% | 0.00% | 7.14% | 5.26% | 6.14% | 5.12% (245/4782) |
| moderate | 51 | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 0 | 51/51 (100.0%) | 1.71% | 0.00% | 0.25% | 5.18% | 1.24% | 0.00% | 1.32% (63/4782) |
| hard | 51 | 45/51 (88.2%; 95% CI 76.6 to 94.5%) | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 0 | 51/51 (100.0%) | 0.43% | 0.00% | 0.00% | 0.28% | 0.10% | 0.13% | 0.15% (7/4782) |
| hard_original | 51 | 37/51 (72.5%; 95% CI 59.1 to 82.9%) | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 0 | 51/51 (100.0%) | 0.57% | 0.00% | 0.00% | 3.78% | 0.41% | 1.70% | 1.00% (48/4782) |
| very_hard | 51 | 28/51 (54.9%; 95% CI 41.4 to 67.7%) | 42/102 (41.2%; 95% CI 32.1 to 50.9%) | 0 | 22/51 (43.1%) | 58.12% | 57.72% | 58.95% | 59.10% | 58.31% | 58.04% | 58.36% (2791/4782) |

## Final configuration

### Seeds 100, 101, 102: barcode, symbols and label corners

| Condition | Images | Exact GS1, blind | Exact GS1, template-assisted | Symbols IoU>=0.5, blind | Symbol false positives, blind | Symbols IoU>=0.5, template | Label found | Corners within 10 px | Found by fallback |
| --- | ---: | --- | --- | --- | ---: | --- | --- | --- | ---: |
| clean | 51 | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 0 | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 51/51 (100.0%) | 51/51 (100.0%) | 0 |
| moderate | 51 | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 0 | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 51/51 (100.0%) | 51/51 (100.0%) | 0 |
| hard | 51 | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 0 | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 51/51 (100.0%) | 51/51 (100.0%) | 0 |
| hard_original | 51 | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 50/51 (98.0%; 95% CI 89.7 to 99.7%) | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 0 | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 51/51 (100.0%) | 51/51 (100.0%) | 0 |
| very_hard | 51 | 43/51 (84.3%; 95% CI 72.0 to 91.8%) | 44/51 (86.3%; 95% CI 74.3 to 93.2%) | 93/102 (91.2%; 95% CI 84.1 to 95.3%) | 0 | 93/102 (91.2%; 95% CI 84.1 to 95.3%) | 51/51 (100.0%) | 51/51 (100.0%) | 29 |

### Seeds 100, 101, 102: OCR character error rate per field

Edits / reference characters. "raw" is the OCR text as read, "post" is after format post-correction.

| Condition | Mode | Text | product_name | manufacturer | manufacturer_address | model | lot | expiry | all fields |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| clean | template | raw | 0.00% (0/702) | 0.00% (0/816) | 0.00% (0/816) | 0.00% (0/714) | 0.00% (0/969) | 0.00% (0/765) | 0.00% (0/4782) |
| clean | template | post | 0.00% (0/702) | 0.00% (0/816) | 0.00% (0/816) | 0.00% (0/714) | 0.00% (0/969) | 0.00% (0/765) | 0.00% (0/4782) |
| clean | blind | raw | 0.00% (0/702) | 0.00% (0/816) | 0.00% (0/816) | 0.00% (0/714) | 0.00% (0/969) | 0.00% (0/765) | 0.00% (0/4782) |
| clean | blind | post | 0.00% (0/702) | 0.00% (0/816) | 0.00% (0/816) | 0.00% (0/714) | 0.00% (0/969) | 0.00% (0/765) | 0.00% (0/4782) |
| moderate | template | raw | 0.00% (0/702) | 0.00% (0/816) | 0.00% (0/816) | 0.00% (0/714) | 0.10% (1/969) | 0.00% (0/765) | 0.02% (1/4782) |
| moderate | template | post | 0.00% (0/702) | 0.00% (0/816) | 0.00% (0/816) | 0.00% (0/714) | 0.00% (0/969) | 0.00% (0/765) | 0.00% (0/4782) |
| moderate | blind | raw | 0.00% (0/702) | 0.00% (0/816) | 0.00% (0/816) | 0.00% (0/714) | 0.10% (1/969) | 0.00% (0/765) | 0.02% (1/4782) |
| moderate | blind | post | 0.00% (0/702) | 0.00% (0/816) | 0.00% (0/816) | 0.00% (0/714) | 0.00% (0/969) | 0.00% (0/765) | 0.00% (0/4782) |
| hard | template | raw | 0.00% (0/702) | 0.00% (0/816) | 0.00% (0/816) | 0.14% (1/714) | 0.00% (0/969) | 0.26% (2/765) | 0.06% (3/4782) |
| hard | template | post | 0.00% (0/702) | 0.00% (0/816) | 0.00% (0/816) | 0.00% (0/714) | 0.00% (0/969) | 0.00% (0/765) | 0.00% (0/4782) |
| hard | blind | raw | 2.14% (15/702) | 0.00% (0/816) | 0.00% (0/816) | 0.14% (1/714) | 0.00% (0/969) | 0.26% (2/765) | 0.38% (18/4782) |
| hard | blind | post | 2.14% (15/702) | 0.00% (0/816) | 0.00% (0/816) | 0.00% (0/714) | 0.00% (0/969) | 0.00% (0/765) | 0.31% (15/4782) |
| hard_original | template | raw | 0.00% (0/702) | 0.00% (0/816) | 0.00% (0/816) | 0.28% (2/714) | 0.00% (0/969) | 0.00% (0/765) | 0.04% (2/4782) |
| hard_original | template | post | 0.00% (0/702) | 0.00% (0/816) | 0.00% (0/816) | 0.00% (0/714) | 0.00% (0/969) | 0.00% (0/765) | 0.00% (0/4782) |
| hard_original | blind | raw | 0.00% (0/702) | 0.00% (0/816) | 0.00% (0/816) | 0.28% (2/714) | 0.00% (0/969) | 0.00% (0/765) | 0.04% (2/4782) |
| hard_original | blind | post | 0.00% (0/702) | 0.00% (0/816) | 0.00% (0/816) | 0.00% (0/714) | 0.00% (0/969) | 0.00% (0/765) | 0.00% (0/4782) |
| very_hard | template | raw | 1.71% (12/702) | 2.82% (23/816) | 5.51% (45/816) | 3.78% (27/714) | 3.10% (30/969) | 6.80% (52/765) | 3.95% (189/4782) |
| very_hard | template | post | 1.71% (12/702) | 2.82% (23/816) | 5.51% (45/816) | 3.36% (24/714) | 2.99% (29/969) | 6.67% (51/765) | 3.85% (184/4782) |
| very_hard | blind | raw | 7.98% (56/702) | 9.19% (75/816) | 7.84% (64/816) | 8.26% (59/714) | 7.22% (70/969) | 16.73% (128/765) | 9.45% (452/4782) |
| very_hard | blind | post | 7.98% (56/702) | 9.19% (75/816) | 7.84% (64/816) | 7.84% (56/714) | 7.12% (69/969) | 16.60% (127/765) | 9.35% (447/4782) |

## Original hard against reduced hard

| Decoder | Original hard (blur to 1.8, noise 8) | Reduced hard (blur to 1.6, noise 6) |
| --- | --- | --- |
| Old decoder (`ecc9869`): photo, then rectified label | 11/51 (21.6%; 95% CI 12.5 to 34.6%) | 24/51 (47.1%; 95% CI 34.1 to 60.5%) |
| Starting point (`05869b6`): plus thresholded template slot | 37/51 (72.5%; 95% CI 59.1 to 82.9%) | 45/51 (88.2%; 95% CI 76.6 to 94.5%) |
| Final, template-assisted | 50/51 (98.0%; 95% CI 89.7 to 99.7%) | 51/51 (100.0%; 95% CI 93.0 to 100.0%) |
| Final, blind (no slot position) | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 51/51 (100.0%; 95% CI 93.0 to 100.0%) |

## Negative and variation cases

### Seeds 100, 101, 102: negative and variation cases

"Absent symbols reported" are false positives: the symbol is not on the label but was detected.
"Absence flagged" counts absent symbols for which a `missing_symbol` flag was raised.

| Case | Condition | Mode | Images | Present symbols matched | Absent symbols reported | Absence flagged | Other false positives | Barcode decoded | Print/barcode mismatch flagged |
| --- | --- | --- | ---: | --- | --- | --- | ---: | --- | --- |
| alt_style | hard | blind | 51 | 0/102 (0.0%; 95% CI 0.0 to 3.6%) | 0/0 | 0/0 | 0 | 51/51 (100.0%) | 0/51 (0.0%) |
| alt_style | hard | template | 51 | 0/102 (0.0%; 95% CI 0.0 to 3.6%) | 0/0 | 0/0 | 0 | 51/51 (100.0%) | 0/51 (0.0%) |
| alt_style | moderate | blind | 51 | 0/102 (0.0%; 95% CI 0.0 to 3.6%) | 0/0 | 0/0 | 0 | 51/51 (100.0%) | 0/51 (0.0%) |
| alt_style | moderate | template | 51 | 0/102 (0.0%; 95% CI 0.0 to 3.6%) | 0/0 | 0/0 | 0 | 51/51 (100.0%) | 0/51 (0.0%) |
| large_symbols | hard | blind | 51 | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 0/0 | 0/0 | 0 | 51/51 (100.0%) | 0/51 (0.0%) |
| large_symbols | hard | template | 51 | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 0/0 | 0/0 | 0 | 51/51 (100.0%) | 0/51 (0.0%) |
| large_symbols | moderate | blind | 51 | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 0/0 | 0/0 | 0 | 51/51 (100.0%) | 0/51 (0.0%) |
| large_symbols | moderate | template | 51 | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 0/0 | 0/0 | 0 | 51/51 (100.0%) | 0/51 (0.0%) |
| missing_expiry | hard | blind | 51 | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 0/51 (0.0%; 95% CI 0.0 to 7.0%) | 51/51 (100.0%) | 0 | 51/51 (100.0%) | 0/51 (0.0%) |
| missing_expiry | hard | template | 51 | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 0/51 (0.0%; 95% CI 0.0 to 7.0%) | 51/51 (100.0%) | 0 | 51/51 (100.0%) | 0/51 (0.0%) |
| missing_expiry | moderate | blind | 51 | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 0/51 (0.0%; 95% CI 0.0 to 7.0%) | 51/51 (100.0%) | 0 | 51/51 (100.0%) | 0/51 (0.0%) |
| missing_expiry | moderate | template | 51 | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 0/51 (0.0%; 95% CI 0.0 to 7.0%) | 51/51 (100.0%) | 0 | 51/51 (100.0%) | 0/51 (0.0%) |
| missing_manufacturer | hard | blind | 51 | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 0/51 (0.0%; 95% CI 0.0 to 7.0%) | 51/51 (100.0%) | 0 | 51/51 (100.0%) | 0/51 (0.0%) |
| missing_manufacturer | hard | template | 51 | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 0/51 (0.0%; 95% CI 0.0 to 7.0%) | 51/51 (100.0%) | 0 | 51/51 (100.0%) | 0/51 (0.0%) |
| missing_manufacturer | moderate | blind | 51 | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 0/51 (0.0%; 95% CI 0.0 to 7.0%) | 51/51 (100.0%) | 0 | 51/51 (100.0%) | 0/51 (0.0%) |
| missing_manufacturer | moderate | template | 51 | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 0/51 (0.0%; 95% CI 0.0 to 7.0%) | 51/51 (100.0%) | 0 | 51/51 (100.0%) | 0/51 (0.0%) |
| small_symbols | hard | blind | 51 | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 0/0 | 0/0 | 0 | 51/51 (100.0%) | 0/51 (0.0%) |
| small_symbols | hard | template | 51 | 0/102 (0.0%; 95% CI 0.0 to 3.6%) | 0/0 | 0/0 | 0 | 51/51 (100.0%) | 0/51 (0.0%) |
| small_symbols | moderate | blind | 51 | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 0/0 | 0/0 | 0 | 51/51 (100.0%) | 0/51 (0.0%) |
| small_symbols | moderate | template | 51 | 0/102 (0.0%; 95% CI 0.0 to 3.6%) | 0/0 | 0/0 | 0 | 51/51 (100.0%) | 0/51 (0.0%) |
| wrong_barcode | hard | blind | 51 | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 0/0 | 0/0 | 0 | 51/51 (100.0%) | 51/51 (100.0%) |
| wrong_barcode | hard | template | 51 | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 0/0 | 0/0 | 0 | 51/51 (100.0%) | 51/51 (100.0%) |
| wrong_barcode | moderate | blind | 51 | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 0/0 | 0/0 | 0 | 51/51 (100.0%) | 51/51 (100.0%) |
| wrong_barcode | moderate | template | 51 | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 0/0 | 0/0 | 0 | 51/51 (100.0%) | 51/51 (100.0%) |
| wrong_symbol | hard | blind | 51 | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 0/51 (0.0%; 95% CI 0.0 to 7.0%) | 51/51 (100.0%) | 0 | 51/51 (100.0%) | 0/51 (0.0%) |
| wrong_symbol | hard | template | 51 | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 0/51 (0.0%; 95% CI 0.0 to 7.0%) | 51/51 (100.0%) | 0 | 51/51 (100.0%) | 0/51 (0.0%) |
| wrong_symbol | moderate | blind | 51 | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 0/51 (0.0%; 95% CI 0.0 to 7.0%) | 51/51 (100.0%) | 0 | 51/51 (100.0%) | 0/51 (0.0%) |
| wrong_symbol | moderate | template | 51 | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 0/51 (0.0%; 95% CI 0.0 to 7.0%) | 51/51 (100.0%) | 0 | 51/51 (100.0%) | 0/51 (0.0%) |

### Starting point (`05869b6`) on the same negative and variation cases

| Case | Condition | Images | Present symbols matched | Absent symbols reported |
| --- | --- | ---: | --- | --- |
| alt_style | hard | 51 | 0/102 (0.0%; 95% CI 0.0 to 3.6%) | 0/0 |
| alt_style | moderate | 51 | 0/102 (0.0%; 95% CI 0.0 to 3.6%) | 0/0 |
| large_symbols | hard | 51 | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 0/0 |
| large_symbols | moderate | 51 | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 0/0 |
| missing_expiry | hard | 51 | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 0/51 (0.0%; 95% CI 0.0 to 7.0%) |
| missing_expiry | moderate | 51 | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 0/51 (0.0%; 95% CI 0.0 to 7.0%) |
| missing_manufacturer | hard | 51 | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 0/51 (0.0%; 95% CI 0.0 to 7.0%) |
| missing_manufacturer | moderate | 51 | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 0/51 (0.0%; 95% CI 0.0 to 7.0%) |
| small_symbols | hard | 51 | 0/102 (0.0%; 95% CI 0.0 to 3.6%) | 0/0 |
| small_symbols | moderate | 51 | 0/102 (0.0%; 95% CI 0.0 to 3.6%) | 0/0 |
| wrong_barcode | hard | 51 | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 0/0 |
| wrong_barcode | moderate | 51 | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 0/0 |
| wrong_symbol | hard | 51 | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 0/51 (0.0%; 95% CI 0.0 to 7.0%) |
| wrong_symbol | moderate | 51 | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 0/51 (0.0%; 95% CI 0.0 to 7.0%) |
