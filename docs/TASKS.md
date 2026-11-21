# Task checklist

State of `main` at the v1.0 release check (Step 26). Step numbers match `CLAUDE.md` and `docs/LEARNING_LOG.md`. Every relevance grade here is an LLM grade (claude-sonnet-5-5) except the 308-row human validation sample (see `docs/LLM_GRADER_PROMPT.md`). The honest limits are listed in `README.md` under "Known limits".

## Done and merged into main
- [x] Steps 1 to 10: own index, TF-IDF, BM25, dense (BGE and FAISS), hybrid RRF, metrics, eval harness, eCFR crawler, 903 chunks, qrels tooling
- [x] Steps 11 to 15: LLM-assessed qrels, human validation sample and agreement (Step 13), results and by-type tables, failures, intervals (Step 14), ablations and depth-20 grading (Step 15)
- [x] Step 16 abstention evaluation (medicine), Steps 17 and 18 retrieval experiments (held-out and fresh set, reported honestly; no further tuning on held-out)
- [x] CV: extractor modes, OCR, barcode (`results/cv_final_eval.md`), CV2 (`reports/parth_cv2.md`), CV3 gated GS1 prefill (`reports/cv3.md`), symbol detector v2 (`reports/symbols_final.md`, not trusted)
- [x] Step 19: data model, template spec, OpenAPI (39 operations), API guide, 13 screens, 50 mocks, contract tests
- [x] Step 20: SQLite store, append-only tables, derived status, review rules, role checks
- [x] Step 21: checker (16 rules, cited evidence, `docs/CHECKER_SPEC.md`)
- [x] Step 22: change assessment (parser rules, impact, barcode decision, confirmation)
- [x] Step 23: RAG (scope rule, score gate, extractive default, optional AI answer); selection mode merged but off (`reports/rag_select.md`), MiniLM sentence reranker is the default extractive display (`reports/rag_rerank.md`)
- [x] Step 24: upload and photo-quality gate, generate artwork with Parth's renderer, DRAFT mark, approval bound to the PDF hash and a passed check, optional AI answer job
- [x] Step 25: demo PC (`scripts/run_demo.py`, `scripts/demo_e2e.py`), publish, public medicine mode (30 DailyMed products), print verification (API and template mode)
- [x] Static UI wired to the real API in api mode (`ui/`, `ui/tools/`)
- [x] Step 26: release check from a fresh clone, `docs/DEMO_SCRIPT.md`, tag v1.0

## Not done, by design or by time (see README "Known limits")
- [ ] Real-photo extraction: product name 0/10 on the CV3 real photos, lot 5/7, expiry 7/8
- [ ] Print verification on real print photos (only simulated photos measured)
- [ ] Symbols measured on real photos (detector not trusted, symbol checks need a human)
- [ ] Stronger abstention for the public medicine mode (no score meets the pre-declared targets on the test split)
- [ ] Faster AI answer (about 38 s median on CPU); reranked extractive sentences stay the default (hit 9/15 vs 8/15 held-out, a one-query gap)
- [ ] D7 screen draws no citation box for review findings (the API result has them)
- [ ] Larger medicine corpus (30 products now) and non-US sources
- [ ] Approved (non-DRAFT) export variant; templates with a background image (D-5)
- [ ] Template registration beyond shape and layout checks
- [ ] Multi-side scan (the public scan entry `publicScan` is still a mock)
- [ ] Human grades for more than the 308-row sample
- [ ] Open contract items: D-3, D-5, D-6, D-9 and the remaining D-7 kind names in `docs/contracts/SCHEMA_CHANGE_REQUESTS.md`
- [ ] Report, slides, rehearsal (course deliverables)

## Possible v1.1
- [ ] Real print photos and a real-photo extraction set with human references
- [ ] Hosted publishing instead of the local server
