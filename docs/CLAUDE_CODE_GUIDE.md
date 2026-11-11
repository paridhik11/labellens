# Using Claude Code on this project

## Start (PowerShell)
```powershell
cd C:\Users\parid\Downloads\labellens\labellens
.venv312\Scripts\Activate.ps1
claude
```
If `claude` is not recognised, add `C:\Users\parid\.local\bin` to PATH (see the chat notes) or run it by full path.

First message of a new session:
```
Read CLAUDE.md and docs/TEAM_PLAN.md. Run git status, git log --oneline -5 and python --version. Tell me in 5 lines where we are and what the next step is. Do not change anything yet.
```

## Daily routine
1. Pull, activate the venv, start `claude`, send the first message above.
2. Press Shift+Tab to plan mode. Ask for the next step. Read the plan. Approve or correct.
3. One step per session. Answer the two quiz questions in your own words before saying "continue".
4. At the end: ask it to update "Current state" in CLAUDE.md, commit, push, check CI.
5. `/clear` between steps. `/compact` if a long session must continue.

## Getting the most from a Pro plan
- Plan mode first, so wrong edits do not burn usage.
- Name the file, the command and the expected output in every prompt.
- Use `-m "not slow"` for tests. The real embedding model test takes about 2 minutes.
- Check `/usage` before a big step. Use `/model` to pick a lighter model for routine edits and the strongest one only for design questions.
- Keep `CLAUDE.md` short and current. Do not repeat project background in prompts.
- Use the claude.ai chat for review and thinking. Paste Claude Code's step report there for a second opinion.
- Commit after every step so a hit limit loses nothing.

## Prompts

### Step 10b: queries and no_answer handling
```
Step 10b. Check data/eval/queries_t1.tsv has 62 rows (qid, query, module, type). Run python -m src.ir.qrels_tool pool and report pooled rows per module. Change eval.py so queries of type no_answer are excluded from the main averages and reported in a separate table. Do not fill any grades. Add tests, commit and push. Plan first.
```

### Step 11: first real results (after you graded)
```
Step 11. I finished grading data/eval/pool_t1.csv for the device queries. Run to-qrels, then eval with --module device and --section-level for tfidf, bm25, dense, hybrid. Show chunk-level and section-level tables with p-values against bm25, the number of unjudged results returned per system, and the 5 queries where hybrid did worst versus bm25. Do not interpret beyond what the numbers show. Plan first.
```

### Step 12: ablations
```
Step 12. Add ablation runs: RRF k in 10, 30, 60, 100; fusion weights; BM25 with light stemming; BGE query prefix on and off; chunk size 128, 200, 300 (rebuild and re-pool only if needed, tell me the cost first). Output one markdown table per ablation to results/. Plan first.
```

### Step 13: corpus expansion
```
Step 13. Plan how to add openFDA device and drug label text, one or two FDA labeling guidance documents and the EU MDR labeling annex. For each source check the licence and robots rules and use official APIs. Do not crawl until I approve the plan. New chunks must keep module and source fields.
```

### Step 14: query expansion and LTR
```
Step 14. Implement field-aware query building and a regulatory synonym list (data/eval/synonyms.json) as a retrieval variant, and a LightGBM LambdaMART ranker for T2 product matching with a hand-tuned weights baseline. Evaluate both against the existing systems. Plan first.
```

### Step 15: checker, data model, template spec, API contract
```
Step 15. Implement the checker that produces Flag objects with evidence from T1 retrieval, add the template spec schema from docs/GENERATION.md to src/common/schemas.py (I approve this change), finalise docs/API_CONTRACT.md and create ui/mock/*.json files that match it. Plan first.
```

### Step 16 onward
Relevance feedback, change parser, T3 impact retrieval, RAG with citation check, template registration, approval flow and database, public mode, PDF report: one prompt each, in the order of `docs/TEAM_PLAN.md`. Parth and Ishanvi use the same routine with their own tasks from Day 6.
