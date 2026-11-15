# CV fixes: before and after

Branch `cv-fixes`. All numbers below are on fresh seeds 100, 101 and 102 (17 labels per condition and seed,
51 images per condition), generated once after the pipeline code was frozen at `c594b6d`. Full tables:
`results/cv_final_eval.md`. Dev-seed history: `results/cv_experiments.md`. Diagnosis of the starting point:
`results/cv_diagnosis.md`. Everything is synthetic, from one template family, with test identifiers.

"Before" is the extractor as received (`05869b6`, run from that commit on the same images). "Blind" uses no
template knowledge; "template" uses the known slot positions. CER is character error rate over all six
fields (edits / reference characters, 4,782 characters per condition), after format post-correction for
the final pipeline and as read for the starting point (it had no post-correction). The final pipeline's raw
CER is also in `cv_final_eval.md`; it differs from the post-corrected CER by at most 5 edits per condition.

Intervals are Wilson 95% score intervals computed from the counts in the tables (`python -m src.cv.intervals`;
nothing was re-run). They treat every label, or every symbol, as an independent trial. Labels are
independent draws, but the two symbols on one label share its photo conditions, so the symbol intervals
are somewhat too narrow.

## Main conditions

| Condition | Exact GS1: before | blind | template | CER: before | blind | template | Symbols IoU>=0.5: before | blind | Corners within 10 px: before | after |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- | --- |
| clean | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 5.12% | 0.00% | 0.00% | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 51/51 | 51/51 |
| moderate | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 1.32% | 0.00% | 0.00% | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 51/51 | 51/51 |
| hard (reduced, the published setting) | 45/51 (88.2%; 95% CI 76.6 to 94.5%) | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 0.15% | 0.31% | 0.00% | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 51/51 | 51/51 |
| hard_original (setting before `3c98598`) | 37/51 (72.5%; 95% CI 59.1 to 82.9%) | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 50/51 (98.0%; 95% CI 89.7 to 99.7%) | 1.00% | 0.00% | 0.00% | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 102/102 (100.0%; 95% CI 96.4 to 100.0%) | 51/51 | 51/51 |
| very_hard (new: glare and occlusion) | 28/51 (54.9%; 95% CI 41.4 to 67.7%) | 43/51 (84.3%; 95% CI 72.0 to 91.8%) | 44/51 (86.3%; 95% CI 74.3 to 93.2%) | 58.36% | 9.35% | 3.85% | 42/102 (41.2%; 95% CI 32.1 to 50.9%) | 93/102 (91.2%; 95% CI 84.1 to 95.3%) | 22/51 | 51/51 |

The 0.31% for blind on hard is one label whose product name was not named (15 edits); all other blind
fields on hard were exact.

## Original hard against reduced hard (exact GS1, 51 labels each)

| Decoder | Original hard | Reduced hard |
| --- | --- | --- |
| Old decoder (`ecc9869`), before the slot recovery | 11/51 (21.6%; 95% CI 12.5 to 34.6%) | 24/51 (47.1%; 95% CI 34.1 to 60.5%) |
| Starting point (`05869b6`), with template-slot recovery | 37/51 (72.5%; 95% CI 59.1 to 82.9%) | 45/51 (88.2%; 95% CI 76.6 to 94.5%) |
| Final, template-assisted | 50/51 (98.0%; 95% CI 89.7 to 99.7%) | 51/51 (100.0%; 95% CI 93.0 to 100.0%) |
| Final, blind | 51/51 (100.0%; 95% CI 93.0 to 100.0%) | 51/51 (100.0%; 95% CI 93.0 to 100.0%) |

The published "above 80 percent" hard result needed both the decoder change and the easier benchmark. On the
original setting the starting point reached 72.5% on these seeds.

## Negative and variation cases (moderate and hard together, 102 labels per case)

