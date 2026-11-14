# Step 17e: tuning on the development half (29 queries)

**LLM-assessed qrels (claude-sonnet-5-5), not human grades.** Dev half only (seed 42 split, 21 device and 8 medicine queries). Qrels: data/eval/pool_t1_llm.csv read in memory (2531 graded pairs); no qrels file was written. The held-out half is untouched. Settings were chosen on these same queries, so differences here are optimistic and the intervals are descriptive, not tests. Depth 50, nDCG@10, chunk level; queries are searched in their own module.

Unjudged chunks are not in the pooled qrels (the pool came from the old systems). 'condensed' removes them from the list first. Gain rule: best config beats its base by more than 0.01 on both numbers.

- Part boost on bm25: BM25 part scoring showed no gain, so the summed-RRF top-3 vote scoring was also run (both are in the table).
- basemod on bm25: no gain on dev under the gain rule, so it is left out of the combinations.
- pb on bm25: no gain on dev under the gain rule, so it is left out of the combinations.

**Leak check.** The failure-derived synonym groups were written after reading the failure list. Queries that motivated them: q01, q03, q12, q15, q16, q24, q55, q59 (q01, q03, q12, q16, q59 in dev; q15, q24, q55 in held-out). The last column of each table repeats the difference to the base without the motivating queries that are in dev.

## Baselines

| variant | n | nDCG@10 pooled | condensed pooled | unjudged@10 | device | medicine | diff vs base [95% CI] | gain | diff without 5 motivating queries |
|---|---|---|---|---|---|---|---|---|---|
| bm25 | 29 | 0.561 | 0.561 | 0.000 | 0.537 | 0.623 | +0.000 [+0.000, +0.000] |  | +0.000 |
| hybrid | 29 | 0.548 | 0.548 | 0.000 | 0.531 | 0.592 | +0.000 [+0.000, +0.000] |  | +0.000 |
| dense | 29 | 0.490 | 0.490 | 0.000 | 0.482 | 0.509 | +0.000 [+0.000, +0.000] |  | +0.000 |

## D. Light stemming and BGE query prefix

| variant | n | nDCG@10 pooled | condensed pooled | unjudged@10 | device | medicine | diff vs base [95% CI] | gain | diff without 5 motivating queries |
|---|---|---|---|---|---|---|---|---|---|
| bm25+stem | 29 | 0.571 | 0.571 | 0.000 | 0.558 | 0.604 | +0.010 [-0.032, +0.054] |  | +0.005 |
| dense+prefix | 29 | 0.542 | 0.542 | 0.000 | 0.537 | 0.556 | +0.053 [+0.016, +0.092] | yes | +0.053 |
| hybrid+stem | 29 | 0.585 | 0.585 | 0.000 | 0.580 | 0.601 | +0.037 [+0.001, +0.078] | yes | +0.037 |
| hybrid+prefix | 29 | 0.578 | 0.578 | 0.000 | 0.557 | 0.633 | +0.029 [+0.007, +0.051] | yes | +0.025 |
| hybrid+stem+prefix | 29 | 0.608 | 0.608 | 0.000 | 0.608 | 0.608 | +0.060 [+0.022, +0.099] | yes | +0.045 |

## A. Query expansion

