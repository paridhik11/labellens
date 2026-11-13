# Step 15b: ablation tables

**All tables use LLM-assessed qrels (claude-sonnet-5-5), not human grades.** Sensitivity analysis: every variant changes one thing from
the default (bm25 k1=1.5 b=0.75 unstemmed, dense bge-small-en-v1.5 without query prefix,
hybrid RRF k=60 weights 1:1). The grid was fixed before any result was seen and nothing
here is tuned. Device and medicine are separate tables.

## How to read this
- Each variant is compared with the default it changes (named in its row). The table also
  shows that default as a reference row.
- nDCG@10 is the primary metric. The interval on each nDCG@10 is a percentile bootstrap over
  queries (10000 resamples, seed 42). The difference vs default is a paired bootstrap over
  queries with a two-sided percentile bootstrap p-value (resolution about 0.0002).
  When a variant ranks most queries exactly like its default, many resamples have a mean
  difference of exactly 0, so p is conservative.
- **Holm (this ablation)** adjusts the raw p within one ablation at one level, both modules
  together (rrf_k 6 comparisons, weights 8, stemming 4, query_prefix 4).
  **Holm (all 22)** adjusts over all 22 nDCG@10 comparisons at that level
  (11 variants x 2 modules). Chunk and section level are separate families. A Holm p is
  never smaller than the raw p.
- **unjudged@10** is the number of top-10 chunks (chunk level) or top-10 sections (section
  level) of the variant that have no LLM grade, summed over the scored queries. A section
  counts as judged when any of its chunks is graded. Unjudged items score 0. At chunk level
  every value is 0, so no chunk-level nDCG@10 is understated by missing grades. At section
  level the value is NOT 0: the extra pool graded top-10 chunks, not the sections that the
  chunk ranking aggregates into (built from the top 100 chunks), so some top-10 sections hold
  no graded chunk. Read section-level differences with that in mind.
- Scored queries are the answerable graded queries (no_answer queries and corpus gaps
  excluded), as in the Step 14 main tables.

> **Recall@20, MAP and MRR are provisional until the depth-20 pool is graded.** They reach past rank 10, and the qrels only cover the top 10 of each variant plus the original pool. The chunk-level tables show how many ranks 11 to 20 are still unjudged (counted as 0). nDCG@10 is the primary metric and uses only the top 10.
> The columns marked * (Recall@20, MRR, MAP) are those provisional metrics and carry no
> p-values.

## Ablation: RRF smoothing constant k (default 60) (`rrf_k`)

### Device, chunk level, 40 queries. LLM-assessed qrels (claude-sonnet-5-5), not human grades

| Variant | nDCG@10 [95% CI] | diff vs default [95% CI] | raw p | Holm (this ablation) | Holm (all 22) | unjudged@10 | unjudged ranks 11-20 | Recall@20* | MRR* | MAP* |
|---|---|---|---|---|---|---|---|---|---|---|
| default_hybrid (default) | 0.604 [0.527, 0.679] | reference |  |  |  | 0 | 180 | 0.800 | 0.786 | 0.561 |
| rrf_k10 (vs default_hybrid) | 0.626 [0.550, 0.696] | +0.021 [+0.001, +0.043] | 0.038 | 0.189 | 0.680 | 0 | 76 | 0.883 | 0.799 | 0.616 |
| rrf_k30 (vs default_hybrid) | 0.619 [0.544, 0.689] | +0.015 [+0.004, +0.028] | 0.0002 | 0.001 | 0.004 | 0 | 147 | 0.839 | 0.786 | 0.579 |
| rrf_k100 (vs default_hybrid) | 0.605 [0.526, 0.680] | +0.001 [-0.003, +0.006] | 0.879 | 1.000 | 1.000 | 0 | 179 | 0.800 | 0.786 | 0.558 |

### Device, section level, 40 queries. LLM-assessed qrels (claude-sonnet-5-5), not human grades

