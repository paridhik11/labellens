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
levels that is 48 comparisons in this file. **None of the p-values is corrected for
multiple comparisons.** **nDCG@10 is the primary metric**; Recall@20, MRR and MAP are
secondary and should be read as supporting detail. With only 17 to 40 queries per table,
an uncorrected p just under 0.05 is weak evidence.

## Device module

- Answerable graded queries: 40
- Corpus-gap queries (0): none
- Queries in the main table (gaps excluded): 40
- There are no gap queries in this module, so the with-gaps table would be identical to the main table and is not repeated.

### Device, chunk level, gaps excluded, main (40 queries). LLM-assessed qrels (claude-sonnet-5-5), not human grades

| System | nDCG@10 | Recall@20 | MRR | MAP |
|---|---|---|---|---|
| tfidf | 0.627 | 0.834 | 0.796 | 0.611 |
| bm25 | 0.624 | 0.841 | 0.818 | 0.610 |
| dense | 0.540 | 0.654 | 0.743 | 0.444 |
| hybrid | 0.624 | 0.821 | 0.786 | 0.582 |

| System vs bm25 | nDCG@10 | Recall@20 | MRR | MAP |
|---|---|---|---|---|
| tfidf | +0.002 [-0.048, +0.063] p=0.970 | -0.007 [-0.041, +0.023] p=0.710 | -0.022 [-0.114, +0.075] p=0.654 | +0.001 [-0.043, +0.055] p=0.998 |
| dense | -0.084 [-0.199, +0.039] p=0.175 | -0.186 [-0.303, -0.068] p=0.001 | -0.075 [-0.207, +0.062] p=0.278 | -0.166 [-0.288, -0.039] p=0.009 |
| hybrid | -0.001 [-0.067, +0.065] p=0.990 | -0.020 [-0.103, +0.058] p=0.639 | -0.032 [-0.109, +0.044] p=0.425 | -0.028 [-0.092, +0.036] p=0.393 |

### Device, section level, gaps excluded, main (40 queries). LLM-assessed qrels (claude-sonnet-5-5), not human grades

| System | nDCG@10 | Recall@20 | MRR | MAP |
|---|---|---|---|---|
| tfidf | 0.686 | 0.917 | 0.801 | 0.686 |
| bm25 | 0.690 | 0.894 | 0.837 | 0.687 |
| dense | 0.657 | 0.838 | 0.772 | 0.579 |
| hybrid | 0.726 | 0.937 | 0.802 | 0.698 |

| System vs bm25 | nDCG@10 | Recall@20 | MRR | MAP |
|---|---|---|---|---|
| tfidf | -0.004 [-0.047, +0.044] p=0.841 | +0.023 [-0.000, +0.052] p=0.065 | -0.036 [-0.121, +0.051] p=0.412 | -0.001 [-0.040, +0.046] p=0.921 |
| dense | -0.033 [-0.136, +0.079] p=0.528 | -0.056 [-0.155, +0.037] p=0.265 | -0.065 [-0.189, +0.063] p=0.305 | -0.108 [-0.213, +0.005] p=0.061 |
| hybrid | +0.036 [-0.022, +0.095] p=0.219 | +0.043 [-0.003, +0.089] p=0.067 | -0.036 [-0.111, +0.039] p=0.357 | +0.011 [-0.048, +0.070] p=0.724 |

## Medicine module

- Answerable graded queries: 17
- Corpus-gap queries (0): none
- Queries in the main table (gaps excluded): 17
- There are no gap queries in this module, so the with-gaps table would be identical to the main table and is not repeated.

### Medicine, chunk level, gaps excluded, main (17 queries). LLM-assessed qrels (claude-sonnet-5-5), not human grades

| System | nDCG@10 | Recall@20 | MRR | MAP |
|---|---|---|---|---|
| tfidf | 0.628 | 0.805 | 0.814 | 0.579 |
| bm25 | 0.631 | 0.835 | 0.774 | 0.589 |
| dense | 0.590 | 0.730 | 0.682 | 0.508 |
| hybrid | 0.716 | 0.840 | 0.918 | 0.681 |

| System vs bm25 | nDCG@10 | Recall@20 | MRR | MAP |
|---|---|---|---|---|
| tfidf | -0.003 [-0.059, +0.050] p=0.924 | -0.029 [-0.088, +0.000] p=0.710 | +0.040 [-0.063, +0.143] p=0.447 | -0.009 [-0.053, +0.032] p=0.687 |
| dense | -0.042 [-0.204, +0.133] p=0.614 | -0.105 [-0.258, +0.036] p=0.154 | -0.093 [-0.296, +0.123] p=0.393 | -0.080 [-0.225, +0.070] p=0.291 |
| hybrid | +0.085 [-0.002, +0.175] p=0.057 | +0.005 [-0.096, +0.105] p=0.905 | +0.144 [+0.021, +0.295] p=0.025 | +0.092 [-0.014, +0.196] p=0.086 |

### Medicine, section level, gaps excluded, main (17 queries). LLM-assessed qrels (claude-sonnet-5-5), not human grades

| System | nDCG@10 | Recall@20 | MRR | MAP |
|---|---|---|---|---|
| tfidf | 0.683 | 0.924 | 0.819 | 0.631 |
| bm25 | 0.697 | 0.919 | 0.780 | 0.634 |
| dense | 0.759 | 0.897 | 0.804 | 0.669 |
| hybrid | 0.822 | 0.992 | 0.949 | 0.791 |

| System vs bm25 | nDCG@10 | Recall@20 | MRR | MAP |
|---|---|---|---|---|
| tfidf | -0.014 [-0.053, +0.025] p=0.483 | +0.005 [-0.029, +0.044] p=0.931 | +0.038 [-0.060, +0.137] p=0.497 | -0.002 [-0.044, +0.041] p=0.916 |
| dense | +0.062 [-0.055, +0.183] p=0.307 | -0.022 [-0.114, +0.059] p=0.648 | +0.024 [-0.163, +0.220] p=0.814 | +0.035 [-0.073, +0.142] p=0.516 |
| hybrid | +0.125 [+0.031, +0.222] p=0.008 | +0.072 [+0.016, +0.142] p=0.007 | +0.168 [+0.032, +0.323] p=0.011 | +0.157 [+0.078, +0.238] p<0.0002 |

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

