# Run log (real app, one photo at a time)

Server: `scripts/run_demo.py --port 8030 --no-golden`, `C:\Program Files\Tesseract-OCR` on PATH, headless Chrome driven by a script that does exactly the clicks listed. Times are seconds from choosing the file to the result panel, on a quiet machine (nothing else running). One run per photo; the final pass is the one recorded here.

| file | clicks | result | seconds |
|---|---|---|---|
| 01_clean_ndc_famotidine.jpg | click "Upload a photo"; choose 01_clean_ndc_famotidine.jpg; click "Confirm" | ? Is this FAMOTIDINE? We read NDC barcode 81033002350 on the pack and it matches the reference label for FAMOTIDINE. Check it against your p | 2.7 |
| 02_ndc_moderate_rosuvastatin.jpg | click "Upload a photo"; choose 02_ndc_moderate_rosuvastatin.jpg; click "Confirm" | ? Is this Rosuvastatin Calcium? We read NDC printed line 69367035930 on the pack and it matches the reference label for Rosuvastatin Calcium | 24.8 |
| 03_ndc_hard_rosuvastatin.jpg | click "Upload a photo"; choose 03_ndc_hard_rosuvastatin.jpg; click "Confirm" | ? Is this Rosuvastatin Calcium? We read NDC printed line 69367035930 on the pack and it matches the reference label for Rosuvastatin Calcium | 16.5 |
| 04_barcode_aspirin.jpg | click "Upload a photo"; choose 04_barcode_aspirin.jpg; click "Confirm" | ? Is this Aspirin? We read NDC barcode 46122059602 on the pack and it matches the reference label for Aspirin. Check it against your pack be | 2.6 |
| 05_barcode_metformin.jpg | click "Upload a photo"; choose 05_barcode_metformin.jpg; click "Confirm" | ? Is this METFORMIN HYDROCHLORIDE? We read NDC barcode 82804030978 on the pack and it matches the reference label for METFORMIN HYDROCHLORID | 2.7 |
| 06_name_prednisone.jpg | click "Upload a photo"; choose 06_name_prednisone.jpg; click "Confirm" | ? Is this PredniSONE? We read Prednisone Tablets on the pack and it matches the reference label for PredniSONE. Check it against your pack b | 24.8 |
| 07_live_pregabalin.jpg | click "Upload a photo"; choose 07_live_pregabalin.jpg; type "pregabalin" in "Medicine name"; click "Find"; click "Search DailyMed"; click "Select" on the first candidate | photo: Not identified; then live DailyMed: PREGABALIN CAPSULE PREFERRED PHARMACEUTICALS, INC. Label upd ... label shown: i Fetched live from DailyMed, not in the curated set DailyMed set id 1 | 19.3 (photo 13.3, live label 2.1) |
| 08_live_zetia.jpg | click "Upload a photo"; choose 08_live_zetia.jpg; type "Zetia" in "Medicine name"; click "Find"; click "Search DailyMed"; click "Select" on the first candidate | photo: Not identified; then live DailyMed: ZETIA EZETIMIBE | tablet | ORGANON LLC Label updated Nov 18, ... label shown: i Fetched live from DailyMed, not in the curated set DailyMed set id 1 | 23 (photo 17, live label 2.0) |
| 09_decoy_amitriptyline.jpg | click "Upload a photo"; choose 09_decoy_amitriptyline.jpg | i Not identified This product is not one of the reference labels, so no summary is shown. You can type the name instead. | 12.4 |
| 10_decoy_carvedilol.jpg | click "Upload a photo"; choose 10_decoy_carvedilol.jpg | i Not identified No readable text was found. Retake the photo closer, or type the name. | 15 |
| 11_bonus_review_aripiprazole.jpg | click "Upload a photo"; choose 11_bonus_review_aripiprazole.jpg | "Is this your product? We read RX ONLY ... Candidate reference labels (1): FUROSEMIDE 73% ... Select" (needs review, nothing confirmed) | 25 |

## Professional page (`/ui/pro/index.html`)

| file | clicks | result | seconds |
|---|---|---|---|
| device/01_golden_label.pdf | click "2 Add label"; click "Choose PDF or image" and pick the file; click "Read label" | read: name Golden Pump, manufacturer Demo Labs, address 12 Demo Road, model GP-100 (recovered from the unassigned line), lot LOT1, expiry 2030-06-30, UDI-DI 00000000000000 (TEST), serial SN1; required panel 5 of 5 found; sterilization and storage empty (the label does not print them) | 14.4 |
| device/02_golden_photo_clean.jpg | same | read: manufacturer, address, model, lot, expiry, UDI-DI, serial right; **name wrong (`cl XxX`)**, `Golden Pump` is listed under "Other text read"; required panel 5 of 5 found | 19.5 |
| device/03_golden_blurry.jpg | same | refused: `retake_photo: The photo is too blurry to read. Hold the camera steady and focus on the label. (reasons: blur)`; no label version is created | 2.1 |

## Replacements and failures during the runs

- First picks that failed or were flaky, and what replaced them: Furosemide clean photo (timed out three times at 50 to 53 s, while two other programs were loading the machine) and Furosemide hard (timed out once); a valsartan clean photo (passed once at 51.2 s, timed out the next time at 51.9 s); Rosuvastatin clean photos (refused by the photo gate for glare, twice); Clonidine hard (31 s once, 53 s timeout the next time); Mirtazapine photos (timed out, or glare retake). Replaced by the files in this folder, each of which passed in the final quiet pass.
- Why the times moved: the first passes ran while a stray search process of mine and, later, another test run on the same PC were using the CPU (reads took 45 to 55 s and hit the app's 50 s reader limit). After they ended the same photos took 2 to 25 s. Run nothing else while you present.
- Cold live lookup: the first fetch of a DailyMed label downloads and indexes it. Pregabalin took about 131 s the first time (under load), Zetia about 34 s. Both are cached now (2 to 4 s); a cache on another PC or a fresh database is cold again, so run each live photo once before presenting.
- Not changed: no code, score, threshold or evaluation result was touched. The photos are copies; the originals are in `../labellens-publicscan/data/public_scan_real/photos/` and are unchanged.
