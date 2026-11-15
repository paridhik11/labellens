# Step 18 experiments

**LLM-assessed qrels (claude-sonnet-5-5), not human grades.** 5-fold stratified cross-validation over the 57 answerable queries (`data/eval/cv_folds.json`, seed 42). Every variant is reported against plain hybrid AND hybrid+stem+prefix; gains are pooled over all queries. Rule: gain above 0.01 on both nDCG@10 lists (unjudged=0 and condensed), at least 3 of 5 folds won, survives leaving out the two biggest-gaining queries. unjudged@10 above 0.05 means PENDING_GRADING. CANDIDATE means only that the rule is passed: E0 passed it and then failed the Step 17 held-out check. This file is written by the harness; each section is replaced when its experiment is re-run.

<!-- summary:start -->
| experiment | vs | decision | gain unjudged=0 [95% CI] | gain condensed | Recall@20 gain | folds won | leave-top-2 gain | unjudged@10 |
|---|---|---|---|---|---|---|---|---|
| E0: hybrid+stem+prefix vs hybrid (carried over from Step 17) | hybrid | CANDIDATE | +0.026 [-0.013, +0.062] | +0.026 | +0.017 | 3 of 5 | +0.013 / +0.013 | 0.000 |
| E1a: bge-reranker-base on hybrid, top 30, replace | hybrid | DROPPED | -0.003 [-0.060, +0.053] | -0.000 | -0.017 | 3 of 5 | -0.022 / -0.019 | 0.019 |
| E1a: bge-reranker-base on hybrid, top 30, replace | hybrid+stem+prefix | DROPPED | -0.029 [-0.092, +0.035] | -0.026 | -0.034 | 1 of 5 | -0.052 / -0.049 | 0.019 |
| E1b: bge-reranker-base on hybrid, top 30, blend | hybrid | CANDIDATE | +0.028 [-0.008, +0.065] | +0.028 | +0.024 | 4 of 5 | +0.013 / +0.013 | 0.002 |
| E1b: bge-reranker-base on hybrid, top 30, blend | hybrid+stem+prefix | DROPPED | +0.002 [-0.045, +0.050] | +0.003 | +0.007 | 2 of 5 | -0.019 / -0.018 | 0.002 |
| E1c: bge-reranker-base on hybrid, top 50, replace | hybrid | PENDING_GRADING | -0.028 [-0.090, +0.036] | -0.002 | -0.049 | 2 of 5 | -0.047 / -0.021 | 0.105 |
| E1c: bge-reranker-base on hybrid, top 50, replace | hybrid+stem+prefix | PENDING_GRADING | -0.053 [-0.120, +0.014] | -0.028 | -0.066 | 2 of 5 | -0.078 / -0.052 | 0.105 |
| E1d: bge-reranker-base on hybrid, top 50, blend | hybrid | CANDIDATE | +0.034 [-0.006, +0.075] | +0.036 | +0.041 | 4 of 5 | +0.019 / +0.021 | 0.009 |
| E1d: bge-reranker-base on hybrid, top 50, blend | hybrid+stem+prefix | DROPPED | +0.008 [-0.041, +0.059] | +0.010 | +0.023 | 3 of 5 | -0.012 / -0.010 | 0.009 |
| E1e: bge-reranker-base on hybrid+stem+prefix, top 30, replace | hybrid | DROPPED | -0.007 [-0.064, +0.049] | -0.003 | +0.006 | 2 of 5 | -0.026 / -0.021 | 0.026 |
| E1e: bge-reranker-base on hybrid+stem+prefix, top 30, replace | hybrid+stem+prefix | DROPPED | -0.033 [-0.093, +0.028] | -0.029 | -0.012 | 1 of 5 | -0.056 / -0.052 | 0.026 |
| E1f: bge-reranker-base on hybrid+stem+prefix, top 30, blend | hybrid | CANDIDATE | +0.043 [+0.005, +0.082] | +0.043 | +0.039 | 4 of 5 | +0.029 / +0.029 | 0.002 |
| E1f: bge-reranker-base on hybrid+stem+prefix, top 30, blend | hybrid+stem+prefix | DROPPED | +0.018 [-0.019, +0.058] | +0.018 | +0.022 | 3 of 5 | -0.002 / -0.001 | 0.002 |
| E1g: bge-reranker-base on hybrid+stem+prefix, top 50, replace | hybrid | PENDING_GRADING | -0.039 [-0.100, +0.021] | -0.017 | -0.052 | 2 of 5 | -0.055 / -0.035 | 0.102 |
| E1g: bge-reranker-base on hybrid+stem+prefix, top 50, replace | hybrid+stem+prefix | PENDING_GRADING | -0.065 [-0.129, +0.000] | -0.042 | -0.069 | 0 of 5 | -0.086 / -0.065 | 0.102 |
| E1h: bge-reranker-base on hybrid+stem+prefix, top 50, blend | hybrid | CANDIDATE | +0.040 [-0.001, +0.081] | +0.041 | +0.036 | 4 of 5 | +0.028 / +0.028 | 0.007 |
| E1h: bge-reranker-base on hybrid+stem+prefix, top 50, blend | hybrid+stem+prefix | DROPPED | +0.015 [-0.026, +0.057] | +0.015 | +0.019 | 3 of 5 | -0.003 / -0.002 | 0.007 |
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

