# Step 18f: web_faq fresh set, scored once

**LLM-assessed qrels (claude-sonnet-5-5), not human grades.** Config `data/eval/step18_config.json` (settings_sha256 `02ea0a0f76797add...`), checked before scoring. 30 web_faq queries rewritten from real FDA Q&A (source URLs in `data/eval/fresh_candidates.csv`). chunk_derived queries (written by the same model that grades) were not graded and are NOT scored here.

Caveats: the pool is the top 10 of the three systems, so nDCG@10 is almost fully judged (the unjudged@10 column shows what is left: the pool was built with search depth 10 and this run searches depth 50, which changes the RRF fetch depth and moves a few ranks; the unjudged chunks are scored 0 in the main nDCG column and left out in the condensed column, and the two agree to within 0.007 for every system) but Recall@20 only counts relevant chunks that were pooled, so it is optimistic. A system that ranks a relevant chunk at 11 to 20 that nobody graded gets no credit and the denominator ignores it. Grades come from one LLM that is stricter than humans at the 0/1 boundary.

Queries: 30; corpus gaps (no chunk graded >= 1, excluded from averages): none; answerable with no grade-2 chunk: fw10, fw22, fw24, fw25. Scored: 30 (device 20, medicine 10).

## Absolute numbers, all answerable queries

| system | nDCG@10 | nDCG@10 condensed | Recall@20 (pool-based) | unjudged@10 |
|---|---|---|---|---|
| plain hybrid | 0.701 | 0.708 | 0.927 | 0.027 |
| hybrid+stem+prefix | 0.762 | 0.762 | 0.987 | 0.017 |
| E5b | 0.783 | 0.783 | 0.990 | 0.007 |

## Gains of E5b with paired bootstrap (10,000 resamples, seed 42)

| vs | metric | mean gain | 95% CI | p (two-sided, unadjusted) |
|---|---|---|---|---|
| plain hybrid | nDCG@10 | +0.082 | [+0.037, +0.136] | 0.000 |
| plain hybrid | nDCG@10 condensed | +0.075 | [+0.037, +0.117] | 0.000 |
| plain hybrid | Recall@20 | +0.063 | [+0.013, +0.126] | 0.008 |
| hybrid+stem+prefix | nDCG@10 | +0.021 | [-0.011, +0.054] | 0.196 |
| hybrid+stem+prefix | nDCG@10 condensed | +0.021 | [-0.011, +0.054] | 0.196 |
| hybrid+stem+prefix | Recall@20 | +0.003 | [-0.012, +0.021] | 0.784 |

Also hybrid+stem+prefix over plain hybrid:

| metric | mean gain | 95% CI | p |
|---|---|---|---|
| nDCG@10 | +0.061 | [+0.019, +0.115] | 0.001 |
| nDCG@10 condensed | +0.054 | [+0.019, +0.094] | 0.001 |
| Recall@20 | +0.059 | [+0.013, +0.119] | 0.003 |

## device (20 queries)

| system | nDCG@10 | nDCG@10 condensed | Recall@20 (pool-based) | unjudged@10 |
|---|---|---|---|---|
| plain hybrid | 0.676 | 0.676 | 0.925 | 0.020 |
| hybrid+stem+prefix | 0.719 | 0.719 | 0.980 | 0.015 |
| E5b | 0.746 | 0.746 | 0.985 | 0.000 |

| vs | metric | mean gain | 95% CI | p (two-sided, unadjusted) |
|---|---|---|---|---|
| plain hybrid | nDCG@10 | +0.070 | [+0.034, +0.112] | 0.000 |
| plain hybrid | nDCG@10 condensed | +0.070 | [+0.034, +0.112] | 0.000 |
| plain hybrid | Recall@20 | +0.061 | [+0.008, +0.127] | 0.024 |
| hybrid+stem+prefix | nDCG@10 | +0.027 | [-0.019, +0.076] | 0.238 |
| hybrid+stem+prefix | nDCG@10 condensed | +0.027 | [-0.019, +0.076] | 0.238 |
| hybrid+stem+prefix | Recall@20 | +0.005 | [-0.019, +0.028] | 0.760 |

