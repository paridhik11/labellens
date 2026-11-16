# Step 18 experiments

**LLM-assessed qrels (claude-sonnet-5-5), not human grades.** 5-fold stratified cross-validation over the 57 answerable queries (`data/eval/cv_folds.json`, seed 42). Every variant is reported against plain hybrid AND hybrid+stem+prefix; gains are pooled over all queries. Rule: gain above 0.01 on both nDCG@10 lists (unjudged=0 and condensed), at least 3 of 5 folds won, survives leaving out the two biggest-gaining queries. unjudged@10 above 0.05 means PENDING_GRADING. CANDIDATE means only that the rule is passed: E0 passed it and then failed the Step 17 held-out check. This file is written by the harness; each section is replaced when its experiment is re-run.

<!-- summary:start -->
| experiment | vs | decision | gain unjudged=0 [95% CI] | gain condensed | Recall@20 gain | folds won | leave-top-2 gain | without q55 | unjudged@10 |
|---|---|---|---|---|---|---|---|---|---|
| E0: hybrid+stem+prefix vs hybrid (carried over from Step 17) | hybrid | CANDIDATE | +0.026 [-0.013, +0.062] | +0.026 | +0.017 | 3 of 5 | +0.013 / +0.013 | +0.037 / +0.037 | 0.000 |
| E1a: bge-reranker-base on hybrid, top 30, replace | hybrid | DROPPED | -0.003 [-0.060, +0.053] | -0.000 | -0.017 | 3 of 5 | -0.022 / -0.019 | -0.006 / -0.003 | 0.019 |
| E1a: bge-reranker-base on hybrid, top 30, replace | hybrid+stem+prefix | DROPPED | -0.029 [-0.092, +0.035] | -0.026 | -0.034 | 1 of 5 | -0.052 / -0.049 | -0.043 / -0.040 | 0.019 |
| E1b: bge-reranker-base on hybrid, top 30, blend | hybrid | CANDIDATE | +0.028 [-0.008, +0.065] | +0.028 | +0.024 | 4 of 5 | +0.013 / +0.013 | +0.026 / +0.026 | 0.002 |
| E1b: bge-reranker-base on hybrid, top 30, blend | hybrid+stem+prefix | DROPPED | +0.002 [-0.045, +0.050] | +0.003 | +0.007 | 2 of 5 | -0.019 / -0.018 | -0.012 / -0.011 | 0.002 |
| E1c: bge-reranker-base on hybrid, top 50, replace | hybrid | PENDING_GRADING | -0.028 [-0.090, +0.036] | -0.002 | -0.049 | 2 of 5 | -0.047 / -0.021 | -0.031 / -0.005 | 0.105 |
| E1c: bge-reranker-base on hybrid, top 50, replace | hybrid+stem+prefix | PENDING_GRADING | -0.053 [-0.120, +0.014] | -0.028 | -0.066 | 2 of 5 | -0.078 / -0.052 | -0.068 / -0.042 | 0.105 |
| E1d: bge-reranker-base on hybrid, top 50, blend | hybrid | CANDIDATE | +0.034 [-0.006, +0.075] | +0.036 | +0.041 | 4 of 5 | +0.019 / +0.021 | +0.032 / +0.034 | 0.009 |
| E1d: bge-reranker-base on hybrid, top 50, blend | hybrid+stem+prefix | DROPPED | +0.008 [-0.041, +0.059] | +0.010 | +0.023 | 3 of 5 | -0.012 / -0.010 | -0.005 / -0.003 | 0.009 |
| E1e: bge-reranker-base on hybrid+stem+prefix, top 30, replace | hybrid | DROPPED | -0.007 [-0.064, +0.049] | -0.003 | +0.006 | 2 of 5 | -0.026 / -0.021 | -0.010 / -0.006 | 0.026 |
| E1e: bge-reranker-base on hybrid+stem+prefix, top 30, replace | hybrid+stem+prefix | DROPPED | -0.033 [-0.093, +0.028] | -0.029 | -0.012 | 1 of 5 | -0.056 / -0.052 | -0.047 / -0.043 | 0.026 |
| E1f: bge-reranker-base on hybrid+stem+prefix, top 30, blend | hybrid | CANDIDATE | +0.043 [+0.005, +0.082] | +0.043 | +0.039 | 4 of 5 | +0.029 / +0.029 | +0.043 / +0.043 | 0.002 |
| E1f: bge-reranker-base on hybrid+stem+prefix, top 30, blend | hybrid+stem+prefix | DROPPED | +0.018 [-0.019, +0.058] | +0.018 | +0.022 | 3 of 5 | -0.002 / -0.001 | +0.005 / +0.005 | 0.002 |
| E1g: bge-reranker-base on hybrid+stem+prefix, top 50, replace | hybrid | PENDING_GRADING | -0.039 [-0.100, +0.021] | -0.017 | -0.052 | 2 of 5 | -0.055 / -0.035 | -0.043 / -0.019 | 0.102 |
| E1g: bge-reranker-base on hybrid+stem+prefix, top 50, replace | hybrid+stem+prefix | PENDING_GRADING | -0.065 [-0.129, +0.000] | -0.042 | -0.069 | 0 of 5 | -0.086 / -0.065 | -0.080 / -0.057 | 0.102 |
| E1h: bge-reranker-base on hybrid+stem+prefix, top 50, blend | hybrid | CANDIDATE | +0.040 [-0.001, +0.081] | +0.041 | +0.036 | 4 of 5 | +0.028 / +0.028 | +0.039 / +0.040 | 0.007 |
| E1h: bge-reranker-base on hybrid+stem+prefix, top 50, blend | hybrid+stem+prefix | DROPPED | +0.015 [-0.026, +0.057] | +0.015 | +0.019 | 3 of 5 | -0.003 / -0.002 | +0.002 / +0.003 | 0.007 |
| E2a: heading prepended, BM25 side, plain hybrid | hybrid | CANDIDATE | +0.020 [+0.004, +0.038] | +0.020 | +0.002 | 4 of 5 | +0.011 / +0.011 | +0.019 / +0.019 | 0.002 |
| E2a: heading prepended, BM25 side, plain hybrid | hybrid+stem+prefix | DROPPED | -0.006 [-0.041, +0.032] | -0.006 | -0.015 | 2 of 5 | -0.023 / -0.023 | -0.018 / -0.018 | 0.002 |
| E2b: heading prepended, dense side, plain hybrid | hybrid | CANDIDATE | +0.048 [+0.021, +0.076] | +0.050 | +0.002 | 5 of 5 | +0.038 / +0.039 | +0.051 / +0.053 | 0.009 |
| E2b: heading prepended, dense side, plain hybrid | hybrid+stem+prefix | DROPPED | +0.022 [-0.015, +0.062] | +0.024 | -0.015 | 4 of 5 | +0.007 / +0.008 | +0.014 / +0.016 | 0.009 |
| E2c: heading prepended, both sides, plain hybrid | hybrid | CANDIDATE | +0.058 [+0.028, +0.089] | +0.064 | +0.001 | 4 of 5 | +0.048 / +0.053 | +0.059 / +0.065 | 0.035 |
| E2c: heading prepended, both sides, plain hybrid | hybrid+stem+prefix | CANDIDATE | +0.033 [-0.005, +0.075] | +0.039 | -0.016 | 3 of 5 | +0.015 / +0.019 | +0.021 / +0.027 | 0.035 |
| E2d: heading prepended, BM25 side, stem+prefix hybrid | hybrid | CANDIDATE | +0.033 [-0.005, +0.069] | +0.034 | +0.010 | 3 of 5 | +0.021 / +0.021 | +0.043 / +0.044 | 0.002 |
| E2d: heading prepended, BM25 side, stem+prefix hybrid | hybrid+stem+prefix | DROPPED | +0.008 [-0.004, +0.019] | +0.008 | -0.007 | 4 of 5 | +0.003 / +0.003 | +0.006 / +0.006 | 0.002 |
| E2e: heading prepended, dense side, stem+prefix hybrid | hybrid | CANDIDATE | +0.063 [+0.019, +0.105] | +0.065 | +0.024 | 4 of 5 | +0.051 / +0.052 | +0.075 / +0.077 | 0.007 |
| E2e: heading prepended, dense side, stem+prefix hybrid | hybrid+stem+prefix | CANDIDATE | +0.037 [+0.012, +0.064] | +0.039 | +0.006 | 5 of 5 | +0.026 / +0.027 | +0.038 / +0.040 | 0.007 |
| E2f: heading prepended, both sides, stem+prefix hybrid | hybrid | CANDIDATE | +0.068 [+0.025, +0.111] | +0.077 | +0.011 | 5 of 5 | +0.055 / +0.064 | +0.078 / +0.087 | 0.030 |
| E2f: heading prepended, both sides, stem+prefix hybrid | hybrid+stem+prefix | CANDIDATE | +0.043 [+0.013, +0.075] | +0.051 | -0.007 | 5 of 5 | +0.030 / +0.037 | +0.041 / +0.050 | 0.030 |
| E3a: bge-base as the dense list, plain hybrid | hybrid | CANDIDATE | +0.023 [-0.009, +0.054] | +0.027 | -0.001 | 4 of 5 | +0.014 / +0.018 | +0.026 / +0.030 | 0.018 |
| E3a: bge-base as the dense list, plain hybrid | hybrid+stem+prefix | DROPPED | -0.002 [-0.040, +0.036] | +0.002 | -0.019 | 3 of 5 | -0.017 / -0.013 | -0.011 / -0.007 | 0.018 |
| E3b: bge-base as the dense list, stem+prefix | hybrid | CANDIDATE | +0.046 [+0.005, +0.086] | +0.046 | +0.040 | 4 of 5 | +0.032 / +0.032 | +0.057 / +0.057 | 0.007 |
| E3b: bge-base as the dense list, stem+prefix | hybrid+stem+prefix | CANDIDATE | +0.020 [-0.007, +0.047] | +0.020 | +0.022 | 4 of 5 | +0.012 / +0.012 | +0.019 / +0.019 | 0.007 |
| E3c: bge-large as the dense list, plain hybrid | hybrid | CANDIDATE | +0.037 [+0.001, +0.074] | +0.039 | +0.035 | 4 of 5 | +0.025 / +0.027 | +0.040 / +0.042 | 0.018 |
| E3c: bge-large as the dense list, plain hybrid | hybrid+stem+prefix | DROPPED | +0.011 [-0.029, +0.054] | +0.014 | +0.017 | 4 of 5 | -0.005 / -0.002 | +0.003 / +0.005 | 0.018 |
| E3d: bge-large as the dense list, stem+prefix | hybrid | CANDIDATE | +0.077 [+0.030, +0.123] | +0.079 | +0.050 | 5 of 5 | +0.064 / +0.067 | +0.089 / +0.091 | 0.018 |
| E3d: bge-large as the dense list, stem+prefix | hybrid+stem+prefix | CANDIDATE | +0.051 [+0.024, +0.079] | +0.054 | +0.033 | 5 of 5 | +0.041 / +0.043 | +0.052 / +0.054 | 0.018 |
| E3e: ensemble bge-small + bge-base (+ stemmed BM25) | hybrid | CANDIDATE | +0.049 [+0.013, +0.083] | +0.049 | +0.018 | 5 of 5 | +0.038 / +0.038 | +0.053 / +0.053 | 0.000 |
| E3e: ensemble bge-small + bge-base (+ stemmed BM25) | hybrid+stem+prefix | CANDIDATE | +0.023 [-0.003, +0.048] | +0.023 | +0.001 | 4 of 5 | +0.013 / +0.013 | +0.016 / +0.016 | 0.000 |
| E3f: ensemble bge-small + bge-large (+ stemmed BM25) | hybrid | CANDIDATE | +0.052 [+0.015, +0.091] | +0.052 | +0.024 | 5 of 5 | +0.039 / +0.039 | +0.057 / +0.057 | 0.000 |
| E3f: ensemble bge-small + bge-large (+ stemmed BM25) | hybrid+stem+prefix | CANDIDATE | +0.027 [+0.004, +0.053] | +0.027 | +0.007 | 4 of 5 | +0.015 / +0.015 | +0.020 / +0.020 | 0.000 |
| E4a: MedCPT bi-encoder as the dense list, plain BM25 | hybrid | PENDING_GRADING | -0.024 [-0.076, +0.028] | -0.012 | -0.056 | 1 of 5 | -0.039 / -0.028 | -0.023 / -0.011 | 0.070 |
| E4a: MedCPT bi-encoder as the dense list, plain BM25 | hybrid+stem+prefix | PENDING_GRADING | -0.050 [-0.113, +0.013] | -0.037 | -0.074 | 1 of 5 | -0.070 / -0.059 | -0.061 / -0.048 | 0.070 |
| E4b: MedCPT bi-encoder as the dense list, stemmed BM25 | hybrid | PENDING_GRADING | -0.030 [-0.091, +0.031] | -0.014 | -0.042 | 1 of 5 | -0.047 / -0.031 | -0.021 / -0.006 | 0.091 |
| E4b: MedCPT bi-encoder as the dense list, stemmed BM25 | hybrid+stem+prefix | PENDING_GRADING | -0.056 [-0.115, +0.003] | -0.040 | -0.059 | 1 of 5 | -0.073 / -0.057 | -0.059 / -0.043 | 0.091 |
| E4c: ensemble bge-small + MedCPT (+ stemmed BM25) | hybrid | CANDIDATE | +0.027 [-0.019, +0.073] | +0.029 | -0.007 | 3 of 5 | +0.013 / +0.015 | +0.028 / +0.031 | 0.012 |
| E4c: ensemble bge-small + MedCPT (+ stemmed BM25) | hybrid+stem+prefix | DROPPED | +0.001 [-0.046, +0.050] | +0.004 | -0.025 | 3 of 5 | -0.017 / -0.015 | -0.009 / -0.007 | 0.012 |
| E4d: medcpt-cross on hybrid+stem+prefix, top 30, replace | hybrid | DROPPED | +0.012 [-0.033, +0.060] | +0.013 | +0.042 | 3 of 5 | -0.006 / -0.005 | +0.020 / +0.020 | 0.009 |
| E4d: medcpt-cross on hybrid+stem+prefix, top 30, replace | hybrid+stem+prefix | DROPPED | -0.013 [-0.053, +0.024] | -0.013 | +0.025 | 2 of 5 | -0.022 / -0.022 | -0.017 / -0.017 | 0.009 |
| E4e: medcpt-cross on hybrid+stem+prefix, top 30, blend | hybrid | CANDIDATE | +0.034 [-0.006, +0.074] | +0.034 | +0.039 | 3 of 5 | +0.020 / +0.020 | +0.045 / +0.045 | 0.000 |
| E4e: medcpt-cross on hybrid+stem+prefix, top 30, blend | hybrid+stem+prefix | DROPPED | +0.009 [-0.004, +0.021] | +0.009 | +0.022 | 4 of 5 | +0.005 / +0.005 | +0.008 / +0.008 | 0.000 |
| E5a: best together: bge-large + heading on both sides, stem+prefix | E3d: rrf[bm25+stem, large+prefix] | PENDING_GRADING | +0.021 [-0.004, +0.047] | +0.029 | +0.004 | 4 of 5 | +0.009 / +0.018 | +0.019 / +0.028 | 0.058 |
| E5a: best together: bge-large + heading on both sides, stem+prefix | hybrid | PENDING_GRADING | +0.098 [+0.049, +0.145] | +0.109 | +0.054 | 5 of 5 | +0.085 / +0.095 | +0.108 / +0.120 | 0.058 |
| E5a: best together: bge-large + heading on both sides, stem+prefix | hybrid+stem+prefix | PENDING_GRADING | +0.072 [+0.033, +0.113] | +0.083 | +0.036 | 4 of 5 | +0.057 / +0.067 | +0.071 / +0.083 | 0.058 |
| E5b: best together: bge-large + heading on the dense side only, stem+prefix | E3d: rrf[bm25+stem, large+prefix] | CANDIDATE | +0.022 [-0.001, +0.048] | +0.023 | +0.013 | 4 of 5 | +0.012 / +0.013 | +0.019 / +0.020 | 0.021 |
| E5b: best together: bge-large + heading on the dense side only, stem+prefix | hybrid | CANDIDATE | +0.099 [+0.057, +0.141] | +0.103 | +0.063 | 5 of 5 | +0.088 / +0.091 | +0.108 / +0.111 | 0.021 |
| E5b: best together: bge-large + heading on the dense side only, stem+prefix | hybrid+stem+prefix | CANDIDATE | +0.074 [+0.037, +0.112] | +0.077 | +0.045 | 5 of 5 | +0.060 / +0.062 | +0.070 / +0.074 | 0.021 |
| E6a: bge-ft on rrf[bm25+stem, large+prefix+head], top 30, replace | E5b: rrf[bm25+stem, large+prefix+head] (no rerank) | PENDING_GRADING | -0.104 [-0.176, -0.037] | -0.097 | -0.049 | 1 of 5 | -0.122 / -0.114 | -0.114 / -0.107 | 0.065 |
| E6a: bge-ft on rrf[bm25+stem, large+prefix+head], top 30, replace | hybrid | PENDING_GRADING | -0.004 [-0.068, +0.056] | +0.006 | +0.014 | 4 of 5 | -0.022 / -0.012 | -0.007 / +0.004 | 0.065 |
| E6a: bge-ft on rrf[bm25+stem, large+prefix+head], top 30, replace | hybrid+stem+prefix | PENDING_GRADING | -0.030 [-0.092, +0.030] | -0.020 | -0.003 | 2 of 5 | -0.051 / -0.040 | -0.044 / -0.033 | 0.065 |
| E6b: bge-ft on rrf[bm25+stem, large+prefix+head], top 30, blend | E5b: rrf[bm25+stem, large+prefix+head] (no rerank) | DROPPED | -0.011 [-0.047, +0.023] | -0.007 | +0.021 | 2 of 5 | -0.024 / -0.020 | -0.018 / -0.014 | 0.018 |
| E6b: bge-ft on rrf[bm25+stem, large+prefix+head], top 30, blend | hybrid | CANDIDATE | +0.088 [+0.046, +0.131] | +0.095 | +0.084 | 5 of 5 | +0.077 / +0.084 | +0.089 / +0.096 | 0.018 |
| E6b: bge-ft on rrf[bm25+stem, large+prefix+head], top 30, blend | hybrid+stem+prefix | CANDIDATE | +0.063 [+0.024, +0.105] | +0.069 | +0.067 | 5 of 5 | +0.044 / +0.051 | +0.052 / +0.059 | 0.018 |
| E6c: bge-reranker-base on rrf[bm25+stem, large+prefix+head], top 30, replace | E5b: rrf[bm25+stem, large+prefix+head] (no rerank) | PENDING_GRADING | -0.136 [-0.204, -0.072] | -0.101 | -0.053 | 0 of 5 | -0.156 / -0.123 | -0.148 / -0.112 | 0.104 |
| E6c: bge-reranker-base on rrf[bm25+stem, large+prefix+head], top 30, replace | hybrid | PENDING_GRADING | -0.037 [-0.091, +0.017] | +0.002 | +0.010 | 2 of 5 | -0.053 / -0.019 | -0.040 / -0.001 | 0.104 |
| E6c: bge-reranker-base on rrf[bm25+stem, large+prefix+head], top 30, replace | hybrid+stem+prefix | PENDING_GRADING | -0.063 [-0.122, -0.002] | -0.024 | -0.007 | 1 of 5 | -0.084 / -0.049 | -0.078 / -0.038 | 0.104 |
| E6d: bge-reranker-base on rrf[bm25+stem, large+prefix+head], top 30, blend | E5b: rrf[bm25+stem, large+prefix+head] (no rerank) | DROPPED | -0.032 [-0.072, +0.006] | -0.026 | +0.013 | 1 of 5 | -0.044 / -0.038 | -0.039 / -0.033 | 0.040 |
| E6d: bge-reranker-base on rrf[bm25+stem, large+prefix+head], top 30, blend | hybrid | CANDIDATE | +0.068 [+0.028, +0.109] | +0.077 | +0.076 | 4 of 5 | +0.056 / +0.063 | +0.069 / +0.078 | 0.040 |
| E6d: bge-reranker-base on rrf[bm25+stem, large+prefix+head], top 30, blend | hybrid+stem+prefix | CANDIDATE | +0.042 [-0.000, +0.086] | +0.051 | +0.058 | 5 of 5 | +0.025 / +0.032 | +0.032 / +0.041 | 0.040 |
<!-- summary:end -->

