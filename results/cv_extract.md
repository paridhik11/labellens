# Synthetic device-label extraction baseline

Seed: 42. Images evaluated: 51.

Synthetic device labels from one template family do not validate real-photo performance.
The extractor and its warning thresholds were not tuned during this measurement step.

## Metric definitions

- OCR character error rate (CER) is total edit distance divided by total reference characters,
  separately per field and condition. Insertions, deletions and substitutions each cost one.
  Case, spaces and punctuation count; nothing is normalized.
  Missing or ambiguous fields use an empty hypothesis, so all reference characters count as deletions.
  CER can exceed 100% when insertions outnumber reference characters.
  Characters are Python Unicode code points.
- Barcode decode rate counts images with any decoded symbol, including failed GS1 parses.
- Exact GS1 accuracy requires one decoded symbol. Per-AI and all-four matches use all images as denominator.
  Missing decodes and ambiguous multiple symbols count as incorrect.
  Conditional all-four accuracy is also shown, with decoded images as denominator.
- Detection/correction success requires four detected corners, successful rectification, and every corner
  within 10 original-image pixels of known corners. A deterministic geometry probe reruns the unchanged
  detector because the shared schema does not expose internal corners. It is independent of OCR success.
- A symbol match needs the expected synthetic name and axis-aligned box intersection over union (IoU)
  of at least 0.50. Mean same-name IoU is also reported. The two pictograms are not certified ISO artwork.
- Extraction exceptions stay in denominators, with empty text hypotheses and failed barcode results.
  Missing or malformed ground truth aborts evaluation rather than inventing references.

## Per-condition summary

| Condition | Images | Barcode decoded | All four AIs exact | All four exact given decode | Boundary detected | Corrected within 10 px | Symbols IoU >= 0.50 | Exact symbol sets | Mean symbol IoU | Extraction exceptions |
| --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| clean | 17 | 17/17 (100.00%) | 17/17 (100.00%) | 17/17 (100.00%) | 17/17 (100.00%) | 17/17 (100.00%) | 34/34 (100.00%) | 17/17 (100.00%) | 0.988 | 0/17 (0.00%) |
| moderate | 17 | 17/17 (100.00%) | 17/17 (100.00%) | 17/17 (100.00%) | 17/17 (100.00%) | 17/17 (100.00%) | 34/34 (100.00%) | 17/17 (100.00%) | 0.988 | 0/17 (0.00%) |
| hard | 17 | 4/17 (23.53%) | 4/17 (23.53%) | 4/4 (100.00%) | 17/17 (100.00%) | 17/17 (100.00%) | 34/34 (100.00%) | 17/17 (100.00%) | 0.990 | 0/17 (0.00%) |

## OCR character error by field

| Condition | Field | CER | Edits / reference characters | Images | Field present |
| --- | --- | ---: | --- | ---: | --- |
| clean | product_name | 15.15% | 35/231 | 17 | 17/17 |
| clean | manufacturer | 0.00% | 0/272 | 17 | 17/17 |
| clean | manufacturer_address | 0.00% | 0/272 | 17 | 17/17 |
| clean | model | 7.14% | 17/238 | 17 | 17/17 |
| clean | lot | 5.26% | 17/323 | 17 | 17/17 |
| clean | expiry | 5.10% | 13/255 | 17 | 17/17 |
| moderate | product_name | 1.73% | 4/231 | 17 | 17/17 |
| moderate | manufacturer | 0.00% | 0/272 | 17 | 17/17 |
| moderate | manufacturer_address | 0.00% | 0/272 | 17 | 17/17 |
| moderate | model | 6.30% | 15/238 | 17 | 17/17 |
| moderate | lot | 2.48% | 8/323 | 17 | 17/17 |
| moderate | expiry | 0.00% | 0/255 | 17 | 17/17 |
| hard | product_name | 0.87% | 2/231 | 17 | 17/17 |
| hard | manufacturer | 0.00% | 0/272 | 17 | 17/17 |
| hard | manufacturer_address | 0.00% | 0/272 | 17 | 17/17 |
| hard | model | 4.20% | 10/238 | 17 | 17/17 |
| hard | lot | 0.00% | 0/323 | 17 | 17/17 |
| hard | expiry | 1.57% | 4/255 | 17 | 17/17 |

## Exact GS1 matches per AI

| Condition | AI 01 | AI 17 | AI 10 | AI 21 |
| --- | --- | --- | --- | --- |
| clean | 17/17 (100.00%) | 17/17 (100.00%) | 17/17 (100.00%) | 17/17 (100.00%) |
| moderate | 17/17 (100.00%) | 17/17 (100.00%) | 17/17 (100.00%) | 17/17 (100.00%) |
| hard | 4/17 (23.53%) | 4/17 (23.53%) | 4/17 (23.53%) | 4/17 (23.53%) |

## Warning counts

Counts are images with each warning code, not individual occurrences. Informational warnings are included.

| Condition | Warning | Images |
| --- | --- | --- |
| clean | LOW_OCR_CONFIDENCE | 12/17 |
| clean | TEMPLATE_ASSUMED | 17/17 |
| moderate | LOW_OCR_CONFIDENCE | 13/17 |
| moderate | TEMPLATE_ASSUMED | 17/17 |
| hard | BARCODE_NOT_DECODED | 13/17 |
| hard | LOW_OCR_CONFIDENCE | 13/17 |
| hard | TEMPLATE_ASSUMED | 17/17 |

## Largest text errors

