# Step 25: demo PC

**Done (branch step25-demo)**
- `scripts/run_demo.py`: env check, model download, index copy or build, seed, checker retrieval gate, API, warm-up, golden package, URLs. `requirements-demo.txt` is one venv for everything.
- `publishVersion` real (CR-24): approval of this exact version, pinned page `/versions/<id>`, PDF at `/versions/<id>/label.pdf`.
- Public medicine mode (CR-23): `POST /public/match` (E5b recipe over 10 products, accept at bge-large cosine 0.65, else `no_reference_match`), reference fields derived from label text with evidence, sections (summary, ingredients, warnings, sources), `askPublic` answers from the matched product's chunks, `/public/medicine` page.
- Checker `e5b` method (CR-25) with automatic fallback to plain hybrid that says so in `retrieval_config`. Default unchanged.
- `scripts/demo_e2e.py`: real API, real extractor and renderer.

**Measured on this PC**
- E5b gate: first load 11.7 s (both modules, cached), one check 0.3 s, so E5b is the demo default. Index step on first run 178 s (147-chunk medicine index).
- e2e, golden PDF plus one synthetic photo: 20/20 PASS, no mocks, no fallback. Fresh clone (new venv, `requirements-demo.txt`): 19/19 PASS.
- AI answer: qwen2.5 3b ran, failed verification, fell back to passages (29 s).
- Tests: 914 passed, 7 skipped; ruff clean.

**Choices and limits**
- Manufacturer is never in the corpus, so it is null (`not_in_corpus`); nothing was fetched or typed in.
- The 0.65 threshold is fitted on 30 names I wrote (0/30 wrong): a sanity check, not an error rate. "Lipitor" does not match atorvastatin.
- No golden packages were found in the repo; the golden package is Parth's test template plus a rendered label.
- (b) multi-side scan NOT built (time box exceeded after (a)).
- No UI build exists; `publicScan` and print verification are still mocks. Stored files keep the DRAFT mark after approval.
- A fresh clone must point `LABELLENS_INDEX_DIR` at an existing index store, or wait about 40 minutes for the bge-large build.