## E0: hybrid+stem+prefix vs hybrid (carried over from Step 17)

**Decisions:** vs hybrid: CANDIDATE.

- What changed: BM25 half uses the light-stemmed index and the dense half adds the BGE query instruction. Base is plain hybrid. Run first to check the harness; Step 17 already saw these queries and its held-out check did not confirm the gain. It is also the second base of every later experiment.
- Parameters: variant=hybrid+stem+prefix

### vs hybrid

**CANDIDATE.** gain +0.026 / +0.026, wins 3 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.026, condensed +0.026, Recall@20 +0.017.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.013, +0.062].
- Folds won: 3 of 5.
- Without q55: nDCG@10 gain +0.037 (unjudged=0) / +0.037 (condensed).
- Leave-top-2-out gain: +0.013 / +0.013; top gainers: q15 +0.417, q01 +0.322.
- unjudged@10: variant 0.000, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.563 | 0.607 | +0.044 | 0.563 | 0.607 | +0.044 | yes |
| 2 | 12 | 0.677 | 0.650 | -0.027 | 0.677 | 0.650 | -0.027 |  |
| 3 | 11 | 0.519 | 0.560 | +0.041 | 0.519 | 0.560 | +0.041 | yes |
| 4 | 11 | 0.653 | 0.744 | +0.091 | 0.653 | 0.744 | +0.091 | yes |
| 5 | 11 | 0.607 | 0.588 | -0.019 | 0.607 | 0.588 | -0.019 |  |

Pooled base nDCG@10 0.604, variant 0.630.

## E1a: bge-reranker-base on hybrid, top 30, replace

**Decisions:** vs hybrid: DROPPED; vs hybrid+stem+prefix: DROPPED.

- What changed: BAAI/bge-reranker-base reorders the top 30 of hybrid; mode replace (sorted by cross-encoder score alone). Hits beyond depth 30 keep their first-stage order.
- Parameters: model=BAAI/bge-reranker-base, first_stage=hybrid, depth=30, mode=replace, alpha=-, max_length=512

### vs hybrid

**DROPPED.** gain -0.003 (unjudged=0) / -0.000 (condensed) is not above 0.01.

- Pooled over 57 queries: nDCG@10 unjudged=0 -0.003, condensed -0.000, Recall@20 -0.017.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.060, +0.053].
- Folds won: 3 of 5.
- Without q55: nDCG@10 gain -0.006 (unjudged=0) / -0.003 (condensed).
- Leave-top-2-out gain: -0.022 / -0.019; top gainers: q39 +0.559, q01 +0.466.
- unjudged@10: variant 0.019, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.563 | 0.666 | +0.103 | 0.563 | 0.674 | +0.111 | yes |
| 2 | 12 | 0.677 | 0.641 | -0.036 | 0.677 | 0.641 | -0.035 |  |
| 3 | 11 | 0.519 | 0.532 | +0.013 | 0.519 | 0.536 | +0.017 | yes |
| 4 | 11 | 0.653 | 0.661 | +0.008 | 0.653 | 0.661 | +0.008 | yes |
| 5 | 11 | 0.607 | 0.498 | -0.109 | 0.607 | 0.498 | -0.109 |  |

Pooled base nDCG@10 0.604, variant 0.601.

### vs hybrid+stem+prefix

**DROPPED.** gain -0.029 (unjudged=0) / -0.026 (condensed) is not above 0.01.

- Pooled over 57 queries: nDCG@10 unjudged=0 -0.029, condensed -0.026, Recall@20 -0.034.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.092, +0.035].
- Folds won: 1 of 5.
- Without q55: nDCG@10 gain -0.043 (unjudged=0) / -0.040 (condensed).
- Leave-top-2-out gain: -0.052 / -0.049; top gainers: q55 +0.777, q39 +0.435.
- unjudged@10: variant 0.019, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.607 | 0.666 | +0.059 | 0.607 | 0.674 | +0.067 | yes |
| 2 | 12 | 0.650 | 0.641 | -0.009 | 0.650 | 0.641 | -0.009 |  |
| 3 | 11 | 0.560 | 0.532 | -0.029 | 0.560 | 0.536 | -0.024 |  |
| 4 | 11 | 0.744 | 0.661 | -0.083 | 0.744 | 0.661 | -0.083 |  |
| 5 | 11 | 0.588 | 0.498 | -0.090 | 0.588 | 0.498 | -0.090 |  |

Pooled base nDCG@10 0.630, variant 0.601.

Cross-encoder scores were reused from the on-disk cache. Original scoring pass (shared by E1a to E1h): 71.7 min for 3415 pairs at 0.80 pairs/s, batch 8, 6 torch threads, machine shared with other jobs.

## E1b: bge-reranker-base on hybrid, top 30, blend

**Decisions:** vs hybrid: CANDIDATE; vs hybrid+stem+prefix: DROPPED.

- What changed: BAAI/bge-reranker-base reorders the top 30 of hybrid; mode blend (alpha 0.5: 0.5 x min-max cross-encoder score + 0.5 x min-max first-stage score). Hits beyond depth 30 keep their first-stage order.
- Parameters: model=BAAI/bge-reranker-base, first_stage=hybrid, depth=30, mode=blend, alpha=0.5, max_length=512

### vs hybrid

**CANDIDATE.** gain +0.028 / +0.028, wins 4 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.028, condensed +0.028, Recall@20 +0.024.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.008, +0.065].
- Folds won: 4 of 5.
- Without q55: nDCG@10 gain +0.026 (unjudged=0) / +0.026 (condensed).
- Leave-top-2-out gain: +0.013 / +0.013; top gainers: q39 +0.503, q01 +0.374.
- unjudged@10: variant 0.002, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.563 | 0.654 | +0.091 | 0.563 | 0.656 | +0.093 | yes |
| 2 | 12 | 0.677 | 0.696 | +0.020 | 0.677 | 0.696 | +0.020 | yes |
| 3 | 11 | 0.519 | 0.547 | +0.028 | 0.519 | 0.547 | +0.028 | yes |
| 4 | 11 | 0.653 | 0.696 | +0.043 | 0.653 | 0.696 | +0.043 | yes |
| 5 | 11 | 0.607 | 0.560 | -0.047 | 0.607 | 0.560 | -0.047 |  |

Pooled base nDCG@10 0.604, variant 0.632.

### vs hybrid+stem+prefix

**DROPPED.** gain +0.002 (unjudged=0) / +0.003 (condensed) is not above 0.01.

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.002, condensed +0.003, Recall@20 +0.007.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.045, +0.050].
- Folds won: 2 of 5.
- Without q55: nDCG@10 gain -0.012 (unjudged=0) / -0.011 (condensed).
- Leave-top-2-out gain: -0.019 / -0.018; top gainers: q55 +0.777, q39 +0.380.
- unjudged@10: variant 0.002, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.607 | 0.654 | +0.047 | 0.607 | 0.656 | +0.049 | yes |
| 2 | 12 | 0.650 | 0.696 | +0.046 | 0.650 | 0.696 | +0.046 | yes |
| 3 | 11 | 0.560 | 0.547 | -0.014 | 0.560 | 0.547 | -0.014 |  |
| 4 | 11 | 0.744 | 0.696 | -0.048 | 0.744 | 0.696 | -0.048 |  |
| 5 | 11 | 0.588 | 0.560 | -0.028 | 0.588 | 0.560 | -0.028 |  |

Pooled base nDCG@10 0.630, variant 0.632.

Cross-encoder scores were reused from the on-disk cache. Original scoring pass (shared by E1a to E1h): 71.7 min for 3415 pairs at 0.80 pairs/s, batch 8, 6 torch threads, machine shared with other jobs.

## E1c: bge-reranker-base on hybrid, top 50, replace

**Decisions:** vs hybrid: PENDING_GRADING; vs hybrid+stem+prefix: PENDING_GRADING.

- What changed: BAAI/bge-reranker-base reorders the top 50 of hybrid; mode replace (sorted by cross-encoder score alone). Hits beyond depth 50 keep their first-stage order.
- Parameters: model=BAAI/bge-reranker-base, first_stage=hybrid, depth=50, mode=replace, alpha=-, max_length=512

### vs hybrid

**PENDING_GRADING.** unjudged@10 is 0.105, above 0.05; grade the pairs in results/step18_unjudged.csv, then re-judge.

- Pooled over 57 queries: nDCG@10 unjudged=0 -0.028, condensed -0.002, Recall@20 -0.049.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.090, +0.036].
- Folds won: 2 of 5.
- Without q55: nDCG@10 gain -0.031 (unjudged=0) / -0.005 (condensed).
- Leave-top-2-out gain: -0.047 / -0.021; top gainers: q39 +0.529, q24 +0.494.
- unjudged@10: variant 0.105, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.563 | 0.607 | +0.044 | 0.563 | 0.633 | +0.070 | yes |
| 2 | 12 | 0.677 | 0.603 | -0.074 | 0.677 | 0.641 | -0.036 |  |
| 3 | 11 | 0.519 | 0.565 | +0.046 | 0.519 | 0.598 | +0.079 | yes |
| 4 | 11 | 0.653 | 0.635 | -0.018 | 0.653 | 0.651 | -0.002 |  |
| 5 | 11 | 0.607 | 0.466 | -0.141 | 0.607 | 0.480 | -0.127 |  |

