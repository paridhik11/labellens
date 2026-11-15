# Parth Task 6: structured revision engine

## 1. What I did
Implemented and reviewed the local revision engine. It copies the source template and record, increments versions, applies structured text changes and produces a new draft export snapshot. Unchanged barcodes reuse the exact element/matrix; confirmed encoded changes regenerate and decode-check. Missing inputs produce no artwork.

## 2. Files created or changed
- `src/gen/revise.py`: revision result, identity/staleness checks, field/symbol updates, audit log and render guard.
- `src/export/template.py`: validated reuse of an existing barcode without encoding it again.
- `tests/test_revise.py`: 35 cases, including actual GS1-type validation and PDF/SVG integration.
- Generator README: usage and supported scope.
- `docs/PARTH_WORK_SUMMARY.md`: durable deferred-photo note and revision status.
- This report and learning log: actual verification and limits.

## 3. How it works
Changing an address keeps the existing barcode. Changing a lot requires confirmed_lot_change=True. If a model requires a new identifier, the caller must supply one; entering the old identifier does not satisfy that requirement. EO-to-gamma updates the bound synthetic symbol while keeping encoded data. New drafts carry audit and partial-check metadata; approvals are not copied or issued.

## 4. How I verified it
```text
/opt/anaconda3/envs/labellens-cv/bin/python -m pytest -q -p no:cacheprovider -m "not slow"
........................................................................ [ 17%]
........................................................................ [ 35%]
........................................................................ [ 52%]
........................................................................ [ 70%]
........................................................................ [ 87%]
...................................................                      [100%]
411 passed, 3 deselected in 106.93s (0:01:46)

/opt/anaconda3/envs/labellens-cv/bin/python -m ruff check --no-cache src tests
All checks passed!
```
Review caught plain-text barcode acceptance; the regression passed after correction.
Both GS1 formats decoded to the revised lot from independently rasterized 600-DPI PDFs. A local synthetic review run produced:
```text
keep_address DRAFT KEEP PDF/SVG present
regenerate_lot DRAFT REGENERATE PDF/SVG present
blocked_lot NEEDS_INPUT NEEDS_INPUT no artwork
missing_identifier NEEDS_INPUT NEEDS_INPUT no artwork
Original template and record unchanged; no approvals or publication created.
```

## 5. What you should check yourself
Inspect local data/synthetic/task6_revision_review: revised PDF text, audit JSON and blocked folders without artwork. Review exact barcode reuse and the deferred-photo status note.

## 6. What I am unsure about or assumed
This engine uses Task 2 export snapshots, not legacy renderer manifests. Trusted confirmations, storage and publication remain application responsibilities. Revision OCR/symbol checks are NOT_RUN. Photo extraction remains deferred: name 1/10, lot 0/10, expiry 0/10; human spot-check NOT_RUN. Future summaries must retain these limits. No dependencies or shared schemas changed.