| Variant | nDCG@10 [95% CI] | diff vs default [95% CI] | raw p | Holm (this ablation) | Holm (all 22) | unjudged@10 | Recall@20* | MRR* | MAP* |
|---|---|---|---|---|---|---|---|---|---|
| default_hybrid (default) | 0.720 [0.640, 0.794] | reference |  |  |  | 31 | 0.922 | 0.808 | 0.689 |
| rrf_k10 (vs default_hybrid) | 0.749 [0.677, 0.816] | +0.030 [+0.012, +0.049] | 0.0008 | 0.005 | 0.018 | 16 | 0.951 | 0.812 | 0.715 |
| rrf_k30 (vs default_hybrid) | 0.735 [0.659, 0.806] | +0.015 [+0.004, +0.027] | 0.004 | 0.022 | 0.084 | 20 | 0.962 | 0.808 | 0.704 |
| rrf_k100 (vs default_hybrid) | 0.716 [0.635, 0.791] | -0.004 [-0.015, +0.005] | 0.402 | 1.000 | 1.000 | 37 | 0.878 | 0.807 | 0.681 |

### Medicine, chunk level, 17 queries. LLM-assessed qrels (claude-sonnet-5-5), not human grades

| Variant | nDCG@10 [95% CI] | diff vs default [95% CI] | raw p | Holm (this ablation) | Holm (all 22) | unjudged@10 | unjudged ranks 11-20 | Recall@20* | MRR* | MAP* |
|---|---|---|---|---|---|---|---|---|---|---|
| default_hybrid (default) | 0.689 [0.578, 0.789] | reference |  |  |  | 0 | 88 | 0.824 | 0.918 | 0.652 |
| rrf_k10 (vs default_hybrid) | 0.703 [0.591, 0.800] | +0.013 [-0.007, +0.042] | 0.278 | 1.000 | 1.000 | 0 | 37 | 0.916 | 0.909 | 0.678 |
| rrf_k30 (vs default_hybrid) | 0.691 [0.580, 0.790] | +0.002 [-0.002, +0.007] | 0.399 | 1.000 | 1.000 | 0 | 69 | 0.845 | 0.918 | 0.657 |
| rrf_k100 (vs default_hybrid) | 0.684 [0.571, 0.786] | -0.005 [-0.020, +0.003] | 0.667 | 1.000 | 1.000 | 0 | 88 | 0.824 | 0.918 | 0.654 |

### Medicine, section level, 17 queries. LLM-assessed qrels (claude-sonnet-5-5), not human grades

| Variant | nDCG@10 [95% CI] | diff vs default [95% CI] | raw p | Holm (this ablation) | Holm (all 22) | unjudged@10 | Recall@20* | MRR* | MAP* |
|---|---|---|---|---|---|---|---|---|---|
| default_hybrid (default) | 0.806 [0.695, 0.891] | reference |  |  |  | 25 | 0.973 | 0.949 | 0.765 |
| rrf_k10 (vs default_hybrid) | 0.815 [0.730, 0.884] | +0.008 [-0.025, +0.046] | 0.691 | 1.000 | 1.000 | 20 | 0.973 | 0.950 | 0.743 |
| rrf_k30 (vs default_hybrid) | 0.820 [0.708, 0.901] | +0.013 [-0.007, +0.040] | 0.284 | 1.000 | 1.000 | 23 | 0.973 | 0.949 | 0.763 |
| rrf_k100 (vs default_hybrid) | 0.806 [0.695, 0.891] | -0.001 [-0.006, +0.003] | 0.830 | 1.000 | 1.000 | 27 | 0.973 | 0.949 | 0.768 |

## Ablation: RRF weights bm25:dense (default 1:1) (`weights`)

### Device, chunk level, 40 queries. LLM-assessed qrels (claude-sonnet-5-5), not human grades

