# Step 14b: results by query type

**All tables use LLM-assessed qrels (claude-sonnet-5-5), not human grades.** Chunk level only, nDCG@10 only.

## How to read this
- Each cell is the mean nDCG@10 of one system over the queries of one type, and **n is the
  number of queries behind the row**. Corpus-gap queries (no chunk graded >= 1) and
  no_answer queries are left out, the same rule as the main table in step14_results.md.
  'gaps left out' counts the gap queries removed from that row.
- Rows with n<5 are flagged. With so few queries one query moves the mean by up to
  1/n (0.25 at n=4, 1.0 at n=1), so those rows are descriptive and say nothing about
  which system is better. Rows with n of 5 to 7 are also noisy and have no interval.
- Rows with n>=8 show the mean with a bootstrap 95% interval in brackets (10000
  resamples of the queries in that row, seed 42). The intervals are for each system's own
  mean, not for a difference between systems: overlapping intervals do not mean 'no
  difference' and non-overlapping ones are not a significance test, because all systems
  are scored on the same queries.
- No significance tests are run per type: the cells are too small, and 4 systems x 5 types x
  2 modules would add many more uncorrected comparisons.

## Device module (40 queries after dropping 0 gap(s): none)

| Query type | n | gaps left out | tfidf | bm25 | dense | hybrid | note |
|---|---|---|---|---|---|---|---|
| direct | 10 | 0 | 0.591 [0.449, 0.729] | 0.681 [0.582, 0.783] | 0.488 [0.337, 0.639] | 0.619 [0.517, 0.714] |  |
| vocab_mismatch | 9 | 0 | 0.341 [0.177, 0.512] | 0.365 [0.190, 0.539] | 0.475 [0.339, 0.601] | 0.443 [0.350, 0.539] |  |
| symbol | 5 | 0 | 0.853 | 0.787 | 0.498 | 0.668 |  |
| field_req | 11 | 0 | 0.682 [0.557, 0.801] | 0.650 [0.496, 0.796] | 0.541 [0.355, 0.716] | 0.707 [0.539, 0.838] |  |
| change_impact | 5 | 0 | 0.468 | 0.403 | 0.465 | 0.374 |  |

## Medicine module (17 queries after dropping 0 gap(s): none)

| Query type | n | gaps left out | tfidf | bm25 | dense | hybrid | note |
|---|---|---|---|---|---|---|---|
| direct | 7 | 0 | 0.599 | 0.574 | 0.437 | 0.636 |  |
| vocab_mismatch | 4 | 0 | 0.356 | 0.331 | 0.583 | 0.497 | n<5, descriptive only |
| symbol | 0 | 0 | n/a | n/a | n/a | n/a | no queries |
| field_req | 5 | 0 | 0.748 | 0.811 | 0.648 | 0.779 |  |
| change_impact | 1 | 0 | 0.233 | 0.236 | 0.332 | 0.431 | n<5, descriptive only |

