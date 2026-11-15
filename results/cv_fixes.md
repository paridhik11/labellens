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

## Main conditions

| Condition | Exact GS1: before | blind | template | CER: before | blind | template | Symbols IoU>=0.5: before | blind | Corners within 10 px: before | after |
| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- | --- |
| clean | 51/51 | 51/51 | 51/51 | 5.12% | 0.00% | 0.00% | 102/102 | 102/102 | 51/51 | 51/51 |
| moderate | 51/51 | 51/51 | 51/51 | 1.32% | 0.00% | 0.00% | 102/102 | 102/102 | 51/51 | 51/51 |
| hard (reduced, the published setting) | 45/51 | 51/51 | 51/51 | 0.15% | 0.31% | 0.00% | 102/102 | 102/102 | 51/51 | 51/51 |
| hard_original (setting before `3c98598`) | 37/51 | 51/51 | 50/51 | 1.00% | 0.00% | 0.00% | 102/102 | 102/102 | 51/51 | 51/51 |
| very_hard (new: glare and occlusion) | 28/51 | 43/51 | 44/51 | 58.36% | 9.35% | 3.85% | 42/102 | 93/102 | 22/51 | 51/51 |

The 0.31% for blind on hard is one label whose product name was not named (15 edits); all other blind
fields on hard were exact.

## Original hard against reduced hard (exact GS1, 51 labels each)

| Decoder | Original hard | Reduced hard |
| --- | --- | --- |
| Old decoder (`ecc9869`), before the slot recovery | 11/51 | 24/51 |
| Starting point (`05869b6`), with template-slot recovery | 37/51 | 45/51 |
| Final, template-assisted | 50/51 | 51/51 |
| Final, blind | 51/51 | 51/51 |

The published "above 80 percent" hard result needed both the decoder change and the easier benchmark. On the
original setting the starting point reached 72.5% on these seeds.

## Negative and variation cases (moderate and hard together, 102 labels per case)

| Case | Measure | Before | Final, blind | Final, template |
| --- | --- | --- | --- | --- |
| missing_manufacturer, missing_expiry, wrong_symbol | absent symbols reported (false positives) | 0/306 | 0/306 | 0/306 |
| same | absences flagged as `missing_symbol` | n/a (warning only) | 306/306 | 306/306 |
| small_symbols (0.6 size) | symbols found | 0/204 | 204/204 | 0/204 |
| large_symbols (1.25 size) | symbols found | 204/204 | 204/204 | 204/204 |
| alt_style (independent artwork) | symbols found | 0/204 | 0/204 | 0/204 |
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