## medicine (10 queries)

| system | nDCG@10 | nDCG@10 condensed | Recall@20 (pool-based) | unjudged@10 |
|---|---|---|---|---|
| plain hybrid | 0.750 | 0.772 | 0.933 | 0.040 |
| hybrid+stem+prefix | 0.849 | 0.849 | 1.000 | 0.020 |
| E5b | 0.857 | 0.857 | 1.000 | 0.020 |

| vs | metric | mean gain | 95% CI | p (two-sided, unadjusted) |
|---|---|---|---|---|
| plain hybrid | nDCG@10 | +0.106 | [-0.000, +0.237] | 0.050 |
| plain hybrid | nDCG@10 condensed | +0.084 | [-0.000, +0.181] | 0.050 |
| plain hybrid | Recall@20 | +0.067 | [+0.000, +0.200] | 0.699 |
| hybrid+stem+prefix | nDCG@10 | +0.008 | [-0.019, +0.036] | 0.592 |
| hybrid+stem+prefix | nDCG@10 condensed | +0.008 | [-0.019, +0.036] | 0.592 |
| hybrid+stem+prefix | Recall@20 | +0.000 | [+0.000, +0.000] | 1.000 |

## Per query nDCG@10 (unjudged = 0)

| qid | module | type | plain | h+s+p | E5b |
|---|---|---|---|---|---|
| fw01 | device | field_req | 0.96 | 0.96 | 0.94 |
| fw02 | device | change_impact | 0.95 | 0.95 | 1.00 |
| fw03 | device | vocab_mismatch | 0.68 | 0.62 | 0.67 |
| fw04 | device | direct | 0.92 | 0.91 | 0.92 |
| fw05 | device | direct | 0.60 | 0.62 | 0.65 |
| fw06 | device | field_req | 0.40 | 0.39 | 0.41 |
| fw07 | device | direct | 0.80 | 0.80 | 0.80 |
| fw08 | device | vocab_mismatch | 1.00 | 1.00 | 1.00 |
| fw09 | device | direct | 0.54 | 0.72 | 0.69 |
| fw10 | device | direct | 0.39 | 0.43 | 0.50 |
| fw11 | device | field_req | 0.68 | 0.80 | 0.77 |
| fw12 | device | change_impact | 0.50 | 0.63 | 0.63 |
| fw13 | device | field_req | 0.73 | 0.63 | 0.82 |
| fw14 | device | field_req | 0.00 | 0.00 | 0.34 |
| fw15 | device | direct | 0.70 | 0.78 | 0.76 |
| fw16 | device | vocab_mismatch | 0.71 | 0.81 | 0.78 |
| fw17 | device | field_req | 0.92 | 0.99 | 0.95 |
| fw18 | device | change_impact | 0.50 | 0.70 | 0.46 |
| fw19 | device | direct | 0.58 | 0.68 | 0.83 |
| fw20 | device | change_impact | 0.96 | 0.96 | 1.00 |
| fw21 | medicine | direct | 1.00 | 1.00 | 1.00 |
| fw22 | medicine | change_impact | 0.72 | 0.86 | 0.96 |
| fw23 | medicine | vocab_mismatch | 1.00 | 1.00 | 1.00 |
| fw24 | medicine | symbol | 1.00 | 1.00 | 1.00 |
| fw25 | medicine | field_req | 0.69 | 0.69 | 0.69 |
| fw26 | medicine | field_req | 0.00 | 0.65 | 0.61 |
| fw27 | medicine | direct | 0.63 | 0.63 | 0.62 |
| fw28 | medicine | field_req | 0.75 | 0.75 | 0.69 |
| fw29 | medicine | symbol | 0.98 | 0.95 | 1.00 |
| fw30 | medicine | field_req | 0.73 | 0.95 | 1.00 |