Up to three field errors per condition, sorted by edit count, filename and field. Quotes expose whitespace.

| Condition | Image | Field | Reference | Observed | Edits |
| --- | --- | --- | --- | --- | ---: |
| clean | clean/test_label_001_clean.png | product_name | "TEST SENSOR 001" | "TESTSENSORO01" | 3 |
| clean | clean/test_label_008_clean.png | product_name | "TEST SENSOR 008" | "TESTSENSORO08" | 3 |
| clean | clean/test_label_010_clean.png | product_name | "TEST SENSOR 010" | "TESTSENSORO10" | 3 |
| moderate | moderate/test_label_009_moderate.png | product_name | "TEST DEVICE 009" | "TESTDEVICE009" | 2 |
| moderate | moderate/test_label_001_moderate.png | lot | "LOT: TESTLOT0016232" | "LOT:TESTLOT0016232" | 1 |
| moderate | moderate/test_label_001_moderate.png | model | "REF: TEST-M001" | "REF:TEST-M001" | 1 |
| hard | hard/test_label_001_hard.png | product_name | "TEST SENSOR 001" | "TEST SENSOR O01" | 1 |
| hard | hard/test_label_002_hard.png | model | "REF: TEST-M002" | "REF TEST-M002" | 1 |
| hard | hard/test_label_003_hard.png | model | "REF: TEST-M003" | "REF TEST-M003" | 1 |

## Evaluation failures

No extraction or geometry-probe exceptions occurred. Decode and OCR errors are still reflected above.

## Reproduce

Generate inputs once, then run the evaluator with one command:

```bash
python -m src.gen.generate_dataset --output-dir data/synthetic/task1 --seed 42 --labels-per-condition 17
python -m src.cv.eval_extract --dataset data/synthetic/task1 --output results/cv_extract.md
```

Python: 3.12.16. Platform: Darwin arm64.
Extraction defaults: {"blur_threshold": 100.0, "min_confidence": 0.8}.
Install recorded dependencies from `src/gen/requirements-cv.txt`. Models are bundled with RapidOCR.

| Package | Version |
| --- | --- |
| Pillow | 13.0.0 |
| numpy | 2.5.4 |
| opencv-python | 5.0.0.93 |
| zxing-cpp | 3.1.1 |
| rapidocr-onnxruntime | 1.4.4 |
| onnxruntime | 1.31.1 |
| pydantic | 2.14.3 |

### SHA-256 fingerprints

Dataset contents: `9051431585118afc8c649665c947fb632616148c1f43e4242ce9e617f2194cca`.
Template: `1a0b096f89eecfb0edcbb716468335cde54036984d6b0893c9ab19bbb0ab9a2a`.

| File | SHA-256 |
| --- | --- |
| src/cv/eval_extract.py | e8ed372e033bfcfc55966ba78f032ec0a2cc332d3cc174cc9372ed505d3fe3d4 |
| src/cv/extract.py | f2dac669da083ec04074e874df136f09eaa7b4eafa659156d3f37b6766b78536 |
| src/cv/preprocess.py | 8c92d6810f723528483a364b2a32c1c9274ce40e341d94c6213e3eb0cabfe02f |
| src/cv/symbols.py | d47726be2a47bb296b0612eba4ba15188b0e6e2a8824f9ef25838d28f1dbd6de |
| src/cv/verify.py | 6eaa3e7e452db2f09d89a8b1733e332e1474e2c7ed69058befd74aa16e49572e |
| src/cv/ocr.py | 734345b4eaa610931a9ef1621daefdec9a846bb419fe1223e95fc530fa0e9696 |
| src/cv/barcode.py | e716823548cb9ef0fdf94d2274026e0ab142fce33a82a91fd3bfe8c39b848605 |
| src/gen/generate_dataset.py | 2bb3a4d820a5a2a3552b20da9a296527812ddb2bc44f0fef3512809704ba55c7 |
| src/gen/smoke_label.py | 22158f6401499dd6fbc935900847418df1bb6bda52bf3827bde5716500026289 |
| src/gen/augment.py | 5c769f58a0a691090113b4f0a96a5ed32fe4ddf38985f4094a313a0fc9cd6205 |
| src/gen/symbols.py | 14d141d85db61ed59e15552ebe76f41d081e39ea1e0b377cc6230655fd27ee38 |
| src/gen/render.py | 6b3df664627f1ad3d369f27a197749cdb382834c91e1be2e02fad9147798a6d5 |
| ch_PP-OCRv4_det_infer.onnx | d2a7720d45a54257208b1e13e36a8479894cb74155a5efe29462512d42f49da9 |
| ch_PP-OCRv4_rec_infer.onnx | 48fc40f24f6d2a207a2b1091d3437eb3cc3eb6b676dc3ef9c37384005483683b |
| ch_ppocr_mobile_v2.0_cls_infer.onnx | e47acedf663230f8863ff1ab0e64dd2d82b838fceb5957146dab185a89d6215c |

## Limits

- One synthetic template family does not establish performance on real labels or other layouts.
- GS1 values include an all-zero test identifier. Syntax matches do not prove allocation or authenticity.
- Fields preserve printed prefixes and OCR whitespace errors. Barcode values never replace text hypotheses.
- Confidence and blur warnings are provisional. High-confidence errors and noise-masked blur remain possible.
- Symbols are two simplified synthetic pictograms in one template family, not certified ISO artwork.
  The measured set has no symbol-absent examples and cannot measure false-positive behavior broadly.
- All dataset files were read only; this report is generated from the computed results.
