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
| | | | | | No batches graded yet |
