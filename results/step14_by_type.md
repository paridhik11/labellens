# Step 14b: results by query type

**All tables use LLM-assessed qrels (claude-sonnet-5-5), not human grades.** Chunk level only, nDCG@10 only.

## How to read this
- Each cell is the mean nDCG@10 of one system over the queries of one type, and **n is the
  number of queries behind the row**. Corpus-gap queries (no chunk graded >= 1) and
  no_answer queries are left out, the same rule as the main table in step14_results.md.
  'gaps left out' counts the gap queries removed from that row.
- Rows with n<5 are flagged. With so few queries one query moves the mean by up to
  1/n (0.25 at n=4, 1.0 at n=1), so those rows are descriptive and say nothing about
  which system is better. Rows with n of 5 to 11 are also noisy.
- No significance tests are run per type: the cells are too small, and 4 systems x 5 types x
  2 modules would add many more uncorrected comparisons.

## Device module (40 queries after dropping 0 gap(s): none)

| Query type | n | gaps left out | tfidf | bm25 | dense | hybrid | note |
|---|---|---|---|---|---|---|---|
| direct | 10 | 0 | 0.633 | 0.728 | 0.518 | 0.659 |  |
| vocab_mismatch | 9 | 0 | 0.371 | 0.395 | 0.543 | 0.489 |  |
| symbol | 5 | 0 | 0.910 | 0.840 | 0.524 | 0.709 |  |
| field_req | 11 | 0 | 0.735 | 0.692 | 0.579 | 0.754 |  |
| change_impact | 5 | 0 | 0.551 | 0.465 | 0.510 | 0.423 |  |

## Medicine module (17 queries after dropping 0 gap(s): none)

| Query type | n | gaps left out | tfidf | bm25 | dense | hybrid | note |
|---|---|---|---|---|---|---|---|
| direct | 7 | 0 | 0.662 | 0.636 | 0.476 | 0.716 |  |
| vocab_mismatch | 4 | 0 | 0.384 | 0.355 | 0.601 | 0.526 | n<5, descriptive only |
| symbol | 0 | 0 | n/a | n/a | n/a | n/a | no queries |
| field_req | 5 | 0 | 0.798 | 0.868 | 0.711 | 0.845 |  |
| change_impact | 1 | 0 | 0.514 | 0.521 | 0.732 | 0.832 | n<5, descriptive only |