Pooled base nDCG@10 0.604, variant 0.576.

### vs hybrid+stem+prefix

**PENDING_GRADING.** unjudged@10 is 0.105, above 0.05; grade the pairs in results/step18_unjudged.csv, then re-judge.

- Pooled over 57 queries: nDCG@10 unjudged=0 -0.053, condensed -0.028, Recall@20 -0.066.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.120, +0.014].
- Folds won: 2 of 5.
- Without q55: nDCG@10 gain -0.068 (unjudged=0) / -0.042 (condensed).
- Leave-top-2-out gain: -0.078 / -0.052; top gainers: q55 +0.777, q24 +0.494.
- unjudged@10: variant 0.105, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.607 | 0.607 | +0.000 | 0.607 | 0.633 | +0.026 | yes |
| 2 | 12 | 0.650 | 0.603 | -0.047 | 0.650 | 0.641 | -0.009 |  |
| 3 | 11 | 0.560 | 0.565 | +0.005 | 0.560 | 0.598 | +0.038 | yes |
| 4 | 11 | 0.744 | 0.635 | -0.109 | 0.744 | 0.651 | -0.093 |  |
| 5 | 11 | 0.588 | 0.466 | -0.122 | 0.588 | 0.480 | -0.108 |  |

Pooled base nDCG@10 0.630, variant 0.576.

Cross-encoder scores were reused from the on-disk cache. Original scoring pass (shared by E1a to E1h): 71.7 min for 3415 pairs at 0.80 pairs/s, batch 8, 6 torch threads, machine shared with other jobs.

## E1d: bge-reranker-base on hybrid, top 50, blend

**Decisions:** vs hybrid: CANDIDATE; vs hybrid+stem+prefix: DROPPED.

- What changed: BAAI/bge-reranker-base reorders the top 50 of hybrid; mode blend (alpha 0.5: 0.5 x min-max cross-encoder score + 0.5 x min-max first-stage score). Hits beyond depth 50 keep their first-stage order.
- Parameters: model=BAAI/bge-reranker-base, first_stage=hybrid, depth=50, mode=blend, alpha=0.5, max_length=512

### vs hybrid

**CANDIDATE.** gain +0.034 / +0.036, wins 4 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.034, condensed +0.036, Recall@20 +0.041.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.006, +0.075].
- Folds won: 4 of 5.
- Without q55: nDCG@10 gain +0.032 (unjudged=0) / +0.034 (condensed).
- Leave-top-2-out gain: +0.019 / +0.021; top gainers: q39 +0.503, q01 +0.381.
- unjudged@10: variant 0.009, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.563 | 0.651 | +0.089 | 0.563 | 0.659 | +0.097 | yes |
| 2 | 12 | 0.677 | 0.694 | +0.017 | 0.677 | 0.694 | +0.017 | yes |
| 3 | 11 | 0.519 | 0.603 | +0.084 | 0.519 | 0.603 | +0.084 | yes |
| 4 | 11 | 0.653 | 0.679 | +0.026 | 0.653 | 0.681 | +0.028 | yes |
| 5 | 11 | 0.607 | 0.557 | -0.050 | 0.607 | 0.557 | -0.050 |  |

Pooled base nDCG@10 0.604, variant 0.638.

### vs hybrid+stem+prefix

**DROPPED.** gain +0.008 (unjudged=0) / +0.010 (condensed) is not above 0.01.

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.008, condensed +0.010, Recall@20 +0.023.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.041, +0.059].
- Folds won: 3 of 5.
- Without q55: nDCG@10 gain -0.005 (unjudged=0) / -0.003 (condensed).
- Leave-top-2-out gain: -0.012 / -0.010; top gainers: q55 +0.777, q39 +0.380.
- unjudged@10: variant 0.009, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.607 | 0.651 | +0.045 | 0.607 | 0.659 | +0.053 | yes |
| 2 | 12 | 0.650 | 0.694 | +0.044 | 0.650 | 0.694 | +0.044 | yes |
| 3 | 11 | 0.560 | 0.603 | +0.043 | 0.560 | 0.603 | +0.043 | yes |
| 4 | 11 | 0.744 | 0.679 | -0.065 | 0.744 | 0.681 | -0.063 |  |
| 5 | 11 | 0.588 | 0.557 | -0.031 | 0.588 | 0.557 | -0.031 |  |

Pooled base nDCG@10 0.630, variant 0.638.

Cross-encoder scores were reused from the on-disk cache. Original scoring pass (shared by E1a to E1h): 71.7 min for 3415 pairs at 0.80 pairs/s, batch 8, 6 torch threads, machine shared with other jobs.

## E1e: bge-reranker-base on hybrid+stem+prefix, top 30, replace

**Decisions:** vs hybrid: DROPPED; vs hybrid+stem+prefix: DROPPED.

- What changed: BAAI/bge-reranker-base reorders the top 30 of hybrid+stem+prefix; mode replace (sorted by cross-encoder score alone). Hits beyond depth 30 keep their first-stage order.
- Parameters: model=BAAI/bge-reranker-base, first_stage=hybrid+stem+prefix, depth=30, mode=replace, alpha=-, max_length=512

### vs hybrid

**DROPPED.** gain -0.007 (unjudged=0) / -0.003 (condensed) is not above 0.01.

- Pooled over 57 queries: nDCG@10 unjudged=0 -0.007, condensed -0.003, Recall@20 +0.006.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.064, +0.049].
- Folds won: 2 of 5.
- Without q55: nDCG@10 gain -0.010 (unjudged=0) / -0.006 (condensed).
- Leave-top-2-out gain: -0.026 / -0.021; top gainers: q39 +0.559, q01 +0.442.
- unjudged@10: variant 0.026, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.563 | 0.665 | +0.102 | 0.563 | 0.681 | +0.118 | yes |
| 2 | 12 | 0.677 | 0.643 | -0.033 | 0.677 | 0.644 | -0.033 |  |
| 3 | 11 | 0.519 | 0.560 | +0.041 | 0.519 | 0.560 | +0.041 | yes |
| 4 | 11 | 0.653 | 0.618 | -0.035 | 0.653 | 0.618 | -0.035 |  |
| 5 | 11 | 0.607 | 0.487 | -0.119 | 0.607 | 0.492 | -0.115 |  |

Pooled base nDCG@10 0.604, variant 0.597.

### vs hybrid+stem+prefix

**DROPPED.** gain -0.033 (unjudged=0) / -0.029 (condensed) is not above 0.01.

- Pooled over 57 queries: nDCG@10 unjudged=0 -0.033, condensed -0.029, Recall@20 -0.012.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.093, +0.028].
- Folds won: 1 of 5.
- Without q55: nDCG@10 gain -0.047 (unjudged=0) / -0.043 (condensed).
- Leave-top-2-out gain: -0.056 / -0.052; top gainers: q55 +0.777, q39 +0.435.
- unjudged@10: variant 0.026, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.607 | 0.665 | +0.058 | 0.607 | 0.681 | +0.074 | yes |
| 2 | 12 | 0.650 | 0.643 | -0.007 | 0.650 | 0.644 | -0.006 |  |
| 3 | 11 | 0.560 | 0.560 | -0.000 | 0.560 | 0.560 | -0.000 |  |
| 4 | 11 | 0.744 | 0.618 | -0.126 | 0.744 | 0.618 | -0.126 |  |
| 5 | 11 | 0.588 | 0.487 | -0.101 | 0.588 | 0.492 | -0.096 |  |

Pooled base nDCG@10 0.630, variant 0.597.

Cross-encoder scores were reused from the on-disk cache. Original scoring pass (shared by E1a to E1h): 71.7 min for 3415 pairs at 0.80 pairs/s, batch 8, 6 torch threads, machine shared with other jobs.

## E1f: bge-reranker-base on hybrid+stem+prefix, top 30, blend

**Decisions:** vs hybrid: CANDIDATE; vs hybrid+stem+prefix: DROPPED.

- What changed: BAAI/bge-reranker-base reorders the top 30 of hybrid+stem+prefix; mode blend (alpha 0.5: 0.5 x min-max cross-encoder score + 0.5 x min-max first-stage score). Hits beyond depth 30 keep their first-stage order.
- Parameters: model=BAAI/bge-reranker-base, first_stage=hybrid+stem+prefix, depth=30, mode=blend, alpha=0.5, max_length=512

### vs hybrid

**CANDIDATE.** gain +0.043 / +0.043, wins 4 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.043, condensed +0.043, Recall@20 +0.039.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [+0.005, +0.082].
- Folds won: 4 of 5.
- Without q55: nDCG@10 gain +0.043 (unjudged=0) / +0.043 (condensed).
- Leave-top-2-out gain: +0.029 / +0.029; top gainers: q39 +0.503, q01 +0.339.
- unjudged@10: variant 0.002, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.563 | 0.674 | +0.111 | 0.563 | 0.674 | +0.111 | yes |
| 2 | 12 | 0.677 | 0.703 | +0.026 | 0.677 | 0.703 | +0.026 | yes |
| 3 | 11 | 0.519 | 0.589 | +0.070 | 0.519 | 0.589 | +0.070 | yes |
| 4 | 11 | 0.653 | 0.722 | +0.069 | 0.653 | 0.722 | +0.069 | yes |
| 5 | 11 | 0.607 | 0.543 | -0.064 | 0.607 | 0.543 | -0.064 |  |

Pooled base nDCG@10 0.604, variant 0.647.

### vs hybrid+stem+prefix

**DROPPED.** driven by 1 to 2 queries (q55 +0.708, q39 +0.380); without them the gain is -0.002 / -0.001.

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.018, condensed +0.018, Recall@20 +0.022.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.019, +0.058].
- Folds won: 3 of 5.
- Without q55: nDCG@10 gain +0.005 (unjudged=0) / +0.005 (condensed).
- Leave-top-2-out gain: -0.002 / -0.001; top gainers: q55 +0.708, q39 +0.380.
- unjudged@10: variant 0.002, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.607 | 0.674 | +0.067 | 0.607 | 0.674 | +0.067 | yes |
| 2 | 12 | 0.650 | 0.703 | +0.053 | 0.650 | 0.703 | +0.053 | yes |
| 3 | 11 | 0.560 | 0.589 | +0.028 | 0.560 | 0.589 | +0.028 | yes |
| 4 | 11 | 0.744 | 0.722 | -0.022 | 0.744 | 0.722 | -0.022 |  |
| 5 | 11 | 0.588 | 0.543 | -0.045 | 0.588 | 0.543 | -0.045 |  |

Pooled base nDCG@10 0.630, variant 0.647.

Cross-encoder scores were reused from the on-disk cache. Original scoring pass (shared by E1a to E1h): 71.7 min for 3415 pairs at 0.80 pairs/s, batch 8, 6 torch threads, machine shared with other jobs.

## E1g: bge-reranker-base on hybrid+stem+prefix, top 50, replace

**Decisions:** vs hybrid: PENDING_GRADING; vs hybrid+stem+prefix: PENDING_GRADING.

- What changed: BAAI/bge-reranker-base reorders the top 50 of hybrid+stem+prefix; mode replace (sorted by cross-encoder score alone). Hits beyond depth 50 keep their first-stage order.
- Parameters: model=BAAI/bge-reranker-base, first_stage=hybrid+stem+prefix, depth=50, mode=replace, alpha=-, max_length=512

### vs hybrid

**PENDING_GRADING.** unjudged@10 is 0.102, above 0.05; grade the pairs in results/step18_unjudged.csv, then re-judge.

- Pooled over 57 queries: nDCG@10 unjudged=0 -0.039, condensed -0.017, Recall@20 -0.052.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.100, +0.021].
- Folds won: 2 of 5.
- Without q55: nDCG@10 gain -0.043 (unjudged=0) / -0.019 (condensed).
- Leave-top-2-out gain: -0.055 / -0.035; top gainers: q01 +0.458, q61 +0.335.
- unjudged@10: variant 0.102, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.563 | 0.582 | +0.020 | 0.563 | 0.619 | +0.056 | yes |
| 2 | 12 | 0.677 | 0.625 | -0.052 | 0.677 | 0.640 | -0.036 |  |
| 3 | 11 | 0.519 | 0.548 | +0.029 | 0.519 | 0.579 | +0.060 | yes |
| 4 | 11 | 0.653 | 0.587 | -0.067 | 0.653 | 0.605 | -0.048 |  |
| 5 | 11 | 0.607 | 0.476 | -0.131 | 0.607 | 0.489 | -0.118 |  |

Pooled base nDCG@10 0.604, variant 0.565.

### vs hybrid+stem+prefix

**PENDING_GRADING.** unjudged@10 is 0.102, above 0.05; grade the pairs in results/step18_unjudged.csv, then re-judge.

- Pooled over 57 queries: nDCG@10 unjudged=0 -0.065, condensed -0.042, Recall@20 -0.069.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.129, +0.000].
- Folds won: 0 of 5.
- Without q55: nDCG@10 gain -0.080 (unjudged=0) / -0.057 (condensed).
- Leave-top-2-out gain: -0.086 / -0.065; top gainers: q55 +0.777, q61 +0.283.
- unjudged@10: variant 0.102, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.607 | 0.582 | -0.024 | 0.607 | 0.619 | +0.012 |  |
| 2 | 12 | 0.650 | 0.625 | -0.025 | 0.650 | 0.640 | -0.010 |  |
| 3 | 11 | 0.560 | 0.548 | -0.012 | 0.560 | 0.579 | +0.018 |  |
| 4 | 11 | 0.744 | 0.587 | -0.158 | 0.744 | 0.605 | -0.139 |  |
| 5 | 11 | 0.588 | 0.476 | -0.112 | 0.588 | 0.489 | -0.100 |  |

Pooled base nDCG@10 0.630, variant 0.565.

Cross-encoder scores were reused from the on-disk cache. Original scoring pass (shared by E1a to E1h): 71.7 min for 3415 pairs at 0.80 pairs/s, batch 8, 6 torch threads, machine shared with other jobs.

## E1h: bge-reranker-base on hybrid+stem+prefix, top 50, blend

**Decisions:** vs hybrid: CANDIDATE; vs hybrid+stem+prefix: DROPPED.

- What changed: BAAI/bge-reranker-base reorders the top 50 of hybrid+stem+prefix; mode blend (alpha 0.5: 0.5 x min-max cross-encoder score + 0.5 x min-max first-stage score). Hits beyond depth 50 keep their first-stage order.
- Parameters: model=BAAI/bge-reranker-base, first_stage=hybrid+stem+prefix, depth=50, mode=blend, alpha=0.5, max_length=512

### vs hybrid

