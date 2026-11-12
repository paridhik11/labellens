# Step 15a: unjudged top-10 results per ablation variant

**Judged means present in the LLM qrels (`data/eval/qrels_t1_llm.tsv`, model
claude-sonnet-5-5); there are no human grades for most queries.** Nothing was graded
in this step and no qrels, pool or grade file was written.

A chunk is unjudged for a query when it is absent from that query's qrels. The metrics
treat unjudged chunks as grade 0, so a variant with many of them is understated, and
differences vs the default are provisional until these rows are graded.

Each variant changes one thing from the default (bm25 k1=1.5 b=0.75 unstemmed, dense
without query prefix, hybrid RRF k=60 with weights 1:1). The grid was fixed in advance.
All 62 queries are searched, each in its own module's chunks, top 10 chunks of the same
ranked list the evaluation uses (search depth 20 at chunk level). Ranks 11 to 20 also
feed Recall@20, MRR and MAP and are not listed here.

| Variant | Unjudged chunks in top 10 | Share of top-10 slots | Section-level top-10 sections with no judged chunk |
|---|---|---|---|
| default_bm25 | 0 | 0.0% | 105 |
| default_dense | 0 | 0.0% | 115 |
| default_hybrid | 10 | 1.6% | 97 |
| rrf_k10 | 0 | 0.0% | 51 |
| rrf_k30 | 13 | 2.1% | 73 |
| rrf_k100 | 14 | 2.3% | 110 |
| w_bm25_2_dense_1 | 27 | 4.4% | 97 |
| w_bm25_3_dense_1 | 34 | 5.5% | 97 |
| w_bm25_1_dense_2 | 21 | 3.4% | 90 |
| w_bm25_1_dense_3 | 25 | 4.0% | 94 |
| bm25_stem | 95 | 15.3% | 170 |
| hybrid_stem | 61 | 9.8% | 134 |
| dense_prefix | 92 | 14.8% | 156 |
| hybrid_prefix | 41 | 6.6% | 114 |

- Rows in `results/step15_unjudged.csv` (one per qid, chunk, variant): 433
- Unique (qid, chunk) pairs over all variants: 285
- Of those, also unjudged under a default system: 10
- Unique pairs per module: device 206, medicine 79

The section-level column is informational: a section counts as judged when any of its
chunks is in the qrels, so a judged section can still hide a better unjudged chunk.
Those chunks are not in the CSV, which lists chunk-level top-10 results only.

