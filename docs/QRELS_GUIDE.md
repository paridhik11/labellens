# Qrels Grading Guide

This guide explains how to grade pooled candidate chunks in `data/eval/pool_t1.csv` to create the evaluation qrels (`data/eval/qrels_t1.tsv`).

## Grading Rubric

- **2**: The passage states the rule that answers the query.
- **1**: Related and useful context, but not the rule itself.
- **0**: Not useful for the query.

Grade the passage text only, and do not think about which system found it. Leave blank only for queries you have not graded yet (in a later session).

## Workload and Sessions

62 queries at roughly 18 candidates each is roughly 1,100 rows (about 6 to 10 hours of grading).

- If that is too much in one go, grade the **device queries first** (`q01` through `q44`, 44 queries) and the **medicine queries later** (`q45` through `q62`, 18 queries).
- Do not shrink the candidate pool, because keeping the full 4-system top-10 pool is what keeps the comparison across TF-IDF, BM25, Dense, and Hybrid fair.
- Work in sessions of about **15 queries** at a time (for example: Session 1 `q01`-`q15`, Session 2 `q16`-`q30`, Session 3 `q31`-`q44`, Session 4 `q45`-`q62`).

## Workflow Commands

### 1. Generate or refresh the pool CSV

```powershell
.\.venv312\Scripts\Activate.ps1
python -m src.ir.qrels_tool pool --queries data/eval/queries_t1.tsv --out data/eval/pool_t1.csv
```

Open `data/eval/pool_t1.csv` and fill the `grade` column with `0`, `1`, or `2` for each chunk in your current session.

### 2. Convert graded rows to TREC qrels

Rows with an empty `grade` are skipped automatically unless `--strict` is passed, so you can run evaluation right after Session 1:

```powershell
python -m src.ir.qrels_tool to-qrels --csv data/eval/pool_t1.csv --out data/eval/qrels_t1.tsv
```

### 3. Run device evaluation (chunk-level and section-level)

```powershell
python -m src.ir.eval --corpus data/processed/regs.jsonl --queries data/eval/queries_t1.tsv --qrels data/eval/qrels_t1.tsv --module device --section-level --out results/t1_device.md
```

### 4. Check inter-annotator agreement (when comparing two graded CSVs)

```powershell
python -m src.ir.qrels_tool kappa data/eval/pool_t1_a.csv data/eval/pool_t1_b.csv
```