Cross-encoder scores were reused from the on-disk cache. Original scoring pass (shared by E1a to E1h): 71.7 min for 3415 pairs at 0.80 pairs/s, batch 8, 6 torch threads, machine shared with other jobs, qrels of that time 2801 pairs.

## E1b: bge-reranker-base on hybrid, top 30, blend

**Decisions:** vs hybrid: CANDIDATE; vs hybrid+stem+prefix: DROPPED.

- What changed: BAAI/bge-reranker-base reorders the top 30 of hybrid; mode blend (alpha 0.5: 0.5 x min-max cross-encoder score + 0.5 x min-max first-stage score). Hits beyond depth 30 keep their first-stage order.
- Parameters: model=BAAI/bge-reranker-base, first_stage=hybrid, depth=30, mode=blend, alpha=0.5, max_length=512

### vs hybrid

**CANDIDATE.** gain +0.028 / +0.028, wins 4 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.028, condensed +0.028, Recall@20 +0.024.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.008, +0.065].
- Folds won: 4 of 5.
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

Cross-encoder scores were reused from the on-disk cache. Original scoring pass (shared by E1a to E1h): 71.7 min for 3415 pairs at 0.80 pairs/s, batch 8, 6 torch threads, machine shared with other jobs, qrels of that time 2801 pairs.

## E1c: bge-reranker-base on hybrid, top 50, replace

**Decisions:** vs hybrid: PENDING_GRADING; vs hybrid+stem+prefix: PENDING_GRADING.

- What changed: BAAI/bge-reranker-base reorders the top 50 of hybrid; mode replace (sorted by cross-encoder score alone). Hits beyond depth 50 keep their first-stage order.
- Parameters: model=BAAI/bge-reranker-base, first_stage=hybrid, depth=50, mode=replace, alpha=-, max_length=512

### vs hybrid

**PENDING_GRADING.** unjudged@10 is 0.105, above 0.05; grade the pairs in results/step18_unjudged.csv, then re-judge.

- Pooled over 57 queries: nDCG@10 unjudged=0 -0.028, condensed -0.002, Recall@20 -0.049.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.090, +0.036].
- Folds won: 2 of 5.
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

Cross-encoder scores were reused from the on-disk cache. Original scoring pass (shared by E1a to E1h): 71.7 min for 3415 pairs at 0.80 pairs/s, batch 8, 6 torch threads, machine shared with other jobs, qrels of that time 2801 pairs.

## E1d: bge-reranker-base on hybrid, top 50, blend

**Decisions:** vs hybrid: CANDIDATE; vs hybrid+stem+prefix: DROPPED.

- What changed: BAAI/bge-reranker-base reorders the top 50 of hybrid; mode blend (alpha 0.5: 0.5 x min-max cross-encoder score + 0.5 x min-max first-stage score). Hits beyond depth 50 keep their first-stage order.
- Parameters: model=BAAI/bge-reranker-base, first_stage=hybrid, depth=50, mode=blend, alpha=0.5, max_length=512

### vs hybrid

**CANDIDATE.** gain +0.034 / +0.036, wins 4 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.034, condensed +0.036, Recall@20 +0.041.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.006, +0.075].
- Folds won: 4 of 5.
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

Cross-encoder scores were reused from the on-disk cache. Original scoring pass (shared by E1a to E1h): 71.7 min for 3415 pairs at 0.80 pairs/s, batch 8, 6 torch threads, machine shared with other jobs, qrels of that time 2801 pairs.

## E1e: bge-reranker-base on hybrid+stem+prefix, top 30, replace

**Decisions:** vs hybrid: DROPPED; vs hybrid+stem+prefix: DROPPED.

