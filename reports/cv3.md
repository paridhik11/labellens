# CV round 3

1. **What I did**

Acquired 30 new device-package photos and froze a 20-dev/10-test family split.
Kept GS1 prefill after dev lots improved 8/17 to 10/17; rejected crops at 9/17.
Perspective correction was connected; absent newer models left PP-OCRv4 unchanged.
Scored once: **gate PASS**, zero errors/timeouts.

Effective counts [Wilson 95% interval, percent]:

| Set / field | CV2 baseline | Prefill candidate |
|---|---|---|
| New photos / name | 0/10 [0.0,27.8] | 0/10 [0.0,27.8] |
| New photos / lot | 4/7 [25.0,84.2] | 5/7 [35.9,91.8] |
| New photos / expiry | 7/8 [52.9,97.8] | 7/8 [52.9,97.8] |
| Synthetic clean / each field | 16/16 [80.6,100] | 16/16 [80.6,100] |
| Synthetic moderate / name | 13/16 [57.0,93.4] | 13/16 [57.0,93.4] |
| Synthetic moderate / lot; expiry, each | 16/16 [80.6,100] | 16/16 [80.6,100] |
| Synthetic hard / name | 10/16 [38.6,81.5] | 10/16 [38.6,81.5] |
| Synthetic hard / lot; expiry, each | 16/16 [80.6,100] | 16/16 [80.6,100] |

Printed counts were unchanged, including real lot 4/7.
All 12 mismatch flags remained across six conflict cases. Synthetic seeds
12000–12015 use reduced-hard, one template.

2. **Files created or changed**

| Files | Reason |
|---|---|
| `src/cv/cv3.py`; `extract.py` | Validated suggestions, separate printed fields, explicit opt-in |
| `src/gen/cv3_acquire.py` | Re-fetch pinned source bytes |
| `src/gen/cv3_dataset.json`; `cv3_references.tsv` | Sources, LLM references, split |
| `scripts/cv_experiments/cv3_eval.py`; `cv3_crops.py` | Scoring/gate; rejected prototype audit |
| `tests/test_cv3.py` | Provenance, coordinates, unchanged checker, lazy imports |
| `reports/cv3_*.{md,json}`; `results/cv3/` | Protocol, freeze, choices, raw observations and intervals |
| `docs/LEARNING_LOG.md` | Short step report |

3. **How it works**

GS1 application identifiers 10/17 encode lot/expiry. For example, observed
`C928GWW` stays printed OCR; decoded `C928GWV` becomes a separate suggestion
with payload/coordinates. Use `extract_label(..., mode="blind", cv3_stage=1)`;
`extract_label_modes` returns provenance. CV2 remains default.

4. **How I verified it**

Commands/output: `reports/cv3_validation.json`.

```text
963 passed, 5 deselected in 66.26s (0:01:06)
All checks passed!
```

Code `2f62d93`; freeze `798d555`; plan `389e759`.
Verdict: `results/cv3/verdict.json`.

5. **What you should check yourself**

Check provenance, printed fields and manifests. Re-fetch:
`python -m src.gen.cv3_acquire --frozen`.

6. **What I am unsure about or assumed**

LLM references lack human validation; unreadable fields are unscored.
Names remain poor. One publisher, small samples and correlated frames limit
generalization. Symbols/clinical phone-photo performance were unmeasured here.
Previous ten photos excluded. No checker/schema/dependency changes.
Final set now exposed; no further tuning.
