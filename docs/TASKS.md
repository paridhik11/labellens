# Task checklist

Tick items as they are done. Status checked against `origin/main` at 305951d on 17 Nov 2026. Step numbers match `CLAUDE.md` and `docs/LEARNING_LOG.md`; days match `docs/TEAM_PLAN.md`. Human relevance grades are not a task here: the qrels are LLM-assessed with a graded human validation sample (see `docs/LLM_GRADER_PROMPT.md`).

## Done (merged to main)
- [x] Steps 1 to 10: own index, TF-IDF, BM25, dense (BGE and FAISS), hybrid RRF, metrics, eval harness, eCFR crawler, 903 chunks, qrels tooling
- [x] Steps 11 to 15: LLM-assessed qrels, human validation sample and agreement (Step 13), results and by-type tables, failures, intervals (Step 14), ablations and depth-20 grading (Step 15)
- [x] Step 16: medicine abstention evaluation (merged)
- [x] Steps 17 and 18: retrieval experiments merged. E5b frozen and scored once on fresh queries. No claim of an improvement beyond the dev and fresh numbers in `results/step18_final.md`
- [x] CV fixes and symbols experiments merged. Negative results kept (symbol detector 0/204 on independent drawings)
- [x] Step 19: data model, template spec, OpenAPI, API guide, 13 screens, 50 mocks, contract tests
- [x] Step 20: backend (SQLite, real endpoints with role checks, mock fallback, OpenAPI response tests)
- [x] Step 21: checker with evidence (16 rules, retrieval cites, needs_human default)
- [x] Step 22: change assessment (rules parser, barcode KEEP/REGENERATE/NEEDS_INPUT, confirmations). Parser is narrow by design
- [x] Step 23: RAG with extractive answers and citation verification
- [x] Step 23e: structured JSON answers. No model passed the frozen rule, so extractive stays the default
- [x] Step 24a: real scan upload, photo-quality gate, extraction confirmation (CR-20)
- [x] Step 24b: generateArtwork, exports, artifact download, DRAFT mark kept on every export (CR-22)
- [x] Step 24c: optional AI answer, `mode=ai` job with fallbacks (CR-21)
- [x] Parth (merged in `e95b274`): GS1 barcode outcomes, export (PDF, SVG groups, QR), DailyMed device-label set, revision engine, perspective module (not wired), medicine corpus (10 products, 147 chunks), print verification module (not wired to an endpoint), GEN_HANDOFF.md
- [x] Ishanvi, public pages P1 to P3 pushed to `ishanvi-ui` (`8a7a078`): every mock state, public mode separate from professional

## Pari
Retrieval
- [x] Step 16 abstention evaluation (merged)
- [x] Steps 17 and 18 retrieval experiments (merged)
- [x] Decide how to use the LLM grades; first full results table with the Step 13 caveat (`results/`)
- [x] Merge the retrieval branches into main

Backend and product
- [x] Checker with evidence (Step 21)
- [x] Natural-language change parser (narrow, Step 22). The structured form is the main entry
- [ ] T3 change impact retrieval: the affected-items list is still a mock on the demo change. Real retrieval-based impact is NOT done
- [x] RAG with citation check and the abstain rule (Step 23, extractive default)
- [x] Generate endpoint wired to Parth's renderer, DRAFT mark, self-check (Step 24b)
- [~] Review and approval flow: rules and endpoints done (approval bound to `artifact_sha256`, `check_id`, confirmed assessment; reject terminal; new version voids approval). Approval screen wiring is Ishanvi's (Prompt D)
- [ ] Template registration flow: registerTemplate checks shape only. Layout findings and the draw-and-name-slots flow are NOT done
- [ ] Public medicine mode: product match to the 10-product corpus, reference fields, Ingredients and Warnings data, "no reference match" outcome. NOT done (planned for Step 25)
- [ ] Print verification endpoint: Parth's `verify_print` behind a 202 Job. NOT wired
- [ ] Publish: `publishVersion` is still a mock. Planned in Step 25
- [ ] Multi-side scan (front and back on one label version). NOT done. Optional in Step 25
- [ ] Decide the open contract items. Accepted so far: CR-2, 3, 4, 5, 9, 10, 11 (Parth's review), plus CR-18, 20, 21, 22 (merged). Still to decide: CR-1, 6, 7, 8, 12, 13, 14, 15, 16, and the remaining D-7 kind names. Decide before the feature freeze

Integration and delivery
- [ ] Step 25: one-command demo start, `publishVersion`, E5b switch with fallback, demo script, README, medicine mode, multi-side scan (optional). In progress
- [ ] Step 26 (Thu 19 Nov): feature freeze at noon. Clean-clone test, bug fixes only
- [ ] Final retrieval numbers and the release tag
- [ ] Report, slides, rehearsal (Fri 20 to Sat 21)

## Parth (from Day 6)
- [x] Review of CRs marked "touches Parth" (conditional YES recorded for CR-2, 3, 4, 5, 9, 10, 11)
- [~] Align the renderer and approval record to the contract: D-3 (background, still refused in generation), D-5 (one `artifact_sha256`, done in 24b), D-6 (approval names, done), D-9 (named SVG groups, done). Confirm D-3 status in his final report
- [~] Layout finding kind names (rest of D-7): open
- [x] Template rendering engine against `docs/contracts/TEMPLATE_SPEC.md`
- [x] Conditional GS1 barcode (KEEP, REGENERATE, NEEDS_INPUT), layout checks, self-check loop
- [~] `extract_label` OCR and barcode decode: works on synthetic and DailyMed-style labels. Real-photo extraction is weak (product name 0/4, lot 2/4, expiry 0/4 on the last test). Round 2 in progress (`reports/parth_cv2.md`), capped at Wed 18 evening
- [~] Print verification (`verify_print`): module done, endpoint not wired (Pari, Step 25)
- [ ] Golden demo packages and the DRAFT warning check on every export
- [ ] Report chapter (CV methodology, generator, real-photo limits)

## Ishanvi (from Day 6, small tasks only)
Build from `src/api/mock/` only, using `docs/contracts/SCREENS.md` for states.
- [x] Scan and Understand, public pages (P1, P2, P3) pushed (`8a7a078`). Ingredients and Warnings tabs stay hidden until the medicine mode API lands
- [ ] Professional Round A: Products, Template setup, Inspect (with the DRAFT mark and signed-in user)
- [ ] Professional Round B: Evidence, Changes (side by side, structured form as the main entry), History
- [ ] Professional Round C: Review and approval, Export package, Print verification
- [ ] Check pass: every screen and state, pass or fail, in `ui/REPORT.md`
- [ ] Wire to the real API (Prompt A, after Pari merges the UI branch)
- [ ] Upload and take photo, AI answer panel, generate and download (Prompts B to D)
- [ ] Screenshots, UI report section, backup recording after the freeze

## Gaps to show honestly in the report
- Real-photo extraction accuracy (small test set, exposed photos, LLM-generated references, real symbols unmeasured)
- Abstention is weak (AUROC about 0.80 to 0.88 on the fair set)
- Small-model AI answers: none passed the frozen speed rule, so extractive is the default
- Medicine mode is a small corpus, not general coverage
- Exports are DRAFT only. Approved, unmarked output is not produced
- ML: the shipped detector is template matching. Symbol classifiers (CNN and CLIP) missed their targets, reported as negative results
