# Task checklist

Tick items as they are done. Step numbers match `CLAUDE.md` and `docs/LEARNING_LOG.md`; days match `docs/TEAM_PLAN.md`. Human relevance grades are not a task here: the qrels are LLM-assessed with a graded human validation sample (see `docs/LLM_GRADER_PROMPT.md`).

## Done
- [x] Steps 1 to 10: own index, TF-IDF, BM25, dense (BGE and FAISS), hybrid RRF, metrics, eval harness, eCFR crawler, 903 chunks, qrels tooling
- [x] Steps 11 to 15: LLM-assessed qrels, human validation sample and agreement (Step 13), results and by-type tables, failures, intervals (Step 14), ablations and depth-20 grading (Step 15)
- [x] CV fixes (merged): extractor modes, OCR, barcode, fresh-seed evaluation in `results/cv_final_eval.md`
- [x] Step 19 (merged): data model, template spec, OpenAPI, API guide, 13 screens, 50 mocks, contract tests

## Pari
Retrieval
- [x] Step 16 abstention evaluation for the medicine mode (branch `step16-abstain`, not merged)
- [ ] Steps 17 and 18 retrieval experiments (branch `step17-opt`, not merged): report honestly, no further tuning on the held-out half
- [ ] Decide how to use the LLM grades for queries without human grades; first full results table with the Step 13 caveat
- [ ] Merge the retrieval branches into main once reviewed

Backend (Step 20, branch `step20-backend`, not merged)
- [x] Phase 0: contract follows the merged renderer (D-2, D-4, D-8, part of D-7)
- [x] 20a: SQLite store, append-only triggers, derived status, review rules, 20 tests
- [ ] 20b: endpoints from `openapi.yaml` (`POST /changes` returns `"parser": "not_implemented"` until the parser exists)
- [ ] 20c: mock fallback with the `X-Mock` header
- [ ] 20d: OpenAPI response tests

Product features (v1 build order, see `docs/TEAM_PLAN.md`)
- [ ] Checker with evidence (Flag objects from T1 retrieval)
- [ ] Natural-language change parser, T3 change impact retrieval
- [ ] RAG with citation check and the abstain rule
- [ ] Generate endpoint wired to Parth's renderer, DRAFT mark, self-check
- [ ] Review and approval flow (approval bound to `artifact_sha256` and a passed `check_id`, new version voids it, reject is terminal)
- [ ] Template registration flow (draw and name slots)
- [ ] Public medicine mode (small), PDF inspection report
- [ ] Decide the open contract items: remaining D-7 kind names, CR-1 to CR-16
- [ ] Feature freeze, integration, final retrieval numbers, tag release
- [ ] Report, slides, rehearsal

## Parth (from Day 6)
- [ ] Review CR-1 to CR-16 marked "touches Parth" in `docs/contracts/SCHEMA_CHANGE_REQUESTS.md`
- [ ] Align the renderer and approval record to the contract: D-3 (background), D-5 (one `artifact_sha256`), D-6 (approval record names, `check_id`), D-9 (named SVG groups)
- [ ] Layout finding kind names (rest of D-7)
- [ ] Template rendering engine against `docs/contracts/TEMPLATE_SPEC.md` (slots to SVG to PDF at physical size)
- [ ] Conditional GS1 barcode (KEEP, REGENERATE, NEEDS_INPUT), layout checks, self-check loop
- [ ] `extract_label` OCR and barcode decode, report per condition (clean, scan, photo)
- [ ] Print verification (`verify_print`), final CV and generation numbers
- [ ] Report chapter

## Ishanvi (from Day 6, small tasks only)
Build from `src/api/mock/` only, using `docs/contracts/SCREENS.md` for states.
- [ ] Scan and Understand page (public, P1 and P2)
- [ ] Inspect page layout (professional, with the DRAFT mark and signed-in user)
- [ ] Change Impact side-by-side layout
- [ ] History page and visual polish
- [ ] Screenshots and slide visuals
