# Step 18 final retrieval summary

**All relevance grades are LLM grades (claude-sonnet-5-5), not human grades.** Frozen system: E5b (stemmed BM25 + bge-large with query prefix and heading enrichment, RRF), config `data/eval/step18_config.json`, hash checked before every scoring run. Details: `results/step18_fresh_web.md` (fresh set), `results/step18_experiments.md` (cross-validation), `results/step18_abstain_test.md` (abstention).

## 1. Fresh set (the honest test): 30 web_faq queries, scored once

Queries are real FDA Q&A questions rewritten as short queries (20 device, 10 medicine). The 30 chunk_derived queries were written by the same model that grades, were not graded and are **not scored**.

| system | nDCG@10 | Recall@20 (pool-based) |
|---|---|---|
| plain hybrid | 0.701 | 0.927 |
| hybrid+stem+prefix | 0.762 | 0.987 |
| **E5b** | **0.783** | **0.990** |

Gains with paired bootstrap 95% intervals (10,000 resamples, seed 42, unadjusted p):

| E5b minus | nDCG@10 | Recall@20 |
|---|---|---|
| plain hybrid | +0.082 [+0.037, +0.136] | +0.063 [+0.013, +0.126] |
| hybrid+stem+prefix | +0.021 [-0.011, +0.054], p 0.20 | +0.003 [-0.012, +0.021] |

Also hybrid+stem+prefix minus plain hybrid: nDCG@10 +0.061 [+0.019, +0.115].
By module, E5b nDCG@10: device 0.746 (20 queries), medicine 0.857 (10 queries; interval on the gain over plain hybrid just touches 0).

## 2. Cross-validation (where E5b was selected)

57 answerable queries, 5 folds, E5b nDCG@10 gain over plain hybrid +0.099 [+0.057, +0.141] (5 of 5 folds), over hybrid+stem+prefix +0.074 [+0.037, +0.112] (5 of 5 folds; +0.070 without q55). Recall@20 gains +0.063 and +0.045.

## 3. Caveats

- **E5b was selected on the cross-validation queries** among about 20 ideas, so the CV gains are optimistic. The fresh set is the check, and there the gain over hybrid+stem+prefix shrank from +0.074 to +0.021 and its interval includes 0. What the fresh set does show is a clear gain over plain hybrid. The step from hybrid+stem+prefix to E5b is not established.
- Fresh-set pool is the top 10 of three systems, so nDCG@10 is nearly fully judged (unjudged@10: 0.027 plain, 0.017 h+s+p, 0.007 E5b; unjudged chunks scored 0 in the main column) but **Recall@20 only counts relevant chunks that were pooled and is optimistic**. Do not read 0.99 as true recall.
- One LLM graded everything and is stricter than humans at the 0/1 boundary (Step 13). 30 queries, 4 of them with no grade-2 chunk, so intervals are wide.
- The fresh queries are one FDA Q&A style over the same 21 CFR corpus. Corpus gaps (symbols, non-US sources) are untouched.

## 4. Against the targets (nDCG@10 0.75, Recall@20 0.90)

- nDCG@10 0.75: met pooled on the fresh set (0.783) but **not for device alone (0.746)** and not on cross-validation (about 0.70, hybrid+stem+prefix 0.63). Medicine passes (0.857, 10 queries).
- Recall@20 0.90: passes on the fresh set only because the pool is shallow (optimistic). On cross-validation, which is judged to rank 20, it is about 0.81, **below 0.90**.
- Abstention (separate task, medicine only, 13 test queries, 8 answerable and 5 no_answer): **no score meets AUROC 0.90 or leave-one-out precision 0.80.** Best is the z-averaged top bm25 and dense score, AUROC 0.800 [0.500, 1.000], precision 0.429. cross-encoder top score 0.500, logistic regression precision 0.250. The dev half had looked better (0.889 to 0.911), which did not hold on test. With 13 queries this is weak evidence either way; Step 16 (hybrid top AUROC 0.985 on a different 20 queries) is not confirmed by it.
