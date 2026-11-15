# Step 17 held-out update on newer qrels (labelled update)

**LLM-assessed qrels (claude-sonnet-5-5), not human grades.** This is an UPDATE of `results/step17_heldout.md`, not a second blind scoring. The held-out queries were seen in Step 17 and nothing is tuned or changed here: the frozen settings (hash 33c3a6e6395c) and data files are verified intact. Only the qrels differ.

- Original run: qrels at main commit `8ca347813d`, 2801 graded pairs.
- This update: `data/eval/qrels_t1_llm.tsv`, 3599 graded pairs (sha256 `ad7bf1c8a52f`). The extra pairs include the 10 held-out pairs listed unjudged in Step 17, and the Step 16 abstention pool.
- Held-out half: 28 answerable queries; the same Holm family P1 to P3 as before.

## Primaries, all 28 held-out queries, old qrels (reproduces the Step 17 report)

| id | variant | vs | n | variant nDCG@10 | base | diff [95% CI] | condensed diff | raw p | Holm p | wins / losses / ties |
|---|---|---|---|---|---|---|---|---|---|---|
| P1 | bm25+exp(w=0.5,all) | bm25 | 28 | 0.624 | 0.592 | +0.033 [-0.010, +0.105] | +0.038 | 0.4474 | 1.0000 | 3 / 2 / 23 |
| P2 | hybrid+stem+prefix+exp(w=0.3,all,dense)+pb(top=1,beta=0.1,bm25) | hybrid | 28 | 0.688 | 0.663 | +0.026 [-0.030, +0.083] | +0.026 | 0.3736 | 1.0000 | 14 / 10 / 4 |
| P3 | hybrid+stem+prefix | hybrid | 28 | 0.652 | 0.663 | -0.010 [-0.074, +0.049] | -0.010 | 0.7868 | 1.0000 | 12 / 12 / 4 |

## Primaries, all 28 held-out queries, newer qrels (update)

| id | variant | vs | n | variant nDCG@10 | base | diff [95% CI] | condensed diff | raw p | Holm p | wins / losses / ties |
|---|---|---|---|---|---|---|---|---|---|---|
| P1 | bm25+exp(w=0.5,all) | bm25 | 28 | 0.644 | 0.590 | +0.054 [+0.000, +0.134] | +0.054 | 0.0548 | 0.1644 | 4 / 1 / 23 |
| P2 | hybrid+stem+prefix+exp(w=0.3,all,dense)+pb(top=1,beta=0.1,bm25) | hybrid | 28 | 0.698 | 0.663 | +0.035 [-0.023, +0.094] | +0.035 | 0.2354 | 0.4708 | 15 / 10 / 3 |
| P3 | hybrid+stem+prefix | hybrid | 28 | 0.652 | 0.663 | -0.010 [-0.074, +0.049] | -0.010 | 0.7868 | 0.7868 | 12 / 12 / 4 |

## Primaries, without q15, q24, q55 (25 queries), old qrels (reproduces the Step 17 report)

| id | variant | vs | n | variant nDCG@10 | base | diff [95% CI] | condensed diff | raw p | Holm p | wins / losses / ties |
|---|---|---|---|---|---|---|---|---|---|---|
| P1 | bm25+exp(w=0.5,all) | bm25 | 25 | 0.660 | 0.655 | +0.004 [+0.000, +0.012] | +0.004 | 0.2458 | 0.7374 | 2 / 0 / 23 |
| P2 | hybrid+stem+prefix+exp(w=0.3,all,dense)+pb(top=1,beta=0.1,bm25) | hybrid | 25 | 0.716 | 0.703 | +0.013 [-0.047, +0.073] | +0.013 | 0.6650 | 1.0000 | 12 / 10 / 3 |
| P3 | hybrid+stem+prefix | hybrid | 25 | 0.701 | 0.703 | -0.003 [-0.040, +0.034] | -0.003 | 0.8842 | 1.0000 | 11 / 11 / 3 |

## Primaries, without q15, q24, q55 (25 queries), newer qrels (update)

| id | variant | vs | n | variant nDCG@10 | base | diff [95% CI] | condensed diff | raw p | Holm p | wins / losses / ties |
|---|---|---|---|---|---|---|---|---|---|---|
| P1 | bm25+exp(w=0.5,all) | bm25 | 25 | 0.660 | 0.655 | +0.004 [+0.000, +0.012] | +0.004 | 0.2458 | 0.7374 | 2 / 0 / 23 |
| P2 | hybrid+stem+prefix+exp(w=0.3,all,dense)+pb(top=1,beta=0.1,bm25) | hybrid | 25 | 0.716 | 0.703 | +0.013 [-0.047, +0.073] | +0.013 | 0.6650 | 1.0000 | 12 / 10 / 3 |
| P3 | hybrid+stem+prefix | hybrid | 25 | 0.701 | 0.703 | -0.003 [-0.040, +0.034] | -0.003 | 0.8842 | 1.0000 | 11 / 11 / 3 |

## Baselines on the held-out half

| system | nDCG@10 old qrels | nDCG@10 newer qrels | Recall@20 old | Recall@20 newer |
|---|---|---|---|---|
| bm25 | 0.592 | 0.590 | 0.736 | 0.724 |
| hybrid | 0.663 | 0.663 | 0.758 | 0.758 |
| bm25+exp(w=0.5,all) | 0.624 | 0.644 | 0.745 | 0.751 |
| hybrid+stem+prefix+exp(w=0.3,all,dense)+pb(top=1,beta=0.1,bm25) | 0.688 | 0.698 | 0.772 | 0.784 |
| hybrid+stem+prefix | 0.652 | 0.652 | 0.753 | 0.753 |

Change in each primary's held-out gain from the new qrels: P1 +0.021, P2 +0.010, P3 +0.000.
