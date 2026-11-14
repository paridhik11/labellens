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

> **Recall@20, MAP and MRR use the depth-20 pool.** The qrels now cover the top 20 of every variant at chunk level (the unjudged ranks 11-20 column should be 0 there). Sections can still contain unjudged chunks, because grading followed chunk rankings, not the sections they aggregate into. nDCG@10 stays the primary metric and the only one with p-values.

## Ablation: RRF smoothing constant k (default 60) (`rrf_k`)

### Device, chunk level, 40 queries. LLM-assessed qrels (claude-sonnet-5-5), not human grades

| Variant | nDCG@10 [95% CI] | diff vs default [95% CI] | raw p | Holm (this ablation) | Holm (all 22) | unjudged@10 | unjudged ranks 11-20 | Recall@20 | MRR | MAP |
|---|---|---|---|---|---|---|---|---|---|---|
| default_hybrid (default) | 0.579 [0.505, 0.651] | reference |  |  |  | 0 | 0 | 0.731 | 0.786 | 0.502 |
| rrf_k10 (vs default_hybrid) | 0.600 [0.527, 0.668] | +0.021 [+0.001, +0.041] | 0.037 | 0.183 | 0.659 | 0 | 0 | 0.780 | 0.799 | 0.539 |
| rrf_k30 (vs default_hybrid) | 0.593 [0.521, 0.661] | +0.014 [+0.004, +0.026] | 0.0006 | 0.004 | 0.013 | 0 | 0 | 0.755 | 0.786 | 0.514 |
| rrf_k100 (vs default_hybrid) | 0.580 [0.505, 0.652] | +0.001 [-0.003, +0.006] | 0.885 | 1.000 | 1.000 | 0 | 0 | 0.731 | 0.786 | 0.500 |

### Device, section level, 40 queries. LLM-assessed qrels (claude-sonnet-5-5), not human grades

| Variant | nDCG@10 [95% CI] | diff vs default [95% CI] | raw p | Holm (this ablation) | Holm (all 22) | unjudged@10 | Recall@20 | MRR | MAP |
|---|---|---|---|---|---|---|---|---|---|
| default_hybrid (default) | 0.695 [0.616, 0.767] | reference |  |  |  | 1 | 0.862 | 0.820 | 0.649 |
| rrf_k10 (vs default_hybrid) | 0.721 [0.650, 0.786] | +0.026 [+0.009, +0.044] | 0.001 | 0.008 | 0.029 | 0 | 0.907 | 0.824 | 0.665 |
| rrf_k30 (vs default_hybrid) | 0.708 [0.633, 0.778] | +0.012 [+0.002, +0.024] | 0.014 | 0.070 | 0.258 | 0 | 0.899 | 0.820 | 0.660 |
| rrf_k100 (vs default_hybrid) | 0.692 [0.612, 0.767] | -0.003 [-0.013, +0.005] | 0.529 | 1.000 | 1.000 | 1 | 0.823 | 0.820 | 0.642 |

### Medicine, chunk level, 17 queries. LLM-assessed qrels (claude-sonnet-5-5), not human grades

| Variant | nDCG@10 [95% CI] | diff vs default [95% CI] | raw p | Holm (this ablation) | Holm (all 22) | unjudged@10 | unjudged ranks 11-20 | Recall@20 | MRR | MAP |
|---|---|---|---|---|---|---|---|---|---|---|
| default_hybrid (default) | 0.633 [0.525, 0.735] | reference |  |  |  | 0 | 0 | 0.724 | 0.918 | 0.559 |
| rrf_k10 (vs default_hybrid) | 0.647 [0.537, 0.749] | +0.014 [-0.006, +0.042] | 0.258 | 1.000 | 1.000 | 0 | 0 | 0.767 | 0.909 | 0.564 |
| rrf_k30 (vs default_hybrid) | 0.636 [0.526, 0.737] | +0.002 [-0.002, +0.007] | 0.353 | 1.000 | 1.000 | 0 | 0 | 0.728 | 0.918 | 0.556 |
| rrf_k100 (vs default_hybrid) | 0.628 [0.518, 0.731] | -0.005 [-0.020, +0.003] | 0.685 | 1.000 | 1.000 | 0 | 0 | 0.724 | 0.918 | 0.561 |

### Medicine, section level, 17 queries. LLM-assessed qrels (claude-sonnet-5-5), not human grades