**CANDIDATE.** gain +0.040 / +0.041, wins 4 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.040, condensed +0.041, Recall@20 +0.036.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.001, +0.081].
- Folds won: 4 of 5.
- Without q55: nDCG@10 gain +0.039 (unjudged=0) / +0.040 (condensed).
- Leave-top-2-out gain: +0.028 / +0.028; top gainers: q39 +0.390, q01 +0.381.
- unjudged@10: variant 0.007, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.563 | 0.663 | +0.101 | 0.563 | 0.664 | +0.101 | yes |
| 2 | 12 | 0.677 | 0.699 | +0.022 | 0.677 | 0.699 | +0.022 | yes |
| 3 | 11 | 0.519 | 0.603 | +0.084 | 0.519 | 0.604 | +0.085 | yes |
| 4 | 11 | 0.653 | 0.713 | +0.060 | 0.653 | 0.716 | +0.062 | yes |
| 5 | 11 | 0.607 | 0.536 | -0.070 | 0.607 | 0.536 | -0.070 |  |

Pooled base nDCG@10 0.604, variant 0.644.

### vs hybrid+stem+prefix

**DROPPED.** driven by 1 to 2 queries (q55 +0.708, q39 +0.267); without them the gain is -0.003 / -0.002.

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.015, condensed +0.015, Recall@20 +0.019.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.026, +0.057].
- Folds won: 3 of 5.
- Without q55: nDCG@10 gain +0.002 (unjudged=0) / +0.003 (condensed).
- Leave-top-2-out gain: -0.003 / -0.002; top gainers: q55 +0.708, q39 +0.267.
- unjudged@10: variant 0.007, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.607 | 0.663 | +0.057 | 0.607 | 0.664 | +0.057 | yes |
| 2 | 12 | 0.650 | 0.699 | +0.049 | 0.650 | 0.699 | +0.049 | yes |
| 3 | 11 | 0.560 | 0.603 | +0.043 | 0.560 | 0.604 | +0.044 | yes |
| 4 | 11 | 0.744 | 0.713 | -0.031 | 0.744 | 0.716 | -0.029 |  |
| 5 | 11 | 0.588 | 0.536 | -0.052 | 0.588 | 0.536 | -0.052 |  |

Pooled base nDCG@10 0.630, variant 0.644.

Cross-encoder scores were reused from the on-disk cache. Original scoring pass (shared by E1a to E1h): 71.7 min for 3415 pairs at 0.80 pairs/s, batch 8, 6 torch threads, machine shared with other jobs.

## E2a: heading prepended, BM25 side, plain hybrid

**Decisions:** vs hybrid: CANDIDATE; vs hybrid+stem+prefix: DROPPED.

- What changed: BM25 index text gets part, section and heading
- Parameters: system=rrf[bm25+head, small], wall_s_to_build_and_rank=4

### vs hybrid

**CANDIDATE.** gain +0.020 / +0.020, wins 4 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.020, condensed +0.020, Recall@20 +0.002.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [+0.004, +0.038].
- Folds won: 4 of 5.
- Without q55: nDCG@10 gain +0.019 (unjudged=0) / +0.019 (condensed).
- Leave-top-2-out gain: +0.011 / +0.011; top gainers: q15 +0.294, q40 +0.247.
- unjudged@10: variant 0.002, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.563 | 0.569 | +0.006 | 0.563 | 0.569 | +0.006 | yes |
| 2 | 12 | 0.677 | 0.684 | +0.007 | 0.677 | 0.684 | +0.007 | yes |
| 3 | 11 | 0.519 | 0.545 | +0.026 | 0.519 | 0.545 | +0.026 | yes |
| 4 | 11 | 0.653 | 0.719 | +0.065 | 0.653 | 0.719 | +0.065 | yes |
| 5 | 11 | 0.607 | 0.603 | -0.004 | 0.607 | 0.603 | -0.004 |  |

Pooled base nDCG@10 0.604, variant 0.624.

### vs hybrid+stem+prefix

**DROPPED.** gain -0.006 (unjudged=0) / -0.006 (condensed) is not above 0.01.

- Pooled over 57 queries: nDCG@10 unjudged=0 -0.006, condensed -0.006, Recall@20 -0.015.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.041, +0.032].
- Folds won: 2 of 5.
- Without q55: nDCG@10 gain -0.018 (unjudged=0) / -0.018 (condensed).
- Leave-top-2-out gain: -0.023 / -0.023; top gainers: q55 +0.703, q21 +0.212.
- unjudged@10: variant 0.002, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.607 | 0.569 | -0.038 | 0.607 | 0.569 | -0.038 |  |
| 2 | 12 | 0.650 | 0.684 | +0.034 | 0.650 | 0.684 | +0.034 | yes |
| 3 | 11 | 0.560 | 0.545 | -0.015 | 0.560 | 0.545 | -0.015 |  |
| 4 | 11 | 0.744 | 0.719 | -0.026 | 0.744 | 0.719 | -0.026 |  |
| 5 | 11 | 0.588 | 0.603 | +0.015 | 0.588 | 0.603 | +0.015 | yes |

Pooled base nDCG@10 0.630, variant 0.624.

Build and ranking wall time: 0.1 min (embeddings cached on disk afterwards).

## E2b: heading prepended, dense side, plain hybrid

**Decisions:** vs hybrid: CANDIDATE; vs hybrid+stem+prefix: DROPPED.

- What changed: bge-small embeds heading plus text
- Parameters: system=rrf[bm25, small+head], wall_s_to_build_and_rank=318

### vs hybrid

**CANDIDATE.** gain +0.048 / +0.050, wins 5 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.048, condensed +0.050, Recall@20 +0.002.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [+0.021, +0.076].
- Folds won: 5 of 5.
- Without q55: nDCG@10 gain +0.051 (unjudged=0) / +0.053 (condensed).
- Leave-top-2-out gain: +0.038 / +0.039; top gainers: q50 +0.363, q06 +0.279.
- unjudged@10: variant 0.009, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.563 | 0.619 | +0.056 | 0.563 | 0.625 | +0.062 | yes |
| 2 | 12 | 0.677 | 0.722 | +0.045 | 0.677 | 0.722 | +0.045 | yes |
| 3 | 11 | 0.519 | 0.638 | +0.119 | 0.519 | 0.638 | +0.119 | yes |
| 4 | 11 | 0.653 | 0.667 | +0.014 | 0.653 | 0.667 | +0.014 | yes |
| 5 | 11 | 0.607 | 0.612 | +0.005 | 0.607 | 0.615 | +0.008 | yes |

Pooled base nDCG@10 0.604, variant 0.652.

### vs hybrid+stem+prefix

**DROPPED.** driven by 1 to 2 queries (q55 +0.514, q50 +0.386); without them the gain is +0.007 / +0.008.

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.022, condensed +0.024, Recall@20 -0.015.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.015, +0.062].
- Folds won: 4 of 5.
- Without q55: nDCG@10 gain +0.014 (unjudged=0) / +0.016 (condensed).
- Leave-top-2-out gain: +0.007 / +0.008; top gainers: q55 +0.514, q50 +0.386.
- unjudged@10: variant 0.009, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.607 | 0.619 | +0.012 | 0.607 | 0.625 | +0.018 | yes |
| 2 | 12 | 0.650 | 0.722 | +0.072 | 0.650 | 0.722 | +0.072 | yes |
| 3 | 11 | 0.560 | 0.638 | +0.078 | 0.560 | 0.638 | +0.078 | yes |
| 4 | 11 | 0.744 | 0.667 | -0.077 | 0.744 | 0.667 | -0.077 |  |
| 5 | 11 | 0.588 | 0.612 | +0.024 | 0.588 | 0.615 | +0.027 | yes |

Pooled base nDCG@10 0.630, variant 0.652.

Build and ranking wall time: 5.3 min (embeddings cached on disk afterwards).

## E2c: heading prepended, both sides, plain hybrid

**Decisions:** vs hybrid: CANDIDATE; vs hybrid+stem+prefix: CANDIDATE.

- What changed: BM25 and bge-small both index heading plus text
- Parameters: system=rrf[bm25+head, small+head], wall_s_to_build_and_rank=4

### vs hybrid

**CANDIDATE.** gain +0.058 / +0.064, wins 4 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.058, condensed +0.064, Recall@20 +0.001.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [+0.028, +0.089].
- Folds won: 4 of 5.
- Without q55: nDCG@10 gain +0.059 (unjudged=0) / +0.065 (condensed).
- Leave-top-2-out gain: +0.048 / +0.053; top gainers: q50 +0.365, q06 +0.287.
- unjudged@10: variant 0.035, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.563 | 0.600 | +0.037 | 0.563 | 0.610 | +0.047 | yes |
| 2 | 12 | 0.677 | 0.736 | +0.059 | 0.677 | 0.742 | +0.065 | yes |
| 3 | 11 | 0.519 | 0.641 | +0.122 | 0.519 | 0.645 | +0.126 | yes |
| 4 | 11 | 0.653 | 0.732 | +0.079 | 0.653 | 0.732 | +0.079 | yes |
| 5 | 11 | 0.607 | 0.603 | -0.004 | 0.607 | 0.612 | +0.005 |  |

Pooled base nDCG@10 0.604, variant 0.662.

### vs hybrid+stem+prefix

**CANDIDATE.** gain +0.033 / +0.039, wins 3 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.033, condensed +0.039, Recall@20 -0.016.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.005, +0.075].
- Folds won: 3 of 5.
- Without q55: nDCG@10 gain +0.021 (unjudged=0) / +0.027 (condensed).
- Leave-top-2-out gain: +0.015 / +0.019; top gainers: q55 +0.667, q50 +0.387.
- unjudged@10: variant 0.035, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.607 | 0.600 | -0.007 | 0.607 | 0.610 | +0.003 |  |
| 2 | 12 | 0.650 | 0.736 | +0.086 | 0.650 | 0.742 | +0.092 | yes |
| 3 | 11 | 0.560 | 0.641 | +0.081 | 0.560 | 0.645 | +0.084 | yes |
| 4 | 11 | 0.744 | 0.732 | -0.013 | 0.744 | 0.732 | -0.013 |  |
| 5 | 11 | 0.588 | 0.603 | +0.015 | 0.588 | 0.612 | +0.024 | yes |

Pooled base nDCG@10 0.630, variant 0.662.

Build and ranking wall time: 0.1 min (embeddings cached on disk afterwards).

## E2d: heading prepended, BM25 side, stem+prefix hybrid

**Decisions:** vs hybrid: CANDIDATE; vs hybrid+stem+prefix: DROPPED.

- What changed: as E2a on the stem+prefix hybrid
- Parameters: system=rrf[bm25+stem+head, small+prefix], wall_s_to_build_and_rank=4

### vs hybrid

**CANDIDATE.** gain +0.033 / +0.034, wins 3 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.033, condensed +0.034, Recall@20 +0.010.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.005, +0.069].
- Folds won: 3 of 5.
- Without q55: nDCG@10 gain +0.043 (unjudged=0) / +0.044 (condensed).
- Leave-top-2-out gain: +0.021 / +0.021; top gainers: q15 +0.417, q01 +0.323.
- unjudged@10: variant 0.002, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.563 | 0.586 | +0.023 | 0.563 | 0.588 | +0.025 | yes |
| 2 | 12 | 0.677 | 0.662 | -0.015 | 0.677 | 0.662 | -0.015 |  |
| 3 | 11 | 0.519 | 0.586 | +0.067 | 0.519 | 0.586 | +0.067 | yes |
| 4 | 11 | 0.653 | 0.756 | +0.103 | 0.653 | 0.756 | +0.103 | yes |
| 5 | 11 | 0.607 | 0.599 | -0.008 | 0.607 | 0.599 | -0.008 |  |

Pooled base nDCG@10 0.604, variant 0.637.

### vs hybrid+stem+prefix

**DROPPED.** gain +0.008 (unjudged=0) / +0.008 (condensed) is not above 0.01.

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.008, condensed +0.008, Recall@20 -0.007.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.004, +0.019].
- Folds won: 4 of 5.
- Without q55: nDCG@10 gain +0.006 (unjudged=0) / +0.006 (condensed).
- Leave-top-2-out gain: +0.003 / +0.003; top gainers: q02 +0.165, q09 +0.113.
- unjudged@10: variant 0.002, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.607 | 0.586 | -0.021 | 0.607 | 0.588 | -0.019 |  |
| 2 | 12 | 0.650 | 0.662 | +0.012 | 0.650 | 0.662 | +0.012 | yes |
| 3 | 11 | 0.560 | 0.586 | +0.026 | 0.560 | 0.586 | +0.026 | yes |
| 4 | 11 | 0.744 | 0.756 | +0.012 | 0.744 | 0.756 | +0.012 | yes |
| 5 | 11 | 0.588 | 0.599 | +0.011 | 0.588 | 0.599 | +0.011 | yes |

Pooled base nDCG@10 0.630, variant 0.637.

Build and ranking wall time: 0.1 min (embeddings cached on disk afterwards).

## E2e: heading prepended, dense side, stem+prefix hybrid

**Decisions:** vs hybrid: CANDIDATE; vs hybrid+stem+prefix: CANDIDATE.

- What changed: as E2b on the stem+prefix hybrid
- Parameters: system=rrf[bm25+stem, small+prefix+head], wall_s_to_build_and_rank=4

### vs hybrid

**CANDIDATE.** gain +0.063 / +0.065, wins 4 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.063, condensed +0.065, Recall@20 +0.024.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [+0.019, +0.105].
- Folds won: 4 of 5.
- Without q55: nDCG@10 gain +0.075 (unjudged=0) / +0.077 (condensed).
- Leave-top-2-out gain: +0.051 / +0.052; top gainers: q15 +0.399, q50 +0.381.
- unjudged@10: variant 0.007, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.563 | 0.637 | +0.075 | 0.563 | 0.646 | +0.084 | yes |
| 2 | 12 | 0.677 | 0.670 | -0.007 | 0.677 | 0.670 | -0.007 |  |
| 3 | 11 | 0.519 | 0.646 | +0.127 | 0.519 | 0.646 | +0.127 | yes |
| 4 | 11 | 0.653 | 0.756 | +0.103 | 0.653 | 0.756 | +0.103 | yes |
| 5 | 11 | 0.607 | 0.628 | +0.022 | 0.607 | 0.628 | +0.022 | yes |

Pooled base nDCG@10 0.604, variant 0.667.

### vs hybrid+stem+prefix

**CANDIDATE.** gain +0.037 / +0.039, wins 5 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.037, condensed +0.039, Recall@20 +0.006.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [+0.012, +0.064].
- Folds won: 5 of 5.
- Without q55: nDCG@10 gain +0.038 (unjudged=0) / +0.040 (condensed).
- Leave-top-2-out gain: +0.026 / +0.027; top gainers: q50 +0.403, q09 +0.286.
- unjudged@10: variant 0.007, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.607 | 0.637 | +0.031 | 0.607 | 0.646 | +0.040 | yes |
| 2 | 12 | 0.650 | 0.670 | +0.020 | 0.650 | 0.670 | +0.020 | yes |
| 3 | 11 | 0.560 | 0.646 | +0.086 | 0.560 | 0.646 | +0.086 | yes |
| 4 | 11 | 0.744 | 0.756 | +0.012 | 0.744 | 0.756 | +0.012 | yes |
| 5 | 11 | 0.588 | 0.628 | +0.040 | 0.588 | 0.628 | +0.040 | yes |

