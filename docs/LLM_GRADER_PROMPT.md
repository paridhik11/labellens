# LLM grader prompt and batch log

This file is the single source for LLM relevance grading in LabelLens. The LLM grader uses only the text in the "Grader prompt" section below. If this text changes, every batch graded before the change must be marked in the log, because the grades are no longer comparable.

## Why LLM grades, and their limits

- There is no public set of relevance grades for our 21 CFR device and medicine corpus, so grades must be made for our own pool.
- LLM relevance assessment is an established method. UMBRELA (an open reproduction of the Bing LLM relevance assessor, arXiv 2406.06519) produced system rankings at TREC RAG 2024 that closely matched rankings from manual NIST judgments (arXiv 2411.08275).
- Known limits: agreement on single passages is only fair, and LLMs tend to give top grades more readily than humans. This is why a human-graded sample is compared against the LLM grades in Step 13.
- Grading happens inside a Claude Code session, not through an API script. Re-grading would not give identical grades. What is reproducible is this prompt, the fixed batches (seeded order) and the recorded outputs and model id.

## Files

| File | Who writes it | Contents |
|---|---|---|
| `data/eval/pool_t1.csv` | Human only | The pool with the human `grade` column. The LLM grader never writes here. |
| `data/eval/pool_t1_human_sample.csv` | Human only | 15 sampled queries for human grading. Contains no LLM grades. |
| `data/eval/sample_pari.csv`, `data/eval/sample_parth.csv` | One human each | The sample split between two annotators, 3 queries shared. No LLM grades. |
| `data/eval/pool_t1_llm.csv` | LLM grader via the tool | `qid, chunk_id, llm_grade, batch, model, date` |
| `data/eval/qrels_t1_llm.tsv` | Tool | TREC qrels built from `pool_t1_llm.csv` |

## Procedure

1. The batch tool reads only `qid`, `query`, `chunk_id` and `text` from `pool_t1.csv`. It never shows the `grade` or `section` columns to the grader.
2. Each batch holds about 40 rows and keeps all rows of a query together. Queries in the human sample are graded first, so they are always fully LLM-graded.
3. Rows inside a batch are shuffled with seed `42:<batch number>`, so the order does not follow system rank.
4. The grader assigns exactly one grade per row, and the tool checks and appends the batch to `pool_t1_llm.csv` before the next batch starts. Grading can stop and resume at any batch.
5. After each batch, add one line to the batch log below. Record the model id exactly as `/model` shows it at grading time. Do not guess the model id.
6. The grader does not look at any human grades, and the human grader does not open `pool_t1_llm.csv` until her sample is finished.

## Grader prompt

Use this text exactly.

```
You are grading the relevance of passages from US federal regulations
(21 CFR) to search queries for a medical device and medicine labelling
project.

For each row you get a query and one passage. Give one grade:

2 = The passage states the rule that answers the query.
1 = The passage is related and useful context, but it is not the rule itself.
0 = The passage is not useful for the query.

Rules:
- Judge only the query and the passage text shown. Do not use outside
  knowledge to fill in what the passage does not say.
- Ignore section numbers and which system may have found the passage.
- A passage that uses the right words but is about a different topic is 0.
- Some queries have no answer in the corpus. For those, most passages
  should be 0. Do not raise a grade because nothing better is available.
- If you are unsure between two grades, pick the lower one.
- Grade each row on its own. Do not try to give every query at least one 2.

Output: one line per row, in the form   <row_id><TAB><grade>
using the row_id exactly as shown, with grade 0, 1 or 2, and nothing else.
```

The row id is `<qid>:<chunk_id>`, because 253 passages appear under more than one query in the pool, so a chunk id alone does not identify a row.

## Commands

```powershell
# once: create the human sample (refuses to overwrite an existing file)
python -m src.ir.llm_grade_tool sample

# each batch: write the next batch, grade it, then record it
python -m src.ir.llm_grade_tool next-batch --out <scratchpad>/batch.md
python -m src.ir.llm_grade_tool record --grades <scratchpad>/grades.tsv --model "<model id as /model shows it>"

# when done (or any time): build LLM qrels
python -m src.ir.llm_grade_tool to-qrels
```

