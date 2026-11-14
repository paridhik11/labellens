# Step 14a: results table

**All tables below use LLM-assessed qrels (claude-sonnet-5-5), not human grades.** They are not human relevance grades. In Step 13 the
LLM was stricter than the humans at the 0/1 boundary and agreed with Pari at weighted kappa
0.746 (linear), measured on a 15-query human sample, so absolute scores here may differ
from human-graded scores. Compare systems with each other, not with other papers.

## How to read this
- Systems: tfidf, bm25, dense (bge-small-en-v1.5 + FAISS), hybrid (RRF of bm25 and dense).
- Device and medicine are separate tables (separate corpora, separate queries).
- Chunk level ranks chunks. Section level takes the best chunk score per section and the
  best grade per section.
- no_answer queries are excluded from every average here and reported at the end.
- Corpus gaps are answerable queries where no chunk has an LLM grade >= 1. Every system
  scores 0 on them. Each table is shown without them (the main table) and with them.
- Each difference vs bm25 is a paired bootstrap over queries (10000 resamples, seed 42):
  mean difference, 95% percentile interval, and a two-sided percentile bootstrap p-value.
  p-values below 0.0002 are the resolution limit of 10000 resamples, not exact zeros.
  When most per-query differences are exactly 0, many resamples have a mean of exactly 0.
  Those ties count in both tails, so p is conservative and an interval can end at +0.000
  while p is large.

## Multiple comparisons
Each table has 12 comparisons against bm25 (3 systems x 4 metrics). With 2 modules x 2
levels that is 48 comparisons in this file. **The p-values in the module tables are not
corrected for multiple comparisons.** **nDCG@10 is the primary metric**; Recall@20, MRR and MAP are
secondary and should be read as supporting detail. With only 17 to 40 queries per table,
an uncorrected p just under 0.05 is weak evidence.

The module tables further down keep the raw p-values. The table below treats the 12
nDCG@10 comparisons vs bm25 (2 modules x 2 levels x 3 systems) as one family and adds a
Holm step-down adjusted p. Holm controls the chance of any false positive across those 12
and is never smaller than the raw p. The 36 secondary-metric comparisons stay uncorrected.

## nDCG@10 vs bm25, Holm-adjusted over 12 comparisons. LLM-assessed qrels (claude-sonnet-5-5), not human grades

| Module | Level | System vs bm25 | n | nDCG@10 diff [95% CI] | raw p | Holm-adjusted p |
|---|---|---|---|---|---|---|
| device | chunk | tfidf | 40 | -0.003 [-0.048, +0.048] | 0.877 | 1.000 |
| device | chunk | dense | 40 | -0.082 [-0.187, +0.030] | 0.147 | 1.000 |
| device | chunk | hybrid | 40 | -0.001 [-0.061, +0.058] | 0.987 | 1.000 |
| device | section | tfidf | 40 | -0.005 [-0.045, +0.040] | 0.812 | 1.000 |
| device | section | dense | 40 | -0.031 [-0.123, +0.068] | 0.510 | 1.000 |
| device | section | hybrid | 40 | +0.036 [-0.015, +0.086] | 0.160 | 1.000 |
| medicine | chunk | tfidf | 17 | -0.002 [-0.052, +0.046] | 0.945 | 1.000 |
| medicine | chunk | dense | 17 | -0.040 [-0.196, +0.128] | 0.615 | 1.000 |
| medicine | chunk | hybrid | 17 | +0.067 [-0.014, +0.150] | 0.103 | 1.000 |
| medicine | section | tfidf | 17 | -0.005 [-0.047, +0.038] | 0.829 | 1.000 |
| medicine | section | dense | 17 | +0.051 [-0.056, +0.161] | 0.359 | 1.000 |
| medicine | section | hybrid | 17 | +0.122 [+0.032, +0.217] | 0.009 | 0.103 |

## Device module

- Answerable graded queries: 40
- Corpus-gap queries (0): none
- Queries in the main table (gaps excluded): 40
- There are no gap queries in this module, so the with-gaps table would be identical to the main table and is not repeated.

### Device, chunk level, gaps excluded, main (40 queries). LLM-assessed qrels (claude-sonnet-5-5), not human grades

| System | nDCG@10 | Recall@20 | MRR | MAP |
|---|---|---|---|---|
| tfidf | 0.577 | 0.733 | 0.797 | 0.526 |
| bm25 | 0.580 | 0.737 | 0.818 | 0.528 |
| dense | 0.498 | 0.591 | 0.748 | 0.376 |
| hybrid | 0.579 | 0.731 | 0.786 | 0.502 |

| System vs bm25 | nDCG@10 | Recall@20 | MRR | MAP |
|---|---|---|---|---|
| tfidf | -0.003 [-0.048, +0.048] p=0.877 | -0.004 [-0.031, +0.025] p=0.797 | -0.021 [-0.113, +0.076] p=0.670 | -0.003 [-0.041, +0.040] p=0.861 |
| dense | -0.082 [-0.187, +0.030] p=0.147 | -0.146 [-0.241, -0.051] p=0.002 | -0.070 [-0.202, +0.066] p=0.304 | -0.153 [-0.261, -0.042] p=0.006 |
| hybrid | -0.001 [-0.061, +0.058] p=0.987 | -0.006 [-0.072, +0.056] p=0.867 | -0.031 [-0.109, +0.044] p=0.431 | -0.026 [-0.086, +0.031] p=0.391 |

### Device, section level, gaps excluded, main (40 queries). LLM-assessed qrels (claude-sonnet-5-5), not human grades