Pooled base nDCG@10 0.630, variant 0.667.

Build and ranking wall time: 0.1 min (embeddings cached on disk afterwards).

## E2f: heading prepended, both sides, stem+prefix hybrid

**Decisions:** vs hybrid: CANDIDATE; vs hybrid+stem+prefix: CANDIDATE.

- What changed: as E2c on the stem+prefix hybrid
- Parameters: system=rrf[bm25+stem+head, small+prefix+head], wall_s_to_build_and_rank=3

### vs hybrid

**CANDIDATE.** gain +0.068 / +0.077, wins 5 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.068, condensed +0.077, Recall@20 +0.011.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [+0.025, +0.111].
- Folds won: 5 of 5.
- Without q55: nDCG@10 gain +0.078 (unjudged=0) / +0.087 (condensed).
- Leave-top-2-out gain: +0.055 / +0.064; top gainers: q50 +0.456, q15 +0.395.
- unjudged@10: variant 0.030, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.563 | 0.624 | +0.061 | 0.563 | 0.630 | +0.067 | yes |
| 2 | 12 | 0.677 | 0.697 | +0.020 | 0.677 | 0.703 | +0.026 | yes |
| 3 | 11 | 0.519 | 0.669 | +0.150 | 0.519 | 0.678 | +0.159 | yes |
| 4 | 11 | 0.653 | 0.767 | +0.114 | 0.653 | 0.768 | +0.115 | yes |
| 5 | 11 | 0.607 | 0.609 | +0.002 | 0.607 | 0.631 | +0.024 | yes |

Pooled base nDCG@10 0.604, variant 0.673.

### vs hybrid+stem+prefix

**CANDIDATE.** gain +0.043 / +0.051, wins 5 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.043, condensed +0.051, Recall@20 -0.007.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [+0.013, +0.075].
- Folds won: 5 of 5.
- Without q55: nDCG@10 gain +0.041 (unjudged=0) / +0.050 (condensed).
- Leave-top-2-out gain: +0.030 / +0.037; top gainers: q50 +0.479, q09 +0.321.
- unjudged@10: variant 0.030, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.607 | 0.624 | +0.017 | 0.607 | 0.630 | +0.023 | yes |
| 2 | 12 | 0.650 | 0.697 | +0.047 | 0.650 | 0.703 | +0.053 | yes |
| 3 | 11 | 0.560 | 0.669 | +0.109 | 0.560 | 0.678 | +0.117 | yes |
| 4 | 11 | 0.744 | 0.767 | +0.023 | 0.744 | 0.768 | +0.023 | yes |
| 5 | 11 | 0.588 | 0.609 | +0.021 | 0.588 | 0.631 | +0.043 | yes |

Pooled base nDCG@10 0.630, variant 0.673.

Build and ranking wall time: 0.1 min (embeddings cached on disk afterwards).

## E3a: bge-base as the dense list, plain hybrid

**Decisions:** vs hybrid: CANDIDATE; vs hybrid+stem+prefix: DROPPED.

- What changed: dense list is bge-base, no prefix, plain BM25
- Parameters: system=rrf[bm25, base], wall_s_to_build_and_rank=725

### vs hybrid

**CANDIDATE.** gain +0.023 / +0.027, wins 4 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.023, condensed +0.027, Recall@20 -0.001.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.009, +0.054].
- Folds won: 4 of 5.
- Without q55: nDCG@10 gain +0.026 (unjudged=0) / +0.030 (condensed).
- Leave-top-2-out gain: +0.014 / +0.018; top gainers: q01 +0.290, q50 +0.274.
- unjudged@10: variant 0.018, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.563 | 0.619 | +0.057 | 0.563 | 0.619 | +0.057 | yes |
| 2 | 12 | 0.677 | 0.681 | +0.005 | 0.677 | 0.681 | +0.005 | yes |
| 3 | 11 | 0.519 | 0.552 | +0.033 | 0.519 | 0.552 | +0.033 | yes |
| 4 | 11 | 0.653 | 0.689 | +0.036 | 0.653 | 0.691 | +0.038 | yes |
| 5 | 11 | 0.607 | 0.591 | -0.016 | 0.607 | 0.610 | +0.003 |  |

Pooled base nDCG@10 0.604, variant 0.627.

### vs hybrid+stem+prefix

**DROPPED.** gain -0.002 (unjudged=0) / +0.002 (condensed) is not above 0.01.

- Pooled over 57 queries: nDCG@10 unjudged=0 -0.002, condensed +0.002, Recall@20 -0.019.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.040, +0.036].
- Folds won: 3 of 5.
- Without q55: nDCG@10 gain -0.011 (unjudged=0) / -0.007 (condensed).
- Leave-top-2-out gain: -0.017 / -0.013; top gainers: q55 +0.502, q50 +0.297.
- unjudged@10: variant 0.018, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.607 | 0.619 | +0.013 | 0.607 | 0.619 | +0.013 | yes |
| 2 | 12 | 0.650 | 0.681 | +0.031 | 0.650 | 0.681 | +0.031 | yes |
| 3 | 11 | 0.560 | 0.552 | -0.008 | 0.560 | 0.552 | -0.008 |  |
| 4 | 11 | 0.744 | 0.689 | -0.055 | 0.744 | 0.691 | -0.053 |  |
| 5 | 11 | 0.588 | 0.591 | +0.003 | 0.588 | 0.610 | +0.022 | yes |

Pooled base nDCG@10 0.630, variant 0.627.

Build and ranking wall time: 12.1 min (embeddings cached on disk afterwards).

## E3b: bge-base as the dense list, stem+prefix

**Decisions:** vs hybrid: CANDIDATE; vs hybrid+stem+prefix: CANDIDATE.

- What changed: bge-base with the query prefix, stemmed BM25
- Parameters: system=rrf[bm25+stem, base+prefix], wall_s_to_build_and_rank=6

### vs hybrid

**CANDIDATE.** gain +0.046 / +0.046, wins 4 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.046, condensed +0.046, Recall@20 +0.040.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [+0.005, +0.086].
- Folds won: 4 of 5.
- Without q55: nDCG@10 gain +0.057 (unjudged=0) / +0.057 (condensed).
- Leave-top-2-out gain: +0.032 / +0.032; top gainers: q01 +0.542, q35 +0.280.
- unjudged@10: variant 0.007, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.563 | 0.625 | +0.062 | 0.563 | 0.625 | +0.062 | yes |
| 2 | 12 | 0.677 | 0.676 | -0.001 | 0.677 | 0.676 | -0.001 |  |
| 3 | 11 | 0.519 | 0.606 | +0.087 | 0.519 | 0.606 | +0.087 | yes |
| 4 | 11 | 0.653 | 0.716 | +0.063 | 0.653 | 0.716 | +0.063 | yes |
| 5 | 11 | 0.607 | 0.626 | +0.020 | 0.607 | 0.626 | +0.020 | yes |

Pooled base nDCG@10 0.604, variant 0.650.

### vs hybrid+stem+prefix

**CANDIDATE.** gain +0.020 / +0.020, wins 4 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.020, condensed +0.020, Recall@20 +0.022.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.007, +0.047].
- Folds won: 4 of 5.
- Without q55: nDCG@10 gain +0.019 (unjudged=0) / +0.019 (condensed).
- Leave-top-2-out gain: +0.012 / +0.012; top gainers: q50 +0.239, q47 +0.225.
- unjudged@10: variant 0.007, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.607 | 0.625 | +0.018 | 0.607 | 0.625 | +0.018 | yes |
| 2 | 12 | 0.650 | 0.676 | +0.026 | 0.650 | 0.676 | +0.026 | yes |
| 3 | 11 | 0.560 | 0.606 | +0.046 | 0.560 | 0.606 | +0.046 | yes |
| 4 | 11 | 0.744 | 0.716 | -0.028 | 0.744 | 0.716 | -0.028 |  |
| 5 | 11 | 0.588 | 0.626 | +0.038 | 0.588 | 0.626 | +0.038 | yes |

Pooled base nDCG@10 0.630, variant 0.650.

Build and ranking wall time: 0.1 min (embeddings cached on disk afterwards).

## E3c: bge-large as the dense list, plain hybrid

**Decisions:** vs hybrid: CANDIDATE; vs hybrid+stem+prefix: DROPPED.

- What changed: dense list is bge-large, no prefix, plain BM25
- Parameters: system=rrf[bm25, large], wall_s_to_build_and_rank=2208

### vs hybrid

**CANDIDATE.** gain +0.037 / +0.039, wins 4 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.037, condensed +0.039, Recall@20 +0.035.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [+0.001, +0.074].
- Folds won: 4 of 5.
- Without q55: nDCG@10 gain +0.040 (unjudged=0) / +0.042 (condensed).
- Leave-top-2-out gain: +0.025 / +0.027; top gainers: q50 +0.386, q47 +0.363.
- unjudged@10: variant 0.018, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.563 | 0.618 | +0.055 | 0.563 | 0.623 | +0.060 | yes |
| 2 | 12 | 0.677 | 0.714 | +0.038 | 0.677 | 0.714 | +0.038 | yes |
| 3 | 11 | 0.519 | 0.585 | +0.066 | 0.519 | 0.585 | +0.066 | yes |
| 4 | 11 | 0.653 | 0.684 | +0.030 | 0.653 | 0.684 | +0.030 | yes |
| 5 | 11 | 0.607 | 0.600 | -0.007 | 0.607 | 0.607 | -0.000 |  |

Pooled base nDCG@10 0.604, variant 0.641.

### vs hybrid+stem+prefix

**DROPPED.** driven by 1 to 2 queries (q55 +0.497, q50 +0.409); without them the gain is -0.005 / -0.002.

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.011, condensed +0.014, Recall@20 +0.017.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.029, +0.054].
- Folds won: 4 of 5.
- Without q55: nDCG@10 gain +0.003 (unjudged=0) / +0.005 (condensed).
- Leave-top-2-out gain: -0.005 / -0.002; top gainers: q55 +0.497, q50 +0.409.
- unjudged@10: variant 0.018, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.607 | 0.618 | +0.011 | 0.607 | 0.623 | +0.016 | yes |
| 2 | 12 | 0.650 | 0.714 | +0.064 | 0.650 | 0.714 | +0.064 | yes |
| 3 | 11 | 0.560 | 0.585 | +0.025 | 0.560 | 0.585 | +0.025 | yes |
| 4 | 11 | 0.744 | 0.684 | -0.061 | 0.744 | 0.684 | -0.061 |  |
| 5 | 11 | 0.588 | 0.600 | +0.012 | 0.588 | 0.607 | +0.018 | yes |

Pooled base nDCG@10 0.630, variant 0.641.

Build and ranking wall time: 36.8 min (embeddings cached on disk afterwards).

## E3d: bge-large as the dense list, stem+prefix

**Decisions:** vs hybrid: CANDIDATE; vs hybrid+stem+prefix: CANDIDATE.

- What changed: bge-large with the query prefix, stemmed BM25
- Parameters: system=rrf[bm25+stem, large+prefix], wall_s_to_build_and_rank=14

### vs hybrid

**CANDIDATE.** gain +0.077 / +0.079, wins 5 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.077, condensed +0.079, Recall@20 +0.050.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [+0.030, +0.123].
- Folds won: 5 of 5.
- Without q55: nDCG@10 gain +0.089 (unjudged=0) / +0.091 (condensed).
- Leave-top-2-out gain: +0.064 / +0.067; top gainers: q01 +0.462, q50 +0.389.
- unjudged@10: variant 0.018, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.563 | 0.631 | +0.068 | 0.563 | 0.634 | +0.071 | yes |
| 2 | 12 | 0.677 | 0.707 | +0.030 | 0.677 | 0.711 | +0.034 | yes |
| 3 | 11 | 0.519 | 0.637 | +0.118 | 0.519 | 0.637 | +0.118 | yes |
| 4 | 11 | 0.653 | 0.779 | +0.126 | 0.653 | 0.779 | +0.126 | yes |
| 5 | 11 | 0.607 | 0.655 | +0.049 | 0.607 | 0.659 | +0.052 | yes |

Pooled base nDCG@10 0.604, variant 0.681.

### vs hybrid+stem+prefix

**CANDIDATE.** gain +0.051 / +0.054, wins 5 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.051, condensed +0.054, Recall@20 +0.033.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [+0.024, +0.079].
- Folds won: 5 of 5.
- Without q55: nDCG@10 gain +0.052 (unjudged=0) / +0.054 (condensed).
- Leave-top-2-out gain: +0.041 / +0.043; top gainers: q50 +0.411, q54 +0.241.
- unjudged@10: variant 0.018, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.607 | 0.631 | +0.024 | 0.607 | 0.634 | +0.027 | yes |
| 2 | 12 | 0.650 | 0.707 | +0.057 | 0.650 | 0.711 | +0.061 | yes |
| 3 | 11 | 0.560 | 0.637 | +0.077 | 0.560 | 0.637 | +0.077 | yes |
| 4 | 11 | 0.744 | 0.779 | +0.035 | 0.744 | 0.779 | +0.035 | yes |
| 5 | 11 | 0.588 | 0.655 | +0.067 | 0.588 | 0.659 | +0.071 | yes |

Pooled base nDCG@10 0.630, variant 0.681.

Build and ranking wall time: 0.2 min (embeddings cached on disk afterwards).

## E3e: ensemble bge-small + bge-base (+ stemmed BM25)

**Decisions:** vs hybrid: CANDIDATE; vs hybrid+stem+prefix: CANDIDATE.

- What changed: three-list RRF: stemmed BM25, small+prefix, base+prefix
- Parameters: system=rrf[bm25+stem, small+prefix, base+prefix], wall_s_to_build_and_rank=7

### vs hybrid

**CANDIDATE.** gain +0.049 / +0.049, wins 5 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.049, condensed +0.049, Recall@20 +0.018.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [+0.013, +0.083].
- Folds won: 5 of 5.
- Without q55: nDCG@10 gain +0.053 (unjudged=0) / +0.053 (condensed).
- Leave-top-2-out gain: +0.038 / +0.038; top gainers: q15 +0.364, q03 +0.316.
- unjudged@10: variant 0.000, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.563 | 0.620 | +0.057 | 0.563 | 0.620 | +0.057 | yes |
| 2 | 12 | 0.677 | 0.704 | +0.028 | 0.677 | 0.704 | +0.028 | yes |
| 3 | 11 | 0.519 | 0.537 | +0.018 | 0.519 | 0.537 | +0.018 | yes |
| 4 | 11 | 0.653 | 0.778 | +0.125 | 0.653 | 0.778 | +0.125 | yes |
| 5 | 11 | 0.607 | 0.623 | +0.016 | 0.607 | 0.623 | +0.016 | yes |

