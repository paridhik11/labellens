# Step 13: LLM grades vs human grades

> **Note added after Step 15a4 (this report is frozen and was not re-run).** Every number below
> was computed on the original 308-row human sample pool and the original 1269-row LLM grades.
> The LLM qrels have since grown to 1554 rows (285 extra pairs graded in batches 44 to 51), so the
> system ranking and nDCG@10 tables in sections 3 and 4 use the old qrels and will differ from
> `results/step14_results.md` and `results/step15_ablations.md`. The agreement statistics
> (sections 1 and 2) compare grades on the 308 human rows only and do not depend on the extra pool.
> The generator (`src/ir/grade_compare.py`) does not write this note, so regenerating the file
> would drop it.

## Data
- Human-graded rows (merged, first file wins on shared rows): 308
- Human queries: 15
- LLM model id(s) in pool_t1_llm.csv: claude-sonnet-5-5

- pari: 182 rows, grades {0: 99, 1: 56, 2: 27}
- parth: 195 rows, grades {0: 106, 1: 71, 2: 18}
- Merged human grades: {0: 168, 1: 103, 2: 37}
- LLM grades on the same rows: {0: 218, 1: 62, 2: 28} (308 of 308 rows have an LLM grade)

## 1. LLM vs human agreement

### All rows

| rows | exact agreement | weighted kappa (linear) | weighted kappa (quadratic) | binary agreement | binary kappa |
|---|---|---|---|---|---|
| **pari only (headline)**  182 | 0.819 | 0.746 | 0.823 | 0.879 | 0.752 |
| all human rows (merged)  308 | 0.782 | 0.675 | 0.768 | 0.825 | 0.636 |
| parth only  195 | 0.744 | 0.591 | 0.698 | 0.764 | 0.504 |

### Excluding no_answer queries (q44)

A no_answer query has no right passage, so nearly every row is 0 and agreement on
it is easy. Dropping it shows agreement on queries that do have an answer.

| rows | exact agreement | weighted kappa (linear) | weighted kappa (quadratic) | binary agreement | binary kappa |
|---|---|---|---|---|---|
| **pari only (headline)**  158 | 0.791 | 0.725 | 0.807 | 0.861 | 0.724 |
| all human rows (merged)  284 | 0.764 | 0.663 | 0.759 | 0.810 | 0.618 |
| parth only  171 | 0.708 | 0.570 | 0.681 | 0.731 | 0.473 |

Confusion matrix, pari only (rows = human, columns = LLM):

| pari \ LLM | 0 | 1 | 2 |
|---|---|---|---|
| 0 | 97 | 2 | 0 |
| 1 | 20 | 34 | 2 |
| 2 | 0 | 9 | 18 |

Confusion matrix, all human rows (rows = human, columns = LLM):

| human \ LLM | 0 | 1 | 2 |
|---|---|---|---|
| 0 | 166 | 2 | 0 |
| 1 | 52 | 49 | 2 |
| 2 | 0 | 11 | 26 |

## 2. Human vs human (pari vs parth, rows both graded)

| rows | exact agreement | weighted kappa (linear) | weighted kappa (quadratic) | binary agreement | binary kappa |
|---|---|---|---|---|---|
| shared rows  69 | 0.957 | 0.938 | 0.955 | 0.957 | 0.912 |

| pari \ parth | 0 | 1 | 2 |
|---|---|---|---|
| 0 | 37 | 3 | 0 |
| 1 | 0 | 21 | 0 |
| 2 | 0 | 0 | 8 |

On the same shared rows, each human against the LLM:

| rows | exact agreement | weighted kappa (linear) | weighted kappa (quadratic) | binary agreement | binary kappa |
|---|---|---|---|---|---|
| pari vs LLM  69 | 0.754 | 0.618 | 0.731 | 0.783 | 0.529 |
| parth vs LLM  69 | 0.768 | 0.652 | 0.751 | 0.797 | 0.580 |

## 3. System ranking by nDCG@10

Systems are built per module (device queries search device chunks, medicine queries
search medicine chunks), the same way the pool was made, so no result is unjudged
because of a module mix-up.
Queries used (answerable, graded by both, not a corpus gap under either): 14
Human-sample queries left out (no_answer or gap): q44

### device module (10 queries)

| system | nDCG@10 human | nDCG@10 LLM | rank human | rank LLM |
|---|---|---|---|---|
| tfidf | 0.569 | 0.594 | 4 | 3 |
| bm25 | 0.586 | 0.635 | 3 | 2 |
| dense | 0.613 | 0.578 | 2 | 4 |
| hybrid | 0.620 | 0.640 | 1 | 1 |