| System | nDCG@10 | Recall@20 | MRR | MAP |
|---|---|---|---|---|
| tfidf | 0.655 | 0.843 | 0.820 | 0.637 |
| bm25 | 0.660 | 0.836 | 0.845 | 0.634 |
| dense | 0.629 | 0.788 | 0.791 | 0.531 |
| hybrid | 0.695 | 0.862 | 0.820 | 0.649 |

| System vs bm25 | nDCG@10 | Recall@20 | MRR | MAP |
|---|---|---|---|---|
| tfidf | -0.005 [-0.045, +0.040] p=0.812 | +0.007 [-0.013, +0.029] p=0.536 | -0.025 [-0.113, +0.065] p=0.583 | +0.004 [-0.030, +0.042] p=0.871 |
| dense | -0.031 [-0.123, +0.068] p=0.510 | -0.048 [-0.124, +0.028] p=0.223 | -0.054 [-0.179, +0.071] p=0.393 | -0.102 [-0.194, -0.010] p=0.029 |
| hybrid | +0.036 [-0.015, +0.086] p=0.160 | +0.026 [-0.019, +0.070] p=0.241 | -0.025 [-0.099, +0.046] p=0.499 | +0.015 [-0.034, +0.065] p=0.555 |

## Medicine module

- Answerable graded queries: 17
- Corpus-gap queries (0): none
- Queries in the main table (gaps excluded): 17
- There are no gap queries in this module, so the with-gaps table would be identical to the main table and is not repeated.

### Medicine, chunk level, gaps excluded, main (17 queries). LLM-assessed qrels (claude-sonnet-5-5), not human grades

| System | nDCG@10 | Recall@20 | MRR | MAP |
|---|---|---|---|---|
| tfidf | 0.564 | 0.704 | 0.814 | 0.493 |
| bm25 | 0.567 | 0.738 | 0.774 | 0.490 |
| dense | 0.527 | 0.604 | 0.682 | 0.419 |
| hybrid | 0.633 | 0.724 | 0.918 | 0.559 |

| System vs bm25 | nDCG@10 | Recall@20 | MRR | MAP |
|---|---|---|---|---|
| tfidf | -0.002 [-0.052, +0.046] p=0.945 | -0.034 [-0.114, +0.029] p=0.371 | +0.040 [-0.063, +0.143] p=0.447 | +0.003 [-0.040, +0.047] p=0.888 |
| dense | -0.040 [-0.196, +0.128] p=0.615 | -0.134 [-0.263, -0.011] p=0.032 | -0.093 [-0.296, +0.123] p=0.393 | -0.071 [-0.212, +0.074] p=0.319 |
| hybrid | +0.067 [-0.014, +0.150] p=0.103 | -0.014 [-0.102, +0.063] p=0.769 | +0.144 [+0.021, +0.295] p=0.025 | +0.070 [-0.029, +0.161] p=0.156 |

### Medicine, section level, gaps excluded, main (17 queries). LLM-assessed qrels (claude-sonnet-5-5), not human grades

| System | nDCG@10 | Recall@20 | MRR | MAP |
|---|---|---|---|---|
| tfidf | 0.623 | 0.861 | 0.819 | 0.590 |
| bm25 | 0.628 | 0.881 | 0.780 | 0.580 |
| dense | 0.678 | 0.793 | 0.804 | 0.593 |
| hybrid | 0.749 | 0.945 | 0.949 | 0.713 |

| System vs bm25 | nDCG@10 | Recall@20 | MRR | MAP |
|---|---|---|---|---|
| tfidf | -0.005 [-0.047, +0.038] p=0.829 | -0.020 [-0.057, +0.000] p=0.239 | +0.038 [-0.060, +0.137] p=0.497 | +0.011 [-0.030, +0.052] p=0.613 |
| dense | +0.051 [-0.056, +0.161] p=0.359 | -0.088 [-0.176, -0.007] p=0.030 | +0.024 [-0.163, +0.220] p=0.814 | +0.014 [-0.091, +0.114] p=0.779 |
| hybrid | +0.122 [+0.032, +0.217] p=0.009 | +0.065 [+0.015, +0.132] p=0.007 | +0.168 [+0.032, +0.323] p=0.011 | +0.133 [+0.059, +0.208] p=0.000 |

## no_answer queries (reported separately, not in any average above)

Share of no_answer queries with a grade >= 1 chunk in the top 10 (related context is
expected and not an error) and with a grade 2 chunk (which would suggest a mislabelled
query). Scores are comparable within one system only. LLM-assessed qrels (claude-sonnet-5-5), not human grades.

### Device (4 queries: q41, q42, q43, q44)

| System | Any grade>=1 in top 10 | Grade 2 in top 10 | Mean top-1 score (no_answer) | Mean top-1 score (answerable) |
|---|---|---|---|---|
| tfidf | 0.250 | 0.000 | 0.235 | 0.259 |
| bm25 | 0.250 | 0.000 | 9.334 | 11.964 |
| dense | 0.250 | 0.000 | 0.691 | 0.762 |
| hybrid | 0.250 | 0.000 | 0.032 | 0.032 |

### Medicine (1 queries: q62)

| System | Any grade>=1 in top 10 | Grade 2 in top 10 | Mean top-1 score (no_answer) | Mean top-1 score (answerable) |
|---|---|---|---|---|
| tfidf | 0.000 | 0.000 | 0.205 | 0.259 |
| bm25 | 0.000 | 0.000 | 9.767 | 11.969 |
| dense | 0.000 | 0.000 | 0.680 | 0.805 |
| hybrid | 0.000 | 0.000 | 0.033 | 0.032 |