| Variant | nDCG@10 [95% CI] | diff vs default [95% CI] | raw p | Holm (this ablation) | Holm (all 22) | unjudged@10 | Recall@20 | MRR | MAP |
|---|---|---|---|---|---|---|---|---|---|
| default_hybrid (default) | 0.749 [0.636, 0.842] | reference |  |  |  | 2 | 0.945 | 0.949 | 0.713 |
| rrf_k10 (vs default_hybrid) | 0.760 [0.670, 0.840] | +0.011 [-0.022, +0.049] | 0.578 | 1.000 | 1.000 | 1 | 0.918 | 0.950 | 0.695 |
| rrf_k30 (vs default_hybrid) | 0.761 [0.651, 0.850] | +0.012 [-0.006, +0.037] | 0.306 | 1.000 | 1.000 | 1 | 0.918 | 0.949 | 0.709 |
| rrf_k100 (vs default_hybrid) | 0.748 [0.636, 0.842] | -0.001 [-0.005, +0.002] | 0.691 | 1.000 | 1.000 | 2 | 0.949 | 0.949 | 0.712 |

## Ablation: RRF weights bm25:dense (default 1:1) (`weights`)

### Device, chunk level, 40 queries. LLM-assessed qrels (claude-sonnet-5-5), not human grades

| Variant | nDCG@10 [95% CI] | diff vs default [95% CI] | raw p | Holm (this ablation) | Holm (all 22) | unjudged@10 | unjudged ranks 11-20 | Recall@20 | MRR | MAP |
|---|---|---|---|---|---|---|---|---|---|---|
| default_hybrid (default) | 0.579 [0.505, 0.651] | reference |  |  |  | 0 | 0 | 0.731 | 0.786 | 0.502 |
| w_bm25_2_dense_1 (vs default_hybrid) | 0.591 [0.516, 0.664] | +0.012 [-0.007, +0.033] | 0.223 | 1.000 | 1.000 | 0 | 0 | 0.763 | 0.818 | 0.528 |
| w_bm25_3_dense_1 (vs default_hybrid) | 0.605 [0.530, 0.676] | +0.026 [-0.000, +0.055] | 0.053 | 0.424 | 0.901 | 0 | 0 | 0.770 | 0.838 | 0.548 |
| w_bm25_1_dense_2 (vs default_hybrid) | 0.568 [0.497, 0.637] | -0.011 [-0.034, +0.012] | 0.346 | 1.000 | 1.000 | 0 | 0 | 0.707 | 0.798 | 0.463 |
| w_bm25_1_dense_3 (vs default_hybrid) | 0.557 [0.482, 0.629] | -0.022 [-0.054, +0.010] | 0.174 | 1.000 | 1.000 | 0 | 0 | 0.702 | 0.813 | 0.454 |

### Device, section level, 40 queries. LLM-assessed qrels (claude-sonnet-5-5), not human grades

| Variant | nDCG@10 [95% CI] | diff vs default [95% CI] | raw p | Holm (this ablation) | Holm (all 22) | unjudged@10 | Recall@20 | MRR | MAP |
|---|---|---|---|---|---|---|---|---|---|
| default_hybrid (default) | 0.695 [0.616, 0.767] | reference |  |  |  | 1 | 0.862 | 0.820 | 0.649 |
| w_bm25_2_dense_1 (vs default_hybrid) | 0.703 [0.624, 0.776] | +0.008 [-0.013, +0.030] | 0.477 | 1.000 | 1.000 | 0 | 0.861 | 0.848 | 0.666 |
| w_bm25_3_dense_1 (vs default_hybrid) | 0.700 [0.621, 0.773] | +0.004 [-0.021, +0.031] | 0.744 | 1.000 | 1.000 | 2 | 0.858 | 0.868 | 0.668 |
| w_bm25_1_dense_2 (vs default_hybrid) | 0.683 [0.608, 0.753] | -0.012 [-0.033, +0.008] | 0.230 | 1.000 | 1.000 | 0 | 0.843 | 0.839 | 0.616 |
| w_bm25_1_dense_3 (vs default_hybrid) | 0.675 [0.600, 0.746] | -0.020 [-0.043, +0.002] | 0.081 | 0.651 | 1.000 | 0 | 0.842 | 0.839 | 0.607 |

