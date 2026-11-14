# Step 17e: tuning on the development half (29 queries)

**LLM-assessed qrels (claude-sonnet-5-5), not human grades.** Dev half only (seed 42 split, 21 device and 8 medicine queries). The held-out half is untouched. Settings were chosen on these same queries, so differences here are optimistic and the intervals are descriptive, not tests. Depth 50, nDCG@10, chunk level; queries are searched in their own module.

Unjudged chunks are not in the pooled qrels (the pool came from the old systems). 'condensed' removes them from the list first. Gain rule: best config beats its base by more than 0.01 on both numbers.

- Part boost on bm25: BM25 part scoring showed no gain, so the summed-RRF top-3 vote scoring was also run (both are in the table).
- Part boost on hybrid: BM25 part scoring showed no gain, so the summed-RRF top-3 vote scoring was also run (both are in the table).
- No A+B combo on bm25: one of the two components showed no gain on dev.

**Leak check.** The failure-derived synonym groups were written after reading the failure list. Queries that motivated them: q01, q03, q12, q15, q16, q24, q55, q59 (q01, q03, q12, q16, q59 in dev; q15, q24, q55 in held-out). The last column of each table repeats the difference to the base without the motivating queries that are in dev.

## Baselines

| variant | n | nDCG@10 pooled | condensed pooled | unjudged@10 | device | medicine | diff vs base [95% CI] | gain | diff without 5 motivating queries |
|---|---|---|---|---|---|---|---|---|---|
| bm25 | 29 | 0.602 | 0.602 | 0.000 | 0.582 | 0.654 | +0.000 [+0.000, +0.000] |  | +0.000 |
| hybrid | 29 | 0.589 | 0.589 | 0.000 | 0.575 | 0.626 | +0.000 [+0.000, +0.000] |  | +0.000 |

## A. Query expansion

| variant | n | nDCG@10 pooled | condensed pooled | unjudged@10 | device | medicine | diff vs base [95% CI] | gain | diff without 5 motivating queries |
|---|---|---|---|---|---|---|---|---|---|
| bm25+exp(w=0.3,all) | 29 | 0.625 | 0.636 | 0.041 | 0.607 | 0.675 | +0.024 [-0.001, +0.049] | yes | -0.000 |
| hybrid+exp(w=0.3,all,bm25side) | 29 | 0.599 | 0.607 | 0.031 | 0.577 | 0.657 | +0.010 [-0.020, +0.045] | yes | -0.002 |
| hybrid+exp(w=0.3,all,dense) | 29 | 0.632 | 0.651 | 0.093 | 0.607 | 0.698 | +0.043 [-0.010, +0.106] | yes | -0.008 |
| bm25+exp(w=0.5,all) | 29 | 0.632 | 0.644 | 0.062 | 0.602 | 0.708 | +0.030 [-0.004, +0.072] | yes | -0.002 |
| hybrid+exp(w=0.5,all,bm25side) | 29 | 0.604 | 0.616 | 0.034 | 0.582 | 0.661 | +0.015 [-0.026, +0.063] | yes | -0.008 |
| hybrid+exp(w=0.5,all,dense) | 29 | 0.629 | 0.649 | 0.093 | 0.605 | 0.693 | +0.040 [-0.021, +0.108] | yes | -0.019 |
| bm25+exp(w=1.0,all) | 29 | 0.604 | 0.644 | 0.145 | 0.564 | 0.708 | +0.002 [-0.049, +0.060] |  | -0.040 |
| hybrid+exp(w=1.0,all,bm25side) | 29 | 0.605 | 0.620 | 0.066 | 0.581 | 0.670 | +0.016 [-0.029, +0.070] | yes | -0.012 |
| hybrid+exp(w=1.0,all,dense) | 29 | 0.612 | 0.651 | 0.121 | 0.580 | 0.697 | +0.023 [-0.031, +0.086] | yes | -0.021 |
| bm25+exp(w=0.3,cfr) | 29 | 0.604 | 0.612 | 0.021 | 0.586 | 0.654 | +0.003 [-0.012, +0.014] |  | -0.000 |
| hybrid+exp(w=0.3,cfr,bm25side) | 29 | 0.597 | 0.598 | 0.007 | 0.586 | 0.626 | +0.008 [-0.004, +0.029] |  | +0.010 |
| hybrid+exp(w=0.3,cfr,dense) | 29 | 0.591 | 0.599 | 0.028 | 0.577 | 0.626 | +0.002 [-0.012, +0.017] |  | -0.001 |
| bm25+exp(w=0.5,cfr) | 29 | 0.606 | 0.615 | 0.028 | 0.587 | 0.654 | +0.004 [-0.011, +0.017] |  | +0.002 |
| hybrid+exp(w=0.5,cfr,bm25side) | 29 | 0.597 | 0.599 | 0.007 | 0.586 | 0.626 | +0.008 [-0.005, +0.029] |  | +0.009 |
| hybrid+exp(w=0.5,cfr,dense) | 29 | 0.591 | 0.600 | 0.031 | 0.578 | 0.626 | +0.002 [-0.013, +0.019] |  | -0.002 |
| bm25+exp(w=1.0,cfr) | 29 | 0.594 | 0.609 | 0.038 | 0.571 | 0.654 | -0.008 [-0.027, +0.007] |  | -0.009 |
| hybrid+exp(w=1.0,cfr,bm25side) | 29 | 0.595 | 0.596 | 0.014 | 0.584 | 0.626 | +0.006 [-0.010, +0.032] |  | +0.007 |
| hybrid+exp(w=1.0,cfr,dense) | 29 | 0.582 | 0.598 | 0.041 | 0.566 | 0.626 | -0.007 [-0.023, +0.008] |  | -0.008 |