Pooled base nDCG@10 0.604, variant 0.653.

### vs hybrid+stem+prefix

**CANDIDATE.** gain +0.023 / +0.023, wins 4 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.023, condensed +0.023, Recall@20 +0.001.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.003, +0.048].
- Folds won: 4 of 5.
- Without q55: nDCG@10 gain +0.016 (unjudged=0) / +0.016 (condensed).
- Leave-top-2-out gain: +0.013 / +0.013; top gainers: q55 +0.412, q29 +0.182.
- unjudged@10: variant 0.000, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.607 | 0.620 | +0.013 | 0.607 | 0.620 | +0.013 | yes |
| 2 | 12 | 0.650 | 0.704 | +0.055 | 0.650 | 0.704 | +0.055 | yes |
| 3 | 11 | 0.560 | 0.537 | -0.023 | 0.560 | 0.537 | -0.023 |  |
| 4 | 11 | 0.744 | 0.778 | +0.034 | 0.744 | 0.778 | +0.034 | yes |
| 5 | 11 | 0.588 | 0.623 | +0.035 | 0.588 | 0.623 | +0.035 | yes |

Pooled base nDCG@10 0.630, variant 0.653.

Build and ranking wall time: 0.1 min (embeddings cached on disk afterwards).

## E3f: ensemble bge-small + bge-large (+ stemmed BM25)

**Decisions:** vs hybrid: CANDIDATE; vs hybrid+stem+prefix: CANDIDATE.

- What changed: three-list RRF: stemmed BM25, small+prefix, large+prefix
- Parameters: system=rrf[bm25+stem, small+prefix, large+prefix], wall_s_to_build_and_rank=17

### vs hybrid

**CANDIDATE.** gain +0.052 / +0.052, wins 5 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.052, condensed +0.052, Recall@20 +0.024.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [+0.015, +0.091].
- Folds won: 5 of 5.
- Without q55: nDCG@10 gain +0.057 (unjudged=0) / +0.057 (condensed).
- Leave-top-2-out gain: +0.039 / +0.039; top gainers: q15 +0.437, q12 +0.399.
- unjudged@10: variant 0.000, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.563 | 0.627 | +0.064 | 0.563 | 0.627 | +0.064 | yes |
| 2 | 12 | 0.677 | 0.733 | +0.056 | 0.677 | 0.733 | +0.056 | yes |
| 3 | 11 | 0.519 | 0.542 | +0.023 | 0.519 | 0.542 | +0.023 | yes |
| 4 | 11 | 0.653 | 0.755 | +0.102 | 0.653 | 0.755 | +0.102 | yes |
| 5 | 11 | 0.607 | 0.622 | +0.016 | 0.607 | 0.622 | +0.016 | yes |

Pooled base nDCG@10 0.604, variant 0.657.

### vs hybrid+stem+prefix

**CANDIDATE.** gain +0.027 / +0.027, wins 4 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.027, condensed +0.027, Recall@20 +0.007.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [+0.004, +0.053].
- Folds won: 4 of 5.
- Without q55: nDCG@10 gain +0.020 (unjudged=0) / +0.020 (condensed).
- Leave-top-2-out gain: +0.015 / +0.015; top gainers: q55 +0.419, q12 +0.293.
- unjudged@10: variant 0.000, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.607 | 0.627 | +0.020 | 0.607 | 0.627 | +0.020 | yes |
| 2 | 12 | 0.650 | 0.733 | +0.083 | 0.650 | 0.733 | +0.083 | yes |
| 3 | 11 | 0.560 | 0.542 | -0.018 | 0.560 | 0.542 | -0.018 |  |
| 4 | 11 | 0.744 | 0.755 | +0.011 | 0.744 | 0.755 | +0.011 | yes |
| 5 | 11 | 0.588 | 0.622 | +0.034 | 0.588 | 0.622 | +0.034 | yes |

Pooled base nDCG@10 0.630, variant 0.657.

Build and ranking wall time: 0.3 min (embeddings cached on disk afterwards).

## E4a: MedCPT bi-encoder as the dense list, plain BM25

**Decisions:** vs hybrid: PENDING_GRADING; vs hybrid+stem+prefix: PENDING_GRADING.

- What changed: dense list is MedCPT (query and article encoders)
- Parameters: system=rrf[bm25, medcpt], wall_s_to_build_and_rank=534

### vs hybrid

**PENDING_GRADING.** unjudged@10 is 0.070, above 0.05; grade the pairs in results/step18_unjudged.csv, then re-judge.

- Pooled over 57 queries: nDCG@10 unjudged=0 -0.024, condensed -0.012, Recall@20 -0.056.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.076, +0.028].
- Folds won: 1 of 5.
- Without q55: nDCG@10 gain -0.023 (unjudged=0) / -0.011 (condensed).
- Leave-top-2-out gain: -0.039 / -0.028; top gainers: q50 +0.437, q16 +0.348.
- unjudged@10: variant 0.070, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.563 | 0.527 | -0.036 | 0.563 | 0.543 | -0.020 |  |
| 2 | 12 | 0.677 | 0.595 | -0.081 | 0.677 | 0.609 | -0.067 |  |
| 3 | 11 | 0.519 | 0.657 | +0.138 | 0.519 | 0.665 | +0.146 | yes |
| 4 | 11 | 0.653 | 0.632 | -0.022 | 0.653 | 0.644 | -0.009 |  |
| 5 | 11 | 0.607 | 0.493 | -0.114 | 0.607 | 0.504 | -0.103 |  |

Pooled base nDCG@10 0.604, variant 0.580.

### vs hybrid+stem+prefix

**PENDING_GRADING.** unjudged@10 is 0.070, above 0.05; grade the pairs in results/step18_unjudged.csv, then re-judge.

- Pooled over 57 queries: nDCG@10 unjudged=0 -0.050, condensed -0.037, Recall@20 -0.074.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.113, +0.013].
- Folds won: 1 of 5.
- Without q55: nDCG@10 gain -0.061 (unjudged=0) / -0.048 (condensed).
- Leave-top-2-out gain: -0.070 / -0.059; top gainers: q55 +0.560, q50 +0.460.
- unjudged@10: variant 0.070, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.607 | 0.527 | -0.080 | 0.607 | 0.543 | -0.064 |  |
| 2 | 12 | 0.650 | 0.595 | -0.055 | 0.650 | 0.609 | -0.040 |  |
| 3 | 11 | 0.560 | 0.657 | +0.097 | 0.560 | 0.665 | +0.104 | yes |
| 4 | 11 | 0.744 | 0.632 | -0.113 | 0.744 | 0.644 | -0.100 |  |
| 5 | 11 | 0.588 | 0.493 | -0.095 | 0.588 | 0.504 | -0.084 |  |

Pooled base nDCG@10 0.630, variant 0.580.

Build and ranking wall time: 8.9 min (embeddings cached on disk afterwards).

## E4b: MedCPT bi-encoder as the dense list, stemmed BM25

**Decisions:** vs hybrid: PENDING_GRADING; vs hybrid+stem+prefix: PENDING_GRADING.

- What changed: as E4a with stemmed BM25
- Parameters: system=rrf[bm25+stem, medcpt], wall_s_to_build_and_rank=3

### vs hybrid

**PENDING_GRADING.** unjudged@10 is 0.091, above 0.05; grade the pairs in results/step18_unjudged.csv, then re-judge.

- Pooled over 57 queries: nDCG@10 unjudged=0 -0.030, condensed -0.014, Recall@20 -0.042.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.091, +0.031].
- Folds won: 1 of 5.
- Without q55: nDCG@10 gain -0.021 (unjudged=0) / -0.006 (condensed).
- Leave-top-2-out gain: -0.047 / -0.031; top gainers: q50 +0.487, q38 +0.367.
- unjudged@10: variant 0.091, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.563 | 0.541 | -0.021 | 0.563 | 0.563 | +0.001 |  |
| 2 | 12 | 0.677 | 0.572 | -0.105 | 0.677 | 0.583 | -0.094 |  |
| 3 | 11 | 0.519 | 0.665 | +0.146 | 0.519 | 0.667 | +0.148 | yes |
| 4 | 11 | 0.653 | 0.650 | -0.004 | 0.653 | 0.666 | +0.013 |  |
| 5 | 11 | 0.607 | 0.446 | -0.161 | 0.607 | 0.472 | -0.135 |  |

Pooled base nDCG@10 0.604, variant 0.574.

### vs hybrid+stem+prefix

**PENDING_GRADING.** unjudged@10 is 0.091, above 0.05; grade the pairs in results/step18_unjudged.csv, then re-judge.

- Pooled over 57 queries: nDCG@10 unjudged=0 -0.056, condensed -0.040, Recall@20 -0.059.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.115, +0.003].
- Folds won: 1 of 5.
- Without q55: nDCG@10 gain -0.059 (unjudged=0) / -0.043 (condensed).
- Leave-top-2-out gain: -0.073 / -0.057; top gainers: q50 +0.509, q09 +0.321.
- unjudged@10: variant 0.091, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.607 | 0.541 | -0.065 | 0.607 | 0.563 | -0.043 |  |
| 2 | 12 | 0.650 | 0.572 | -0.078 | 0.650 | 0.583 | -0.067 |  |
| 3 | 11 | 0.560 | 0.665 | +0.105 | 0.560 | 0.667 | +0.107 | yes |
| 4 | 11 | 0.744 | 0.650 | -0.095 | 0.744 | 0.666 | -0.078 |  |
| 5 | 11 | 0.588 | 0.446 | -0.142 | 0.588 | 0.472 | -0.116 |  |

Pooled base nDCG@10 0.630, variant 0.574.

Build and ranking wall time: 0.1 min (embeddings cached on disk afterwards).

## E4c: ensemble bge-small + MedCPT (+ stemmed BM25)

**Decisions:** vs hybrid: CANDIDATE; vs hybrid+stem+prefix: DROPPED.

- What changed: three-list RRF: stemmed BM25, small+prefix, MedCPT
- Parameters: system=rrf[bm25+stem, small+prefix, medcpt], wall_s_to_build_and_rank=5

### vs hybrid

**CANDIDATE.** gain +0.027 / +0.029, wins 3 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.027, condensed +0.029, Recall@20 -0.007.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.019, +0.073].
- Folds won: 3 of 5.
- Without q55: nDCG@10 gain +0.028 (unjudged=0) / +0.031 (condensed).
- Leave-top-2-out gain: +0.013 / +0.015; top gainers: q13 +0.414, q50 +0.411.
- unjudged@10: variant 0.012, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.563 | 0.636 | +0.074 | 0.563 | 0.639 | +0.076 | yes |
| 2 | 12 | 0.677 | 0.668 | -0.008 | 0.677 | 0.668 | -0.008 |  |
| 3 | 11 | 0.519 | 0.603 | +0.084 | 0.519 | 0.607 | +0.088 | yes |
| 4 | 11 | 0.653 | 0.731 | +0.078 | 0.653 | 0.738 | +0.085 | yes |
| 5 | 11 | 0.607 | 0.513 | -0.094 | 0.607 | 0.513 | -0.094 |  |

Pooled base nDCG@10 0.604, variant 0.631.

### vs hybrid+stem+prefix

**DROPPED.** gain +0.001 (unjudged=0) / +0.004 (condensed) is not above 0.01.

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.001, condensed +0.004, Recall@20 -0.025.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.046, +0.050].
- Folds won: 3 of 5.
- Without q55: nDCG@10 gain -0.009 (unjudged=0) / -0.007 (condensed).
- Leave-top-2-out gain: -0.017 / -0.015; top gainers: q55 +0.590, q50 +0.433.
- unjudged@10: variant 0.012, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.607 | 0.636 | +0.030 | 0.607 | 0.639 | +0.032 | yes |
| 2 | 12 | 0.650 | 0.668 | +0.018 | 0.650 | 0.668 | +0.018 | yes |
| 3 | 11 | 0.560 | 0.603 | +0.043 | 0.560 | 0.607 | +0.047 | yes |
| 4 | 11 | 0.744 | 0.731 | -0.014 | 0.744 | 0.738 | -0.006 |  |
| 5 | 11 | 0.588 | 0.513 | -0.075 | 0.588 | 0.513 | -0.075 |  |

Pooled base nDCG@10 0.630, variant 0.631.

Build and ranking wall time: 0.1 min (embeddings cached on disk afterwards).

## E4d: medcpt-cross on hybrid+stem+prefix, top 30, replace

**Decisions:** vs hybrid: DROPPED; vs hybrid+stem+prefix: DROPPED.

- What changed: ncbi/MedCPT-Cross-Encoder reorders the top 30 of hybrid+stem+prefix; mode replace (sorted by cross-encoder score alone). Hits beyond depth 30 keep their first-stage order.
- Parameters: model=ncbi/MedCPT-Cross-Encoder, first_stage=hybrid+stem+prefix, depth=30, mode=replace, alpha=-, max_length=512

### vs hybrid

**DROPPED.** driven by 1 to 2 queries (q01 +0.560, q15 +0.441); without them the gain is -0.006 / -0.005.

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.012, condensed +0.013, Recall@20 +0.042.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.033, +0.060].
- Folds won: 3 of 5.
- Without q55: nDCG@10 gain +0.020 (unjudged=0) / +0.020 (condensed).
- Leave-top-2-out gain: -0.006 / -0.005; top gainers: q01 +0.560, q15 +0.441.
- unjudged@10: variant 0.009, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.563 | 0.602 | +0.039 | 0.563 | 0.602 | +0.039 | yes |
| 2 | 12 | 0.677 | 0.657 | -0.020 | 0.677 | 0.657 | -0.020 |  |
| 3 | 11 | 0.519 | 0.606 | +0.087 | 0.519 | 0.607 | +0.088 | yes |
| 4 | 11 | 0.653 | 0.679 | +0.026 | 0.653 | 0.679 | +0.026 | yes |
| 5 | 11 | 0.607 | 0.536 | -0.071 | 0.607 | 0.536 | -0.071 |  |

Pooled base nDCG@10 0.604, variant 0.616.

### vs hybrid+stem+prefix

**DROPPED.** gain -0.013 (unjudged=0) / -0.013 (condensed) is not above 0.01.

- Pooled over 57 queries: nDCG@10 unjudged=0 -0.013, condensed -0.013, Recall@20 +0.025.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.053, +0.024].
- Folds won: 2 of 5.
- Without q55: nDCG@10 gain -0.017 (unjudged=0) / -0.017 (condensed).
- Leave-top-2-out gain: -0.022 / -0.022; top gainers: q01 +0.239, q16 +0.220.
- unjudged@10: variant 0.009, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.607 | 0.602 | -0.005 | 0.607 | 0.602 | -0.005 |  |
| 2 | 12 | 0.650 | 0.657 | +0.007 | 0.650 | 0.657 | +0.007 | yes |
| 3 | 11 | 0.560 | 0.606 | +0.046 | 0.560 | 0.607 | +0.047 | yes |
| 4 | 11 | 0.744 | 0.679 | -0.065 | 0.744 | 0.679 | -0.065 |  |
| 5 | 11 | 0.588 | 0.536 | -0.052 | 0.588 | 0.536 | -0.052 |  |

