# Step 23 report (23a to 23d)

**Headline: the language models did not work.** In the frozen run no generated answer passed verification, for qwen2.5 1.5b (primary) or 3b: answered 0/27 public and 0/20 professional, 0/10 and 0/4 wrong answers (upper bounds 0.28, 0.49). Both returned bare numbers such as `[1][3]` or put them before the sentence. Faithfulness was **not measured** (nothing to grade), so the 20 percent second-pass re-grade is empty. No grades of any kind were made.

**Run findings.** The run exposed two verifier holes: a marker-only sentence and `NO_ANSWER [1]` counted as answers (run 1 showed 14 and 34 "answered"). I fixed them, added tests and recomputed from stored model text (deterministic; run 1 kept as `step23_run1_*`). Two prompt variants failed a six-query dev check, so I stopped tuning; v1 stays.

**What works.** Scope rule 10/10 on advice queries, 0 false triggers on 61. Score gate (0.0315, dev half): all no_answer queries unanswered. Extractive mode (default): 58/75 public and 27/51 device shown passages have LLM qrels grade >= 1, 0.3 s.

**Speed (this CPU).** 3b: 34 to 39 s uncached, median 29 to 33 s in the run, fails my 30 s rule; 1.5b: median 16 to 17 s. Primary was 1.5b by that rule.

**Choices.** Provider default off. Threshold on dev half only. Score below threshold reports `needs_human_check`. q41 to q44 included. CR-18 and CR-19 were additive, so approved. Second-pass re-grade replaced human check (empty).

**Shared indexes (your request).** `src/rag/indexes.py` plus `python scripts/build_indexes.py` keep bge-large and bge-small caches in `data/cache/indexes` of the main checkout (git-ignored, named by model and corpus hash, never overwritten or rebuilt on a match; `LABELLENS_INDEX_DIR` overrides). I did it by copying into `data/processed`, so `src/ir` is untouched. `--check` reports 8 of 8 present.

**Caveats.** Queries are not fresh (used in earlier abstention work and E5b selection), LLM grades only, 0 of 71 queries reach the model with a usable format. Tests: 503 passed, ruff clean. CI: not checked, `gh` is not logged in here.

**Not done.** A model that follows the format (larger, or JSON output with a new verifier contract) needs a new frozen run. Not merged.