| Variant | nDCG@10 [95% CI] | diff vs default [95% CI] | raw p | Holm (this ablation) | Holm (all 22) | unjudged@10 | unjudged ranks 11-20 | Recall@20* | MRR* | MAP* |
|---|---|---|---|---|---|---|---|---|---|---|
| default_hybrid (default) | 0.604 [0.527, 0.679] | reference |  |  |  | 0 | 180 | 0.800 | 0.786 | 0.561 |
| w_bm25_2_dense_1 (vs default_hybrid) | 0.618 [0.540, 0.694] | +0.014 [-0.007, +0.036] | 0.213 | 1.000 | 1.000 | 0 | 169 | 0.824 | 0.818 | 0.586 |
| w_bm25_3_dense_1 (vs default_hybrid) | 0.632 [0.554, 0.706] | +0.028 [-0.000, +0.058] | 0.051 | 0.411 | 0.874 | 0 | 150 | 0.842 | 0.838 | 0.613 |
| w_bm25_1_dense_2 (vs default_hybrid) | 0.594 [0.519, 0.665] | -0.010 [-0.035, +0.013] | 0.371 | 1.000 | 1.000 | 0 | 161 | 0.788 | 0.798 | 0.525 |
| w_bm25_1_dense_3 (vs default_hybrid) | 0.583 [0.505, 0.658] | -0.022 [-0.055, +0.011] | 0.190 | 1.000 | 1.000 | 0 | 151 | 0.777 | 0.813 | 0.514 |

### Device, section level, 40 queries. LLM-assessed qrels (claude-sonnet-5-5), not human grades

| Variant | nDCG@10 [95% CI] | diff vs default [95% CI] | raw p | Holm (this ablation) | Holm (all 22) | unjudged@10 | Recall@20* | MRR* | MAP* |
|---|---|---|---|---|---|---|---|---|---|
| default_hybrid (default) | 0.720 [0.640, 0.794] | reference |  |  |  | 31 | 0.922 | 0.808 | 0.689 |
| w_bm25_2_dense_1 (vs default_hybrid) | 0.730 [0.648, 0.806] | +0.010 [-0.014, +0.037] | 0.428 | 1.000 | 1.000 | 37 | 0.917 | 0.848 | 0.714 |
| w_bm25_3_dense_1 (vs default_hybrid) | 0.729 [0.647, 0.804] | +0.009 [-0.019, +0.039] | 0.534 | 1.000 | 1.000 | 37 | 0.912 | 0.868 | 0.719 |
| w_bm25_1_dense_2 (vs default_hybrid) | 0.709 [0.631, 0.782] | -0.010 [-0.032, +0.012] | 0.340 | 1.000 | 1.000 | 28 | 0.890 | 0.822 | 0.658 |
| w_bm25_1_dense_3 (vs default_hybrid) | 0.704 [0.624, 0.778] | -0.016 [-0.040, +0.008] | 0.202 | 1.000 | 1.000 | 29 | 0.877 | 0.827 | 0.650 |

### Medicine, chunk level, 17 queries. LLM-assessed qrels (claude-sonnet-5-5), not human grades

| Variant | nDCG@10 [95% CI] | diff vs default [95% CI] | raw p | Holm (this ablation) | Holm (all 22) | unjudged@10 | unjudged ranks 11-20 | Recall@20* | MRR* | MAP* |
|---|---|---|---|---|---|---|---|---|---|---|
| default_hybrid (default) | 0.689 [0.578, 0.789] | reference |  |  |  | 0 | 88 | 0.824 | 0.918 | 0.652 |
| w_bm25_2_dense_1 (vs default_hybrid) | 0.683 [0.568, 0.784] | -0.006 [-0.031, +0.018] | 0.619 | 1.000 | 1.000 | 0 | 73 | 0.841 | 0.855 | 0.634 |
| w_bm25_3_dense_1 (vs default_hybrid) | 0.693 [0.580, 0.793] | +0.004 [-0.023, +0.030] | 0.771 | 1.000 | 1.000 | 0 | 61 | 0.858 | 0.858 | 0.645 |
| w_bm25_1_dense_2 (vs default_hybrid) | 0.664 [0.531, 0.783] | -0.025 [-0.074, +0.011] | 0.258 | 1.000 | 1.000 | 0 | 78 | 0.847 | 0.870 | 0.626 |
| w_bm25_1_dense_3 (vs default_hybrid) | 0.662 [0.531, 0.782] | -0.027 [-0.091, +0.028] | 0.401 | 1.000 | 1.000 | 0 | 70 | 0.800 | 0.838 | 0.601 |

