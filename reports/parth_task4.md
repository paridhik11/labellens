# Parth Task 4: online-photo baseline, human review pending

## 1. What I did
Used online photos after Parth confirmed Paridhi accepted the substitution. Inspected 12 photos and froze ten readable field values across seven images as LLM-labelled references before OCR. Left absent, unreadable and ambiguous values blank; five images are unscored. Saved every requested field's comparison, including misses.

## 2. Files created or changed
- `src/cv/eval_real.py`: per-photo report, reference provenance and explicit blank-reference skips.
- `tests/test_real_photo_report.py`: report escaping, failure denominators and skipped fields.
- `data/real/SOURCES.md` and photo README: accepted substitution, evaluated download URLs, fingerprints and limits.
- `results/cv_real_photos.md`: actual results and complete standard output.
- This report and learning log: status and checks. Photos, CSV and annotations remain local.

## 3. How it works
OCR means reading text from pixels. References were read visually before OCR, then exact text was compared field by field. Blank references cannot become successes. The two needle-kit views are correlated; two accessory images and two non-English labels are identified separately. Five files are originals; seven are 1280-pixel server thumbnails recommended after original-download HTTP 429 responses.

## 4. How I verified it
```text
/opt/anaconda3/envs/labellens-cv/bin/python -m src.cv.eval_real --folder data/real_photos/online --reference-source LLM-labelled --report results/cv_real_photos.md
```
Actual field-output excerpt; full output is in the results file:
```text
lot | 1 | 0/1 | 100.00% (11/11)
product_name | 6 | 0/6 | 97.30% (36/37)
expiry | 3 | 0/3 | 91.67% (22/24)
```
```text
/opt/anaconda3/envs/labellens-cv/bin/python -m pytest -q -p no:cacheprovider -m "not slow"
........................................................................ [ 19%]
........................................................................ [ 38%]
........................................................................ [ 57%]
........................................................................ [ 76%]
........................................................................ [ 95%]
................                                                         [100%]
376 passed, 3 deselected in 37.57s

/opt/anaconda3/envs/labellens-cv/bin/python -m ruff check --no-cache src tests scripts/real
All checks passed!
```

## 5. What you should check yourself
Review photos 04, 06 and 12 against the four requested AI readings. Inspect each field mismatch and the thumbnail/source distinctions.

## 6. What I am unsure about or assumed
The real-photo baseline is poor; region/field selection and recognition need further work. These are provisional AI-reference results, not validated device accuracy. Human spot-check is NOT_RUN; Task 4 is not fully complete. No detector tuning, invented references or new dependencies were added.
