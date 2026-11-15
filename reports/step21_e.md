# Step 21e report: merge, very hard check, live smoke test

**Merge.** origin/main had no new commits, so `step21-checker` merged cleanly. Fast suite 354 passed, 3 skipped, 3 deselected; ruff clean. `--no-ff` merge on main (confirmed) is 28ca94f, pushed; CI on main: success.

**1. Very hard, dev seeds 200 and 201** (34 base labels, 170 images, hybrid RRF, thresholds unchanged). Clean-but-very-hard labels, n=34, Wilson 95%:
- Any finding: template 26/34 = 0.76 [0.60, 0.88]; blind 28/34 = 0.82 [0.66, 0.92].
- Confident finding (needs_human false): template 13/34 = 0.38 [0.24, 0.55]; blind 7/34 = 0.21 [0.10, 0.37].
- Per rule, any finding, template / blind (each over 34; intervals in `results/step21_checker_dev_very_hard.md`): B-READ 7 / 7, P-REF 5 / 6, P-NAME 4 / 4, S-EXP 4 / 4, P-ADDR 4 / 1, B-LOT 3 / 3, D-FMT 3 / 4, P-MFR 3 / 1, R-NAMEPLACE 1 / 4, S-MFR 1 / 2, B-EXP 1 / 0.
- Confident ones come mostly from text rules (P-NAME, B-LOT, P-REF, P-ADDR, P-MFR).
- Cause: OCR sometimes misreads above the 0.8 gate. Not a bug, and thresholds are frozen. Recall also drops (barcode_mismatch 24/34 template, 23/34 blind, since an unreadable barcode gives B-READ, not a verdict). Proposal: a photo-quality gate that turns very hard photos into needs_human. Not built.

**2. Live smoke test** (uvicorn, temp database, real CV extractor, one clean label and one with a bad date format). Registered a product, inspect gave 202, job polled to done (7.1 s and 3.1 s), CheckResult fetched, second inspect 200. Findings, `coverage` (16 rules) and `needs_human_count` (2) came back, and every response, including `/search`, validated against openapi.yaml with no errors. The bad date gave D-FMT critical citing 801.18. Bugs found: none. Limit: no real upload endpoint exists (uploadScan is a mock), so the version row was written to the database directly.