### Medicine, section level, 17 queries. LLM-assessed qrels (claude-sonnet-5-5), not human grades

| Variant | nDCG@10 [95% CI] | diff vs default [95% CI] | raw p | Holm (this ablation) | Holm (all 22) | unjudged@10 | Recall@20* | MRR* | MAP* |
|---|---|---|---|---|---|---|---|---|---|
| default_hybrid (default) | 0.806 [0.695, 0.891] | reference |  |  |  | 25 | 0.973 | 0.949 | 0.765 |
| w_bm25_2_dense_1 (vs default_hybrid) | 0.790 [0.674, 0.881] | -0.016 [-0.073, +0.037] | 0.570 | 1.000 | 1.000 | 27 | 0.958 | 0.894 | 0.723 |
| w_bm25_3_dense_1 (vs default_hybrid) | 0.792 [0.679, 0.881] | -0.014 [-0.071, +0.040] | 0.624 | 1.000 | 1.000 | 25 | 0.943 | 0.897 | 0.705 |
| w_bm25_1_dense_2 (vs default_hybrid) | 0.806 [0.709, 0.891] | -0.000 [-0.044, +0.046] | 0.974 | 1.000 | 1.000 | 23 | 0.940 | 0.901 | 0.725 |
| w_bm25_1_dense_3 (vs default_hybrid) | 0.772 [0.670, 0.865] | -0.034 [-0.094, +0.020] | 0.232 | 1.000 | 1.000 | 28 | 0.932 | 0.870 | 0.707 |

## Ablation: Light stemming in BM25 (`stemming`)

### Device, chunk level, 40 queries. LLM-assessed qrels (claude-sonnet-5-5), not human grades

| Variant | nDCG@10 [95% CI] | diff vs default [95% CI] | raw p | Holm (this ablation) | Holm (all 22) | unjudged@10 | unjudged ranks 11-20 | Recall@20* | MRR* | MAP* |
|---|---|---|---|---|---|---|---|---|---|---|
| default_bm25 (default) | 0.603 [0.516, 0.685] | reference |  |  |  | 0 | 222 | 0.795 | 0.818 | 0.580 |
| default_hybrid (default) | 0.604 [0.527, 0.679] | reference |  |  |  | 0 | 180 | 0.800 | 0.786 | 0.561 |
| bm25_stem (vs default_bm25) | 0.643 [0.562, 0.719] | +0.040 [-0.004, +0.087] | 0.079 | 0.238 | 1.000 | 0 | 209 | 0.838 | 0.832 | 0.619 |
| hybrid_stem (vs default_hybrid) | 0.657 [0.589, 0.720] | +0.053 [+0.020, +0.090] | 0.001 | 0.004 | 0.021 | 0 | 174 | 0.829 | 0.840 | 0.602 |

### Device, section level, 40 queries. LLM-assessed qrels (claude-sonnet-5-5), not human grades

| Variant | nDCG@10 [95% CI] | diff vs default [95% CI] | raw p | Holm (this ablation) | Holm (all 22) | unjudged@10 | Recall@20* | MRR* | MAP* |
|---|---|---|---|---|---|---|---|---|---|
| default_bm25 (default) | 0.683 [0.593, 0.768] | reference |  |  |  | 48 | 0.876 | 0.845 | 0.680 |
| default_hybrid (default) | 0.720 [0.640, 0.794] | reference |  |  |  | 31 | 0.922 | 0.808 | 0.689 |
| bm25_stem (vs default_bm25) | 0.730 [0.650, 0.805] | +0.047 [+0.007, +0.090] | 0.022 | 0.067 | 0.403 | 51 | 0.922 | 0.865 | 0.723 |
| hybrid_stem (vs default_hybrid) | 0.764 [0.689, 0.830] | +0.044 [+0.013, +0.078] | 0.002 | 0.009 | 0.046 | 37 | 0.936 | 0.866 | 0.725 |