## B. Part boost

| variant | n | nDCG@10 pooled | condensed pooled | unjudged@10 | device | medicine | diff vs base [95% CI] | gain | diff without 5 motivating queries |
|---|---|---|---|---|---|---|---|---|---|
| bm25+pb(top=1,beta=0.1,bm25) | 29 | 0.596 | 0.604 | 0.062 | 0.560 | 0.689 | -0.006 [-0.041, +0.027] |  | -0.013 |
| bm25+pb(top=1,beta=0.25,bm25) | 29 | 0.546 | 0.596 | 0.162 | 0.500 | 0.669 | -0.056 [-0.113, -0.002] |  | -0.059 |
| bm25+pb(top=1,beta=0.5,bm25) | 29 | 0.517 | 0.583 | 0.252 | 0.460 | 0.669 | -0.085 [-0.151, -0.023] |  | -0.090 |
| bm25+pb(top=1,beta=1.0,bm25) | 29 | 0.520 | 0.593 | 0.266 | 0.463 | 0.669 | -0.082 [-0.150, -0.017] |  | -0.085 |
| bm25+pb(top=2,beta=0.1,bm25) | 29 | 0.599 | 0.604 | 0.031 | 0.574 | 0.667 | -0.003 [-0.031, +0.021] |  | -0.013 |
| bm25+pb(top=2,beta=0.25,bm25) | 29 | 0.585 | 0.603 | 0.076 | 0.554 | 0.667 | -0.016 [-0.059, +0.021] |  | -0.034 |
| bm25+pb(top=2,beta=0.5,bm25) | 29 | 0.578 | 0.604 | 0.100 | 0.543 | 0.667 | -0.024 [-0.085, +0.027] |  | -0.048 |
| bm25+pb(top=2,beta=1.0,bm25) | 29 | 0.578 | 0.601 | 0.100 | 0.543 | 0.667 | -0.024 [-0.085, +0.027] |  | -0.048 |
| hybrid+pb(top=1,beta=0.1,bm25) | 29 | 0.582 | 0.594 | 0.069 | 0.559 | 0.642 | -0.007 [-0.061, +0.040] |  | -0.018 |
| hybrid+pb(top=1,beta=0.25,bm25) | 29 | 0.562 | 0.590 | 0.162 | 0.530 | 0.644 | -0.027 [-0.096, +0.036] |  | -0.036 |
| hybrid+pb(top=1,beta=0.5,bm25) | 29 | 0.518 | 0.593 | 0.252 | 0.474 | 0.634 | -0.071 [-0.150, +0.002] |  | -0.068 |
| hybrid+pb(top=1,beta=1.0,bm25) | 29 | 0.513 | 0.596 | 0.262 | 0.467 | 0.634 | -0.076 [-0.163, +0.004] |  | -0.074 |
| hybrid+pb(top=2,beta=0.1,bm25) | 29 | 0.587 | 0.593 | 0.024 | 0.573 | 0.626 | -0.002 [-0.044, +0.034] |  | -0.013 |
| hybrid+pb(top=2,beta=0.25,bm25) | 29 | 0.592 | 0.609 | 0.052 | 0.579 | 0.626 | +0.003 [-0.056, +0.055] |  | -0.018 |
| hybrid+pb(top=2,beta=0.5,bm25) | 29 | 0.579 | 0.601 | 0.090 | 0.561 | 0.626 | -0.010 [-0.081, +0.050] |  | -0.032 |
| hybrid+pb(top=2,beta=1.0,bm25) | 29 | 0.579 | 0.597 | 0.093 | 0.561 | 0.626 | -0.010 [-0.081, +0.050] |  | -0.032 |
| bm25+pb(top=1,beta=0.1,votes) | 29 | 0.583 | 0.592 | 0.055 | 0.568 | 0.622 | -0.019 [-0.072, +0.025] |  | -0.028 |
| bm25+pb(top=1,beta=0.25,votes) | 29 | 0.532 | 0.586 | 0.152 | 0.515 | 0.578 | -0.070 [-0.151, -0.001] |  | -0.076 |
| bm25+pb(top=1,beta=0.5,votes) | 29 | 0.512 | 0.578 | 0.228 | 0.487 | 0.578 | -0.090 [-0.172, -0.019] |  | -0.096 |
| bm25+pb(top=1,beta=1.0,votes) | 29 | 0.509 | 0.585 | 0.245 | 0.482 | 0.578 | -0.093 [-0.176, -0.022] |  | -0.098 |
| bm25+pb(top=2,beta=0.1,votes) | 29 | 0.597 | 0.601 | 0.038 | 0.575 | 0.654 | -0.005 [-0.025, +0.012] |  | -0.011 |
| bm25+pb(top=2,beta=0.25,votes) | 29 | 0.589 | 0.606 | 0.069 | 0.564 | 0.654 | -0.013 [-0.048, +0.015] |  | -0.020 |
| bm25+pb(top=2,beta=0.5,votes) | 29 | 0.588 | 0.611 | 0.090 | 0.562 | 0.654 | -0.014 [-0.050, +0.014] |  | -0.022 |
| bm25+pb(top=2,beta=1.0,votes) | 29 | 0.588 | 0.617 | 0.090 | 0.562 | 0.654 | -0.014 [-0.050, +0.014] |  | -0.022 |
| hybrid+pb(top=1,beta=0.1,votes) | 29 | 0.559 | 0.565 | 0.048 | 0.572 | 0.527 | -0.030 [-0.093, +0.028] |  | -0.037 |
| hybrid+pb(top=1,beta=0.25,votes) | 29 | 0.536 | 0.562 | 0.124 | 0.560 | 0.476 | -0.053 [-0.137, +0.022] |  | -0.053 |
| hybrid+pb(top=1,beta=0.5,votes) | 29 | 0.488 | 0.571 | 0.207 | 0.499 | 0.462 | -0.101 [-0.197, -0.010] |  | -0.084 |
| hybrid+pb(top=1,beta=1.0,votes) | 29 | 0.484 | 0.570 | 0.224 | 0.492 | 0.462 | -0.106 [-0.208, -0.009] |  | -0.090 |
| hybrid+pb(top=2,beta=0.1,votes) | 29 | 0.598 | 0.602 | 0.028 | 0.587 | 0.626 | +0.009 [-0.005, +0.026] |  | +0.011 |
| hybrid+pb(top=2,beta=0.25,votes) | 29 | 0.603 | 0.613 | 0.059 | 0.594 | 0.626 | +0.014 [-0.008, +0.038] | yes | +0.014 |
| hybrid+pb(top=2,beta=0.5,votes) | 29 | 0.602 | 0.610 | 0.066 | 0.592 | 0.626 | +0.013 [-0.010, +0.037] | yes | +0.012 |
| hybrid+pb(top=2,beta=1.0,votes) | 29 | 0.602 | 0.612 | 0.066 | 0.592 | 0.626 | +0.013 [-0.010, +0.037] | yes | +0.012 |

