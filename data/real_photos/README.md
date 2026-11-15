# Real phone photos and LLM-labelled transcriptions

Parth must capture about 10 actual phone photos of labels he can photograph and
share. The coding agent cannot take physical photos or substitute downloaded
artwork for them. No photos have been supplied in this folder yet.

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
/opt/anaconda3/envs/labellens-cv/bin/python -m src.cv.eval_real
```

Without photos and transcriptions it prints that there is nothing to evaluate.
With inputs, it runs blind extraction with post-correction and reports exact
matches and character errors per field. Save the real output in the requested
report. Label any scores against AI references as LLM-reference results and
report the human spot-check separately. Keep device/medicine and real/synthetic
results separate.

New photos, transcriptions and provenance files remain local under the repository
ignore rules. Reports may contain counts and errors without publishing the photos.