| variant | n | nDCG@10 pooled | condensed pooled | unjudged@10 | device | medicine | diff vs base [95% CI] | gain | diff without 5 motivating queries |
|---|---|---|---|---|---|---|---|---|---|
| bm25+exp(w=0.3,all) | 29 | 0.589 | 0.589 | 0.000 | 0.567 | 0.648 | +0.028 [+0.007, +0.053] | yes | +0.006 |
| hybrid+exp(w=0.3,all,bm25side) | 29 | 0.561 | 0.562 | 0.003 | 0.538 | 0.624 | +0.013 [-0.016, +0.047] | yes | +0.002 |
| hybrid+exp(w=0.3,all,dense) | 29 | 0.601 | 0.605 | 0.017 | 0.573 | 0.677 | +0.053 [-0.001, +0.117] | yes | +0.004 |
| bm25+exp(w=0.5,all) | 29 | 0.596 | 0.596 | 0.010 | 0.563 | 0.682 | +0.035 [+0.003, +0.076] | yes | +0.004 |
| hybrid+exp(w=0.5,all,bm25side) | 29 | 0.568 | 0.569 | 0.003 | 0.543 | 0.632 | +0.020 [-0.020, +0.065] | yes | -0.003 |
| hybrid+exp(w=0.5,all,dense) | 29 | 0.599 | 0.604 | 0.017 | 0.571 | 0.672 | +0.051 [-0.009, +0.120] | yes | -0.006 |
| bm25+exp(w=1.0,all) | 29 | 0.572 | 0.586 | 0.069 | 0.529 | 0.687 | +0.012 [-0.035, +0.067] | yes | -0.028 |
| hybrid+exp(w=1.0,all,bm25side) | 29 | 0.569 | 0.571 | 0.017 | 0.542 | 0.642 | +0.021 [-0.022, +0.073] | yes | -0.005 |
| hybrid+exp(w=1.0,all,dense) | 29 | 0.583 | 0.590 | 0.034 | 0.548 | 0.678 | +0.035 [-0.019, +0.098] | yes | -0.008 |
| bm25+exp(w=0.3,cfr) | 29 | 0.568 | 0.568 | 0.000 | 0.546 | 0.623 | +0.007 [-0.002, +0.018] |  | +0.005 |
| hybrid+exp(w=0.3,cfr,bm25side) | 29 | 0.559 | 0.559 | 0.000 | 0.546 | 0.592 | +0.011 [-0.002, +0.032] | yes | +0.013 |
| hybrid+exp(w=0.3,cfr,dense) | 29 | 0.558 | 0.558 | 0.000 | 0.545 | 0.592 | +0.010 [-0.007, +0.030] |  | +0.009 |
| bm25+exp(w=0.5,cfr) | 29 | 0.569 | 0.569 | 0.000 | 0.548 | 0.623 | +0.008 [-0.002, +0.022] |  | +0.007 |
| hybrid+exp(w=0.5,cfr,bm25side) | 29 | 0.559 | 0.559 | 0.000 | 0.546 | 0.592 | +0.011 [-0.003, +0.032] | yes | +0.012 |
| hybrid+exp(w=0.5,cfr,dense) | 29 | 0.558 | 0.559 | 0.003 | 0.545 | 0.592 | +0.010 [-0.007, +0.030] | yes | +0.007 |
| bm25+exp(w=1.0,cfr) | 29 | 0.560 | 0.560 | 0.000 | 0.536 | 0.623 | -0.000 [-0.010, +0.010] |  | -0.002 |
| hybrid+exp(w=1.0,cfr,bm25side) | 29 | 0.557 | 0.557 | 0.000 | 0.544 | 0.592 | +0.009 [-0.007, +0.033] |  | +0.011 |
| hybrid+exp(w=1.0,cfr,dense) | 29 | 0.550 | 0.551 | 0.003 | 0.534 | 0.592 | +0.002 [-0.016, +0.021] |  | +0.002 |

## B. Part boost

