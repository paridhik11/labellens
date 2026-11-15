# Parth Task 4: photo-input procedure, awaiting photos

## 1. What I did
Aligned the photo instructions with Paridhi's clarification. The agent will transcribe three fields in-session and label them LLM-labelled, then Parth will spot-check three photos. Confirmed the evaluator already reads transcriptions.csv, so no filename change is needed in the script.

## 2. Files changed
`data/real_photos/README.md`: capture, CSV, label provenance and spot-check procedure. This report and `docs/LEARNING_LOG.md`: input status and limits.

## 3. How it works
The CSV has filename, product_name, lot and expiry only. A separate local annotations.json records module, LLM-labelled origin, uncertainty and actual human spot-check feedback. Extra metadata columns are not added to the CSV because the evaluator would score them as label fields. Medicine and device photos must be evaluated separately.

## 4. How I verified it
```text
/opt/anaconda3/envs/labellens-cv/bin/python -m src.cv.eval_real
No real photos to evaluate: add photos and transcriptions.csv to data/real_photos (see its README.md).
```
A direct folder check found 0 supplied photos. No real-photo OCR or accuracy calculation was run.

## 5. What to check yourself
Capture about 10 actual phone photos. After in-session transcription, check three photos and identify wrong fields. Review that transcriptions.csv has only the four expected columns and that AI origin remains explicit.

## 6. Assumptions and remaining work
Task 4 is not complete. Physical captures must come from Parth; the coding agent cannot take them. Human spot-check result is NOT_RUN, not zero errors. Counts and error rates will be reported only after photos and actual human feedback are supplied.
