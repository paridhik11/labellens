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
| device | chunk | tfidf | 40 | -0.003 [-0.049, +0.049] | 0.877 | 1.000 |
| device | chunk | dense | 40 | -0.080 [-0.190, +0.037] | 0.175 | 1.000 |
| device | chunk | hybrid | 40 | +0.001 [-0.062, +0.063] | 0.962 | 1.000 |
| device | section | tfidf | 40 | -0.004 [-0.046, +0.041] | 0.832 | 1.000 |
| device | section | dense | 40 | -0.030 [-0.128, +0.078] | 0.554 | 1.000 |
| device | section | hybrid | 40 | +0.037 [-0.018, +0.092] | 0.187 | 1.000 |
| medicine | chunk | tfidf | 17 | -0.001 [-0.053, +0.051] | 0.988 | 1.000 |
| medicine | chunk | dense | 17 | -0.041 [-0.202, +0.133] | 0.619 | 1.000 |
| medicine | chunk | hybrid | 17 | +0.083 [-0.003, +0.174] | 0.060 | 0.664 |
| medicine | section | tfidf | 17 | -0.018 [-0.056, +0.019] | 0.349 | 1.000 |
| medicine | section | dense | 17 | +0.057 [-0.055, +0.171] | 0.323 | 1.000 |
| medicine | section | hybrid | 17 | +0.128 [+0.037, +0.222] | 0.006 | 0.070 |

## Device module

- Answerable graded queries: 40
- Corpus-gap queries (0): none
- Queries in the main table (gaps excluded): 40
- There are no gap queries in this module, so the with-gaps table would be identical to the main table and is not repeated.

### Device, chunk level, gaps excluded, main (40 queries). LLM-assessed qrels (claude-sonnet-5-5), not human grades

| System | nDCG@10 | Recall@20 | MRR | MAP |
|---|---|---|---|---|
| tfidf | 0.600 | 0.788 | 0.796 | 0.577 |
| bm25 | 0.603 | 0.795 | 0.818 | 0.580 |
| dense | 0.523 | 0.642 | 0.748 | 0.426 |
| hybrid | 0.604 | 0.800 | 0.786 | 0.561 |

| System vs bm25 | nDCG@10 | Recall@20 | MRR | MAP |
|---|---|---|---|---|
| tfidf | -0.003 [-0.049, +0.049] p=0.877 | -0.006 [-0.042, +0.029] p=0.751 | -0.022 [-0.114, +0.075] p=0.654 | -0.003 [-0.043, +0.043] p=0.878 |
| dense | -0.080 [-0.190, +0.037] p=0.175 | -0.153 [-0.253, -0.050] p=0.003 | -0.070 [-0.202, +0.066] p=0.304 | -0.154 [-0.270, -0.032] p=0.012 |
| hybrid | +0.001 [-0.062, +0.063] p=0.962 | +0.006 [-0.058, +0.064] p=0.848 | -0.031 [-0.109, +0.044] p=0.431 | -0.019 [-0.080, +0.040] p=0.544 |

### Device, section level, gaps excluded, main (40 queries). LLM-assessed qrels (claude-sonnet-5-5), not human grades

| System | nDCG@10 | Recall@20 | MRR | MAP |
|---|---|---|---|---|
| tfidf | 0.679 | 0.885 | 0.820 | 0.677 |
| bm25 | 0.683 | 0.876 | 0.845 | 0.680 |
| dense | 0.653 | 0.839 | 0.779 | 0.573 |
| hybrid | 0.720 | 0.922 | 0.808 | 0.689 |

| System vs bm25 | nDCG@10 | Recall@20 | MRR | MAP |
|---|---|---|---|---|
| tfidf | -0.004 [-0.046, +0.041] p=0.832 | +0.009 [-0.014, +0.036] p=0.489 | -0.025 [-0.113, +0.065] p=0.582 | -0.002 [-0.038, +0.037] p=0.870 |
| dense | -0.030 [-0.128, +0.078] p=0.554 | -0.037 [-0.114, +0.040] p=0.343 | -0.067 [-0.191, +0.060] p=0.298 | -0.106 [-0.209, +0.004] p=0.058 |
| hybrid | +0.037 [-0.018, +0.092] p=0.187 | +0.045 [+0.005, +0.088] p=0.029 | -0.038 [-0.113, +0.037] p=0.331 | +0.009 [-0.049, +0.068] p=0.768 |

## Medicine module

- Answerable graded queries: 17
- Corpus-gap queries (0): none
- Queries in the main table (gaps excluded): 17
- There are no gap queries in this module, so the with-gaps table would be identical to the main table and is not repeated.

### Medicine, chunk level, gaps excluded, main (17 queries). LLM-assessed qrels (claude-sonnet-5-5), not human grades

| System | nDCG@10 | Recall@20 | MRR | MAP |
|---|---|---|---|---|
| tfidf | 0.605 | 0.764 | 0.814 | 0.544 |
| bm25 | 0.606 | 0.805 | 0.774 | 0.551 |
| dense | 0.565 | 0.681 | 0.682 | 0.478 |
| hybrid | 0.689 | 0.824 | 0.918 | 0.652 |

| System vs bm25 | nDCG@10 | Recall@20 | MRR | MAP |
|---|---|---|---|---|
| tfidf | -0.001 [-0.053, +0.051] p=0.988 | -0.041 [-0.110, +0.005] p=0.163 | +0.040 [-0.063, +0.143] p=0.447 | -0.007 [-0.050, +0.033] p=0.750 |
| dense | -0.041 [-0.202, +0.133] p=0.619 | -0.125 [-0.268, +0.001] p=0.051 | -0.093 [-0.296, +0.123] p=0.393 | -0.073 [-0.217, +0.074] p=0.323 |
| hybrid | +0.083 [-0.003, +0.174] p=0.060 | +0.018 [-0.079, +0.107] p=0.668 | +0.144 [+0.021, +0.295] p=0.025 | +0.101 [+0.001, +0.197] p=0.048 |

### Medicine, section level, gaps excluded, main (17 queries). LLM-assessed qrels (claude-sonnet-5-5), not human grades

| System | nDCG@10 | Recall@20 | MRR | MAP |
|---|---|---|---|---|
| tfidf | 0.660 | 0.901 | 0.819 | 0.607 |
| bm25 | 0.678 | 0.896 | 0.780 | 0.607 |
| dense | 0.735 | 0.852 | 0.804 | 0.636 |
| hybrid | 0.806 | 0.973 | 0.949 | 0.765 |

| System vs bm25 | nDCG@10 | Recall@20 | MRR | MAP |
|---|---|---|---|---|
| tfidf | -0.018 [-0.056, +0.019] p=0.349 | +0.005 [-0.029, +0.044] p=0.931 | +0.038 [-0.060, +0.137] p=0.497 | +0.001 [-0.039, +0.042] p=0.986 |
| dense | +0.057 [-0.055, +0.171] p=0.323 | -0.044 [-0.144, +0.044] p=0.368 | +0.024 [-0.163, +0.220] p=0.814 | +0.030 [-0.075, +0.131] p=0.562 |
| hybrid | +0.128 [+0.037, +0.222] p=0.006 | +0.076 [+0.023, +0.145] p=0.002 | +0.168 [+0.032, +0.323] p=0.011 | +0.158 [+0.084, +0.234] p<0.0002 |

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

