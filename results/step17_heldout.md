# Step 17f: held-out results of the frozen configuration

**LLM-assessed qrels (claude-sonnet-5-5), not human grades.** Held-out half only: 28 answerable queries (19 device, 9 medicine), seed 42 split. Settings were frozen on the dev half (`data/eval/step17_config.json`, settings hash 33c3a6e6395c) and scored here once. Qrels: `data/eval/qrels_t1_llm.tsv`, 2801 rows, main commit `8ca347813d`. Depth 50, nDCG@10, chunk level, each query searched in its own module.

## Read this first

- **These are LLM grades, not human grades.** The LLM is stricter than humans at the 0/1 boundary (Step 13), and all numbers inherit that.
- **n = 28.** Intervals are wide; a difference whose interval contains 0 is not evidence of a gain. Medicine has too few queries to say anything on its own.
- **Held-out was not entirely unseen for stemming and the BGE prefix.** The Step 15b ablation had already evaluated bm25_stem, hybrid_stem, dense_prefix and hybrid_prefix on all 62 queries, including this half. Their settings were not tuned on it (stemming and the prefix have no parameters), but P3 and the stem and prefix parts of P2 were chosen with that knowledge in the project, so treat them as less independent than P1.
- **Failure-derived synonym groups.** q15, q24, q55 are held-out queries that motivated groups in the lexicon, so P1 and P2 may be favoured on them. Every primary is therefore also reported without these three queries.
- The config was frozen against the 2531-pair qrels of the dev run; held-out is scored on the final 2801-pair qrels. The variants and settings are the same.
- Holm adjusts over the three declared primaries only; secondary rows have no p-values.

## Primaries (Holm over P1, P2, P3), all 28 held-out queries

| id | variant | vs | n | variant nDCG@10 | base | diff [95% CI] | condensed diff | raw p | Holm p | wins / losses / ties |
|---|---|---|---|---|---|---|---|---|---|---|
| P1 | bm25+exp(w=0.5,all) | bm25 | 28 | 0.624 | 0.592 | +0.033 [-0.010, +0.105] | +0.038 | 0.4474 | 1.0000 | 3 / 2 / 23 |
| P2 | hybrid+stem+prefix+exp(w=0.3,all,dense)+pb(top=1,beta=0.1,bm25) | hybrid | 28 | 0.688 | 0.663 | +0.026 [-0.030, +0.083] | +0.026 | 0.3736 | 1.0000 | 14 / 10 / 4 |
| P3 | hybrid+stem+prefix | hybrid | 28 | 0.652 | 0.663 | -0.010 [-0.074, +0.049] | -0.010 | 0.7868 | 1.0000 | 12 / 12 / 4 |

## Primaries without q15, q24 and q55 (25 queries)

| id | variant | vs | n | variant nDCG@10 | base | diff [95% CI] | condensed diff | raw p | Holm p | wins / losses / ties |
|---|---|---|---|---|---|---|---|---|---|---|
| P1 | bm25+exp(w=0.5,all) | bm25 | 25 | 0.660 | 0.655 | +0.004 [+0.000, +0.012] | +0.004 | 0.2458 | 0.7374 | 2 / 0 / 23 |
| P2 | hybrid+stem+prefix+exp(w=0.3,all,dense)+pb(top=1,beta=0.1,bm25) | hybrid | 25 | 0.716 | 0.703 | +0.013 [-0.047, +0.073] | +0.013 | 0.6650 | 1.0000 | 12 / 10 / 3 |
| P3 | hybrid+stem+prefix | hybrid | 25 | 0.701 | 0.703 | -0.003 [-0.040, +0.034] | -0.003 | 0.8842 | 1.0000 | 11 / 11 / 3 |

Biggest query-level changes (nDCG@10 difference), all held-out queries:

- **P1** q24 (field_req, device, motivating) -0.136; q15 (vocab_mismatch, device, motivating) -0.004; q55 (vocab_mismatch, medicine, motivating) +0.948; q56 (vocab_mismatch, medicine) +0.100; q37 (change_impact, device) +0.003
- **P2** q56 (vocab_mismatch, medicine) -0.369; q48 (direct, medicine) -0.299; q14 (vocab_mismatch, device) -0.118; q40 (change_impact, device) +0.377; q18 (vocab_mismatch, device) +0.354; q55 (vocab_mismatch, medicine, motivating) +0.297
- **P3** q55 (vocab_mismatch, medicine, motivating) -0.629; q21 (field_req, device) -0.206; q48 (direct, medicine) -0.182; q15 (vocab_mismatch, device, motivating) +0.417; q40 (change_impact, device) +0.198; q18 (vocab_mismatch, device) +0.162

## Secondary variants and baselines (descriptive, no p-values)

