# Step 21b report: checker rules and injected-error evaluation

**1. What I did.** Built `src/checker/` (16 rules, citations by fixed query plus accepted section, one retrieval setting, own GS1 parser) and an evaluation tool. Labels come from the existing generator hooks, 5 error kinds plus clean, in three photo conditions, with two record-side kinds (wrong UDI-DI, missing Rx) reusing the clean image. Rules and queries were frozen by commit 0ae33df, then seeds 300 to 302 were run once.

**2. Files.** `src/checker/{settings,gs1,retrieval,citations,models,runner,synthetic,eval_injected}.py`; tests `test_checker_{gs1,citations,rules,eval}.py`; `results/step21_checker_dev.md` and `results/step21_checker_final.md`.

**3. How it works.** Each rule returns pass, fail, needs_human, not_applicable or not_checked. A flag cites the first top-10 hit from its accepted section, with a quote asserted to be a substring of the chunk. Symbols are needs_human in both directions (detector untrusted).

**4. How I verified it.** `python -m pytest -q -m "not slow"` gave 354 passed, 3 skipped, 3 deselected; the 2 slow hybrid tests passed; ruff clean. Final run (51 base labels, 765 images, hybrid RRF), per condition clean/moderate/hard, n=51 per cell, Wilson 95%:
- Recall on injected errors: 51/51 [0.93, 1.00] in every cell, template and blind, except blind hard wrong_name confident recall 50/51 (one flagged needs_human after an OCR misread).
- Precision: 51/51 everywhere, except blind hard wrong_name 51/52 [0.90, 1.00] (that same kind of OCR misread, needs_human).
- False alarm on clean labels: 0/51 [0.00, 0.07] per condition and per rule, both layers.
- Missing symbol and missing Rx: flagged 51/51 but 0/51 confident, by design.
- Citations: finding has a citation 1.00 per rule (n 72 to 153 each, lower bound 0.95 to 0.98); quote verbatim in all; accepted section is rank 1 for hybrid except S-MFR and S-EXP rank 2.

**5. Check yourself.** (a) `_check_date_format` precedence over B-EXP. (b) `_ais` in `eval_injected.py`. (c) Dev report versus final report.

**6. Unsure or assumed.** Results are saturated: synthetic errors are easy, one template family, symbol detector in-distribution. Rules B-GS1, B-READ, P-MFR, P-ADDR, R-NAMEPLACE, R-UDI, X-HEALTH raised no findings in the evaluation and are covered only by unit tests. Citation hit@10 is 1.00 because the queries are fixed, so it measures the queries, not label content. The record-side UDI-DI value is a test constant, not an allocated identifier. A confusable 0/O misprint remains invisible. CV libraries live in `.venv-cv` (git-ignored), created with your approval.