### Medicine, chunk level, 17 queries. LLM-assessed qrels (claude-sonnet-5-5), not human grades

| Variant | nDCG@10 [95% CI] | diff vs default [95% CI] | raw p | Holm (this ablation) | Holm (all 22) | unjudged@10 | unjudged ranks 11-20 | Recall@20 | MRR | MAP |
|---|---|---|---|---|---|---|---|---|---|---|
| default_hybrid (default) | 0.633 [0.525, 0.735] | reference |  |  |  | 0 | 0 | 0.724 | 0.918 | 0.559 |
| w_bm25_2_dense_1 (vs default_hybrid) | 0.628 [0.516, 0.731] | -0.006 [-0.030, +0.017] | 0.636 | 1.000 | 1.000 | 0 | 0 | 0.735 | 0.855 | 0.540 |
| w_bm25_3_dense_1 (vs default_hybrid) | 0.637 [0.526, 0.738] | +0.003 [-0.023, +0.028] | 0.799 | 1.000 | 1.000 | 0 | 0 | 0.749 | 0.858 | 0.551 |
| w_bm25_1_dense_2 (vs default_hybrid) | 0.609 [0.481, 0.729] | -0.024 [-0.073, +0.011] | 0.279 | 1.000 | 1.000 | 0 | 0 | 0.732 | 0.870 | 0.532 |
| w_bm25_1_dense_3 (vs default_hybrid) | 0.609 [0.482, 0.731] | -0.024 [-0.086, +0.029] | 0.438 | 1.000 | 1.000 | 0 | 0 | 0.687 | 0.838 | 0.509 |

### Medicine, section level, 17 queries. LLM-assessed qrels (claude-sonnet-5-5), not human grades

| Variant | nDCG@10 [95% CI] | diff vs default [95% CI] | raw p | Holm (this ablation) | Holm (all 22) | unjudged@10 | Recall@20 | MRR | MAP |
|---|---|---|---|---|---|---|---|---|---|
| default_hybrid (default) | 0.749 [0.636, 0.842] | reference |  |  |  | 2 | 0.945 | 0.949 | 0.713 |
| w_bm25_2_dense_1 (vs default_hybrid) | 0.747 [0.638, 0.837] | -0.002 [-0.060, +0.052] | 0.956 | 1.000 | 1.000 | 1 | 0.931 | 0.894 | 0.674 |
| w_bm25_3_dense_1 (vs default_hybrid) | 0.740 [0.626, 0.836] | -0.009 [-0.064, +0.042] | 0.738 | 1.000 | 1.000 | 1 | 0.916 | 0.897 | 0.658 |
| w_bm25_1_dense_2 (vs default_hybrid) | 0.743 [0.650, 0.828] | -0.006 [-0.048, +0.039] | 0.756 | 1.000 | 1.000 | 3 | 0.901 | 0.901 | 0.667 |
| w_bm25_1_dense_3 (vs default_hybrid) | 0.715 [0.613, 0.813] | -0.034 [-0.088, +0.019] | 0.215 | 1.000 | 1.000 | 3 | 0.871 | 0.870 | 0.653 |

## Ablation: Light stemming in BM25 (`stemming`)

### Device, chunk level, 40 queries. LLM-assessed qrels (claude-sonnet-5-5), not human grades

| Variant | nDCG@10 [95% CI] | diff vs default [95% CI] | raw p | Holm (this ablation) | Holm (all 22) | unjudged@10 | unjudged ranks 11-20 | Recall@20 | MRR | MAP |
|---|---|---|---|---|---|---|---|---|---|---|
| default_bm25 (default) | 0.580 [0.495, 0.660] | reference |  |  |  | 0 | 0 | 0.737 | 0.818 | 0.528 |
| default_hybrid (default) | 0.579 [0.505, 0.651] | reference |  |  |  | 0 | 0 | 0.731 | 0.786 | 0.502 |
| bm25_stem (vs default_bm25) | 0.618 [0.540, 0.693] | +0.038 [-0.004, +0.084] | 0.082 | 0.245 | 1.000 | 0 | 0 | 0.783 | 0.832 | 0.569 |
| hybrid_stem (vs default_hybrid) | 0.628 [0.564, 0.687] | +0.049 [+0.018, +0.083] | 0.001 | 0.004 | 0.021 | 0 | 0 | 0.748 | 0.840 | 0.534 |