## C. Cross-encoder rerank (hybrid top 50)

| variant | n | nDCG@10 pooled | condensed pooled | unjudged@10 | device | medicine | diff vs base [95% CI] | gain | diff without 5 motivating queries |
|---|---|---|---|---|---|---|---|---|---|
| hybrid+rr(replace) | 29 | 0.581 | 0.650 | 0.214 | 0.581 | 0.581 | -0.008 [-0.068, +0.052] |  | -0.035 |
| hybrid+rr(rrf) | 29 | 0.619 | 0.634 | 0.069 | 0.626 | 0.603 | +0.030 [-0.013, +0.077] | yes | +0.012 |

## Combinations

| variant | n | nDCG@10 pooled | condensed pooled | unjudged@10 | device | medicine | diff vs base [95% CI] | gain | diff without 5 motivating queries |
|---|---|---|---|---|---|---|---|---|---|
| hybrid+exp(w=0.3,all,dense)+pb(top=2,beta=0.25,votes) | 29 | 0.645 | 0.669 | 0.145 | 0.625 | 0.698 | +0.056 [-0.002, +0.122] | yes | +0.009 |
| hybrid+exp(w=0.3,all,dense)+rr(rrf) | 29 | 0.643 | 0.663 | 0.090 | 0.645 | 0.637 | +0.054 [-0.001, +0.110] | yes | +0.007 |
| hybrid+pb(top=2,beta=0.25,votes)+rr(rrf) | 29 | 0.622 | 0.640 | 0.097 | 0.630 | 0.600 | +0.033 [-0.012, +0.080] | yes | +0.014 |
| hybrid+exp(w=0.3,all,dense)+pb(top=2,beta=0.25,votes)+rr(rrf) | 29 | 0.648 | 0.673 | 0.134 | 0.651 | 0.638 | +0.059 [+0.002, +0.119] | yes | +0.011 |

