# Step 18-abs: abstention track (dev half only)

**LLM-assessed qrels are not used here; the labels are the query classes. The TEST split is not scored in this file: it is scored once at 18f, so these numbers come from 14 queries and are development numbers.** Step 16's files are untouched.

Setup: medicine index only; positives q45 to q61 (17), negatives ab11 to ab20 (10). Scores come from hybrid+stem+prefix top 30; ce = bge-reranker-base. The z-scores use the dev half. Split saved in `data\eval\abstain_split.json` (seed 42): dev 9 + 5, test 8 + 5.

## Dev half

**DEV split: 9 answerable, 5 no_answer.** Targets: AUROC >= 0.9, leave-one-out precision >= 0.8.

| score | AUROC [95% CI] | abstained | LOO precision | LOO recall | meets targets |
|---|---|---|---|---|---|
| ce_top | 0.889 [0.667, 1.000] | 5 of 14 | 0.600 | 0.600 | AUROC no, precision no |
| ce_margin | 0.222 [0.000, 0.511] | 12 of 14 | 0.333 | 0.800 | AUROC no, precision no |
| zavg(bm25 top, dense top) | 0.911 [0.733, 1.000] | 6 of 14 | 0.667 | 0.800 | AUROC yes, precision no |
| logreg (LOO) on [bm25 top, dense top, ce top, coverage] | n/a (no single score) | 5 of 14 | 0.800 | 0.800 | AUROC no, precision yes |

Per query (qid: label, ce_top, ce_margin, bm25 top, dense top, coverage):

- ab13: no_answer, 0.981, 0.029, 6.54, 0.764, 0.50
- ab14: no_answer, 0.394, 0.108, 7.86, 0.741, 0.75
- ab16: no_answer, 0.045, 0.012, 8.02, 0.713, 0.60
- ab18: no_answer, 0.689, 0.268, 14.61, 0.727, 0.50
- ab19: no_answer, 0.398, 0.161, 8.26, 0.705, 0.14
- q50: answerable, 0.993, 0.014, 12.34, 0.806, 0.67
- q51: answerable, 0.996, 0.005, 18.94, 0.792, 1.00
- q52: answerable, 0.985, 0.009, 14.41, 0.836, 0.83
- q53: answerable, 0.994, 0.001, 10.73, 0.846, 1.00
- q54: answerable, 0.827, 0.026, 10.59, 0.796, 0.80
- q55: answerable, 0.976, 0.016, 4.08, 0.764, 0.67
- q58: answerable, 0.973, 0.078, 18.72, 0.840, 0.83
- q59: answerable, 0.636, 0.336, 7.43, 0.773, 0.80
- q60: answerable, 0.988, 0.003, 14.71, 0.795, 0.83
