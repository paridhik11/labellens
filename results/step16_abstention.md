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

## Notes (written AFTER the results above were seen)

- **Primary result:** hybrid top RRF score separates the 20 queries almost perfectly (AUROC 0.985, one near-tie: answerable ab09 at 0.03200 vs hard no_answer ab11 at 0.03202 and ab19 at 0.03200). The interval [0.930, 1.000] is wide for 10 vs 10 queries.
- **Easy-only 1.000 [1.000, 1.000]** is degenerate: with perfect separation every bootstrap resample scores 1.0. It says nothing about uncertainty (3 negatives only).
- **Margin scores run backwards.** Hybrid margin has AUROC 0.26: answerable queries tend to have several near-equal top chunks (rankers agree on a section's chunks), so a small rank-1 minus rank-2 gap goes with answerable. The pre-declared rule "low score means abstain" does not suit margin, so its precision and recall rows (abstains on 15 to 18 of 20) are not meaningful.
- **bm25 top is not comparable across queries** (it grows with query length and term rarity). Hybrid top takes few discrete values (RRF of rank positions), so it mostly measures whether both rankers put the same chunk first.
- **Possible optimism (confirmed in the secondary section).** I drafted ab01 to ab10 from corpus section titles, so they are closer to the corpus wording than real queries. On the fairer set (q45 to q61 answerable vs the same 10 no_answer) hybrid top RRF falls from 0.985 to 0.797 [0.612, 0.941] and dense top cosine is best at 0.876 [0.729, 0.976]. The pre-declared primary is unchanged, but its 0.985 should not be quoted as the expected accuracy on real queries. Distinct hybrid top values: 13 over the 20 queries, 20 over the 27.
- **Labels:** all relevance grades are LLM grades (claude-sonnet-5-5), not human. No no_answer query had a grade 2 chunk, so no relabelling happened; grade 1 chunks exist for 7 of the 10 no_answer queries (see "Highest grade seen").
- Not computed: cross-encoder score (none in the repo). It will be added after Step 18b downloads bge-reranker-base; nothing was downloaded in Step 16.

## Secondary, post-hoc

Written after the primary results were seen. SECONDARY and exploratory: it does not change the pre-declared primary (hybrid top RRF, ab01 to ab20). Same method as above (stratified bootstrap, 10,000 resamples, seed 42; leave-one-out threshold, no_answer is the positive class). z-scores use the mean and std of the evaluated set itself (no labels). Set B uses q45 to q61 (17 answerable; q62 is no_answer, so it is not a positive). Both sets use the same 10 no_answer queries. Intervals are wide.

### Set A (ab01 to ab10): 10 answerable vs 10 no_answer

| Score | AUROC [95% CI] | vs hard only | vs easy only | LOO abstained | Precision | Recall |
|---|---|---|---|---|---|---|
| hybrid top RRF | 0.985 [0.930, 1.000] | 0.979 [0.900, 1.000] | 1.000 [1.000, 1.000] | 11 | 0.909 | 1.000 |
| bm25 top | 0.940 [0.820, 1.000] | 0.943 [0.800, 1.000] | 0.933 [0.733, 1.000] | 10 | 0.700 | 0.700 |
| bm25 top / query length | 0.910 [0.750, 1.000] | 0.886 [0.686, 1.000] | 0.967 [0.867, 1.000] | 10 | 0.800 | 0.800 |
| dense top cosine | 0.900 [0.740, 1.000] | 0.900 [0.714, 1.000] | 0.900 [0.667, 1.000] | 12 | 0.750 | 0.900 |
| dense gap rank1-rank5 | 0.900 [0.730, 1.000] | 0.957 [0.829, 1.000] | 0.767 [0.400, 1.000] | 10 | 0.900 | 0.900 |
| z-avg(bm25 top, dense top) | 0.980 [0.910, 1.000] | 0.971 [0.871, 1.000] | 1.000 [1.000, 1.000] | 11 | 0.909 | 1.000 |

Distinct hybrid top RRF values across these 20 queries: 13.

### Set B (q45 to q61): 17 answerable vs 10 no_answer

| Score | AUROC [95% CI] | vs hard only | vs easy only | LOO abstained | Precision | Recall |
|---|---|---|---|---|---|---|
| hybrid top RRF | 0.797 [0.612, 0.941] | 0.727 [0.504, 0.908] | 0.961 [0.843, 1.000] | 16 | 0.500 | 0.800 |
| bm25 top | 0.694 [0.459, 0.900] | 0.697 [0.445, 0.924] | 0.686 [0.294, 1.000] | 10 | 0.600 | 0.600 |
| bm25 top / query length | 0.771 [0.571, 0.929] | 0.739 [0.496, 0.933] | 0.843 [0.608, 1.000] | 11 | 0.545 | 0.600 |
| dense top cosine | 0.876 [0.729, 0.976] | 0.891 [0.739, 0.983] | 0.843 [0.588, 1.000] | 14 | 0.571 | 0.800 |
| dense gap rank1-rank5 | 0.594 [0.365, 0.806] | 0.630 [0.387, 0.840] | 0.510 [0.118, 0.882] | 17 | 0.529 | 0.900 |
| z-avg(bm25 top, dense top) | 0.853 [0.688, 0.982] | 0.857 [0.681, 0.983] | 0.843 [0.647, 1.000] | 13 | 0.538 | 0.700 |

Distinct hybrid top RRF values across these 27 queries: 20.

