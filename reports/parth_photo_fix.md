# Parth: perspective integration and fixed photo evaluation

## 1. What I did
Wired perspective correction into the extractor. Added deterministic orientation/crop OCR and generic key/date rules, developed on invented examples and synthetic labels. Recorded Pari's acceptance of CR-2,3,4,5,9,10,11.

## 2. Files changed
- `src/cv/extract.py`, `perspective.py`, new `photo_ocr.py`, `photo_fields.py`: integrated geometry, original-coordinate evidence and photo fields.
- New tests and `scripts/cv_experiments/eval_photo_protocol.py`: regression tests, fingerprint checks and archived-code comparison.
- Contract decisions, source protocol, CV README, work summary and learning log: decisions and remaining limits.
- `results/cv_photo_before_after.md`: generated paired results and reproduction commands.

## 3. How it works
Known templates supply proportions; blind photos use observed edges, never the synthetic ratio. Original and flattened views use quarter-turn OCR, overlapping crops and spatial keys. Same immutable images/references on both sides. No scoring-set tuning or reference/product-name copying.

## 4. How I verified it
Condition photo, ten LLM-generated transcriptions, baseline 88f9c9d versus frozen c2759e9:

| Field | Before exact | After exact |
|---|---|---|
| Product name | 1/10 | 1/10 |
| Lot | 0/10 | 7/10 |
| Expiry | 0/10 | 3/10 |

Conda Python, real output:
```text
/opt/anaconda3/envs/labellens-cv/bin/python -m pytest -q -p no:cacheprovider -m "not slow"
790 passed, 5 deselected, 1 warning in 127.17s (0:02:07)
/opt/anaconda3/envs/labellens-cv/bin/python -m pytest -q -p no:cacheprovider src/gen src/cv
398 passed, 1 skipped in 162.27s (0:02:42)
/opt/anaconda3/envs/labellens-cv/bin/python -m ruff check --no-cache src tests
All checks passed!
```

## 5. Check yourself
Inspect coordinate tests, paired results and accepted contract IDs.

## 6. Limits
Names remain weak; 80% real-photo accuracy is not established. Previously exposed convenience set, not unseen validation. Human spot-check/crop review deferred; real-photo symbol accuracy unmeasured. Pari owns auth, reviews, publication and step-24b snapshot mapping.
