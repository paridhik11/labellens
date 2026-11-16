# Parth Task 7: per-field print verification

## 1. What I did
Added a standalone verifier with per-field match, mismatch or needs-human-review results and OCR evidence confidence. Preserved approval, passed-check and artifact-integrity gates before extraction. Compared the ten online device photos against AI transcriptions without inventing approval records. This completes local comparison code, not real approved-print validation.

## 2. Files created or changed
- `src/cv/print_verify.py`: blind extraction, per-field evidence, approved-package gate and separate photo evaluation.
- `tests/test_print_verify.py`: confidence, missing/ambiguous evidence, tampering, approval rejection, failures and provenance tests.
- CV README and learning log: API distinction and limitations.
- Local `data/real_photos/clear_online/print_comparison_llm.json`: all 30 field decisions and evidence.

## 3. How it works
A unique confident reading of LOT: TEST001 matches reference TEST001 after removing the key. A different confident reading is a mismatch. Missing, ambiguous or weak OCR asks for review. Confidence measures OCR evidence, not probability that a decision is correct. Blank references are not scored.

## 4. How I verified it
```text
/opt/anaconda3/envs/labellens-cv/bin/python -m src.cv.print_verify
```
Actual output values, condition photo, LLM-labelled references:

| Field | Exact | MATCH | MISMATCH | NEEDS_HUMAN_REVIEW |
|---|---|---|---|---|
| product_name | 1/10 | 1 | 5 | 4 |
| lot | 0/10 | 0 | 0 | 10 |
| expiry | 0/10 | 0 | 0 | 10 |

```text
/opt/anaconda3/envs/labellens-cv/bin/python -m pytest -q -p no:cacheprovider -m "not slow"
436 passed, 3 deselected in 158.85s (0:02:38)

/opt/anaconda3/envs/labellens-cv/bin/python -m ruff check --no-cache src tests scripts/real scripts/cv_experiments/eval_perspective.py
All checks passed!
```
Full raw output and per-photo evidence remain local. Permission-gate tests use synthetic reviewer fixtures only.

## 5. What you should check yourself
Inspect confidence/abstention tests, approval-before-OCR ordering and individual photo outcomes. Confirm no approvals are created.

## 6. What I am unsure about or assumed
Existing extractor unchanged; poor extraction remains deferred. Human spot-check deferred explicitly by Parth, NOT_RUN. Approved-print evaluation is NOT_RUN because these online photos have no trusted approved reference packages. No 80% photo accuracy claim. The new entry uses legacy manifest packages, not Task 2 Label snapshots; application integration and real reviewer records remain separate.