| Case | Measure | Before | Final, blind | Final, template |
| --- | --- | --- | --- | --- |
| missing_manufacturer, missing_expiry, wrong_symbol | absent symbols reported (false positives) | 0/306 (0.0%; 95% CI 0.0 to 1.2%) | 0/306 (0.0%; 95% CI 0.0 to 1.2%) | 0/306 (0.0%; 95% CI 0.0 to 1.2%) |
| same | absences flagged as `missing_symbol` | n/a (warning only) | 306/306 (100.0%; 95% CI 98.8 to 100.0%) | 306/306 (100.0%; 95% CI 98.8 to 100.0%) |
| small_symbols (0.6 size) | symbols found | 0/204 (0.0%; 95% CI 0.0 to 1.8%) | 204/204 (100.0%; 95% CI 98.2 to 100.0%) | 0/204 (0.0%; 95% CI 0.0 to 1.8%) |
| large_symbols (1.25 size) | symbols found | 204/204 (100.0%; 95% CI 98.2 to 100.0%) | 204/204 (100.0%; 95% CI 98.2 to 100.0%) | 204/204 (100.0%; 95% CI 98.2 to 100.0%) |
| alt_style (independent artwork) | symbols found | 0/204 (0.0%; 95% CI 0.0 to 1.8%) | 0/204 (0.0%; 95% CI 0.0 to 1.8%) | 0/204 (0.0%; 95% CI 0.0 to 1.8%) |
| wrong_barcode | print/barcode mismatch flagged | no check existed | 102/102 | 102/102 |
| all other cases | false mismatch alarms | no check existed | 0/612 | 0/612 |

## What remains weak

- Very hard barcodes: 43/51 blind and 44/51 template-assisted, against 33/34 on the dev seeds. The dev seeds
  flattered this condition; the fresh number is the one to quote.
- Very hard text. Blind field naming (9.35% CER) is much worse than the template mapping (3.85%), because
  an occluder or glare spot that removes the address line also breaks the rules that name the manufacturer
  and product.
- False mismatch alarms under glare. On very hard, the print/barcode check raised a false
  `barcode_mismatch` flag on 5 of 43 decoded labels in blind mode and 10 of 44 in template mode, because
  OCR misread the lot or expiry. Every flag needs human review, but it is noise for the reviewer.
  After the fresh evaluation, the checker was changed (on request) to emit `needs_human_review` instead of
  `barcode_mismatch` when the OCR confidence of the lot or expiry line is below 0.8, the extractor's existing
  low-confidence threshold, chosen before measuring. Measured on the dev seeds only (the fresh seeds were
  not re-run): very hard false mismatch flags stayed at 9 of 33 labels (template) and 5 of 33 (blind), with
  0 review flags, and real mismatches were still flagged on 68/68 wrong-barcode labels per mode. Every false
  alarm came from a confident misreading (OCR confidence 0.876 to 0.999,
  `scripts/cv_experiments/false_alarm_confidence.py`), so OCR confidence does not separate them here. Most
  of those readings had lost their printed key (`LOT`, `EXP`) or were not a valid date, which a format check
  could catch; that was not tried.
- Symbols are template matching against drawings made by the same code that draws the test labels. An
  independently drawn version of the same two pictograms was found 0 of 204 times. Real ISO artwork would
  need real reference images or a trained detector with real data.
- One layout, one font, one barcode size. The blind mode removes the use of slot positions but its rules were
  only ever tested on this layout.
- No real photo has been evaluated. `data/real_photos/README.md` describes what to add, and
  `python -m src.cv.eval_real` runs when it exists.

## Reproduce

```bash
python -m src.gen.generate_dataset --output-dir data/synthetic/fresh100 --seed 100 --conditions clean moderate hard hard_original very_hard
python -m src.gen.generate_negatives --output-dir data/synthetic/freshneg100 --seed 100
python -m src.cv.eval_v2 run --dataset data/synthetic/fresh100 --records results/cv_records/fresh100.json
python -m src.cv.eval_v2 run --dataset data/synthetic/freshneg100 --records results/cv_records/freshneg100.json
```

Repeat for seeds 101 and 102, then:

```bash
python -m src.cv.final_report --main data/synthetic/fresh100 data/synthetic/fresh101 data/synthetic/fresh102 --neg data/synthetic/freshneg100 data/synthetic/freshneg101 data/synthetic/freshneg102 --output results/cv_final_eval.md
```

Environment: Windows, Python 3.12.10, packages pinned in `requirements-cv.txt`.
