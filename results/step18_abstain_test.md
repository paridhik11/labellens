# Step 18-abs: abstention TEST split (scored once)

**TEST split: 8 answerable, 5 no_answer.** Targets: AUROC >= 0.9, leave-one-out precision >= 0.8.

| score | AUROC [95% CI] | abstained | LOO precision | LOO recall | meets targets |
|---|---|---|---|---|---|
| ce_top | 0.500 [0.175, 0.850] | 8 of 13 | 0.125 | 0.200 | AUROC no, precision no |
| ce_margin | 0.575 [0.250, 0.900] | 5 of 13 | 0.400 | 0.400 | AUROC no, precision no |
| zavg(bm25 top, dense top) | 0.800 [0.500, 1.000] | 7 of 13 | 0.429 | 0.600 | AUROC no, precision no |
| logreg (LOO) on [bm25 top, dense top, ce top, coverage] | n/a (no single score) | 4 of 13 | 0.250 | 0.200 | AUROC no, precision no |

Per query (qid: label, ce_top, ce_margin, bm25 top, dense top, coverage):

- ab11: no_answer, 0.461, 0.078, 9.98, 0.783, 0.75
- ab12: no_answer, 0.971, 0.037, 7.91, 0.751, 0.60
- ab15: no_answer, 0.996, 0.013, 7.49, 0.677, 0.38
- ab17: no_answer, 0.682, 0.008, 11.83, 0.750, 0.60
- ab20: no_answer, 0.944, 0.295, 15.39, 0.692, 0.50
- q45: answerable, 0.998, 0.375, 15.23, 0.832, 0.83
- q46: answerable, 0.996, 0.002, 8.69, 0.835, 0.80
- q47: answerable, 0.594, 0.169, 9.02, 0.726, 0.50
- q48: answerable, 0.344, 0.072, 10.50, 0.748, 0.75
- q49: answerable, 0.886, 0.069, 11.67, 0.738, 1.00
- q56: answerable, 0.775, 0.040, 10.06, 0.791, 0.75
- q57: answerable, 0.980, 0.012, 12.53, 0.784, 1.00
- q61: answerable, 0.762, 0.289, 13.85, 0.805, 0.50
