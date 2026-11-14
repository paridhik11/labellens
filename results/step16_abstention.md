# Step 16: abstention evaluation (medicine mode)

## Pre-declaration (committed before any score was computed)

# Step 16 abstention: pre-declaration

Written and committed BEFORE any abstention score was computed or looked at. It is copied into `results/step16_abstention.md`.

## Setup
- Module: medicine only (468 chunks), systems built on the medicine index only.
- Queries: `data/eval/queries_t1_abstain_draft.csv`, 10 answerable and 10 no_answer (7 hard, 3 easy). Labels are final after the grade 2 check in Step 2b (a no_answer query with a grade 2 chunk is relabelled answerable and listed).
- Prediction target: answerable (1) versus no_answer (0), from a retrieval score. A higher score means "answerable"; the system abstains when the score is below a threshold.

## Primary result (declared in advance)
- **Primary score: the hybrid top RRF score** (the rank-1 score of `HybridRetriever`, default k=60, equal weights).
- **Primary metric: AUROC over all 20 queries**, with a stratified bootstrap 95% percentile interval (10,000 resamples, seed 42; answerable and no_answer queries are resampled separately so both classes are always present).
- Everything else (bm25 and dense top score, the margin between rank 1 and rank 2 for all three systems, the subgroup AUROCs answerable vs hard-only and answerable vs easy-only) is secondary and exploratory. No multiple-comparison correction is applied; they are not used to pick the primary.
- A cross-encoder score is reported only if the repo already has a cross-encoder. It has none, so it is not computed.

## Abstention threshold
- Chosen by leave-one-out over the 20 queries: for each query, the threshold is picked on the other 19 (maximum balanced accuracy over midpoints between consecutive distinct scores, plus one below the minimum and one above the maximum; ties broken by the median of the tied thresholds), then applied to the held-out query.
- Precision and recall of abstaining are computed from the 20 held-out predictions, with no_answer as the positive class. Precision is reported as n/a when the system never abstains.

## Caveats stated in advance
- 20 queries (10 vs 10, and 10 vs 7, 10 vs 3 in the subgroups) is tiny. Intervals will be wide, a bootstrap on this little data is itself unstable, and no result should be read as a precise estimate.
- Relevance grades come from an LLM grader (claude-sonnet-5-5) under the frozen prompt, not from humans. The no_answer labels are checked against them only for grade 2 chunks.

## Data

- Queries: 20 (10 answerable, 10 no_answer: 7 hard, 3 easy). Medicine index only (468 chunks).
- Relabelling check (grade >= 2 chunk for a no_answer query in the judged pool): 0 queries flipped.
- Pool: bm25, dense and hybrid top 20, 788 unique (query, chunk) pairs, all graded by the LLM grader (claude-sonnet-5-5, frozen prompt). Grades are not human grades.
- Highest grade seen per no_answer query: ab11=0, ab12=1, ab13=1, ab14=0, ab15=1, ab16=0, ab17=1, ab18=1, ab19=1, ab20=1.
- No cross-encoder exists in this repo, so the cross-encoder rank-1 score was not computed.

## Size warning

With 10 answerable and 10 no_answer queries (10 vs 7 hard, 10 vs 3 easy) every interval below is very wide and the bootstrap itself is unstable at this size. The easy-only comparison has only 3 negatives, so its AUROC can take only a few values and its interval is close to uninformative. Treat all numbers as indicative, not as estimates.

## AUROC (answerable = positive, higher score = more likely answerable)

Stratified bootstrap, 10000 resamples, seed 42, 95% percentile interval.

| System | Score | AUROC all 20 [95% CI] | vs hard only (10 v 7) | vs easy only (10 v 3) |
|---|---|---|---|---|
| bm25 | top | 0.940 [0.820, 1.000] | 0.943 [0.800, 1.000] | 0.933 [0.733, 1.000] |
| bm25 | margin | 0.640 [0.370, 0.870] | 0.657 [0.371, 0.886] | 0.600 [0.300, 0.900] |
| dense | top | 0.900 [0.740, 1.000] | 0.900 [0.714, 1.000] | 0.900 [0.667, 1.000] |
| dense | margin | 0.530 [0.260, 0.790] | 0.529 [0.243, 0.800] | 0.533 [0.100, 1.000] |
| hybrid | top (PRIMARY) | 0.985 [0.930, 1.000] | 0.979 [0.900, 1.000] | 1.000 [1.000, 1.000] |
| hybrid | margin | 0.260 [0.040, 0.520] | 0.229 [0.000, 0.500] | 0.333 [0.000, 0.700] |

## Abstaining at a leave-one-out threshold (all 20 queries)

no_answer is the positive class. Threshold picked on the other 19 queries (max balanced accuracy), applied to the held-out one.

| System | Score | Abstained | Precision | Recall | Recall hard | Recall easy |
|---|---|---|---|---|---|---|
| bm25 | top | 10 | 0.700 | 0.700 | 0.714 | 0.667 |
| bm25 | margin | 15 | 0.600 | 0.900 | 0.857 | 1.000 |
| dense | top | 12 | 0.750 | 0.900 | 1.000 | 0.667 |
| dense | margin | 17 | 0.529 | 0.900 | 1.000 | 0.667 |
| hybrid | top | 11 | 0.909 | 1.000 | 1.000 | 1.000 |
| hybrid | margin | 18 | 0.500 | 0.900 | 0.857 | 1.000 |

## Per query, primary score (hybrid top RRF score)

| qid | label | difficulty | hybrid top | LOO abstain | query |
|---|---|---|---|---|---|
| ab01 | answerable | - | 0.03227 | answer | tamper-evident packaging for over the counter drugs |
| ab02 | answerable | - | 0.03252 | answer | what is the National Drug Code number and where must it appear |
| ab03 | answerable | - | 0.03279 | answer | required warning for prescription drugs that contain sulfites |
| ab04 | answerable | - | 0.03227 | answer | sunscreen labeling based on effectiveness testing |
| ab05 | answerable | - | 0.03279 | answer | do drug labels need a Spanish version |
| ab06 | answerable | - | 0.03252 | answer | when must the pharmacy give the patient a Medication Guide at dispensing |
| ab07 | answerable | - | 0.03252 | answer | aluminum content warning on intravenous feeding products |
| ab08 | answerable | - | 0.03279 | answer | why do aspirin products carry a warning about children and flu symptoms |
| ab09 | answerable | - | 0.03200 | abstain | how are oxygen and other medical gas cylinders labeled |
| ab10 | answerable | - | 0.03252 | answer | label statement for a yellow food dye that can cause allergic reactions in some people |
| ab11 | no_answer | hard | 0.03202 | abstain | dietary supplement label requirements |
| ab12 | no_answer | hard | 0.02869 | abstain | child resistant packaging for prescription drugs |
| ab13 | no_answer | easy | 0.02625 | abstain | Health Canada bilingual drug label rules |
| ab14 | no_answer | hard | 0.03128 | abstain | labeling requirements for blood and blood components |
| ab15 | no_answer | hard | 0.03089 | abstain | what are the rules for handing out free drug samples to physicians |
| ab16 | no_answer | easy | 0.02565 | abstain | how to apply for orphan drug designation |
| ab17 | no_answer | hard | 0.03151 | abstain | drug establishment registration and listing with FDA |
| ab18 | no_answer | easy | 0.03031 | abstain | what must a clinical trial informed consent form contain |
| ab19 | no_answer | hard | 0.03200 | abstain | USP beyond use dating for compounded sterile preparations |
| ab20 | no_answer | hard | 0.03021 | abstain | does a tablet need an imprint code so it can be identified |