Kendall's tau between the two rankings: 0.333 (only 6 pairs).

### medicine module (4 queries)

| system | nDCG@10 human | nDCG@10 LLM | rank human | rank LLM |
|---|---|---|---|---|
| tfidf | 0.763 | 0.745 | 3 | 3 |
| bm25 | 0.852 | 0.756 | 1 | 2 |
| dense | 0.620 | 0.601 | 4 | 4 |
| hybrid | 0.826 | 0.808 | 2 | 1 |

Kendall's tau between the two rankings: 0.667 (only 6 pairs).

### Both modules, mean over all queries (reference only) (14 queries)

| system | nDCG@10 human | nDCG@10 LLM | rank human | rank LLM |
|---|---|---|---|---|
| tfidf | 0.625 | 0.637 | 3 | 3 |
| bm25 | 0.662 | 0.670 | 2 | 2 |
| dense | 0.615 | 0.584 | 4 | 4 |
| hybrid | 0.679 | 0.688 | 1 | 1 |

Kendall's tau between the two rankings: 1.000 (only 6 pairs).

### nDCG@10 difference, LLM minus human, with bootstrap 95% interval

Per-query nDCG@10 under LLM qrels minus under human qrels, resampling queries with
replacement (10000 resamples, seed 42). The sample is small, so intervals are wide.

### Both modules (14 queries)

| system | mean LLM - human | 95% CI | interval excludes 0 |
|---|---|---|---|
| tfidf | +0.012 | [-0.046, +0.067] | no |
| bm25 | +0.008 | [-0.042, +0.063] | no |
| dense | -0.031 | [-0.130, +0.059] | no |
| hybrid | +0.009 | [-0.038, +0.056] | no |

Systems whose mean difference is negative (LLM scores lower): dense.

### device module (10 queries)

| system | mean LLM - human | 95% CI | interval excludes 0 |
|---|---|---|---|
| tfidf | +0.024 | [-0.039, +0.088] | no |
| bm25 | +0.049 | [+0.005, +0.106] | yes |
| dense | -0.035 | [-0.160, +0.072] | no |
| hybrid | +0.020 | [-0.035, +0.077] | no |

Systems whose mean difference is negative (LLM scores lower): dense.

### medicine module (4 queries)

| system | mean LLM - human | 95% CI | interval excludes 0 |
|---|---|---|---|
| tfidf | -0.018 | [-0.145, +0.082] | no |
| bm25 | -0.096 | [-0.140, -0.022] | yes |
| dense | -0.020 | [-0.170, +0.130] | no |
| hybrid | -0.018 | [-0.093, +0.063] | no |

Systems whose mean difference is negative (LLM scores lower): tfidf, bm25, dense, hybrid.

### Reading the intervals

- Dense is the only system that falls in: both modules, device module.
- Other scopes (systems that fall): medicine module (tfidf, bm25, dense, hybrid).
- An interval that includes 0 means the shift could be chance at this sample size.

## 4. Grade distribution of each system's top 10

| module | system | grader | share 0 | share 1 | share 2 | results | ungraded |
|---|---|---|---|---|---|---|---|
| device | tfidf | human | 0.500 | 0.390 | 0.110 | 100 | 0 |
| device | tfidf | LLM | 0.630 | 0.290 | 0.080 | 100 | 0 |
| device | bm25 | human | 0.470 | 0.410 | 0.120 | 100 | 0 |
| device | bm25 | LLM | 0.590 | 0.320 | 0.090 | 100 | 0 |
| device | dense | human | 0.470 | 0.420 | 0.110 | 100 | 0 |
| device | dense | LLM | 0.690 | 0.230 | 0.080 | 100 | 0 |
| device | hybrid | human | 0.460 | 0.390 | 0.150 | 100 | 0 |
| device | hybrid | LLM | 0.650 | 0.240 | 0.110 | 100 | 0 |
| medicine | tfidf | human | 0.225 | 0.400 | 0.375 | 40 | 0 |
| medicine | tfidf | LLM | 0.350 | 0.350 | 0.300 | 40 | 0 |
| medicine | bm25 | human | 0.125 | 0.450 | 0.425 | 40 | 0 |
| medicine | bm25 | LLM | 0.325 | 0.300 | 0.375 | 40 | 0 |
| medicine | dense | human | 0.350 | 0.400 | 0.250 | 40 | 0 |
| medicine | dense | LLM | 0.500 | 0.225 | 0.275 | 40 | 0 |
| medicine | hybrid | human | 0.175 | 0.450 | 0.375 | 40 | 0 |
| medicine | hybrid | LLM | 0.325 | 0.350 | 0.325 | 40 | 0 |

