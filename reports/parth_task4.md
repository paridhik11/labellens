# Parth Task 4: online photo candidates, capture benchmark pending

## 1. What I did
Found ten online medical-packaging photo candidates on original Wikimedia Commons file pages. Recorded authors, photograph licenses and suitability limits. These are supplemental sources, not photos taken by Parth. No photo was admitted to the evaluation or transcribed without inspecting its original pixels.

## 2. Files created or changed
- `data/real/SOURCES.md`: ten source links, attribution, licenses and candidate exclusions.
- This report and `docs/LEARNING_LOG.md`: actual progress and outstanding inputs.

## 3. How it works
Start with the epidural-kit, curette and sterile-instrument pages. Follow their original-image links and check whether product_name, lot and expiry are readable. The epidural image has iPhone 11 metadata; other cameras are not assumed to be phones. Wrapping materials, historical Russian packaging and the related needle-holder pair may be unsuitable or dependent samples.

Use transcriptions.csv only after inspection, with filename/product_name/lot/expiry. Record LLM-labelled provenance and uncertainty separately. No human spot-check result has been invented.

## 4. How I verified it
Checked the ten original source pages and their attribution/license notices. Counted the catalog rows using:
```text
/opt/anaconda3/envs/labellens-cv/bin/python -c 'from pathlib import Path; print(Path("data/real/SOURCES.md").read_text().count("| device candidate |"))'
10
```
This verifies the number of source candidates, not ten usable evaluation photos. No Task 4 OCR run or accuracy calculation was performed. Online image binaries were not downloaded or committed.

## 5. What you should check yourself
Inspect the original-resolution fields before selecting any candidate. Confirm whether Paridhi accepts online photos as substitutes. Spot-check three actual AI transcriptions after photos are supplied and transcribed.

## 6. What I am unsure about or assumed
The original capture-and-evaluation task is incomplete. Parth's physical captures and three-photo human review remain pending. Online substitution needs Paridhi's acceptance, and original-pixel readability is still unverified. Medicine remains excluded from device evaluation. Source photograph licenses do not establish an open license for depicted company artwork.