### Device, section level, 40 queries. LLM-assessed qrels (claude-sonnet-5-5), not human grades

| Variant | nDCG@10 [95% CI] | diff vs default [95% CI] | raw p | Holm (this ablation) | Holm (all 22) | unjudged@10 | Recall@20 | MRR | MAP |
|---|---|---|---|---|---|---|---|---|---|
| default_bm25 (default) | 0.660 [0.572, 0.743] | reference |  |  |  | 4 | 0.836 | 0.845 | 0.634 |
| default_hybrid (default) | 0.695 [0.616, 0.767] | reference |  |  |  | 1 | 0.862 | 0.820 | 0.649 |
| bm25_stem (vs default_bm25) | 0.708 [0.630, 0.782] | +0.048 [+0.009, +0.090] | 0.014 | 0.041 | 0.258 | 3 | 0.875 | 0.865 | 0.681 |
| hybrid_stem (vs default_hybrid) | 0.731 [0.659, 0.796] | +0.036 [+0.008, +0.067] | 0.009 | 0.038 | 0.188 | 2 | 0.879 | 0.878 | 0.674 |

### Medicine, chunk level, 17 queries. LLM-assessed qrels (claude-sonnet-5-5), not human grades

| Variant | nDCG@10 [95% CI] | diff vs default [95% CI] | raw p | Holm (this ablation) | Holm (all 22) | unjudged@10 | unjudged ranks 11-20 | Recall@20 | MRR | MAP |
|---|---|---|---|---|---|---|---|---|---|---|
| default_bm25 (default) | 0.567 [0.428, 0.696] | reference |  |  |  | 0 | 0 | 0.738 | 0.774 | 0.490 |
| default_hybrid (default) | 0.633 [0.525, 0.735] | reference |  |  |  | 0 | 0 | 0.724 | 0.918 | 0.559 |
| bm25_stem (vs default_bm25) | 0.573 [0.429, 0.711] | +0.006 [-0.031, +0.041] | 0.738 | 0.918 | 1.000 | 0 | 0 | 0.724 | 0.826 | 0.526 |
| hybrid_stem (vs default_hybrid) | 0.608 [0.469, 0.732] | -0.026 [-0.093, +0.019] | 0.459 | 0.918 | 1.000 | 0 | 0 | 0.649 | 0.859 | 0.512 |

### Medicine, section level, 17 queries. LLM-assessed qrels (claude-sonnet-5-5), not human grades

| Variant | nDCG@10 [95% CI] | diff vs default [95% CI] | raw p | Holm (this ablation) | Holm (all 22) | unjudged@10 | Recall@20 | MRR | MAP |
|---|---|---|---|---|---|---|---|---|---|
| default_bm25 (default) | 0.628 [0.511, 0.743] | reference |  |  |  | 3 | 0.881 | 0.780 | 0.580 |
| default_hybrid (default) | 0.749 [0.636, 0.842] | reference |  |  |  | 2 | 0.945 | 0.949 | 0.713 |
| bm25_stem (vs default_bm25) | 0.651 [0.502, 0.791] | +0.023 [-0.029, +0.077] | 0.383 | 0.766 | 1.000 | 1 | 0.870 | 0.843 | 0.635 |
| hybrid_stem (vs default_hybrid) | 0.727 [0.602, 0.838] | -0.022 [-0.092, +0.035] | 0.507 | 0.766 | 1.000 | 1 | 0.935 | 0.900 | 0.696 |

## Ablation: BGE retrieval instruction prefix on queries (`query_prefix`)

### Device, chunk level, 40 queries. LLM-assessed qrels (claude-sonnet-5-5), not human grades

| Variant | nDCG@10 [95% CI] | diff vs default [95% CI] | raw p | Holm (this ablation) | Holm (all 22) | unjudged@10 | unjudged ranks 11-20 | Recall@20 | MRR | MAP |
|---|---|---|---|---|---|---|---|---|---|---|
| default_dense (default) | 0.498 [0.412, 0.582] | reference |  |  |  | 0 | 0 | 0.591 | 0.748 | 0.376 |
| default_hybrid (default) | 0.579 [0.505, 0.651] | reference |  |  |  | 0 | 0 | 0.731 | 0.786 | 0.502 |
| dense_prefix (vs default_dense) | 0.545 [0.460, 0.628] | +0.047 [+0.016, +0.079] | 0.001 | 0.004 | 0.021 | 0 | 0 | 0.658 | 0.821 | 0.437 |
| hybrid_prefix (vs default_hybrid) | 0.599 [0.524, 0.670] | +0.020 [-0.004, +0.046] | 0.100 | 0.200 | 1.000 | 0 | 0 | 0.764 | 0.828 | 0.539 |

