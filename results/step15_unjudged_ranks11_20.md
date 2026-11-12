# Step 15a (addendum): unjudged chunks at ranks 11 to 20

**Judged means present in the LLM qrels (claude-sonnet-5-5).** Ranks 11 to 20 of the
chunk-level ranking feed Recall@20, MRR and MAP (nDCG@10 does not use them). Nothing was
graded and these pairs are **not** in `data/eval/pool_t1_extra.csv`.

| Variant | Unjudged chunks at ranks 11-20 | Share of those slots |
|---|---|---|
| default_bm25 | 404 | 65.2% |
| default_dense | 487 | 78.5% |
| default_hybrid | 396 | 63.9% |
| rrf_k10 | 201 | 32.4% |
| rrf_k30 | 332 | 53.5% |
| rrf_k100 | 392 | 63.2% |
| w_bm25_2_dense_1 | 347 | 56.0% |
| w_bm25_3_dense_1 | 285 | 46.0% |
| w_bm25_1_dense_2 | 359 | 57.9% |
| w_bm25_1_dense_3 | 318 | 51.3% |
| bm25_stem | 371 | 59.8% |
| hybrid_stem | 385 | 62.1% |
| dense_prefix | 407 | 65.6% |
| hybrid_prefix | 384 | 61.9% |

- Rows in `results/step15_unjudged_ranks11_20.csv` (one per qid, chunk, variant): 5068
- Unique (qid, chunk) pairs at ranks 11 to 20: 1476
- Of those, already in the top-10 listing (285 pairs): 229
- **Extra pairs not in the top-10 listing: 1247**
- Pool size if added: 285 + 1247 = 1532