### Medicine, chunk level, 17 queries. LLM-assessed qrels (claude-sonnet-5-5), not human grades

| Variant | nDCG@10 [95% CI] | diff vs default [95% CI] | raw p | Holm (this ablation) | Holm (all 22) | unjudged@10 | unjudged ranks 11-20 | Recall@20* | MRR* | MAP* |
|---|---|---|---|---|---|---|---|---|---|---|
| default_bm25 (default) | 0.606 [0.474, 0.726] | reference |  |  |  | 0 | 89 | 0.805 | 0.774 | 0.551 |
| default_hybrid (default) | 0.689 [0.578, 0.789] | reference |  |  |  | 0 | 88 | 0.824 | 0.918 | 0.652 |
| bm25_stem (vs default_bm25) | 0.611 [0.471, 0.739] | +0.005 [-0.036, +0.042] | 0.799 | 0.876 | 1.000 | 0 | 91 | 0.801 | 0.826 | 0.581 |
| hybrid_stem (vs default_hybrid) | 0.663 [0.520, 0.788] | -0.026 [-0.094, +0.019] | 0.438 | 0.876 | 1.000 | 0 | 93 | 0.754 | 0.859 | 0.599 |

### Medicine, section level, 17 queries. LLM-assessed qrels (claude-sonnet-5-5), not human grades

| Variant | nDCG@10 [95% CI] | diff vs default [95% CI] | raw p | Holm (this ablation) | Holm (all 22) | unjudged@10 | Recall@20* | MRR* | MAP* |
|---|---|---|---|---|---|---|---|---|---|
| default_bm25 (default) | 0.678 [0.563, 0.786] | reference |  |  |  | 33 | 0.896 | 0.780 | 0.607 |
| default_hybrid (default) | 0.806 [0.695, 0.891] | reference |  |  |  | 25 | 0.973 | 0.949 | 0.765 |
| bm25_stem (vs default_bm25) | 0.693 [0.549, 0.824] | +0.015 [-0.037, +0.066] | 0.575 | 1.000 | 1.000 | 34 | 0.899 | 0.843 | 0.660 |
| hybrid_stem (vs default_hybrid) | 0.785 [0.661, 0.889] | -0.021 [-0.088, +0.028] | 0.504 | 1.000 | 1.000 | 24 | 0.963 | 0.900 | 0.741 |

## Ablation: BGE retrieval instruction prefix on queries (`query_prefix`)

### Device, chunk level, 40 queries. LLM-assessed qrels (claude-sonnet-5-5), not human grades

| Variant | nDCG@10 [95% CI] | diff vs default [95% CI] | raw p | Holm (this ablation) | Holm (all 22) | unjudged@10 | unjudged ranks 11-20 | Recall@20* | MRR* | MAP* |
|---|---|---|---|---|---|---|---|---|---|---|
| default_dense (default) | 0.523 [0.433, 0.613] | reference |  |  |  | 0 | 240 | 0.642 | 0.748 | 0.426 |
| default_hybrid (default) | 0.604 [0.527, 0.679] | reference |  |  |  | 0 | 180 | 0.800 | 0.786 | 0.561 |
| dense_prefix (vs default_dense) | 0.572 [0.482, 0.660] | +0.049 [+0.017, +0.083] | 0.001 | 0.006 | 0.028 | 0 | 226 | 0.712 | 0.821 | 0.492 |
| hybrid_prefix (vs default_hybrid) | 0.625 [0.547, 0.699] | +0.021 [-0.004, +0.047] | 0.098 | 0.196 | 1.000 | 0 | 186 | 0.818 | 0.828 | 0.598 |

