# CV2 previously exposed online package photos

n=10 unchanged images; LLM-generated references. Human spot-check and symbol-crop review deferred.
Real-symbol accuracy unmeasured. These are retail/catalog photos, not newly captured phone photographs.
All ten were previously exposed; six were development photos. This is not an unseen holdout.

Baseline cached at 740a0ab, identical field algorithms at d39b0fb (only lazy-import plumbing differs).
The candidate was frozen at 806c9d0 before this one check; no rule was tuned from these outputs.
Exact counts use src.cv.eval_real.score for both, preserving case, glyphs and printed date formats.

| Field | Baseline exact (95% Wilson) | Candidate exact (95% Wilson) |
|---|---|---|
| product_name | 1/10 (0.018 to 0.404) | 1/10 (0.018 to 0.404) |
| lot | 7/10 (0.397 to 0.892) | 4/10 (0.168 to 0.687) |
| expiry | 3/10 (0.108 to 0.603) | 5/10 (0.237 to 0.763) |

All three exact together: 0/10 before, 0/10 candidate.
Extraction exceptions: 0/10.

Lot accuracy regressed from 7/10 to 4/10; expiry rose from 3/10 to 5/10; names stayed 1/10.
This negative result must accompany every summary of CV2. It is not 80% real-photo accuracy.
Small convenience-sample intervals do not establish population accuracy. The frozen release gate
uses only the fresh transformed-artwork set, not this previously exposed check.
