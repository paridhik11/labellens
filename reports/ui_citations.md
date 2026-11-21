# ui-citations: D7 draws finding citations

Change: `ui/js/render-d7.js` draws each finding's citations (section, title, verbatim quote, link) in the same box as D4,
and marks findings with `data-testid="finding"` and `data-rule`. `docs/DEMO_SCRIPT.md` no longer sends the demo to `/docs`;
the matching item in `docs/TASKS.md` is ticked.

## Checks (all in the ui-citations worktree, one run each)
- `check_screens.cjs` mock mode: 61 states, 0 failed; 11 click-throughs, 0 failed (includes the new
  "D7 draws each finding citation" flow, pass).
- `check_screens.cjs` api mode (demo API on port 8011): 61 states, 0 failed; 11 click-throughs, 0 failed; the new flow passes;
  11 expected 404/409/422/503 fallbacks ignored by the script's own rule.
- `live_flows.cjs` with the golden package: 13 flows, 0 FAIL, e2e 9/9 stages.
- Live B-LOT: the recheck stage found `[data-rule="B-LOT"]` with a citation containing 801.40 and a quoted text of 20+ characters
  ("B-LOT citation drawn (801.40 with quote)"). The assertion was not weakened. The earlier "check" stage shows 0 citations
  for the original upload (1 finding), which is unchanged behavior.
- Fast suite: 931 passed, 8 skipped, 5 deselected. `ruff check src tests`: clean.

## Decisions and notes
- The mock-mode assertion renders a synthetic result built inside the script (no D7 mock has citations); no mock file was added.
- The live assertion checks section 801.40 and a quote, not exact quote text, so retrieval changes do not break it.
- To run the live check I installed the pinned demo packages missing from `.venv312` (opencv-python, zxing-cpp,
  rapidocr-onnxruntime, onnxruntime, reportlab; versions from `requirements-demo.txt`). No requirements file changed.
- `run_demo.py` copied the dense caches into the worktree `data/processed` (git-ignored).
- Merged in a separate worktree (`labellens-merge`), not the main checkout, after fetching: origin/main was already contained.
  Local `main` in the main checkout is still behind origin/main and was not touched.

## Result
Merge commit e855e15 on main, pushed. CI run for e855e15: completed, success (GitHub API).
