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
| direct | 10 | 0 | 0.613 [0.466, 0.758] | 0.706 [0.603, 0.808] | 0.510 [0.346, 0.675] | 0.643 [0.534, 0.747] |  |
| vocab_mismatch | 9 | 0 | 0.357 [0.185, 0.540] | 0.381 [0.198, 0.564] | 0.503 [0.354, 0.641] | 0.467 [0.368, 0.570] |  |
| symbol | 5 | 0 | 0.882 | 0.814 | 0.513 | 0.689 |  |
| field_req | 11 | 0 | 0.706 [0.581, 0.823] | 0.675 [0.517, 0.822] | 0.568 [0.374, 0.752] | 0.739 [0.561, 0.873] |  |
| change_impact | 5 | 0 | 0.500 | 0.429 | 0.497 | 0.394 |  |

## Medicine module (17 queries after dropping 0 gap(s): none)

| Query type | n | gaps left out | tfidf | bm25 | dense | hybrid | note |
|---|---|---|---|---|---|---|---|
| direct | 7 | 0 | 0.634 | 0.606 | 0.455 | 0.677 |  |
| vocab_mismatch | 4 | 0 | 0.384 | 0.355 | 0.601 | 0.526 | n<5, descriptive only |
| symbol | 0 | 0 | n/a | n/a | n/a | n/a | no queries |
| field_req | 5 | 0 | 0.773 | 0.837 | 0.678 | 0.809 |  |
| change_impact | 1 | 0 | 0.446 | 0.452 | 0.636 | 0.825 | n<5, descriptive only |

