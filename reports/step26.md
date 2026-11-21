# Step 26: release check (v1.0)

Fresh clone of origin/main, new Python 3.12 venv from `requirements-demo.txt`, re-run on c4ac3d9 (ui-restore) and 36fc6d5 (rag-rerank).

- `run_demo.py` and `demo_e2e.py`: 20/20 PASS, no mock, no fallback. UI tools: golden 9/9, live flows 13, 0 FAIL; screens 61 states, 0 failed (mock and api).
- Fast suite 973 passed, 7 skipped; `ruff check src tests` clean.
- Manual steps: `LABELLENS_INDEX_DIR` set to the existing store; medicine-reference index built once (about 25 min CPU); Playwright taken from an earlier session's folder.
- One fix, 3 lines: `run_demo.py` now caches the MiniLM reranker.
- Gap, not fixed: D7 lists the cited B-LOT finding without drawing its citation (API result has it).
- Limits: see README "Known limits".
