# Step 18 experiments

**LLM-assessed qrels (claude-sonnet-5-5), not human grades.** 5-fold stratified cross-validation over the 57 answerable queries (`data/eval/cv_folds.json`, seed 42). Gains are over the stated base, pooled over all queries. Keep rule: gain above 0.01 on both nDCG@10 lists (unjudged=0 and condensed), at least 3 of 5 folds won, survives leaving out the two biggest-gaining queries. unjudged@10 above 0.05 means PENDING_GRADING. This file is written by the harness; each section is replaced when its experiment is re-run.

## E0: hybrid+stem+prefix vs hybrid (carried over from Step 17)

**Decision: KEPT.** gain +0.026 / +0.026, wins 3 of 5 folds, survives leave-top-2-out.

- What changed: BM25 half uses the light-stemmed index and the dense half adds the BGE query instruction. Base is plain hybrid. Run first to check the harness; Step 17 already saw these queries.
- Parameters: base=hybrid, variant=hybrid+stem+prefix
- Pooled over 57 queries: nDCG@10 unjudged=0 +0.026, condensed +0.026, Recall@20 +0.017.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.013, +0.062].
- Leave-top-2-out gain: +0.013 / +0.013; top gainers: q15 +0.417, q01 +0.322.
- unjudged@10: variant 0.000, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.563 | 0.607 | +0.044 | 0.563 | 0.607 | +0.044 | yes |
| 2 | 12 | 0.677 | 0.650 | -0.027 | 0.677 | 0.650 | -0.027 |  |
| 3 | 11 | 0.519 | 0.560 | +0.041 | 0.519 | 0.560 | +0.041 | yes |
| 4 | 11 | 0.653 | 0.744 | +0.091 | 0.653 | 0.744 | +0.091 | yes |
| 5 | 11 | 0.607 | 0.588 | -0.019 | 0.607 | 0.588 | -0.019 |  |

Pooled base nDCG@10 0.604, variant 0.630; folds won 3 of 5.
