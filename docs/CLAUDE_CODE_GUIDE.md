# Using Claude Code on this project

## Start (PowerShell)
```powershell
cd C:\Users\parid\Downloads\labellens\labellens
.venv312\Scripts\Activate.ps1
claude
```
If `claude` is not recognised, add `C:\Users\parid\.local\bin` to PATH or run it by full path.

First message of a new session:
```
Read CLAUDE.md and docs/TEAM_PLAN.md. Run git status, git branch and python --version. Tell me in 5 lines where we are and what the next step is. Do not change anything yet.
```

## Daily routine
1. Pull, activate the venv, start `claude`, send the first message above.
2. Press Shift+Tab to plan mode. Ask for the next step. Read the plan. Approve or correct.
3. One step per session. Read the Step Report (six items, no quiz). Say "continue" when you understand it.
4. At the end: ask it to update "Current state" in CLAUDE.md and append to `docs/LEARNING_LOG.md`, then commit `step N: short description`, push, check CI.
5. `/clear` between steps. `/compact` if a long session must continue.

## Rules that matter
- Docs-only tasks touch nothing under `src/`, `tests/` or `data/`. Say so in the prompt.
- Work on a branch, never force push. Several branches are checked out in separate worktrees (`step17-opt`, `cv-fixes`), so create new branches from `origin/main` and check `git branch` first.
- Do not edit `src/common/schemas.py`, `src/ir/base.py` or anything in `docs/contracts/` without asking.
- Relevance grades: the qrels are LLM-assessed (separate `_llm` files, logged in `docs/LLM_GRADER_PROMPT.md`). The agent never writes the human `grade` column or `data/eval/pool_t1.csv`.
- Label artwork comes from templates, never an image model. Never invent GTIN or UDI-DI values.
- No em dashes in docs or comments. No Co-Authored-By or Generated-with lines in commits.

## Getting the most from a Pro plan
- Plan mode first, so wrong edits do not burn usage.
- Name the file, the command and the expected output in every prompt.
- Use `-m "not slow"` for tests. The real embedding model test takes about 2 minutes.
- Check `/usage` before a big step. Use `/model` to pick a lighter model for routine edits and the strongest one only for design questions.
- Keep `CLAUDE.md` short and current. Do not repeat project background in prompts.
- Use the claude.ai chat for review and thinking. Paste Claude Code's step report there for a second opinion.
- Commit after every step so a hit limit loses nothing.

## Where the project is and what to ask next

| Track | Status | Next prompt |
|---|---|---|
| Retrieval Steps 16 to 18 | Step 16 abstention, Steps 17 and 18 experiments exist on branches, not merged | Review the branch results, then merge. Do not tune on the held-out half |
| CV fixes | Merged | Parth continues from `docs/CV_STATUS.md` |
| Step 19 contracts | Merged | Review CR-1 to CR-16 |
| Step 20 backend | Merged into main (6e36e47) | Layout findings on template registration, change parser, impact analysis |

## Prompts

### Step 20b: endpoints
```
Step 20b on branch step20-backend. Read docs/contracts/openapi.yaml, API.md and DATA_MODEL.md. Implement the endpoints for products, templates and label versions in src/api on top of the existing store, following the contract exactly. POST /changes returns "parser": "not_implemented" for now (change the contract and mocks to say so). Add tests per endpoint. Do not touch src/cv, src/gen or src/ir. Plan first, then stop after the step report.
```

### Step 20c and 20d: mock fallback and response tests
```
Step 20c: add the X-Mock header that serves the matching file from src/api/mock/ (index.json lists them). Step 20d: add tests that validate real responses against openapi.yaml. Plan first, one step at a time.
```

### Checker with evidence
```
Implement the checker that produces Finding objects (observed, expected, evidence, severity, confidence, needs_human) from T1 retrieval, matching DATA_MODEL.md. Weak evidence becomes needs_human, never a guess. Do not change src/common/schemas.py without asking me. Plan first.
```

### Change parser and impact
```
Implement the natural-language change parser (proposes a structured change that the user confirms) and T3 change impact retrieval. Then wire POST /changes to them. Evaluate T3 with a small rerunnable command and paste the real output. Plan first.
```

### RAG with citations
```
Implement the cited-answer module for the public mode: answers use only retrieved passages, every claim carries a passage id, and weak evidence returns an AbstainedAnswer with one of the four reasons in openapi.yaml. Keep medicine and device data separate. Plan first.
```

### Generate, review and approve
```
Wire the generate endpoint (202 Job) to the renderer in src/gen, then the review endpoints. Every draft carries the DRAFT mark. Approval needs artifact_sha256 and a passed check_id. Never invent GTIN or UDI-DI, raise IdentifierRequired. Plan first.
```

### Public mode, template registration, PDF report
One prompt each, in the order of `docs/TEAM_PLAN.md` "v1 build order". Parth and Ishanvi use the same routine with their own tasks from Day 6 (see `docs/TASKS.md`).
