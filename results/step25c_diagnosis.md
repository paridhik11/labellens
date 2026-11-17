# Step 25c before: correct prints on fresh seeds

Correct prints only, seeds 7000 to 7007, 8 per condition. Synthetic photos of the approved label. Read-back of the stored verification rows.

| condition | n | match | mismatch | rescan_needed | job failed |
|---|---|---|---|---|---|
| clean | 8 | 0 | 0 | 8 | 0 |
| moderate | 8 | 0 | 0 | 8 | 0 |
| hard | 8 | 0 | 1 | 7 | 0 |

## Which check failed, per rescan

| condition | seed | field statuses (status, OCR confidence) | barcode | reason | warnings |
|---|---|---|---|---|---|
| clean | 7000 | product_name: MATCH 1.00; manufacturer: MATCH 1.00; manufacturer_address: MATCH 1.00; model: NEEDS_HUMAN_REVIEW none (read None); lot: NEEDS_HUMAN_REVIEW none (read '2'); expiry: MATCH 1.00 | decoded, match True | Weak or missing evidence: model, lot. Rescan or check by eye. | BLIND_MODE, LABEL_NOT_FOUND, PHOTO_OCR, LOW_OCR_CONFIDENCE, FIELD_MISSING |
| clean | 7001 | product_name: MATCH 1.00; manufacturer: MATCH 1.00; manufacturer_address: MATCH 1.00; model: NEEDS_HUMAN_REVIEW none (read None); lot: NEEDS_HUMAN_REVIEW none (read '2'); expiry: MATCH 1.00 | decoded, match True | Weak or missing evidence: model, lot. Rescan or check by eye. | BLIND_MODE, LABEL_NOT_FOUND, PHOTO_OCR, LOW_OCR_CONFIDENCE, FIELD_MISSING |
| clean | 7002 | product_name: MATCH 1.00; manufacturer: MATCH 1.00; manufacturer_address: MATCH 1.00; model: NEEDS_HUMAN_REVIEW none (read None); lot: NEEDS_HUMAN_REVIEW none (read '2'); expiry: MATCH 1.00 | decoded, match True | Weak or missing evidence: model, lot. Rescan or check by eye. | BLIND_MODE, LABEL_NOT_FOUND, PHOTO_OCR, LOW_OCR_CONFIDENCE, FIELD_MISSING |
| clean | 7003 | product_name: MATCH 1.00; manufacturer: MATCH 1.00; manufacturer_address: MATCH 1.00; model: NEEDS_HUMAN_REVIEW none (read None); lot: NEEDS_HUMAN_REVIEW none (read '2'); expiry: MATCH 1.00 | decoded, match True | Weak or missing evidence: model, lot. Rescan or check by eye. | BLIND_MODE, LABEL_NOT_FOUND, PHOTO_OCR, LOW_OCR_CONFIDENCE, FIELD_MISSING |
| clean | 7004 | product_name: MATCH 1.00; manufacturer: MATCH 1.00; manufacturer_address: MATCH 1.00; model: NEEDS_HUMAN_REVIEW none (read None); lot: NEEDS_HUMAN_REVIEW none (read '2'); expiry: MATCH 1.00 | decoded, match True | Weak or missing evidence: model, lot. Rescan or check by eye. | BLIND_MODE, LABEL_NOT_FOUND, PHOTO_OCR, LOW_OCR_CONFIDENCE, FIELD_MISSING |
| clean | 7005 | product_name: MATCH 1.00; manufacturer: MATCH 1.00; manufacturer_address: MATCH 1.00; model: NEEDS_HUMAN_REVIEW none (read None); lot: NEEDS_HUMAN_REVIEW none (read '2'); expiry: MATCH 1.00 | decoded, match True | Weak or missing evidence: model, lot. Rescan or check by eye. | BLIND_MODE, LABEL_NOT_FOUND, PHOTO_OCR, LOW_OCR_CONFIDENCE, FIELD_MISSING |
| clean | 7006 | product_name: MATCH 1.00; manufacturer: MATCH 1.00; manufacturer_address: MATCH 1.00; model: NEEDS_HUMAN_REVIEW none (read None); lot: NEEDS_HUMAN_REVIEW none (read '2'); expiry: MATCH 1.00 | decoded, match True | Weak or missing evidence: model, lot. Rescan or check by eye. | BLIND_MODE, LABEL_NOT_FOUND, PHOTO_OCR, LOW_OCR_CONFIDENCE, FIELD_MISSING |
| clean | 7007 | product_name: MATCH 1.00; manufacturer: MATCH 1.00; manufacturer_address: MATCH 1.00; model: NEEDS_HUMAN_REVIEW none (read None); lot: NEEDS_HUMAN_REVIEW none (read '2'); expiry: MATCH 1.00 | decoded, match True | Weak or missing evidence: model, lot. Rescan or check by eye. | BLIND_MODE, LABEL_NOT_FOUND, PHOTO_OCR, LOW_OCR_CONFIDENCE, FIELD_MISSING |
| moderate | 7000 | product_name: MATCH 1.00; manufacturer: MATCH 1.00; manufacturer_address: MATCH 1.00; model: NEEDS_HUMAN_REVIEW none (read None); lot: NEEDS_HUMAN_REVIEW none (read '2'); expiry: MATCH 1.00 | decoded, match True | Weak or missing evidence: model, lot. Rescan or check by eye. | BLIND_MODE, PHOTO_OCR, LOW_OCR_CONFIDENCE, OCR_BLOCKS_IGNORED, FIELD_MISSING |
| moderate | 7001 | product_name: MATCH 1.00; manufacturer: MATCH 1.00; manufacturer_address: MATCH 0.99; model: NEEDS_HUMAN_REVIEW none (read None); lot: NEEDS_HUMAN_REVIEW none (read '2'); expiry: MATCH 1.00 | decoded, match True | Weak or missing evidence: model, lot. Rescan or check by eye. | BLIND_MODE, PHOTO_OCR, LOW_OCR_CONFIDENCE, OCR_BLOCKS_IGNORED, FIELD_MISSING |
| moderate | 7002 | product_name: MATCH 1.00; manufacturer: MATCH 1.00; manufacturer_address: MATCH 1.00; model: NEEDS_HUMAN_REVIEW none (read None); lot: NEEDS_HUMAN_REVIEW 0.19 (read '2'); expiry: MATCH 1.00 | decoded, match True | Weak or missing evidence: model, lot. Rescan or check by eye. | BLIND_MODE, PHOTO_OCR, LOW_OCR_CONFIDENCE, FIELD_MISSING |
| moderate | 7003 | product_name: MATCH 1.00; manufacturer: MATCH 1.00; manufacturer_address: MATCH 1.00; model: NEEDS_HUMAN_REVIEW none (read None); lot: NEEDS_HUMAN_REVIEW none (read '2'); expiry: MATCH 1.00 | decoded, match True | Weak or missing evidence: model, lot. Rescan or check by eye. | BLIND_MODE, PHOTO_OCR, LOW_OCR_CONFIDENCE, OCR_BLOCKS_IGNORED, FIELD_MISSING |
| moderate | 7004 | product_name: MATCH 1.00; manufacturer: MATCH 1.00; manufacturer_address: MATCH 0.99; model: NEEDS_HUMAN_REVIEW none (read None); lot: NEEDS_HUMAN_REVIEW none (read '2'); expiry: MATCH 1.00 | decoded, match True | Weak or missing evidence: model, lot. Rescan or check by eye. | BLIND_MODE, PHOTO_OCR, LOW_OCR_CONFIDENCE, FIELD_MISSING |
| moderate | 7005 | product_name: MATCH 1.00; manufacturer: MATCH 1.00; manufacturer_address: MATCH 1.00; model: NEEDS_HUMAN_REVIEW none (read None); lot: NEEDS_HUMAN_REVIEW none (read '2'); expiry: MATCH 1.00 | decoded, match True | Weak or missing evidence: model, lot. Rescan or check by eye. | BLIND_MODE, PHOTO_OCR, LOW_OCR_CONFIDENCE, OCR_BLOCKS_IGNORED, FIELD_MISSING |
| moderate | 7006 |  | none decoded | Photo quality: glare. Retake it. |  |
| moderate | 7007 | product_name: MATCH 1.00; manufacturer: MATCH 1.00; manufacturer_address: MATCH 1.00; model: NEEDS_HUMAN_REVIEW none (read None); lot: NEEDS_HUMAN_REVIEW none (read '2'); expiry: MATCH 1.00 | decoded, match True | Weak or missing evidence: model, lot. Rescan or check by eye. | BLIND_MODE, PHOTO_OCR, LOW_OCR_CONFIDENCE, OCR_BLOCKS_IGNORED, FIELD_MISSING |
| hard | 7000 | product_name: MATCH 1.00; manufacturer: MATCH 1.00; manufacturer_address: MATCH 0.99; model: NEEDS_HUMAN_REVIEW none (read None); lot: NEEDS_HUMAN_REVIEW none (read '2'); expiry: MATCH 1.00 | decoded, match True | Weak or missing evidence: model, lot. Rescan or check by eye. | BLIND_MODE, PHOTO_OCR, LOW_OCR_CONFIDENCE, FIELD_MISSING |
| hard | 7002 | product_name: MATCH 1.00; manufacturer: MATCH 1.00; manufacturer_address: MATCH 0.98; model: NEEDS_HUMAN_REVIEW none (read None); lot: NEEDS_HUMAN_REVIEW none (read '2'); expiry: MATCH 1.00 | decoded, match True | Weak or missing evidence: model, lot. Rescan or check by eye. | BLIND_MODE, SYMBOL_NOT_DETECTED, PHOTO_OCR, LOW_OCR_CONFIDENCE, OCR_BLOCKS_IGNORED, FIELD_MISSING |
| hard | 7003 | product_name: MATCH 1.00; manufacturer: MATCH 1.00; manufacturer_address: MATCH 1.00; model: NEEDS_HUMAN_REVIEW none (read None); lot: NEEDS_HUMAN_REVIEW none (read '2'); expiry: MATCH 1.00 | decoded, match True | Weak or missing evidence: model, lot. Rescan or check by eye. | BLIND_MODE, PHOTO_OCR, LOW_OCR_CONFIDENCE, FIELD_MISSING |
| hard | 7004 | product_name: MATCH 1.00; manufacturer: MATCH 1.00; manufacturer_address: MATCH 1.00; model: NEEDS_HUMAN_REVIEW none (read None); lot: NEEDS_HUMAN_REVIEW none (read '2'); expiry: MATCH 1.00 | decoded, match True | Weak or missing evidence: model, lot. Rescan or check by eye. | BLIND_MODE, PHOTO_OCR, LOW_OCR_CONFIDENCE, FIELD_MISSING |
| hard | 7005 | product_name: MATCH 1.00; manufacturer: MATCH 1.00; manufacturer_address: MATCH 1.00; model: NEEDS_HUMAN_REVIEW none (read None); lot: NEEDS_HUMAN_REVIEW none (read '2'); expiry: MATCH 1.00 | decoded, match True | Weak or missing evidence: model, lot. Rescan or check by eye. | BLIND_MODE, PHOTO_OCR, LOW_OCR_CONFIDENCE, FIELD_MISSING |
| hard | 7006 | product_name: MATCH 1.00; manufacturer: MATCH 1.00; manufacturer_address: MATCH 1.00; model: NEEDS_HUMAN_REVIEW none (read None); lot: NEEDS_HUMAN_REVIEW none (read '2'); expiry: MATCH 1.00 | decoded, match True | Weak or missing evidence: model, lot. Rescan or check by eye. | BLIND_MODE, PHOTO_OCR, LOW_OCR_CONFIDENCE, OCR_BLOCKS_IGNORED, FIELD_MISSING |
| hard | 7007 | product_name: MATCH 0.98; manufacturer: MATCH 1.00; manufacturer_address: MATCH 1.00; model: NEEDS_HUMAN_REVIEW none (read None); lot: NEEDS_HUMAN_REVIEW none (read '2'); expiry: MATCH 1.00 | decoded, match True | Weak or missing evidence: model, lot. Rescan or check by eye. | BLIND_MODE, PHOTO_OCR, LOW_OCR_CONFIDENCE, FIELD_MISSING |

## Cause counts (one per rescan and failing item)

- model NEEDS_HUMAN_REVIEW (no evidence): 22
- warning BLIND_MODE: 22
- warning PHOTO_OCR: 22
- warning LOW_OCR_CONFIDENCE: 22
- warning FIELD_MISSING: 22
- lot NEEDS_HUMAN_REVIEW (no evidence): 21
- warning LABEL_NOT_FOUND: 8
- warning OCR_BLOCKS_IGNORED: 7
- lot NEEDS_HUMAN_REVIEW (low conf): 1
- barcode not decoded: 1
- warning SYMBOL_NOT_DETECTED: 1