## Finalists and their unjudged top-10 rows

| variant | nDCG@10 | condensed | unjudged rows (dev) |
|---|---|---|---|
| bm25 | 0.602 | 0.602 | 0 |
| hybrid | 0.589 | 0.589 | 0 |
| bm25+exp(w=0.5,all) | 0.632 | 0.644 | 18 |
| hybrid+exp(w=0.3,all,dense) | 0.632 | 0.651 | 27 |
| hybrid+exp(w=1.0,all,dense) | 0.612 | 0.651 | 35 |
| bm25+pb(top=2,beta=0.1,bm25) | 0.599 | 0.604 | 9 |
| bm25+pb(top=2,beta=1.0,votes) | 0.588 | 0.617 | 26 |
| hybrid+pb(top=2,beta=0.25,votes) | 0.603 | 0.613 | 17 |
| hybrid+rr(rrf) | 0.619 | 0.634 | 20 |
| hybrid+rr(replace) | 0.581 | 0.650 | 62 |
| hybrid+exp(w=0.3,all,dense)+pb(top=2,beta=0.25,votes)+rr(rrf) | 0.648 | 0.673 | 39 |
| bm25+exp(w=0.5,cfr) | 0.606 | 0.615 | 8 |
| hybrid+exp(w=0.3,cfr,bm25side) | 0.597 | 0.598 | 2 |

`results/step17_unjudged.csv`: 263 rows, 138 unique (query, chunk) pairs to grade (the same pair can appear under several variants). Nothing was graded here.
