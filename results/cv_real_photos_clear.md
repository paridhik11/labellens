# Real photo evaluation

Reference source: LLM-labelled.
Condition: photograph. Mode: blind, with post-correction.
Human three-photo spot-check: NOT_RUN. Results against AI references are provisional.

Photos found: 10.

| Photo | Extraction status | Field | Reference | Observed | Exact match |
|---|---|---|---|---|---|
| clear_01_crylrex.jpg | ok | product_name | CRYLREX | CRYLREX | yes |
| clear_01_crylrex.jpg | ok | lot | 2201KS517 |  | no |
| clear_01_crylrex.jpg | ok | expiry | 2027-01 |  | no |
| clear_02_braisorb.jpg | ok | product_name | Braisorb | aisorb | no |
| clear_02_braisorb.jpg | ok | lot | 009 |  | no |
| clear_02_braisorb.jpg | ok | expiry | 12/2024 |  | no |
| clear_03_cranberry.jpg | ok | product_name | APÓSITO ADHESIVO TRANSPARENTE | Cranberry | no |
| clear_03_cranberry.jpg | ok | lot | PC-18796 |  | no |
| clear_03_cranberry.jpg | ok | expiry | AGOS-2026 |  | no |
| clear_04_cook_airway.jpg | ok | product_name | Cook Airway Exchange Catheter | COOK` | no |
| clear_04_cook_airway.jpg | ok | lot | 6903756 |  | no |
| clear_04_cook_airway.jpg | ok | expiry | 2019-04-20 |  | no |
| clear_05_stratafix.jpg | ok | product_name | Stratafix™ | Stratafik- | no |
| clear_05_stratafix.jpg | ok | lot | RJMCHQ |  | no |
| clear_05_stratafix.jpg | ok | expiry | 2023-07-31 |  | no |
| clear_06_medtronic_introducer.jpg | ok | product_name | Percutaneous Lead Introducer | pePeadzadmlzastaa | no |
| clear_06_medtronic_introducer.jpg | ok | lot | GB6979375 | number | no |
| clear_06_medtronic_introducer.jpg | ok | expiry | 2024-01-19 |  | no |
| clear_07_introcan_safety.jpg | ok | product_name | Introcan Safety® IV Catheter | 200 | no |
| clear_07_introcan_safety.jpg | ok | lot | 22B25G8316 |  | no |
| clear_07_introcan_safety.jpg | ok | expiry | 2027-02-01 |  | no |
| clear_08_introcan_safety2.jpg | ok | product_name | Introcan Safety® 2 IV Catheter | 200 | no |
| clear_08_introcan_safety2.jpg | ok | lot | 23H17G8271 |  | no |
| clear_08_introcan_safety2.jpg | ok | expiry | 2028-08-01 |  | no |
| clear_09_introcan.jpg | ok | product_name | Introcan® | TKaHAyA | no |
| clear_09_introcan.jpg | ok | lot | 23C11G8361 |  | no |
| clear_09_introcan.jpg | ok | expiry | 2028-03-01 |  | no |
| clear_10_ethibond.jpg | ok | product_name | ETHIBOND EXCEL™ | EXCELW | no |
| clear_10_ethibond.jpg | ok | lot | MAK729 |  | no |
| clear_10_ethibond.jpg | ok | expiry | 2022-12-31 |  | no |

| Field | Scored photos | Exact matches | Character errors |
|---|---|---|---|
| product_name | 10 | 1/10 | 161/193 |
| lot | 10 | 0/10 | 78/78 |
| expiry | 10 | 0/10 | 93/93 |

Blank, absent and unreadable reference fields are not scored. Extraction failures count as misses for every readable reference field.

## Clear-set provenance and scope

This run uses the ten replacement photos selected for visibly readable product
name, lot/batch and expiry in the same image. Thirty candidate downloads were
attempted, 29 photos inspected and ten accepted. Selection and all 30 references
were frozen before this run; no extraction result was used to choose images.
The previous online-photo baseline remains in results/cv_real_photos.md and
uses a different cohort. This is not evidence of a model improvement.

The original evaluated photo bytes are unchanged. Their source URLs, dimensions,
file fingerprints, rights status and exact field readings are recorded in
data/real/SOURCES.md. Images, transcriptions.csv, annotations.json and REVIEW.md
remain local in data/real_photos/clear_online/. No medicine images are included.
Four photos show sutures, five show catheters or a lead introducer, and one
shows a wound dressing. Three Introcan products share one B. Braun family;
two sutures share an Ethicon family. These selected catalog/retail photographs
are a development set and do not establish representative phone-photo accuracy.

All three reference fields are visually readable in every accepted image,
according to AI inspection. References are LLM-labelled, not human truth.
Month-only and Spanish dates retain the printed format. Manufacturer printed
expiry fields are used instead of reseller handwriting or added stickers.
Trademark glyphs are transcribed and product-name line breaks are joined with
spaces. Human three-photo spot-check is NOT_RUN, not zero errors.

The extractor remains poor on this clear set: exact name 1/10, lot 0/10, expiry
0/10. A decoded barcode is not necessarily a correct extracted text field.
No model, field mapper, normalization rule or barcode parser was changed or
tuned during this collection step. No 80% accuracy claim is supported.

Frozen reference CSV SHA-256: `c7d7eb4254497acd2edfa091918832a688e1c5953f199707b7a25cd4a292c857`.

## Recorded evaluation standard output

```text
Reference source: LLM-labelled.
Real photos found: 10. Mode: blind, with post-correction.
  clear_01_crylrex.jpg: ok, barcodes decoded: 1
  clear_02_braisorb.jpg: ok, barcodes decoded: 0
  clear_03_cranberry.jpg: ok, barcodes decoded: 0
  clear_04_cook_airway.jpg: ok, barcodes decoded: 2
  clear_05_stratafix.jpg: ok, barcodes decoded: 1
  clear_06_medtronic_introducer.jpg: ok, barcodes decoded: 2
  clear_07_introcan_safety.jpg: ok, barcodes decoded: 1
  clear_08_introcan_safety2.jpg: ok, barcodes decoded: 1
  clear_09_introcan.jpg: ok, barcodes decoded: 1
  clear_10_ethibond.jpg: ok, barcodes decoded: 0
Field | photos | exact matches | character error rate (edits / characters)
product_name | 10 | 1/10 | 83.42% (161/193)
lot | 10 | 0/10 | 100.00% (78/78)
expiry | 10 | 0/10 | 100.00% (93/93)
Per-photo field comparisons saved to results/cv_real_photos_clear.md.
```
