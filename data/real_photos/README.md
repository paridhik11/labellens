# Real phone photos and LLM-labelled transcriptions

Parth confirmed on 2026-11-16 that Paridhi accepted online photographs as
Task 4 substitutes. The preferred inputs are now in local `clear_online/`: ten device photos,
with product name, lot and expiry visually readable in every image. All 30
readings are LLM-labelled and need a human spot-check. These are selected
retail/catalog photographs, not Parth captures. Each original is unchanged;
source URLs, file fingerprints and reading decisions are in
`data/real/SOURCES.md`. `clear_online/REVIEW.md` links every photo and its values.

The older `online/` set and `results/cv_real_photos.md` baseline remain available
for comparison. Their twelve inputs include five photos with no readable
reference fields, so they are not the preferred set. Do not blend either cohort
with the other or claim that a change of dataset improved the extraction model.

This workflow follows Paridhi's clarification: the agent transcribes fields
in-session and marks them **LLM-labelled**. Parth then spot-checks three photos,
marks any wrong values and reports the result. The previous human-only
transcription instructions are superseded by this procedure.

## Capture and module separation

Keep original, unedited `.jpg`, `.jpeg` or `.png` photos. Vary angle and lighting
without replacing real captures with synthetic images. For a device evaluation,
use actual device labels. Do not mix medicine photos into its result table.
Medicine photos, if used, belong in a separate folder and a separate run with
`--folder`; that folder needs its own transcription and provenance files.

## Transcription filename and fields

The evaluator already reads **transcriptions.csv**, not labels.csv. No evaluator
filename change is necessary. Use these four columns only:

```csv
filename,product_name,lot,expiry
```

The agent reads the three fields directly from each supplied photo. Preserve
case, spaces and punctuation. For lot and expiry, omit the printed keys such as
`LOT:` and `EXP:`. Leave a value blank when it is absent or unreadable; do not
copy it from a product website, source artwork or another photo.

Do not add provenance columns to this CSV: the current evaluator treats every
additional column as another field to score. Store provenance separately in a
local `annotations.json` with, for each filename:

- module: `device` or `medicine`;
- label_source: `LLM-labelled`;
- uncertainty for each field;
- human spot-check status, reviewer and corrections, only after Parth supplies them.

AI transcriptions do not become human ground truth just because they were saved
to CSV. Keep their origin recorded after a human correction.

## Three-photo spot-check

Parth selects and checks three photos against the in-session transcriptions.
Record which photos were checked, which fields were wrong and any corrected
values. Do not fill a human reviewer name or a successful-check count without
his actual feedback. Report both photos with any error out of 3, and incorrect
fields out of the fields actually checked. Until feedback arrives, the result
is **NOT_RUN**, not zero errors.

## Evaluation

```sh
/opt/anaconda3/envs/labellens-cv/bin/python -m src.cv.eval_real \
  --folder data/real_photos/clear_online --reference-source LLM-labelled \
  --report results/cv_real_photos_clear.md
```

Without photos and transcriptions it prints that there is nothing to evaluate.
With inputs, it runs blind extraction with post-correction and reports exact
matches and character errors per field. Save the real output in the requested
report. Label any scores against AI references as LLM-reference results and
report the human spot-check separately. Keep device/medicine and real/synthetic
results separate.

New photos, transcriptions and provenance files remain local under the repository
ignore rules. Reports may contain counts and errors without publishing the photos.

The report lists each of the three requested fields for every photo. A field
without a readable reference is marked not scored, and a photo with no readable
reference fields is skipped before OCR. A failed extraction remains a miss for
its readable fields. AI reference provenance appears in both console and saved
report. Human spot-check status remains NOT_RUN until Parth supplies feedback.
