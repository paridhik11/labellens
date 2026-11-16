# Step 24a report: real scan upload

**Done.** `uploadScan`, `getScan`, `getExtraction` and `confirmExtraction` are real (`src/api/uploads.py`, `scans.py`, `quality.py`). `src/common/schemas.py`, `src/ir`, `src/cv`, `src/gen`, `data/eval` and the checker thresholds are untouched.

**Flow.** Upload is checked, stored, and answered with 202 and a Job (`kind: scan`). The job renders PDF page 1 (optional `pypdfium2`), runs the quality gate on photos, runs the existing extractor, then creates the label version (uploaded, L1) and the extraction. A rejected photo ends the scan and job in `failed` with `retake_photo` (reasons `blur`, `low_contrast`, `glare`, plus metrics and thresholds) and creates no version. Confirmation appends a confirmation row and a new extraction row, so inspect reads the corrected fields.

**Safety.** Type by magic bytes (PNG, JPEG, PDF), never filename or Content-Type; 15 MB cap (read at most cap+1 bytes, plus a Content-Length check before the body is parsed); 40 megapixels and 64 px minimum read from the header; whole-stream `verify()`; stored as `data/api/uploads/<sha256>.<ext>` (git-ignored, atomic write), client filename never used; stored paths are re-validated against `<64 hex>.(png|jpg|pdf)`. cv2 and pypdfium2 are imported lazily.

**Gate, tuned on dev seeds 200 and 201 only** (680 images; `python -m src.api.quality_eval`, which refuses other seeds). Cut-offs: sharpness < 200, contrast < 40, soft-edged saturated blob >= 2% with border gradient < 60.

| condition | n | rejected |
|---|---|---|
| clean | 170 | 0 |
| moderate | 170 | 0 |
| hard | 170 | 1 |
| very_hard | 170 | 71 (5 blur, 66 glare) |

So 0/170 clean and 0/170 moderate labels were wrongly rejected. On very_hard, 30 of the 35 images with no barcode read were caught, but 41 of 135 with a readable barcode were also rejected. Sweeps: glare edge 80 starts rejecting moderate (5/170); 60 to 70 is a plateau; sharpness 150 to 250 and contrast 20 to 80 change nothing on clean or moderate.

**Choices.**
- `product_id` is required (a scan creates a version, which needs a product). File errors are 422 with specific codes, not 413 or 415. Both, and the new codes, are additive CR-20 in `openapi.yaml` and `SCHEMA_CHANGE_REQUESTS.md`.
- PDF pages skip the photo gate (a render has no camera defects).
- Unknown ids that this server never issues still serve the mock (`scn_0001` style), as for jobs.
- Added `python-multipart` (FastAPI forms; CI), `pypdfium2` (PDF), `pillow` to the CI install line.

**Verification.** Fast suite `python -m pytest -q -m "not slow"`: 568 passed, 1 failed (the persistence test needed rows for the two new tables; fixed, file re-run 20 passed, so 569 expected), 11 skipped (cv2 or zxingcpp missing in .venv312); `ruff check src tests` clean. Live smoke with the real extractor and gate (`.venv-cv`): clean, moderate and two very_hard dev images all reached `done` with 6 fields and 1 barcode.

**Limits.** Cut-offs were chosen and measured on the same images, so the real false-reject rate on phone photos is unknown. A glare spot touching the white label merges with it and is missed. Clean images are flat white pages, so the clean row says little about real photos. Chunked uploads without Content-Length skip the early size check (the 15 MB read cap still applies after parsing). Roles: editor or admin upload and confirm; reviewers get 403.
