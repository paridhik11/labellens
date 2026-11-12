# CLAUDE.md for LabelLens

LabelLens is a CSD358 Information Retrieval course project (30% of coursework). IR is the core: retrieval, evaluation and analysis matter more than UI or CV polish. Read README.md, docs/PRODUCT_SPEC.md, docs/GENERATION.md and docs/TEAM_PLAN.md for the full picture.

@AGENTS.md

If AGENTS.md and this file disagree, this file wins.

## What we are building
A website for medical device label teams. Workflow: upload or scan, extract, retrieve evidence, check the label, assess changes, generate updated artwork in the existing editable template, review and approve, download a PDF at physical size, verify the printed label. A smaller public mode explains medication packaging with cited answers. The professional workspace is the main project.

## About the user
Pari is a third-year CSE student and the project lead, doing most of the work. New to OpenCV and still learning IR. She must understand and be able to explain every change, so go slowly and teach as you build. Windows with PowerShell. Parth (CV, template engine, print verification) and Ishanvi (a few static UI pages) join on Day 6. Do not assign them work before then.

## Environment
- Use the Python 3.12 venv at `.venv312`. Activate with `.venv312\Scripts\Activate.ps1` and confirm `python --version` shows 3.12 before running anything.
- Run Python as `python -m ...` from the repo root (the folder containing `src/`).
- Fast tests: `python -m pytest -q -m "not slow"`. Lint: `ruff check src tests`.
- Never commit `.venv*`, `.env`, `data/raw/`, embedding caches (`data/processed/dense_cache_*`) or `__pycache__`.
- Whenever you add a dependency, add it to requirements.txt in the same step and say which package and why.

## Working agreement
Start every task in plan mode: propose the plan (files to touch, steps, how to verify) and wait for approval. Work in numbered steps, ONE at a time. After each step, STOP and wait for the user to say "continue".

After EVERY step give a Step Report:
1. What I did (plain English, 3 to 5 sentences, define jargon)
2. Files created or changed (one line reason each)
3. How it works (tiny worked example or analogy)
4. How I verified it (exact command and the REAL pasted output)
5. What you should check yourself (2 or 3 specific things in the diff)
6. What I am unsure about or assumed
No quiz questions.
Also append a shortened version to docs/LEARNING_LOG.md.

Rules:
- Never invent data, URLs, endpoints, relevance grades or results. If unsure, check official docs. Report failures plainly.
- Do not start the next step or write code for later steps before the user says "continue".
- Do not change src/common/schemas.py or src/ir/base.py without asking.
- Keep changes small and targeted. No unrelated refactors.
- Run tests yourself and paste real output.
- Do not use em dashes in docs or comments.
- Check repo state (git status, counts) before stating it.
- Human relevance grades are made only by humans. The agent never writes to the human `grade` column, to `data/eval/pool_t1.csv` or to the human sample file.
- LLM relevance grades are allowed only in separate files labelled `_llm` (for example `data/eval/pool_t1_llm.csv`, `data/eval/qrels_t1_llm.tsv`). They follow `docs/LLM_GRADER_PROMPT.md` exactly, and every batch is logged there with the model id as `/model` shows it at grading time. Never present LLM grades as human grades.
- Label artwork is generated from templates, never by an image generation model. Never invent GTIN or UDI-DI values, raise `IdentifierRequired` instead. Every generated label carries a DRAFT mark until approved, and nothing is published without an approval record.
- Keep the public medicine module and professional device module separate in data, rules and results.
- No Co-Authored-By, Claude-Session or Generated-with lines in any commit message or PR description.

## Git rules
1. Start by showing `git status`, `git remote -v`, `git branch`. Remote: https://github.com/paridhik11/labellens.
2. After each approved step make ONE commit named `step N: short description`, then push.
3. Show `git status` (files to be committed) before every commit. Stop and ask if anything unexpected is staged.
4. Never force push, rewrite history or change the remote.
5. After pushing show `git log --oneline -5`. If a push fails, report the exact error.
6. Check the GitHub Actions run after pushing and say if CI is red.

## Current state (update at the end of each step)
- Steps 1 to 10 done and pushed (built with Antigravity): eCFR crawler (11 CFR parts), chunker (min 5 words), 903 chunks (435 device, 468 medicine), own BM25 and TF-IDF, dense retrieval (BAAI/bge-small-en-v1.5 and FAISS, cached by content hash), hybrid RRF, metrics, eval harness (--module, --no-dense, --section-level), qrels tooling (pool, to-qrels, kappa).
- 62 queries (`data/eval/queries_t1.tsv`: qid, query, module, type; 44 device, 18 medicine, 5 no_answer) fully pooled in `data/eval/pool_t1.csv` (1269 rows: 908 device, 361 medicine). No qrels graded yet, so no real results table yet.
- Step 10b done: eval leaves no_answer queries and corpus gaps (answerable, no doc graded >= 1) out of the main averages and reports them separately; table headers show the query count.
- Step 11a done: LLM grading allowed in separate `_llm` files only; grader prompt and batch log in `docs/LLM_GRADER_PROMPT.md`.
- Step 11b done: `src/ir/llm_grade_tool.py` (sample, next-batch, record, to-qrels), rows identified as `qid:chunk_id`.
- Step 11c done: human sample `data/eval/pool_t1_human_sample.csv`, 308 rows, 15 queries (seed 42; 4 direct, 4 field_req, 3 vocab_mismatch, 2 change_impact, 1 symbol, 1 no_answer; 11 device, 4 medicine).
- Sample split for two annotators (`llm_grade_tool split`, seed 42): `data/eval/sample_pari.csv` (9 queries, 182 rows) and `data/eval/sample_parth.csv` (9 queries, 195 rows), shared q05, q44, q46 (69 rows) for human kappa. Parth grades his file from Day 6.
- Step 12 done: all 43 LLM batches graded (model claude-sonnet-5-5), 1269/1269 rows in `data/eval/pool_t1_llm.csv` (0/1/2 = 864/280/125; device 627/208/73, medicine 237/72/52).
- Human sample graded: `data/eval/sample_pari.csv` (182 rows) and `data/eval/sample_parth.csv` (195 rows, Parth confirmed human), 308 unique rows, 69 shared. Parth's branch merged into main.
- Step 13 done: `src/ir/grade_compare.py`, tracked report `results/step13_llm_vs_human.md`. Pari-only LLM vs human weighted kappa 0.746 linear / 0.823 quadratic, binary agreement 0.879 (all 308 rows: 0.675 / 0.768 / 0.825). The LLM is stricter than humans (52 of 103 human-1 rows got LLM 0). Hybrid ranks first under both graders; dense is the only system that falls in nDCG@10 pooled and for device, but all four fall for medicine (4 queries), and no pooled bootstrap interval excludes 0.
- Docs updated for the template-based workflow (README, PRODUCT_SPEC, GENERATION, WORKFLOW, EVALUATION, TEAM_PLAN, TASKS, API_CONTRACT, QRELS_GUIDE, CLAUDE_CODE_GUIDE).
- Open issues: corpus lacks symbols and non-US sources.

## Next steps (see docs/TEAM_PLAN.md for the day plan)
1. Decide how to use the LLM grades for the 47 queries without human grades (they are stricter than humans at the 0/1 boundary).
2. First real results table on the full qrels, with the caveat from Step 13.
3. Ablations, corpus expansion, query expansion, LTR.
4. Checker, data model, template spec, API contract, mock JSON, basic synthetic generator.
