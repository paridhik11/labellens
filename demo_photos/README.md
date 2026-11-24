# Demo photo set

Photos for trying LabelLens before presenting. **These are DailyMed package artwork with simulated camera conditions (clean, moderate, hard), not real phone photos.** The medicine images are copies of images used in the NDC scan evaluation (`results/ndc_scan/`); the originals are untouched. The device images are made from `golden/golden_label.pdf` by `make_device_images.py` (a label on a grey desk, and a blurred copy). Everything was run through the real app, one photo at a time, nothing else running; exact clicks and seconds are in `RUN_LOG.md`.

## Public medicine mode (`/ui/public/index.html`)

Route: click **Upload a photo**, choose the file, wait (up to a minute), read the result. A photo never confirms by itself: click **Confirm** to see the label.

| file | what it shows | expected result | time (quiet PC) |
|---|---|---|---|
| `public/01_clean_ndc_famotidine.jpg` | clean artwork, NDC barcode and printed NDC both in the 30-product table | "Is this FAMOTIDINE? We read NDC barcode ..." then Confirm shows the label | 3 s |
| `public/02_ndc_moderate_rosuvastatin.jpg` | moderate camera condition, printed NDC in the table | "Is this Rosuvastatin Calcium? We read NDC printed line 69367035930" | 25 s |
| `public/03_ndc_hard_rosuvastatin.jpg` | hard camera condition, same product | same answer as 02 | 17 s |
| `public/04_barcode_aspirin.jpg` | the NDC barcode decides | "Is this Aspirin? We read NDC barcode 46122059602" | 3 s |
| `public/05_barcode_metformin.jpg` | the NDC barcode decides | "Is this METFORMIN HYDROCHLORIDE? ..." | 3 s |
| `public/06_name_prednisone.jpg` | no NDC, found by name matching | "Is this PredniSONE? We read Prednisone Tablets" | 25 s |
| `public/07_live_pregabalin.jpg` | not one of the 30 curated medicines, but on DailyMed | "Not identified"; type `pregabalin`, click **Find**, **Search DailyMed**, **Select** the first: "Fetched live from DailyMed, not in the curated set" | 19 s (cached) |
| `public/08_live_zetia.jpg` | same, brand name | "Not identified"; type `Zetia`, **Find**, **Search DailyMed**, **Select**: live label shown | 23 s (cached) |
| `public/09_decoy_amitriptyline.jpg` | decoy: product not in the corpus | "Not identified. This product is not one of the reference labels, so no summary is shown." | 12 s |
| `public/10_decoy_carvedilol.jpg` | decoy | "Not identified. No readable text was found. Retake the photo closer, or type the name." | 15 s |
| `public/11_bonus_review_aripiprazole.jpg` | bonus decoy: needs review | "Is this your product? ... close to the reference labels below but not certain" with one wrong candidate (FUROSEMIDE 73%) you can refuse; nothing is confirmed | 25 s |

## Professional device mode (`/ui/pro/index.html`)

Route: click **2 Add label**, **Choose PDF or image**, pick the file, click **Read label**.

| file | what it shows | expected result | time |
|---|---|---|---|
| `device/01_golden_label.pdf` | the golden label | name, manufacturer, address, model GP-100, lot, expiry, UDI-DI (TEST), serial all filled; "What the regulations require" 5 of 5 found | 14 s |
| `device/02_golden_photo_clean.jpg` | the same label photographed on a desk | everything filled except the name, which is read wrongly (`cl XxX`); `Golden Pump` is under "Other text read", pick **Product name** to fix it | 20 s |
| `device/03_golden_blurry.jpg` | blurred copy | refused: "The photo is too blurry to read ... (reasons: blur)", no label is created | 2 s |

## How to run before presenting
1. Open a terminal in the repo and start the server with Tesseract on the PATH: `$env:PATH += ";C:\Program Files\Tesseract-OCR"; .venv312\Scripts\python.exe scripts/run_demo.py`. Wait for "LabelLens demo http://127.0.0.1:8000" and check the line that says Tesseract was found.
2. Close everything else that is heavy (other test runs, builds, many browser tabs): with a loaded PC the reader takes 45 to 55 s and times out.
3. Open the page and press Ctrl+F5 so the browser loads the newest files.
4. Public: `/ui/public/index.html`, **Upload a photo**. Professional: `/ui/pro/index.html`, **2 Add label**, **Choose PDF or image**, **Read label**.
5. Wait up to a minute for a result and do not double click; the page shows a counter while it reads.
6. Run photos 07 and 08 once before you present: the first DailyMed fetch of a label downloads and indexes it (30 s to 2 minutes), later ones take a few seconds.

## Limits
- LLM and software judged only; no human checked the readings. Times are from one PC on one day.
- Photos 01, 04 and 05 are decided by the NDC barcode in 3 s; the others need the slow text reader.
- Clean artwork photos that rely on text only (no barcode) were too slow or were refused by the photo gate for glare, so the "clean" example is Famotidine, which a barcode decides. See the replacements in `RUN_LOG.md`.