| variant | n | nDCG@10 pooled | condensed pooled | unjudged@10 | device | medicine | diff vs base [95% CI] | gain | diff without 5 motivating queries |
|---|---|---|---|---|---|---|---|---|---|
| bm25+pb(top=1,beta=0.1,bm25) | 29 | 0.565 | 0.565 | 0.003 | 0.530 | 0.656 | +0.004 [-0.027, +0.033] |  | -0.000 |
| bm25+pb(top=1,beta=0.25,bm25) | 29 | 0.525 | 0.531 | 0.021 | 0.482 | 0.639 | -0.036 [-0.086, +0.011] |  | -0.037 |
| bm25+pb(top=1,beta=0.5,bm25) | 29 | 0.504 | 0.515 | 0.076 | 0.452 | 0.639 | -0.057 [-0.116, -0.002] |  | -0.061 |
| bm25+pb(top=1,beta=1.0,bm25) | 29 | 0.508 | 0.520 | 0.076 | 0.458 | 0.639 | -0.053 [-0.116, +0.006] |  | -0.054 |
| bm25+pb(top=2,beta=0.1,bm25) | 29 | 0.561 | 0.561 | 0.000 | 0.533 | 0.634 | +0.000 [-0.027, +0.022] |  | -0.010 |
| bm25+pb(top=2,beta=0.25,bm25) | 29 | 0.551 | 0.551 | 0.003 | 0.519 | 0.634 | -0.010 [-0.052, +0.026] |  | -0.027 |
| bm25+pb(top=2,beta=0.5,bm25) | 29 | 0.544 | 0.546 | 0.014 | 0.510 | 0.634 | -0.017 [-0.076, +0.034] |  | -0.041 |
| bm25+pb(top=2,beta=1.0,bm25) | 29 | 0.544 | 0.550 | 0.014 | 0.510 | 0.634 | -0.017 [-0.076, +0.034] |  | -0.041 |
| hybrid+pb(top=1,beta=0.1,bm25) | 29 | 0.564 | 0.564 | 0.000 | 0.543 | 0.619 | +0.016 [-0.036, +0.062] | yes | +0.008 |
| hybrid+pb(top=1,beta=0.25,bm25) | 29 | 0.562 | 0.562 | 0.007 | 0.537 | 0.627 | +0.014 [-0.053, +0.077] | yes | +0.011 |
| hybrid+pb(top=1,beta=0.5,bm25) | 29 | 0.522 | 0.533 | 0.038 | 0.486 | 0.617 | -0.026 [-0.104, +0.048] |  | -0.018 |
| hybrid+pb(top=1,beta=1.0,bm25) | 29 | 0.518 | 0.530 | 0.048 | 0.480 | 0.617 | -0.030 [-0.116, +0.049] |  | -0.024 |
| hybrid+pb(top=2,beta=0.1,bm25) | 29 | 0.553 | 0.553 | 0.000 | 0.538 | 0.592 | +0.005 [-0.038, +0.041] |  | -0.006 |
| hybrid+pb(top=2,beta=0.25,bm25) | 29 | 0.564 | 0.564 | 0.000 | 0.553 | 0.592 | +0.016 [-0.042, +0.067] | yes | -0.004 |
| hybrid+pb(top=2,beta=0.5,bm25) | 29 | 0.555 | 0.555 | 0.007 | 0.541 | 0.592 | +0.007 [-0.063, +0.067] |  | -0.012 |
| hybrid+pb(top=2,beta=1.0,bm25) | 29 | 0.555 | 0.557 | 0.010 | 0.541 | 0.592 | +0.007 [-0.063, +0.067] |  | -0.012 |
| bm25+pb(top=1,beta=0.1,votes) | 29 | 0.549 | 0.549 | 0.003 | 0.534 | 0.589 | -0.011 [-0.063, +0.029] |  | -0.019 |
| bm25+pb(top=1,beta=0.25,votes) | 29 | 0.507 | 0.511 | 0.017 | 0.492 | 0.548 | -0.054 [-0.131, +0.008] |  | -0.058 |
| bm25+pb(top=1,beta=0.5,votes) | 29 | 0.492 | 0.504 | 0.066 | 0.471 | 0.548 | -0.069 [-0.148, -0.003] |  | -0.075 |
| bm25+pb(top=1,beta=1.0,votes) | 29 | 0.490 | 0.509 | 0.072 | 0.468 | 0.548 | -0.071 [-0.150, -0.005] |  | -0.076 |
| bm25+pb(top=2,beta=0.1,votes) | 29 | 0.558 | 0.558 | 0.000 | 0.534 | 0.623 | -0.002 [-0.022, +0.015] |  | -0.007 |
| bm25+pb(top=2,beta=0.25,votes) | 29 | 0.551 | 0.551 | 0.000 | 0.523 | 0.623 | -0.010 [-0.044, +0.018] |  | -0.017 |
| bm25+pb(top=2,beta=0.5,votes) | 29 | 0.549 | 0.551 | 0.014 | 0.521 | 0.623 | -0.012 [-0.045, +0.016] |  | -0.018 |
| bm25+pb(top=2,beta=1.0,votes) | 29 | 0.549 | 0.551 | 0.014 | 0.521 | 0.623 | -0.012 [-0.045, +0.016] |  | -0.018 |

## C. Cross-encoder rerank (hybrid top 50)

| variant | n | nDCG@10 pooled | condensed pooled | unjudged@10 | device | medicine | diff vs base [95% CI] | gain | diff without 5 motivating queries |
|---|---|---|---|---|---|---|---|---|---|
| hybrid+rr(replace) | 29 | 0.568 | 0.583 | 0.048 | 0.562 | 0.585 | +0.020 [-0.033, +0.075] | yes | +0.000 |
| hybrid+rr(rrf) | 29 | 0.590 | 0.590 | 0.007 | 0.590 | 0.592 | +0.042 [+0.002, +0.085] | yes | +0.028 |

## Combinations