Pooled base nDCG@10 0.630, variant 0.616.

Wall time of the scoring pass (shared by E1a to E1h): 25.7 min for 2850 new pairs, 1.85 pairs/s, batch 8, 6 torch threads, on a machine shared with other jobs.

## E4e: medcpt-cross on hybrid+stem+prefix, top 30, blend

**Decisions:** vs hybrid: CANDIDATE; vs hybrid+stem+prefix: DROPPED.

- What changed: ncbi/MedCPT-Cross-Encoder reorders the top 30 of hybrid+stem+prefix; mode blend (alpha 0.5: 0.5 x min-max cross-encoder score + 0.5 x min-max first-stage score). Hits beyond depth 30 keep their first-stage order.
- Parameters: model=ncbi/MedCPT-Cross-Encoder, first_stage=hybrid+stem+prefix, depth=30, mode=blend, alpha=0.5, max_length=512

### vs hybrid

**CANDIDATE.** gain +0.034 / +0.034, wins 3 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.034, condensed +0.034, Recall@20 +0.039.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.006, +0.074].
- Folds won: 3 of 5.
- Without q55: nDCG@10 gain +0.045 (unjudged=0) / +0.045 (condensed).
- Leave-top-2-out gain: +0.020 / +0.020; top gainers: q01 +0.437, q15 +0.421.
- unjudged@10: variant 0.000, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.563 | 0.615 | +0.052 | 0.563 | 0.615 | +0.052 | yes |
| 2 | 12 | 0.677 | 0.641 | -0.036 | 0.677 | 0.641 | -0.036 |  |
| 3 | 11 | 0.519 | 0.579 | +0.060 | 0.519 | 0.579 | +0.060 | yes |
| 4 | 11 | 0.653 | 0.766 | +0.113 | 0.653 | 0.766 | +0.113 | yes |
| 5 | 11 | 0.607 | 0.593 | -0.014 | 0.607 | 0.593 | -0.014 |  |

Pooled base nDCG@10 0.604, variant 0.638.

### vs hybrid+stem+prefix

**DROPPED.** gain +0.009 (unjudged=0) / +0.009 (condensed) is not above 0.01.

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.009, condensed +0.009, Recall@20 +0.022.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.004, +0.021].
- Folds won: 4 of 5.
- Without q55: nDCG@10 gain +0.008 (unjudged=0) / +0.008 (condensed).
- Leave-top-2-out gain: +0.005 / +0.005; top gainers: q08 +0.119, q01 +0.115.
- unjudged@10: variant 0.000, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.607 | 0.615 | +0.008 | 0.607 | 0.615 | +0.008 | yes |
| 2 | 12 | 0.650 | 0.641 | -0.009 | 0.650 | 0.641 | -0.009 |  |
| 3 | 11 | 0.560 | 0.579 | +0.019 | 0.560 | 0.579 | +0.019 | yes |
| 4 | 11 | 0.744 | 0.766 | +0.022 | 0.744 | 0.766 | +0.022 | yes |
| 5 | 11 | 0.588 | 0.593 | +0.005 | 0.588 | 0.593 | +0.005 | yes |

Pooled base nDCG@10 0.630, variant 0.638.

Wall time of the scoring pass (shared by E1a to E1h): 25.7 min for 2850 new pairs, 1.85 pairs/s, batch 8, 6 torch threads, on a machine shared with other jobs.

## E5a: best together: bge-large + heading on both sides, stem+prefix

**Decisions:** vs hybrid: PENDING_GRADING; vs hybrid+stem+prefix: PENDING_GRADING; vs E3d: rrf[bm25+stem, large+prefix]: PENDING_GRADING.

- What changed: E3d and E2f combined: stemmed BM25 and bge-large+prefix both index heading plus text
- Parameters: system=rrf[bm25+stem+head, large+prefix+head], wall_s_to_build_and_rank=2167

### vs hybrid

**PENDING_GRADING.** unjudged@10 is 0.058, above 0.05; grade the pairs in results/step18_unjudged.csv, then re-judge.

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.098, condensed +0.109, Recall@20 +0.054.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [+0.049, +0.145].
- Folds won: 5 of 5.
- Without q55: nDCG@10 gain +0.108 (unjudged=0) / +0.120 (condensed).
- Leave-top-2-out gain: +0.085 / +0.095; top gainers: q01 +0.446, q50 +0.438.
- unjudged@10: variant 0.058, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.563 | 0.605 | +0.042 | 0.563 | 0.616 | +0.053 | yes |
| 2 | 12 | 0.677 | 0.753 | +0.076 | 0.677 | 0.753 | +0.076 | yes |
| 3 | 11 | 0.519 | 0.666 | +0.147 | 0.519 | 0.681 | +0.162 | yes |
| 4 | 11 | 0.653 | 0.803 | +0.150 | 0.653 | 0.811 | +0.158 | yes |
| 5 | 11 | 0.607 | 0.686 | +0.079 | 0.607 | 0.709 | +0.102 | yes |

Pooled base nDCG@10 0.604, variant 0.702.

### vs hybrid+stem+prefix

**PENDING_GRADING.** unjudged@10 is 0.058, above 0.05; grade the pairs in results/step18_unjudged.csv, then re-judge.

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.072, condensed +0.083, Recall@20 +0.036.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [+0.033, +0.113].
- Folds won: 4 of 5.
- Without q55: nDCG@10 gain +0.071 (unjudged=0) / +0.083 (condensed).
- Leave-top-2-out gain: +0.057 / +0.067; top gainers: q21 +0.525, q50 +0.461.
- unjudged@10: variant 0.058, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.607 | 0.605 | -0.002 | 0.607 | 0.616 | +0.009 |  |
| 2 | 12 | 0.650 | 0.753 | +0.103 | 0.650 | 0.753 | +0.103 | yes |
| 3 | 11 | 0.560 | 0.666 | +0.106 | 0.560 | 0.681 | +0.121 | yes |
| 4 | 11 | 0.744 | 0.803 | +0.059 | 0.744 | 0.811 | +0.066 | yes |
| 5 | 11 | 0.588 | 0.686 | +0.098 | 0.588 | 0.709 | +0.121 | yes |

Pooled base nDCG@10 0.630, variant 0.702.

### vs E3d: rrf[bm25+stem, large+prefix]

**PENDING_GRADING.** unjudged@10 is 0.058, above 0.05; grade the pairs in results/step18_unjudged.csv, then re-judge.

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.021, condensed +0.029, Recall@20 +0.004.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.004, +0.047].
- Folds won: 4 of 5.
- Without q55: nDCG@10 gain +0.019 (unjudged=0) / +0.028 (condensed).
- Leave-top-2-out gain: +0.009 / +0.018; top gainers: q21 +0.412, q09 +0.285.
- unjudged@10: variant 0.058, base 0.018.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.631 | 0.605 | -0.025 | 0.634 | 0.616 | -0.018 |  |
| 2 | 12 | 0.707 | 0.753 | +0.046 | 0.711 | 0.753 | +0.042 | yes |
| 3 | 11 | 0.637 | 0.666 | +0.029 | 0.637 | 0.681 | +0.044 | yes |
| 4 | 11 | 0.779 | 0.803 | +0.024 | 0.779 | 0.811 | +0.032 | yes |
| 5 | 11 | 0.655 | 0.686 | +0.031 | 0.659 | 0.709 | +0.050 | yes |

Pooled base nDCG@10 0.681, variant 0.702.

Build and ranking wall time: 36.1 min (embeddings cached on disk afterwards).

## E5b: best together: bge-large + heading on the dense side only, stem+prefix

**Decisions:** vs hybrid: CANDIDATE; vs hybrid+stem+prefix: CANDIDATE; vs E3d: rrf[bm25+stem, large+prefix]: CANDIDATE.

- What changed: E3d and E2e combined: bge-large+prefix embeds heading plus text, BM25 stays stemmed and plain
- Parameters: system=rrf[bm25+stem, large+prefix+head], wall_s_to_build_and_rank=10

### vs hybrid

**CANDIDATE.** gain +0.099 / +0.103, wins 5 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.099, condensed +0.103, Recall@20 +0.063.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [+0.057, +0.141].
- Folds won: 5 of 5.
- Without q55: nDCG@10 gain +0.108 (unjudged=0) / +0.111 (condensed).
- Leave-top-2-out gain: +0.088 / +0.091; top gainers: q01 +0.445, q35 +0.400.
- unjudged@10: variant 0.021, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.563 | 0.609 | +0.046 | 0.563 | 0.615 | +0.053 | yes |
| 2 | 12 | 0.677 | 0.770 | +0.093 | 0.677 | 0.770 | +0.093 | yes |
| 3 | 11 | 0.519 | 0.656 | +0.137 | 0.519 | 0.662 | +0.142 | yes |
| 4 | 11 | 0.653 | 0.782 | +0.128 | 0.653 | 0.782 | +0.128 | yes |
| 5 | 11 | 0.607 | 0.704 | +0.097 | 0.607 | 0.708 | +0.101 | yes |

Pooled base nDCG@10 0.604, variant 0.704.

### vs hybrid+stem+prefix

**CANDIDATE.** gain +0.074 / +0.077, wins 5 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.074, condensed +0.077, Recall@20 +0.045.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [+0.037, +0.112].
- Folds won: 5 of 5.
- Without q55: nDCG@10 gain +0.070 (unjudged=0) / +0.074 (condensed).
- Leave-top-2-out gain: +0.060 / +0.062; top gainers: q21 +0.515, q50 +0.372.
- unjudged@10: variant 0.021, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.607 | 0.609 | +0.002 | 0.607 | 0.615 | +0.009 | yes |
| 2 | 12 | 0.650 | 0.770 | +0.120 | 0.650 | 0.770 | +0.120 | yes |
| 3 | 11 | 0.560 | 0.656 | +0.096 | 0.560 | 0.662 | +0.101 | yes |
| 4 | 11 | 0.744 | 0.782 | +0.037 | 0.744 | 0.782 | +0.037 | yes |
| 5 | 11 | 0.588 | 0.704 | +0.116 | 0.588 | 0.708 | +0.120 | yes |

Pooled base nDCG@10 0.630, variant 0.704.

### vs E3d: rrf[bm25+stem, large+prefix]

**CANDIDATE.** gain +0.022 / +0.023, wins 4 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.022, condensed +0.023, Recall@20 +0.013.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.001, +0.048].
- Folds won: 4 of 5.
- Without q55: nDCG@10 gain +0.019 (unjudged=0) / +0.020 (condensed).
- Leave-top-2-out gain: +0.012 / +0.013; top gainers: q21 +0.402, q55 +0.235.
- unjudged@10: variant 0.021, base 0.018.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.631 | 0.609 | -0.021 | 0.634 | 0.615 | -0.018 |  |
| 2 | 12 | 0.707 | 0.770 | +0.063 | 0.711 | 0.770 | +0.059 | yes |
| 3 | 11 | 0.637 | 0.656 | +0.019 | 0.637 | 0.662 | +0.024 | yes |
| 4 | 11 | 0.779 | 0.782 | +0.003 | 0.779 | 0.782 | +0.003 | yes |
| 5 | 11 | 0.655 | 0.704 | +0.049 | 0.659 | 0.708 | +0.049 | yes |

Pooled base nDCG@10 0.681, variant 0.704.

Build and ranking wall time: 0.2 min (embeddings cached on disk afterwards).

## E6a: bge-ft on rrf[bm25+stem, large+prefix+head], top 30, replace

**Decisions:** vs hybrid: PENDING_GRADING; vs hybrid+stem+prefix: PENDING_GRADING; vs E5b: rrf[bm25+stem, large+prefix+head] (no rerank): PENDING_GRADING.

- What changed: data/processed/ft_reranker_bge reorders the top 30 of rrf[bm25+stem, large+prefix+head]; mode replace (sorted by cross-encoder score alone). Hits beyond depth 30 keep their first-stage order.
- Parameters: model=data/processed/ft_reranker_bge, first_stage=rrf[bm25+stem, large+prefix+head], depth=30, mode=replace, alpha=-, max_length=512

### vs hybrid

**PENDING_GRADING.** unjudged@10 is 0.065, above 0.05; grade the pairs in results/step18_unjudged.csv, then re-judge.

- Pooled over 57 queries: nDCG@10 unjudged=0 -0.004, condensed +0.006, Recall@20 +0.014.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.068, +0.056].
- Folds won: 4 of 5.
- Without q55: nDCG@10 gain -0.007 (unjudged=0) / +0.004 (condensed).
- Leave-top-2-out gain: -0.022 / -0.012; top gainers: q01 +0.506, q39 +0.464.
- unjudged@10: variant 0.065, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.563 | 0.616 | +0.053 | 0.563 | 0.634 | +0.071 | yes |
| 2 | 12 | 0.677 | 0.706 | +0.030 | 0.677 | 0.707 | +0.030 | yes |
| 3 | 11 | 0.519 | 0.522 | +0.003 | 0.519 | 0.529 | +0.010 | yes |
| 4 | 11 | 0.653 | 0.660 | +0.007 | 0.653 | 0.679 | +0.026 | yes |
| 5 | 11 | 0.607 | 0.483 | -0.124 | 0.607 | 0.492 | -0.115 |  |

Pooled base nDCG@10 0.604, variant 0.600.

### vs hybrid+stem+prefix

**PENDING_GRADING.** unjudged@10 is 0.065, above 0.05; grade the pairs in results/step18_unjudged.csv, then re-judge.

- Pooled over 57 queries: nDCG@10 unjudged=0 -0.030, condensed -0.020, Recall@20 -0.003.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.092, +0.030].
- Folds won: 2 of 5.
- Without q55: nDCG@10 gain -0.044 (unjudged=0) / -0.033 (condensed).
- Leave-top-2-out gain: -0.051 / -0.040; top gainers: q55 +0.753, q39 +0.341.
- unjudged@10: variant 0.065, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.607 | 0.616 | +0.009 | 0.607 | 0.634 | +0.027 | yes |
| 2 | 12 | 0.650 | 0.706 | +0.056 | 0.650 | 0.707 | +0.057 | yes |
| 3 | 11 | 0.560 | 0.522 | -0.038 | 0.560 | 0.529 | -0.031 |  |
| 4 | 11 | 0.744 | 0.660 | -0.084 | 0.744 | 0.679 | -0.065 |  |
| 5 | 11 | 0.588 | 0.483 | -0.105 | 0.588 | 0.492 | -0.097 |  |

Pooled base nDCG@10 0.630, variant 0.600.

### vs E5b: rrf[bm25+stem, large+prefix+head] (no rerank)

**PENDING_GRADING.** unjudged@10 is 0.065, above 0.05; grade the pairs in results/step18_unjudged.csv, then re-judge.

