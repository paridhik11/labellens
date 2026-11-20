# Real photo evaluation

Reference source: LLM-labelled.
Condition: photograph. Mode: blind, with post-correction.
Human three-photo spot-check: NOT_RUN. Results against AI references are provisional.

Photos found: 12.

| Photo | Extraction status | Field | Reference | Observed | Exact match |
|---|---|---|---|---|---|
| online_01.jpg | no readable reference fields, skipped | product_name | not transcribed |  | not scored |
| online_01.jpg | no readable reference fields, skipped | lot | not transcribed |  | not scored |
| online_01.jpg | no readable reference fields, skipped | expiry | not transcribed |  | not scored |
| online_02.jpg | no readable reference fields, skipped | product_name | not transcribed |  | not scored |
| online_02.jpg | no readable reference fields, skipped | lot | not transcribed |  | not scored |
| online_02.jpg | no readable reference fields, skipped | expiry | not transcribed |  | not scored |
| online_03.jpg | no readable reference fields, skipped | product_name | not transcribed |  | not scored |
| online_03.jpg | no readable reference fields, skipped | lot | not transcribed |  | not scored |
| online_03.jpg | no readable reference fields, skipped | expiry | not transcribed |  | not scored |
| online_04.jpg | ok | product_name | not transcribed | 3G18258D04 | not scored |
| online_04.jpg | ok | lot | 3G 18258D04 |  | no |
| online_04.jpg | ok | expiry | not transcribed |  | not scored |
| online_05.jpg | ok | product_name | 复诊盒 | 【生产日期】 | no |
| online_05.jpg | ok | lot | not transcribed |  | not scored |
| online_05.jpg | ok | expiry | 2019-10-23 |  | no |
| online_06.jpg | ok | product_name | MELAfol® 502 | MELAGMEA | no |
| online_06.jpg | ok | lot | not transcribed |  | not scored |
| online_06.jpg | ok | expiry | not transcribed |  | not scored |
| online_07.jpg | no readable reference fields, skipped | product_name | not transcribed |  | not scored |
| online_07.jpg | no readable reference fields, skipped | lot | not transcribed |  | not scored |
| online_07.jpg | no readable reference fields, skipped | expiry | not transcribed |  | not scored |
| online_08.jpg | no readable reference fields, skipped | product_name | not transcribed |  | not scored |
| online_08.jpg | no readable reference fields, skipped | lot | not transcribed |  | not scored |
| online_08.jpg | no readable reference fields, skipped | expiry | not transcribed |  | not scored |
| online_09.jpg | ok | product_name | STERIKING | 18mmEN85 | no |
| online_09.jpg | ok | lot | not transcribed |  | not scored |
| online_09.jpg | ok | expiry | not transcribed |  | not scored |
| online_10.png | ok | product_name | ШПРИЦ | HPWL | no |
| online_10.png | ok | lot | not transcribed |  | not scored |
| online_10.png | ok | expiry | not transcribed |  | not scored |
| online_11.jpg | ok | product_name | ARS® | GAMV | no |
| online_11.jpg | ok | lot | not transcribed |  | not scored |
| online_11.jpg | ok | expiry | 2022-06 | :2024 | no |
| online_12.jpg | ok | product_name | ARS® |  | no |
| online_12.jpg | ok | lot | not transcribed |  | not scored |
| online_12.jpg | ok | expiry | 2022-06 |  | no |

| Field | Scored photos | Exact matches | Character errors |
|---|---|---|---|
| lot | 1 | 0/1 | 11/11 |
| product_name | 6 | 0/6 | 36/37 |
| expiry | 3 | 0/3 | 22/24 |

Blank, absent and unreadable reference fields are not scored. Extraction failures count as misses for every readable reference field.

## Input scope and limitations

Parth confirmed on 2026-11-16 that Paridhi accepted online-photo substitution.
Twelve licensed online photos were inspected: five original files and seven
1280-pixel-wide server thumbnails. The exact download URL and SHA-256 for each
evaluated representation are recorded in data/real/SOURCES.md. Inputs, four-column
transcriptions.csv and LLM-labelled annotations.json remain local in
data/real_photos/online/. References were frozen before OCR; no values were filled
from filenames, product descriptions, source artwork or detector output.

Seven photos have ten readable reference values; five have no reliable target
fields and are skipped. Inputs 06 and 09 are sterilization-packaging accessories,
not finished-device labels: their product-name result is 0/2. Excluding those two,
product name is 0/4, lot 0/1, expiry 0/3. These subgroup counts follow directly
from the per-photo comparisons above. No medicine photos are included.

Inputs 05 and 10 contain Chinese and Russian respectively. Inputs 11/12 are
correlated views of the same needle-kit pair, not independent products. The lot
photo has ambiguous dual dates, which remain untranscribed. This convenience
sample and its AI references do not establish representative device accuracy.

The baseline misses all readable fields exactly. Inspection suggests incorrect
region/field selection as well as text-recognition errors. No pipeline tuning was
performed against these reference values. Three-photo human review is pending;
NOT_RUN is not zero errors. The requested review covers photos 04, 06 and 12,
with four transcribed values total.

## Recorded evaluation standard output

```text
Reference source: LLM-labelled.
Real photos found: 12. Mode: blind, with post-correction.
  online_01.jpg: no readable reference fields, skipped
  online_02.jpg: no readable reference fields, skipped
  online_03.jpg: no readable reference fields, skipped
  online_04.jpg: ok, barcodes decoded: 0
  online_05.jpg: ok, barcodes decoded: 0
  online_06.jpg: ok, barcodes decoded: 0
  online_07.jpg: no readable reference fields, skipped
  online_08.jpg: no readable reference fields, skipped
  online_09.jpg: ok, barcodes decoded: 0
  online_10.png: ok, barcodes decoded: 0
  online_11.jpg: ok, barcodes decoded: 0
  online_12.jpg: ok, barcodes decoded: 0
Field | photos | exact matches | character error rate (edits / characters)
lot | 1 | 0/1 | 100.00% (11/11)
product_name | 6 | 0/6 | 97.30% (36/37)
expiry | 3 | 0/3 | 91.67% (22/24)
Per-photo field comparisons saved to results/cv_real_photos.md.
```