`record` rebuilds the same next batch and refuses grades that are missing rows, add rows from outside the batch, repeat a row or use a grade other than 0, 1 or 2.

### Extra pool (Step 15 ablations)

`data/eval/pool_t1_extra.csv` holds 285 (qid, chunk) pairs, 60 queries, that the Step 15 ablation variants retrieve in their top 10 but that the LLM qrels did not judge. It has the columns qid, query, chunk_id and text only, so the grader never sees which variant retrieved a chunk. `pool_t1.csv` is never written. Same prompt, same 0/1/2 scale, same rules as above.

```powershell
# build it once (refuses to overwrite; never touches pool_t1.csv)
python -m src.ir.llm_grade_tool make-extra

# each batch: same flow with --extra. Use the SAME --max-rows for next-batch and record.
python -m src.ir.llm_grade_tool next-batch --extra --out <scratchpad>/batch.md
python -m src.ir.llm_grade_tool record --extra --grades <scratchpad>/grades.tsv --model "<model id as /model shows it>"

# afterwards: rebuild the LLM qrels
python -m src.ir.llm_grade_tool to-qrels
```

With `--extra` the grades are appended to `data/eval/pool_t1_llm.csv` (same columns, same model column), and the batch number continues after the last recorded batch, so the first extra batch is 44. Log every batch in the table below as before. The sample queries have no priority here: whole queries are batched in qid order.

### Second extra pool (ranks 11 to 20, built, NOT graded yet)

`data/eval/pool_t1_extra2.csv` holds 1247 pairs (62 queries): the unique (qid, chunk) pairs of `results/step15_unjudged_ranks11_20.csv` (1476) minus the 229 that already have an LLM grade. Same columns and rules as the first extra pool. It was built with:

```
python -m src.ir.llm_grade_tool make-extra --unjudged results/step15_unjudged_ranks11_20.csv --skip-graded --out data/eval/pool_t1_extra2.csv
# when grading: pass --pool so the tool reads this file, and use the SAME --max-rows for both calls
python -m src.ir.llm_grade_tool next-batch --extra --pool data/eval/pool_t1_extra2.csv --out <scratchpad>/batch.md
python -m src.ir.llm_grade_tool record --extra --pool data/eval/pool_t1_extra2.csv --grades <scratchpad>/grades.tsv --model "<model id as /model shows it>"
```

A dry run of `next-batch` gives batch 52 (the first batch of this pool).

## Batch log