| variant | n | nDCG@10 pooled | condensed pooled | unjudged@10 | device | medicine | diff vs base [95% CI] | gain | diff without 5 motivating queries |
|---|---|---|---|---|---|---|---|---|---|
| hybrid+stem+prefix+exp(w=0.3,all,dense) | 29 | 0.641 | 0.642 | 0.007 | 0.626 | 0.683 | +0.093 [+0.036, +0.155] | yes | +0.048 |
| hybrid+stem+prefix+pb(top=1,beta=0.1,bm25) | 29 | 0.608 | 0.608 | 0.003 | 0.595 | 0.643 | +0.060 [+0.006, +0.109] | yes | +0.051 |
| hybrid+exp(w=0.3,all,dense)+pb(top=1,beta=0.1,bm25) | 29 | 0.596 | 0.598 | 0.010 | 0.559 | 0.693 | +0.047 [-0.026, +0.119] | yes | -0.001 |
| hybrid+stem+prefix+exp(w=0.3,all,dense)+pb(top=1,beta=0.1,bm25) | 29 | 0.644 | 0.644 | 0.007 | 0.620 | 0.705 | +0.095 [+0.030, +0.158] | yes | +0.062 |
| hybrid+stem+prefix+rr(rrf) | 29 | 0.610 | 0.612 | 0.010 | 0.617 | 0.594 | +0.062 [+0.019, +0.108] | yes | +0.043 |
| hybrid+exp(w=0.3,all,dense)+rr(rrf) | 29 | 0.618 | 0.620 | 0.010 | 0.612 | 0.631 | +0.069 [+0.018, +0.124] | yes | +0.026 |
| hybrid+stem+prefix+exp(w=0.3,all,dense)+rr(rrf) | 29 | 0.631 | 0.635 | 0.017 | 0.635 | 0.621 | +0.083 [+0.032, +0.138] | yes | +0.041 |
| hybrid+pb(top=1,beta=0.1,bm25)+rr(rrf) | 29 | 0.602 | 0.603 | 0.014 | 0.604 | 0.596 | +0.054 [+0.009, +0.098] | yes | +0.043 |
| hybrid+stem+prefix+pb(top=1,beta=0.1,bm25)+rr(rrf) | 29 | 0.611 | 0.615 | 0.010 | 0.609 | 0.617 | +0.063 [+0.020, +0.108] | yes | +0.048 |
| hybrid+exp(w=0.3,all,dense)+pb(top=1,beta=0.1,bm25)+rr(rrf) | 29 | 0.615 | 0.618 | 0.010 | 0.607 | 0.638 | +0.067 [+0.019, +0.116] | yes | +0.040 |
| hybrid+stem+prefix+exp(w=0.3,all,dense)+pb(top=1,beta=0.1,bm25)+rr(rrf) | 29 | 0.620 | 0.627 | 0.014 | 0.611 | 0.643 | +0.072 [+0.027, +0.119] | yes | +0.047 |

## Finalists and their unjudged top-10 rows

| variant | nDCG@10 | condensed | unjudged rows (dev) |
|---|---|---|---|
| bm25 | 0.561 | 0.561 | 0 |
| hybrid | 0.548 | 0.548 | 0 |
| bm25+stem | 0.571 | 0.571 | 0 |
| hybrid+stem+prefix | 0.608 | 0.608 | 0 |
| dense+prefix | 0.542 | 0.542 | 0 |
| bm25+exp(w=0.5,all) | 0.596 | 0.596 | 3 |
| hybrid+exp(w=0.3,all,dense) | 0.601 | 0.605 | 5 |
| bm25+pb(top=1,beta=0.1,bm25) | 0.565 | 0.565 | 1 |
| hybrid+pb(top=1,beta=0.1,bm25) | 0.564 | 0.564 | 0 |
| hybrid+rr(rrf) | 0.590 | 0.590 | 2 |
| hybrid+stem+prefix+exp(w=0.3,all,dense)+pb(top=1,beta=0.1,bm25) | 0.644 | 0.644 | 2 |
| bm25+exp(w=0.5,cfr) | 0.569 | 0.569 | 0 |
| hybrid+exp(w=0.3,cfr,bm25side) | 0.559 | 0.559 | 0 |

`results/step17_unjudged.csv`: 13 rows, 11 unique (query, chunk) pairs to grade (the same pair can appear under several variants). Nothing was graded here.