### Device, section level, 40 queries. LLM-assessed qrels (claude-sonnet-5-5), not human grades

| Variant | nDCG@10 [95% CI] | diff vs default [95% CI] | raw p | Holm (this ablation) | Holm (all 22) | unjudged@10 | Recall@20* | MRR* | MAP* |
|---|---|---|---|---|---|---|---|---|---|
| default_dense (default) | 0.653 [0.572, 0.735] | reference |  |  |  | 43 | 0.839 | 0.779 | 0.573 |
| default_hybrid (default) | 0.720 [0.640, 0.794] | reference |  |  |  | 31 | 0.922 | 0.808 | 0.689 |
| dense_prefix (vs default_dense) | 0.705 [0.634, 0.775] | +0.052 [+0.016, +0.087] | 0.003 | 0.010 | 0.052 | 45 | 0.861 | 0.833 | 0.622 |
| hybrid_prefix (vs default_hybrid) | 0.729 [0.648, 0.803] | +0.009 [-0.017, +0.034] | 0.463 | 1.000 | 1.000 | 35 | 0.912 | 0.853 | 0.717 |

### Medicine, chunk level, 17 queries. LLM-assessed qrels (claude-sonnet-5-5), not human grades

| Variant | nDCG@10 [95% CI] | diff vs default [95% CI] | raw p | Holm (this ablation) | Holm (all 22) | unjudged@10 | unjudged ranks 11-20 | Recall@20* | MRR* | MAP* |
|---|---|---|---|---|---|---|---|---|---|---|
| default_dense (default) | 0.565 [0.421, 0.702] | reference |  |  |  | 0 | 116 | 0.681 | 0.682 | 0.478 |
| default_hybrid (default) | 0.689 [0.578, 0.789] | reference |  |  |  | 0 | 88 | 0.824 | 0.918 | 0.652 |
| dense_prefix (vs default_dense) | 0.621 [0.485, 0.747] | +0.056 [+0.013, +0.108] | 0.004 | 0.011 | 0.072 | 0 | 107 | 0.682 | 0.804 | 0.518 |
| hybrid_prefix (vs default_hybrid) | 0.705 [0.588, 0.807] | +0.016 [-0.021, +0.053] | 0.382 | 0.382 | 1.000 | 0 | 90 | 0.832 | 0.945 | 0.654 |

### Medicine, section level, 17 queries. LLM-assessed qrels (claude-sonnet-5-5), not human grades

| Variant | nDCG@10 [95% CI] | diff vs default [95% CI] | raw p | Holm (this ablation) | Holm (all 22) | unjudged@10 | Recall@20* | MRR* | MAP* |
|---|---|---|---|---|---|---|---|---|---|
| default_dense (default) | 0.735 [0.640, 0.829] | reference |  |  |  | 41 | 0.852 | 0.804 | 0.636 |
| default_hybrid (default) | 0.806 [0.695, 0.891] | reference |  |  |  | 25 | 0.973 | 0.949 | 0.765 |
| dense_prefix (vs default_dense) | 0.742 [0.623, 0.851] | +0.007 [-0.056, +0.064] | 0.771 | 1.000 | 1.000 | 32 | 0.874 | 0.870 | 0.665 |
| hybrid_prefix (vs default_hybrid) | 0.821 [0.708, 0.904] | +0.014 [-0.025, +0.052] | 0.458 | 1.000 | 1.000 | 26 | 0.958 | 0.949 | 0.753 |

## Caveats
- Grades are the LLM's. In Step 13 the LLM was stricter than the humans at the 0/1
  boundary. Step 13 used the original 308-row human sample pool and is frozen.
- 10000 bootstrap resamples over 17 to 40 queries per module give wide intervals. A
  non-significant Holm p is absence of evidence, not evidence of no effect.
- Weights and k values were not tuned on these queries, but they were looked at together,
  so read the best variant as a candidate, not a win.

