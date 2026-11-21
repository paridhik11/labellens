# CV4: registered-name evidence

1. **What I did**

Committed protocol before experiments; froze 30 new positive photos
(20 dev/10 test) plus 15 wrong-product photos. Upgraded OCR in a disposable
venv, preserving labellens-cv. Kept CV2 after the PP-OCRv6-small trial failed
the dev promotion rule. Final **gate FAILED: incomplete negative evidence;
no merge to main**.

| Final photo check | Count | Wilson 95% interval |
|---|---|---|
| CV2 blind exact name | 0/10 | 0.0–27.8% |
| Registered-name found | 8/10 | 49.0–94.3% |
| False found, completed negatives only | 0/13 | 0.0–22.8% |
| Negative extraction timeouts | 2/15 | Not successful rejections |

`new_18.jpg` (Tornus) and `new_90.jpg` (Celsius) timed out at 300 seconds.
No valid zero-false-found conclusion for all 15 photos. No final reruns,
replacement negatives or post-test model selection.

Upgrade: RapidOCR **3.10.0**, ONNX Runtime **1.32.0**, PaddleOCR **3.7.0**,
PaddlePaddle **3.3.1**; imports and `pip check` passed. PP-OCRv6 small loaded
and completed 20 dev photos. Dev: blind 3/20; CV2-known **13/20** versus
PP-OCRv6-known **12/20**; both 0/20 dev false found. CV2 had one dev timeout;
v6 had none. V6 was not tested on final photos because it was rejected on dev.
Other sizes/Paddle inference were unmeasured.

2. **Files created or changed**

| Files | Reason |
|---|---|
| `src/cv/{known_product,ocr_modern}.py`; `cv4_release.json` | Fixed matcher, optional adapter, reader choice |
| `src/api/{known_name,scans,checks}.py`; OpenAPI contract | Professional upload evidence, pinned record, confirmation |
| `src/gen/cv4_*` | Source URLs, LLM references, split and re-fetch |
| `scripts/cv_experiments/cv4_eval.py`; OCR lock | Bounded reproducible experiments |
| `tests/test_cv4*.py` | Evidence, wrong-product, API, fallback guards |
| `reports/cv4*`; `results/cv4/`; learning log | Protocol, hashes, observations, limits |

3. **How it works**

Registered-name words/numbers require 0.90 coverage, distinctive-token matches and
0.80 OCR confidence. Return found/not_found plus literal lines, boxes and scores;
never insert the registered name as OCR. Professional uploads use product_id;
public blind extraction stays unchanged. Confirmation preserves evidence.

4. **How I verified it**

Output: `reports/cv4_validation.json`.

```text
993 passed, 5 deselected in 70.00s (0:01:10)
All checks passed!
```

5. **What you should check yourself**

Inspect frozen pairings, literal evidence and the two timeout observations.
Re-fetch: `python -m src.gen.cv4_acquire --frozen`.

6. **What I am unsure about or assumed**

LLM-labelled; no human validation. One publisher and related packages limit
generalization. Found checks supplied-name presence. Clinical photos, symbols
and upload latency remain unmeasured. Timeout stage is unlocalized. Further
work needs dev diagnosis and a fresh evaluation set; this set is exposed.