- Pooled over 57 queries: nDCG@10 unjudged=0 -0.104, condensed -0.097, Recall@20 -0.049.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.176, -0.037].
- Folds won: 1 of 5.
- Without q55: nDCG@10 gain -0.114 (unjudged=0) / -0.107 (condensed).
- Leave-top-2-out gain: -0.122 / -0.114; top gainers: q55 +0.484, q39 +0.296.
- unjudged@10: variant 0.065, base 0.021.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.609 | 0.616 | +0.007 | 0.615 | 0.634 | +0.018 | yes |
| 2 | 12 | 0.770 | 0.706 | -0.064 | 0.770 | 0.707 | -0.063 |  |
| 3 | 11 | 0.656 | 0.522 | -0.134 | 0.662 | 0.529 | -0.133 |  |
| 4 | 11 | 0.782 | 0.660 | -0.121 | 0.782 | 0.679 | -0.102 |  |
| 5 | 11 | 0.704 | 0.483 | -0.221 | 0.708 | 0.492 | -0.216 |  |

Pooled base nDCG@10 0.704, variant 0.600.

Wall time of the scoring pass (shared by E1a to E1h): 40.7 min for 1710 new pairs, 0.73 pairs/s, batch 8, 6 torch threads, on a machine shared with other jobs.

## E6b: bge-ft on rrf[bm25+stem, large+prefix+head], top 30, blend

**Decisions:** vs hybrid: CANDIDATE; vs hybrid+stem+prefix: CANDIDATE; vs E5b: rrf[bm25+stem, large+prefix+head] (no rerank): DROPPED.

- What changed: data/processed/ft_reranker_bge reorders the top 30 of rrf[bm25+stem, large+prefix+head]; mode blend (alpha 0.5: 0.5 x min-max cross-encoder score + 0.5 x min-max first-stage score). Hits beyond depth 30 keep their first-stage order.
- Parameters: model=data/processed/ft_reranker_bge, first_stage=rrf[bm25+stem, large+prefix+head], depth=30, mode=blend, alpha=0.5, max_length=512

### vs hybrid

**CANDIDATE.** gain +0.088 / +0.095, wins 5 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.088, condensed +0.095, Recall@20 +0.084.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [+0.046, +0.131].
- Folds won: 5 of 5.
- Without q55: nDCG@10 gain +0.089 (unjudged=0) / +0.096 (condensed).
- Leave-top-2-out gain: +0.077 / +0.084; top gainers: q15 +0.391, q40 +0.389.
- unjudged@10: variant 0.018, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.563 | 0.645 | +0.083 | 0.563 | 0.652 | +0.089 | yes |
| 2 | 12 | 0.677 | 0.765 | +0.088 | 0.677 | 0.765 | +0.088 | yes |
| 3 | 11 | 0.519 | 0.603 | +0.084 | 0.519 | 0.614 | +0.095 | yes |
| 4 | 11 | 0.653 | 0.790 | +0.137 | 0.653 | 0.804 | +0.150 | yes |
| 5 | 11 | 0.607 | 0.657 | +0.050 | 0.607 | 0.660 | +0.054 | yes |

Pooled base nDCG@10 0.604, variant 0.692.

### vs hybrid+stem+prefix

**CANDIDATE.** gain +0.063 / +0.069, wins 5 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.063, condensed +0.069, Recall@20 +0.067.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [+0.024, +0.105].
- Folds won: 5 of 5.
- Without q55: nDCG@10 gain +0.052 (unjudged=0) / +0.059 (condensed).
- Leave-top-2-out gain: +0.044 / +0.051; top gainers: q55 +0.651, q21 +0.491.
- unjudged@10: variant 0.018, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.607 | 0.645 | +0.039 | 0.607 | 0.652 | +0.045 | yes |
| 2 | 12 | 0.650 | 0.765 | +0.115 | 0.650 | 0.765 | +0.115 | yes |
| 3 | 11 | 0.560 | 0.603 | +0.043 | 0.560 | 0.614 | +0.054 | yes |
| 4 | 11 | 0.744 | 0.790 | +0.046 | 0.744 | 0.804 | +0.059 | yes |
| 5 | 11 | 0.588 | 0.657 | +0.069 | 0.588 | 0.660 | +0.072 | yes |

Pooled base nDCG@10 0.630, variant 0.692.

### vs E5b: rrf[bm25+stem, large+prefix+head] (no rerank)

**DROPPED.** gain -0.011 (unjudged=0) / -0.007 (condensed) is not above 0.01.

- Pooled over 57 queries: nDCG@10 unjudged=0 -0.011, condensed -0.007, Recall@20 +0.021.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.047, +0.023].
- Folds won: 2 of 5.
- Without q55: nDCG@10 gain -0.018 (unjudged=0) / -0.014 (condensed).
- Leave-top-2-out gain: -0.024 / -0.020; top gainers: q55 +0.382, q29 +0.312.
- unjudged@10: variant 0.018, base 0.021.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.609 | 0.645 | +0.036 | 0.615 | 0.652 | +0.036 | yes |
| 2 | 12 | 0.770 | 0.765 | -0.005 | 0.770 | 0.765 | -0.005 |  |
| 3 | 11 | 0.656 | 0.603 | -0.053 | 0.662 | 0.614 | -0.047 |  |
| 4 | 11 | 0.782 | 0.790 | +0.009 | 0.782 | 0.804 | +0.022 | yes |
| 5 | 11 | 0.704 | 0.657 | -0.047 | 0.708 | 0.660 | -0.048 |  |

Pooled base nDCG@10 0.704, variant 0.692.

Wall time of the scoring pass (shared by E1a to E1h): 40.7 min for 1710 new pairs, 0.73 pairs/s, batch 8, 6 torch threads, on a machine shared with other jobs.

## E6c: bge-reranker-base on rrf[bm25+stem, large+prefix+head], top 30, replace

**Decisions:** vs hybrid: PENDING_GRADING; vs hybrid+stem+prefix: PENDING_GRADING; vs E5b: rrf[bm25+stem, large+prefix+head] (no rerank): PENDING_GRADING.

- What changed: BAAI/bge-reranker-base reorders the top 30 of rrf[bm25+stem, large+prefix+head]; mode replace (sorted by cross-encoder score alone). Hits beyond depth 30 keep their first-stage order.
- Parameters: model=BAAI/bge-reranker-base, first_stage=rrf[bm25+stem, large+prefix+head], depth=30, mode=replace, alpha=-, max_length=512

### vs hybrid

**PENDING_GRADING.** unjudged@10 is 0.104, above 0.05; grade the pairs in results/step18_unjudged.csv, then re-judge.

- Pooled over 57 queries: nDCG@10 unjudged=0 -0.037, condensed +0.002, Recall@20 +0.010.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.091, +0.017].
- Folds won: 2 of 5.
- Without q55: nDCG@10 gain -0.040 (unjudged=0) / -0.001 (condensed).
- Leave-top-2-out gain: -0.053 / -0.019; top gainers: q01 +0.458, q39 +0.369.
- unjudged@10: variant 0.104, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.563 | 0.608 | +0.045 | 0.563 | 0.666 | +0.104 | yes |
| 2 | 12 | 0.677 | 0.602 | -0.074 | 0.677 | 0.642 | -0.034 |  |
| 3 | 11 | 0.519 | 0.553 | +0.034 | 0.519 | 0.588 | +0.069 | yes |
| 4 | 11 | 0.653 | 0.586 | -0.067 | 0.653 | 0.631 | -0.022 |  |
| 5 | 11 | 0.607 | 0.480 | -0.127 | 0.607 | 0.493 | -0.114 |  |

Pooled base nDCG@10 0.604, variant 0.567.

### vs hybrid+stem+prefix

**PENDING_GRADING.** unjudged@10 is 0.104, above 0.05; grade the pairs in results/step18_unjudged.csv, then re-judge.

- Pooled over 57 queries: nDCG@10 unjudged=0 -0.063, condensed -0.024, Recall@20 -0.007.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.122, -0.002].
- Folds won: 1 of 5.
- Without q55: nDCG@10 gain -0.078 (unjudged=0) / -0.038 (condensed).
- Leave-top-2-out gain: -0.084 / -0.049; top gainers: q55 +0.777, q06 +0.267.
- unjudged@10: variant 0.104, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.607 | 0.608 | +0.001 | 0.607 | 0.666 | +0.060 | yes |
| 2 | 12 | 0.650 | 0.602 | -0.048 | 0.650 | 0.642 | -0.008 |  |
| 3 | 11 | 0.560 | 0.553 | -0.007 | 0.560 | 0.588 | +0.028 |  |
| 4 | 11 | 0.744 | 0.586 | -0.158 | 0.744 | 0.631 | -0.113 |  |
| 5 | 11 | 0.588 | 0.480 | -0.108 | 0.588 | 0.493 | -0.096 |  |

Pooled base nDCG@10 0.630, variant 0.567.

### vs E5b: rrf[bm25+stem, large+prefix+head] (no rerank)

**PENDING_GRADING.** unjudged@10 is 0.104, above 0.05; grade the pairs in results/step18_unjudged.csv, then re-judge.

- Pooled over 57 queries: nDCG@10 unjudged=0 -0.136, condensed -0.101, Recall@20 -0.053.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.204, -0.072].
- Folds won: 0 of 5.
- Without q55: nDCG@10 gain -0.148 (unjudged=0) / -0.112 (condensed).
- Leave-top-2-out gain: -0.156 / -0.123; top gainers: q55 +0.508, q56 +0.291.
- unjudged@10: variant 0.104, base 0.021.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.609 | 0.608 | -0.002 | 0.615 | 0.666 | +0.051 |  |
| 2 | 12 | 0.770 | 0.602 | -0.167 | 0.770 | 0.642 | -0.128 |  |
| 3 | 11 | 0.656 | 0.553 | -0.103 | 0.662 | 0.588 | -0.073 |  |
| 4 | 11 | 0.782 | 0.586 | -0.195 | 0.782 | 0.631 | -0.151 |  |
| 5 | 11 | 0.704 | 0.480 | -0.224 | 0.708 | 0.493 | -0.216 |  |

Pooled base nDCG@10 0.704, variant 0.567.

Wall time of the scoring pass (shared by E1a to E1h): 7.6 min for 183 new pairs, 0.53 pairs/s, batch 8, 6 torch threads, on a machine shared with other jobs.

## E6d: bge-reranker-base on rrf[bm25+stem, large+prefix+head], top 30, blend

**Decisions:** vs hybrid: CANDIDATE; vs hybrid+stem+prefix: CANDIDATE; vs E5b: rrf[bm25+stem, large+prefix+head] (no rerank): DROPPED.

- What changed: BAAI/bge-reranker-base reorders the top 30 of rrf[bm25+stem, large+prefix+head]; mode blend (alpha 0.5: 0.5 x min-max cross-encoder score + 0.5 x min-max first-stage score). Hits beyond depth 30 keep their first-stage order.
- Parameters: model=BAAI/bge-reranker-base, first_stage=rrf[bm25+stem, large+prefix+head], depth=30, mode=blend, alpha=0.5, max_length=512

### vs hybrid

**CANDIDATE.** gain +0.068 / +0.077, wins 4 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.068, condensed +0.077, Recall@20 +0.076.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [+0.028, +0.109].
- Folds won: 4 of 5.
- Without q55: nDCG@10 gain +0.069 (unjudged=0) / +0.078 (condensed).
- Leave-top-2-out gain: +0.056 / +0.063; top gainers: q24 +0.403, q39 +0.390.
- unjudged@10: variant 0.040, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.563 | 0.646 | +0.084 | 0.563 | 0.661 | +0.098 | yes |
| 2 | 12 | 0.677 | 0.715 | +0.038 | 0.677 | 0.723 | +0.047 | yes |
| 3 | 11 | 0.519 | 0.637 | +0.118 | 0.519 | 0.643 | +0.124 | yes |
| 4 | 11 | 0.653 | 0.766 | +0.113 | 0.653 | 0.778 | +0.124 | yes |
| 5 | 11 | 0.607 | 0.594 | -0.013 | 0.607 | 0.598 | -0.009 |  |

Pooled base nDCG@10 0.604, variant 0.672.

### vs hybrid+stem+prefix

**CANDIDATE.** gain +0.042 / +0.051, wins 5 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.042, condensed +0.051, Recall@20 +0.058.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.000, +0.086].
- Folds won: 5 of 5.
- Without q55: nDCG@10 gain +0.032 (unjudged=0) / +0.041 (condensed).
- Leave-top-2-out gain: +0.025 / +0.032; top gainers: q55 +0.627, q24 +0.403.
- unjudged@10: variant 0.040, base 0.000.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.607 | 0.646 | +0.040 | 0.607 | 0.661 | +0.054 | yes |
| 2 | 12 | 0.650 | 0.715 | +0.065 | 0.650 | 0.723 | +0.073 | yes |
| 3 | 11 | 0.560 | 0.637 | +0.077 | 0.560 | 0.643 | +0.083 | yes |
| 4 | 11 | 0.744 | 0.766 | +0.022 | 0.744 | 0.778 | +0.033 | yes |
| 5 | 11 | 0.588 | 0.594 | +0.006 | 0.588 | 0.598 | +0.009 | yes |

Pooled base nDCG@10 0.630, variant 0.672.

### vs E5b: rrf[bm25+stem, large+prefix+head] (no rerank)

**DROPPED.** gain -0.032 (unjudged=0) / -0.026 (condensed) is not above 0.01.

- Pooled over 57 queries: nDCG@10 unjudged=0 -0.032, condensed -0.026, Recall@20 +0.013.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.072, +0.006].
- Folds won: 1 of 5.
- Without q55: nDCG@10 gain -0.039 (unjudged=0) / -0.033 (condensed).
- Leave-top-2-out gain: -0.044 / -0.038; top gainers: q55 +0.358, q24 +0.273.
- unjudged@10: variant 0.040, base 0.021.

| fold | n | base nDCG | variant nDCG | gain | base cond | variant cond | gain | won |
|---|---|---|---|---|---|---|---|---|
| 1 | 12 | 0.609 | 0.646 | +0.037 | 0.615 | 0.661 | +0.045 | yes |
| 2 | 12 | 0.770 | 0.715 | -0.055 | 0.770 | 0.723 | -0.047 |  |
| 3 | 11 | 0.656 | 0.637 | -0.019 | 0.662 | 0.643 | -0.019 |  |
| 4 | 11 | 0.782 | 0.766 | -0.016 | 0.782 | 0.778 | -0.004 |  |
| 5 | 11 | 0.704 | 0.594 | -0.111 | 0.708 | 0.598 | -0.110 |  |

Pooled base nDCG@10 0.704, variant 0.672.

Wall time of the scoring pass (shared by E1a to E1h): 7.6 min for 183 new pairs, 0.53 pairs/s, batch 8, 6 torch threads, on a machine shared with other jobs.