| Batch | Rows | Queries | Model id (as `/model` shows) | Date | Notes |
|---|---|---|---|---|---|
| 1 | 40 (rows 1 to 40) | q04, q05 | claude-sonnet-5-5 | 2026-11-12 | Grades: 26 zero, 11 one, 3 two |
| 2 | 40 (rows 41 to 80) | q11, q12 | claude-sonnet-5-5 | 2026-11-12 | Grades: 28 zero, 9 one, 3 two |
| 3 | 39 (rows 81 to 119) | q21, q28 | claude-sonnet-5-5 | 2026-11-12 | Grades: 29 zero, 4 one, 6 two |
| 4 | 38 (rows 120 to 157) | q30, q31 | claude-sonnet-5-5 | 2026-11-12 | Grades: 28 zero, 9 one, 1 two |
| 5 | 22 (rows 158 to 179) | q36 | claude-sonnet-5-5 | 2026-11-12 | Grades: 16 zero, 6 one, 0 two |
| 6 | 29 (rows 180 to 208) | q40 | claude-sonnet-5-5 | 2026-11-12 | Grades: 25 zero, 4 one, 0 two |
| 7 | 24 (rows 209 to 232) | q44 | claude-sonnet-5-5 | 2026-11-12 | Grades: 24 zero, 0 one, 0 two |
| 8 | 37 (rows 233 to 269) | q46, q51 | claude-sonnet-5-5 | 2026-11-12 | Grades: 16 zero, 13 one, 8 two |
| 9 | 39 (rows 270 to 308) | q56, q60 | claude-sonnet-5-5 | 2026-11-12 | Grades: 26 zero, 6 one, 7 two |
| 10 | 23 (rows 309 to 331) | q01 | claude-sonnet-5-5 | 2026-11-12 | Grades: 16 zero, 4 one, 3 two |
| 11 | 24 (rows 332 to 355) | q02 | claude-sonnet-5-5 | 2026-11-12 | Grades: 8 zero, 14 one, 2 two |
| 12 | 40 (rows 356 to 395) | q03, q06 | claude-sonnet-5-5 | 2026-11-12 | Grades: 22 zero, 14 one, 4 two |
| 13 | 32 (rows 396 to 427) | q07, q08 | claude-sonnet-5-5 | 2026-11-12 | Grades: 22 zero, 7 one, 3 two |
| 14 | 36 (rows 428 to 463) | q09, q10 | claude-sonnet-5-5 | 2026-11-12 | Grades: 15 zero, 14 one, 7 two |
| 15 | 29 (rows 464 to 492) | q13 | claude-sonnet-5-5 | 2026-11-12 | Grades: 22 zero, 5 one, 2 two |
| 16 | 28 (rows 493 to 520) | q14 | claude-sonnet-5-5 | 2026-11-12 | Grades: 17 zero, 8 one, 3 two |
| 17 | 25 (rows 521 to 545) | q15 | claude-sonnet-5-5 | 2026-11-12 | Grades: 20 zero, 4 one, 1 two |
| 18 | 40 (rows 546 to 585) | q16, q17 | claude-sonnet-5-5 | 2026-11-12 | Grades: 24 zero, 13 one, 3 two |
| 19 | 19 (rows 586 to 604) | q18 | claude-sonnet-5-5 | 2026-11-12 | Grades: 10 zero, 6 one, 3 two |
| 20 | 24 (rows 605 to 628) | q19 | claude-sonnet-5-5 | 2026-11-12 | Grades: 19 zero, 3 one, 2 two |
| 21 | 22 (rows 629 to 650) | q20 | claude-sonnet-5-5 | 2026-11-12 | Grades: 13 zero, 7 one, 2 two |
| 22 | 22 (rows 651 to 672) | q22 | claude-sonnet-5-5 | 2026-11-12 | Grades: 18 zero, 2 one, 2 two |
| 23 | 20 (rows 673 to 692) | q23 | claude-sonnet-5-5 | 2026-11-12 | Grades: 16 zero, 2 one, 2 two |
| 24 | 28 (rows 693 to 720) | q24 | claude-sonnet-5-5 | 2026-11-12 | Grades: 26 zero, 2 one, 0 two |
| 25 | 24 (rows 721 to 744) | q25 | claude-sonnet-5-5 | 2026-11-12 | Grades: 19 zero, 3 one, 2 two |
| 26 | 37 (rows 745 to 781) | q27, q26 | claude-sonnet-5-5 | 2026-11-12 | Grades: 18 zero, 10 one, 9 two |
| 27 | 32 (rows 782 to 813) | q32, q29 | claude-sonnet-5-5 | 2026-11-12 | Grades: 20 zero, 10 one, 2 two |
| 28 | 35 (rows 814 to 848) | q34, q33 | claude-sonnet-5-5 | 2026-11-12 | Grades: 18 zero, 12 one, 5 two |
| 29 | 29 (rows 849 to 877) | q35, q37 | claude-sonnet-5-5 | 2026-11-12 | Grades: 17 zero, 10 one, 2 two |
| 30 | 24 (rows 878 to 901) | q38 | claude-sonnet-5-5 | 2026-11-12 | Grades: 18 zero, 5 one, 1 two |
| 31 | 40 (rows 902 to 941) | q39, q41 | claude-sonnet-5-5 | 2026-11-12 | Grades: 30 zero, 10 one, 0 two |
| 32 | 20 (rows 942 to 961) | q42 | claude-sonnet-5-5 | 2026-11-12 | Grades: 20 zero, 0 one, 0 two |
| 33 | 38 (rows 962 to 999) | q45, q43 | claude-sonnet-5-5 | 2026-11-12 | Grades: 36 zero, 1 one, 1 two |
| 34 | 21 (rows 1000 to 1020) | q47 | claude-sonnet-5-5 | 2026-11-12 | Grades: 12 zero, 8 one, 1 two |
| 35 | 21 (rows 1021 to 1041) | q48 | claude-sonnet-5-5 | 2026-11-12 | Grades: 17 zero, 4 one, 0 two |
| 36 | 21 (rows 1042 to 1062) | q49 | claude-sonnet-5-5 | 2026-11-12 | Grades: 14 zero, 3 one, 4 two |
| 37 | 39 (rows 1063 to 1101) | q52, q50 | claude-sonnet-5-5 | 2026-11-12 | Grades: 14 zero, 13 one, 12 two |
| 38 | 37 (rows 1102 to 1138) | q53, q54 | claude-sonnet-5-5 | 2026-11-12 | Grades: 21 zero, 6 one, 10 two |
| 39 | 27 (rows 1139 to 1165) | q55 | claude-sonnet-5-5 | 2026-11-12 | Grades: 23 zero, 2 one, 2 two |
| 40 | 36 (rows 1166 to 1201) | q57, q58 | claude-sonnet-5-5 | 2026-11-12 | Grades: 22 zero, 8 one, 6 two |
| 41 | 21 (rows 1202 to 1222) | q59 | claude-sonnet-5-5 | 2026-11-12 | Grades: 16 zero, 4 one, 1 two |
| 42 | 26 (rows 1223 to 1248) | q61 | claude-sonnet-5-5 | 2026-11-12 | Grades: 22 zero, 4 one, 0 two |
| 43 | 21 (rows 1249 to 1269) | q62 | claude-sonnet-5-5 | 2026-11-12 | Grades: 21 zero, 0 one, 0 two |
| 44 | 38 (extra rows 1 to 38) | q01, q02, q03, q04, q05, q06, q07, q08, q09, q10, q11 | claude-sonnet-5-5 | 2026-11-13 | Grades: 32 zero, 5 one, 1 two |
| 45 | 39 (extra rows 39 to 77) | q12, q13, q14, q15, q16, q17 | claude-sonnet-5-5 | 2026-11-13 | Grades: 32 zero, 7 one, 0 two |
| 46 | 35 (extra rows 78 to 112) | q18, q19, q20, q21, q22, q23 | claude-sonnet-5-5 | 2026-11-13 | Grades: 31 zero, 2 one, 2 two |
| 47 | 32 (extra rows 113 to 144) | q24, q25, q26, q27, q28, q29 | claude-sonnet-5-5 | 2026-11-13 | Grades: 28 zero, 3 one, 1 two |
| 48 | 33 (extra rows 145 to 177) | q30, q31, q32, q33, q35, q36, q37, q38, q39 | claude-sonnet-5-5 | 2026-11-13 | Grades: 30 zero, 3 one, 0 two |
| 49 | 39 (extra rows 178 to 216) | q40, q41, q42, q43, q44, q45, q46, q47 | claude-sonnet-5-5 | 2026-11-13 | Grades: 33 zero, 6 one, 0 two |
| 50 | 40 (extra rows 217 to 256) | q48, q49, q50, q51, q52, q54, q55, q56 | claude-sonnet-5-5 | 2026-11-13 | Grades: 34 zero, 4 one, 2 two |
| 51 | 29 (extra rows 257 to 285) | q57, q58, q59, q60, q61, q62 | claude-sonnet-5-5 | 2026-11-13 | Grades: 24 zero, 4 one, 1 two |
| 52 | 27 (extra2 rows 1 to 27) | q01 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 26 zero, 1 one, 0 two |
| 53 | 38 (extra2 rows 28 to 65) | q02, q03 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 35 zero, 3 one, 0 two |
| 54 | 22 (extra2 rows 66 to 87) | q04 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 21 zero, 1 one, 0 two |
| 55 | 19 (extra2 rows 88 to 106) | q05 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 19 zero, 0 one, 0 two |
| 56 | 39 (extra2 rows 107 to 145) | q06, q07 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 32 zero, 7 one, 0 two |
| 57 | 24 (extra2 rows 146 to 169) | q08 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 23 zero, 1 one, 0 two |
| 58 | 36 (extra2 rows 170 to 205) | q09, q10 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 31 zero, 4 one, 1 two |
| 59 | 39 (extra2 rows 206 to 244) | q11, q12 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 38 zero, 1 one, 0 two |
| 60 | 22 (extra2 rows 245 to 266) | q13 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 21 zero, 1 one, 0 two |
| 61 | 37 (extra2 rows 267 to 303) | q14, q15 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 28 zero, 9 one, 0 two |
| 62 | 35 (extra2 rows 304 to 338) | q16, q17 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 31 zero, 4 one, 0 two |
| 63 | 38 (extra2 rows 339 to 376) | q18, q19 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 35 zero, 2 one, 1 two |
| 64 | 36 (extra2 rows 377 to 412) | q20, q21 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 35 zero, 1 one, 0 two |
| 65 | 28 (extra2 rows 413 to 440) | q22 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 28 zero, 0 one, 0 two |
| 66 | 39 (extra2 rows 441 to 479) | q23, q24 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 38 zero, 1 one, 0 two |
| 67 | 29 (extra2 rows 480 to 508) | q25 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 24 zero, 5 one, 0 two |
| 68 | 40 (extra2 rows 509 to 548) | q26, q27 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 32 zero, 6 one, 2 two |
| 69 | 25 (extra2 rows 549 to 573) | q28, q29 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 24 zero, 1 one, 0 two |
| 70 | 26 (extra2 rows 574 to 599) | q30 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 26 zero, 0 one, 0 two |
| 71 | 33 (extra2 rows 600 to 632) | q31, q32 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 33 zero, 0 one, 0 two |
| 72 | 19 (extra2 rows 633 to 651) | q33 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 18 zero, 1 one, 0 two |
| 73 | 30 (extra2 rows 652 to 681) | q34 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 28 zero, 2 one, 0 two |
| 74 | 30 (extra2 rows 682 to 711) | q35, q36 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 28 zero, 2 one, 0 two |
| 75 | 31 (extra2 rows 712 to 742) | q37, q38 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 29 zero, 2 one, 0 two |
| 76 | 23 (extra2 rows 743 to 765) | q39 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 22 zero, 1 one, 0 two |
| 77 | 31 (extra2 rows 766 to 796) | q40, q41 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 31 zero, 0 one, 0 two |
| 78 | 38 (extra2 rows 797 to 834) | q42, q43 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 38 zero, 0 one, 0 two |
| 79 | 22 (extra2 rows 835 to 856) | q44 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 22 zero, 0 one, 0 two |
| 80 | 24 (extra2 rows 857 to 880) | q45 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 24 zero, 0 one, 0 two |
| 81 | 20 (extra2 rows 881 to 900) | q46 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 12 zero, 8 one, 0 two |
| 82 | 37 (extra2 rows 901 to 937) | q47, q48 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 32 zero, 4 one, 1 two |
| 83 | 40 (extra2 rows 938 to 977) | q49, q50 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 34 zero, 3 one, 3 two |
| 84 | 24 (extra2 rows 978 to 1001) | q51 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 20 zero, 4 one, 0 two |
| 85 | 25 (extra2 rows 1002 to 1026) | q52 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 18 zero, 5 one, 2 two |
| 86 | 37 (extra2 rows 1027 to 1063) | q53, q54 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 30 zero, 5 one, 2 two |
| 87 | 27 (extra2 rows 1064 to 1090) | q55 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 27 zero, 0 one, 0 two |
| 88 | 40 (extra2 rows 1091 to 1130) | q56, q57 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 37 zero, 2 one, 1 two |
| 89 | 25 (extra2 rows 1131 to 1155) | q58 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 25 zero, 0 one, 0 two |
| 90 | 26 (extra2 rows 1156 to 1181) | q59 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 25 zero, 1 one, 0 two |
| 91 | 19 (extra2 rows 1182 to 1200) | q60 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 17 zero, 1 one, 1 two |
| 92 | 27 (extra2 rows 1201 to 1227) | q61 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool. Grades: 25 zero, 1 one, 1 two |
| 93 | 20 (extra2 rows 1228 to 1247) | q62 | claude-sonnet-5-5 | 2026-11-14 | Second extra pool, last batch. Grades: 20 zero, 0 one, 0 two. Pool total 1247 rows: 1142 zero, 90 one, 15 two |
| 94 | 10 (extra3 rows 1 to 10) | q15, q24, q55 | claude-sonnet-5-5 | 2026-11-14 | Third extra pool (Step 17 held-out unjudged top-10 pairs, `data/eval/pool_t1_extra3.csv`). Grades: 7 zero, 3 one, 0 two |
| 95 | 40 (abstain rows 1 to 40) | ab01 | claude-sonnet-5-5 | 2026-11-14 | Abstention pool (Step 16). Grades: 35 zero, 2 one, 3 two |
| 96 | 43 (abstain rows 41 to 83) | ab02 | claude-sonnet-5-5 | 2026-11-14 | Abstention pool (Step 16). Grades: 37 zero, 5 one, 1 two |
| 97 | 36 (abstain rows 84 to 119) | ab03 | claude-sonnet-5-5 | 2026-11-14 | Abstention pool (Step 16). Grades: 34 zero, 0 one, 2 two |
| 98 | 35 (abstain rows 120 to 154) | ab04 | claude-sonnet-5-5 | 2026-11-14 | Abstention pool (Step 16). Grades: 18 zero, 15 one, 2 two |
| 99 | 44 (abstain rows 155 to 198) | ab05 | claude-sonnet-5-5 | 2026-11-14 | Abstention pool (Step 16). Grades: 42 zero, 1 one, 1 two |
| 100 | 36 (abstain rows 199 to 234) | ab06 | claude-sonnet-5-5 | 2026-11-14 | Abstention pool (Step 16). Grades: 31 zero, 4 one, 1 two |
| 101 | 35 (abstain rows 235 to 269) | ab07 | claude-sonnet-5-5 | 2026-11-14 | Abstention pool (Step 16). Grades: 32 zero, 1 one, 2 two |
| 102 | 29 (abstain rows 270 to 298) | ab08 | claude-sonnet-5-5 | 2026-11-14 | Abstention pool (Step 16). Grades: 26 zero, 2 one, 1 two |
| 103 | 33 (abstain rows 299 to 331) | ab09 | claude-sonnet-5-5 | 2026-11-14 | Abstention pool (Step 16). Grades: 24 zero, 4 one, 5 two |
| 104 | 43 (abstain rows 332 to 374) | ab10 | claude-sonnet-5-5 | 2026-11-14 | Abstention pool (Step 16). Grades: 41 zero, 0 one, 2 two |
| 105 | 43 (abstain rows 375 to 417) | ab11 | claude-sonnet-5-5 | 2026-11-14 | Abstention pool (Step 16). Grades: 43 zero, 0 one, 0 two |
| 106 | 39 (abstain rows 418 to 456) | ab12 | claude-sonnet-5-5 | 2026-11-14 | Abstention pool (Step 16). Grades: 38 zero, 1 one, 0 two |
| 107 | 43 (abstain rows 457 to 499) | ab13 | claude-sonnet-5-5 | 2026-11-14 | Abstention pool (Step 16). Grades: 42 zero, 1 one, 0 two |
| 108 | 44 (abstain rows 500 to 543) | ab14 | claude-sonnet-5-5 | 2026-11-14 | Abstention pool (Step 16). Grades: 44 zero, 0 one, 0 two |
| 109 | 40 (abstain rows 544 to 583) | ab15 | claude-sonnet-5-5 | 2026-11-14 | Abstention pool (Step 16). Grades: 38 zero, 2 one, 0 two |
| 110 | 45 (abstain rows 584 to 628) | ab16 | claude-sonnet-5-5 | 2026-11-14 | Abstention pool (Step 16). Grades: 45 zero, 0 one, 0 two |
| 111 | 45 (abstain rows 629 to 673) | ab17 | claude-sonnet-5-5 | 2026-11-14 | Abstention pool (Step 16). Grades: 42 zero, 3 one, 0 two |
| 112 | 33 (abstain rows 674 to 706) | ab18 | claude-sonnet-5-5 | 2026-11-14 | Abstention pool (Step 16). Grades: 32 zero, 1 one, 0 two |
| 113 | 40 (abstain rows 707 to 746) | ab19 | claude-sonnet-5-5 | 2026-11-14 | Abstention pool (Step 16). Grades: 38 zero, 2 one, 0 two |
| 114 | 42 (abstain rows 747 to 788) | ab20 | claude-sonnet-5-5 | 2026-11-14 | Abstention pool (Step 16). Grades: 40 zero, 2 one, 0 two. Pool total 788 rows: 722 zero, 46 one, 20 two |
