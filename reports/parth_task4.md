# Parth Task 4: clear three-field photo replacement

## 1. What I did
Searched again and downloaded 29 candidate images; one additional URL failed. Inspected each image and accepted ten device-package photographs with product name, lot and expiry visibly readable together. Froze 30 LLM-labelled readings before OCR. Kept the old set and baseline separate, and preserved the new original bytes.

## 2. Files created or changed
- Local `data/real_photos/clear_online/`: ten photos, transcriptions.csv, annotations.json and a clickable REVIEW.md.
- `data/real/SOURCES.md`: source pages, image URLs, fingerprints, values and selection decisions.
- Photo README: preferred input folder and command.
- `results/cv_real_photos_clear.md`: separate clear-set results and actual output.
- This report and learning log: checks and limitations. Application code is unchanged.

## 3. How it works
Every accepted image contains all three printed fields. REF/model codes and manufacture dates are not substituted for lot and expiry. For example, Braisorb's lot is 009, not its reference BRRUP130. Dates keep their printed form. All photos and reference files remain ignored local data.

## 4. How I verified it
Verified ten distinct file fingerprints and 30 nonblank references against the frozen annotations. Actual evaluation:
```text
/opt/anaconda3/envs/labellens-cv/bin/python -m src.cv.eval_real --folder data/real_photos/clear_online --reference-source LLM-labelled --report results/cv_real_photos_clear.md
```
Actual field-output excerpt; complete output is in the results report:
```text
product_name | 10 | 1/10 | 83.42% (161/193)
lot | 10 | 0/10 | 100.00% (78/78)
expiry | 10 | 0/10 | 100.00% (93/93)
```
```text
/opt/anaconda3/envs/labellens-cv/bin/python -m pytest -q -p no:cacheprovider -m "not slow"
........................................................................ [ 19%]
........................................................................ [ 38%]
........................................................................ [ 57%]
........................................................................ [ 76%]
........................................................................ [ 95%]
................                                                         [100%]
376 passed, 3 deselected in 77.03s (0:01:17)

/opt/anaconda3/envs/labellens-cv/bin/python -m ruff check --no-cache src tests scripts/real
All checks passed!
```

## 5. What you should check yourself
Open clear_online/REVIEW.md and compare each field with the original image. Spot-check photos 01, 04 and 08. Confirm images are not staged.

## 6. What I am unsure about or assumed
Visibility is AI-inspected; human review is NOT_RUN. Photos are selected retail/catalog views with related families, not a representative benchmark. Extraction still needs fixing despite readable inputs. No model accuracy improvement is claimed. Image licenses are not established, so binaries stay local.