### Device, section level, 40 queries. LLM-assessed qrels (claude-sonnet-5-5), not human grades

| Variant | nDCG@10 [95% CI] | diff vs default [95% CI] | raw p | Holm (this ablation) | Holm (all 22) | unjudged@10 | Recall@20 | MRR | MAP |
|---|---|---|---|---|---|---|---|---|---|
| default_dense (default) | 0.629 [0.550, 0.706] | reference |  |  |  | 2 | 0.788 | 0.791 | 0.531 |
| default_hybrid (default) | 0.695 [0.616, 0.767] | reference |  |  |  | 1 | 0.862 | 0.820 | 0.649 |
| dense_prefix (vs default_dense) | 0.682 [0.615, 0.747] | +0.053 [+0.020, +0.087] | 0.0006 | 0.002 | 0.013 | 1 | 0.814 | 0.852 | 0.578 |
| hybrid_prefix (vs default_hybrid) | 0.706 [0.628, 0.779] | +0.011 [-0.013, +0.035] | 0.353 | 1.000 | 1.000 | 0 | 0.874 | 0.866 | 0.677 |

### Medicine, chunk level, 17 queries. LLM-assessed qrels (claude-sonnet-5-5), not human grades

| Variant | nDCG@10 [95% CI] | diff vs default [95% CI] | raw p | Holm (this ablation) | Holm (all 22) | unjudged@10 | unjudged ranks 11-20 | Recall@20 | MRR | MAP |
|---|---|---|---|---|---|---|---|---|---|---|
| default_dense (default) | 0.527 [0.383, 0.668] | reference |  |  |  | 0 | 0 | 0.604 | 0.682 | 0.419 |
| default_hybrid (default) | 0.633 [0.525, 0.735] | reference |  |  |  | 0 | 0 | 0.724 | 0.918 | 0.559 |
| dense_prefix (vs default_dense) | 0.576 [0.438, 0.711] | +0.049 [+0.012, +0.095] | 0.004 | 0.013 | 0.084 | 0 | 0 | 0.597 | 0.804 | 0.447 |
| hybrid_prefix (vs default_hybrid) | 0.648 [0.534, 0.753] | +0.014 [-0.019, +0.048] | 0.378 | 0.378 | 1.000 | 0 | 0 | 0.730 | 0.945 | 0.563 |

### Medicine, section level, 17 queries. LLM-assessed qrels (claude-sonnet-5-5), not human grades

| Variant | nDCG@10 [95% CI] | diff vs default [95% CI] | raw p | Holm (this ablation) | Holm (all 22) | unjudged@10 | Recall@20 | MRR | MAP |
|---|---|---|---|---|---|---|---|---|---|
| default_dense (default) | 0.678 [0.579, 0.776] | reference |  |  |  | 4 | 0.793 | 0.804 | 0.593 |
| default_hybrid (default) | 0.749 [0.636, 0.842] | reference |  |  |  | 2 | 0.945 | 0.949 | 0.713 |
| dense_prefix (vs default_dense) | 0.679 [0.562, 0.790] | +0.001 [-0.060, +0.055] | 0.940 | 1.000 | 1.000 | 3 | 0.838 | 0.870 | 0.613 |
| hybrid_prefix (vs default_hybrid) | 0.759 [0.649, 0.850] | +0.010 [-0.026, +0.046] | 0.586 | 1.000 | 1.000 | 1 | 0.918 | 0.949 | 0.709 |

## Caveats
- Grades are the LLM's. In Step 13 the LLM was stricter than the humans at the 0/1
  boundary. Step 13 used the original 308-row human sample pool and is frozen.
- 10000 bootstrap resamples over 17 to 40 queries per module give wide intervals. A
  non-significant Holm p is absence of evidence, not evidence of no effect.
- Weights and k values were not tuned on these queries, but they were looked at together,
  so read the best variant as a candidate, not a win.

