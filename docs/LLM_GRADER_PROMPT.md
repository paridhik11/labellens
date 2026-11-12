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