| variant | vs | nDCG@10 | condensed | unjudged@10 | device | medicine | diff [95% CI] | wins / losses |
|---|---|---|---|---|---|---|---|---|
| bm25 |  | 0.592 | 0.592 | 0.000 | 0.627 | 0.517 |  |  |
| hybrid |  | 0.663 | 0.663 | 0.000 | 0.652 | 0.685 |  |  |
| dense |  | 0.525 | 0.525 | 0.000 | 0.515 | 0.546 |  |  |
| bm25+stem | bm25 | 0.640 | 0.640 | 0.000 | 0.685 | 0.546 | +0.048 [+0.004, +0.100] | 15 / 7 |
| dense+prefix | dense | 0.568 | 0.568 | 0.000 | 0.554 | 0.597 | +0.042 [+0.011, +0.075] | 19 / 8 |
| hybrid+rr(rrf) | hybrid | 0.671 | 0.671 | 0.000 | 0.657 | 0.702 | +0.009 [-0.036, +0.050] | 14 / 9 |
| bm25+exp(w=0.5,cfr) | bm25 | 0.595 | 0.595 | 0.000 | 0.627 | 0.528 | +0.004 [+0.000, +0.011] | 2 / 0 |
| hybrid+exp(w=0.3,cfr,bm25side) | hybrid | 0.664 | 0.664 | 0.000 | 0.654 | 0.685 | +0.002 [+0.000, +0.005] | 1 / 0 |
| hybrid+stem+prefix+pb(top=1,beta=0.1,bm25) | hybrid | 0.673 | 0.673 | 0.000 | 0.726 | 0.561 | +0.010 [-0.050, +0.070] | 14 / 10 |
| hybrid+stem+prefix+exp(w=0.3,cfr,dense)+pb(top=1,beta=0.1,bm25) | hybrid | 0.668 | 0.668 | 0.000 | 0.728 | 0.541 | +0.006 [-0.059, +0.068] | 14 / 10 |

## Expansion both ways (nDCG@10, held-out)

| system | none | all groups | CFR groups only |
|---|---|---|---|
| bm25 (w=0.5) | 0.592 (+0.000 vs bm25) | 0.624 (+0.033 vs bm25) | 0.595 (+0.004 vs bm25) |
| hybrid, BM25 half only (w=0.3) | 0.663 (+0.000 vs hybrid) | not in config | 0.664 (+0.002 vs hybrid) |
| P2 combination | 0.673 (+0.010 vs hybrid) | 0.688 (+0.026 vs hybrid) | 0.668 (+0.006 vs hybrid) |

The P2 combination has the CFR-only version and the no-expansion version as secondaries; the CFR-only P2 structure was not run on dev.

## The same frozen variants on the dev half (29 queries; tuned there, so optimistic)

| variant | vs | nDCG@10 | condensed | unjudged@10 | device | medicine | diff [95% CI] | wins / losses |
|---|---|---|---|---|---|---|---|---|
| bm25 |  | 0.561 | 0.561 | 0.000 | 0.537 | 0.623 |  |  |
| hybrid |  | 0.548 | 0.548 | 0.000 | 0.531 | 0.592 |  |  |
| dense |  | 0.489 | 0.489 | 0.000 | 0.482 | 0.505 |  |  |
| bm25+exp(w=0.5,all) | bm25 | 0.594 | 0.594 | 0.010 | 0.563 | 0.677 | +0.034 [+0.003, +0.073] | 8 / 5 |
| hybrid+stem+prefix+exp(w=0.3,all,dense)+pb(top=1,beta=0.1,bm25) | hybrid | 0.643 | 0.643 | 0.003 | 0.620 | 0.703 | +0.095 [+0.030, +0.158] | 21 / 8 |
| hybrid+stem+prefix | hybrid | 0.608 | 0.608 | 0.000 | 0.608 | 0.608 | +0.060 [+0.022, +0.099] | 22 / 6 |
| bm25+stem | bm25 | 0.571 | 0.571 | 0.000 | 0.558 | 0.603 | +0.010 [-0.032, +0.054] | 13 / 13 |
| dense+prefix | dense | 0.542 | 0.542 | 0.000 | 0.537 | 0.553 | +0.053 [+0.016, +0.092] | 19 / 7 |
| hybrid+rr(rrf) | hybrid | 0.590 | 0.590 | 0.003 | 0.590 | 0.591 | +0.042 [+0.002, +0.085] | 17 / 12 |
| bm25+exp(w=0.5,cfr) | bm25 | 0.568 | 0.568 | 0.000 | 0.548 | 0.623 | +0.008 [-0.002, +0.022] | 4 / 1 |
| hybrid+exp(w=0.3,cfr,bm25side) | hybrid | 0.559 | 0.559 | 0.000 | 0.546 | 0.592 | +0.011 [-0.002, +0.032] | 3 / 2 |
| hybrid+stem+prefix+pb(top=1,beta=0.1,bm25) | hybrid | 0.608 | 0.608 | 0.000 | 0.595 | 0.643 | +0.060 [+0.006, +0.109] | 21 / 7 |
| hybrid+stem+prefix+exp(w=0.3,cfr,dense)+pb(top=1,beta=0.1,bm25) | hybrid | 0.608 | 0.608 | 0.000 | 0.595 | 0.643 | +0.060 [+0.006, +0.112] | 20 / 8 |

## Unjudged pairs on held-out

`results/step17_unjudged_heldout.csv`: 14 rows, **10 unique (query, chunk) pairs** unjudged in the final qrels, over all config variants. Nothing was graded and the config was not changed.

- bm25+exp(w=0.5,all): 8 rows
- hybrid+stem+prefix+exp(w=0.3,all,dense)+pb(top=1,beta=0.1,bm25): 6 rows
