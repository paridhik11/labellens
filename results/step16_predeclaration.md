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