- What changed: BAAI/bge-reranker-base reorders the top 30 of hybrid+stem+prefix; mode replace (sorted by cross-encoder score alone). Hits beyond depth 30 keep their first-stage order.
- Parameters: model=BAAI/bge-reranker-base, first_stage=hybrid+stem+prefix, depth=30, mode=replace, alpha=-, max_length=512

### vs hybrid

**DROPPED.** gain -0.007 (unjudged=0) / -0.003 (condensed) is not above 0.01.

- Pooled over 57 queries: nDCG@10 unjudged=0 -0.007, condensed -0.003, Recall@20 +0.006.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.064, +0.049].
- Folds won: 2 of 5.
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

Cross-encoder scores were reused from the on-disk cache. Original scoring pass (shared by E1a to E1h): 71.7 min for 3415 pairs at 0.80 pairs/s, batch 8, 6 torch threads, machine shared with other jobs, qrels of that time 2801 pairs.

## E1f: bge-reranker-base on hybrid+stem+prefix, top 30, blend

**Decisions:** vs hybrid: CANDIDATE; vs hybrid+stem+prefix: DROPPED.

- What changed: BAAI/bge-reranker-base reorders the top 30 of hybrid+stem+prefix; mode blend (alpha 0.5: 0.5 x min-max cross-encoder score + 0.5 x min-max first-stage score). Hits beyond depth 30 keep their first-stage order.
- Parameters: model=BAAI/bge-reranker-base, first_stage=hybrid+stem+prefix, depth=30, mode=blend, alpha=0.5, max_length=512

### vs hybrid

**CANDIDATE.** gain +0.043 / +0.043, wins 4 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.043, condensed +0.043, Recall@20 +0.039.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [+0.005, +0.082].
- Folds won: 4 of 5.
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

Cross-encoder scores were reused from the on-disk cache. Original scoring pass (shared by E1a to E1h): 71.7 min for 3415 pairs at 0.80 pairs/s, batch 8, 6 torch threads, machine shared with other jobs, qrels of that time 2801 pairs.

## E1g: bge-reranker-base on hybrid+stem+prefix, top 50, replace

**Decisions:** vs hybrid: PENDING_GRADING; vs hybrid+stem+prefix: PENDING_GRADING.

- What changed: BAAI/bge-reranker-base reorders the top 50 of hybrid+stem+prefix; mode replace (sorted by cross-encoder score alone). Hits beyond depth 50 keep their first-stage order.
- Parameters: model=BAAI/bge-reranker-base, first_stage=hybrid+stem+prefix, depth=50, mode=replace, alpha=-, max_length=512

### vs hybrid

**PENDING_GRADING.** unjudged@10 is 0.102, above 0.05; grade the pairs in results/step18_unjudged.csv, then re-judge.

- Pooled over 57 queries: nDCG@10 unjudged=0 -0.039, condensed -0.017, Recall@20 -0.052.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.100, +0.021].
- Folds won: 2 of 5.
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

Cross-encoder scores were reused from the on-disk cache. Original scoring pass (shared by E1a to E1h): 71.7 min for 3415 pairs at 0.80 pairs/s, batch 8, 6 torch threads, machine shared with other jobs, qrels of that time 2801 pairs.

## E1h: bge-reranker-base on hybrid+stem+prefix, top 50, blend

**Decisions:** vs hybrid: CANDIDATE; vs hybrid+stem+prefix: DROPPED.

- What changed: BAAI/bge-reranker-base reorders the top 50 of hybrid+stem+prefix; mode blend (alpha 0.5: 0.5 x min-max cross-encoder score + 0.5 x min-max first-stage score). Hits beyond depth 50 keep their first-stage order.
- Parameters: model=BAAI/bge-reranker-base, first_stage=hybrid+stem+prefix, depth=50, mode=blend, alpha=0.5, max_length=512

### vs hybrid

**CANDIDATE.** gain +0.040 / +0.041, wins 4 of 5 folds, survives leave-top-2-out; a candidate only, since passing CV is not evidence of a real gain (E0 passed CV and failed held-out in Step 17).

- Pooled over 57 queries: nDCG@10 unjudged=0 +0.040, condensed +0.041, Recall@20 +0.036.
- Bootstrap 95% interval of the unjudged=0 gain (information only): [-0.001, +0.081].
- Folds won: 4 of 5.
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

Cross-encoder scores were reused from the on-disk cache. Original scoring pass (shared by E1a to E1h): 71.7 min for 3415 pairs at 0.80 pairs/s, batch 8, 6 torch threads, machine shared with other jobs, qrels of that time 2801 pairs.
