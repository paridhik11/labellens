# Step 21c report: real inspect, recheck, jobs, search

**1. What I did.** `inspectLabel`, `recheckArtwork`, `getJob`, a new `getCheckResult` and `searchEvidence` now run for real. The first inspect of a version starts a job (202). It reads the version's image with the CV extractor (blind mode), stores the extraction, runs the checker and persists a CheckResult. Later inspects of the same version answer 200 at once. Recheck does the same for generated artwork and copies `artifact_sha256`, so the Step 20 approval rules work on it. `CheckResult` gained `needs_human_count` and `coverage` (CR-17); findings hold only problems; `extra.rx_only` is documented for product registration.

**2. Files.** `src/api/checks.py` (jobs, extraction store, check run, search), `src/api/extractor.py` (lazy CV import), `routes.py`, `models.py` (tables `extractions`, `jobs`, three `check_results` columns), `db.py` (adds missing columns to old DB files), `main.py`, `requests.py`, `mock_server.py` (mock fallback for job ids not issued here), `seed.py`; `openapi.yaml`, `API.md`, `DATA_MODEL.md`, `SCHEMA_CHANGE_REQUESTS.md` (CR-17); four mocks; tests `test_api_checker.py` (18), contract and mock tests extended.

**3. How it works.** Job states are appended rows, never updated. An unknown id of the form `job_xxxxxxxx` is 404, other ids still get the mock (scan jobs are mocks).

**4. How I verified it.** `python -m pytest -q -m "not slow"` gives `354 passed, 3 skipped, 3 deselected in 116.53s`; `ruff check src tests` gives `All checks passed!`. The contract test validates every real status of the five new operations against openapi.yaml. A subprocess test confirms `import src.api.main` pulls in no cv2, zxingcpp or rapidocr. `git diff` shows `src/cv`, `src/gen`, `src/ir`, `data/eval`, `src/common` untouched.

**5. Check yourself.** (a) `_start_check` in `routes.py`: 200 versus 202 rule. (b) `image_path` in `checks.py`: an SVG is read through the PNG next to it (my assumption about the renderer package). (c) Deleting `data/api/labellens.db` is not needed; columns are added on start.

**6. Unsure or assumed.** Real extraction through the API was not run end to end in a server (tests stub it; the extractor itself is evaluated in 21b). Layout findings are not part of a real self-check because generate is still a mock. Hybrid search needs sentence-transformers on the server; the one test for it is marked slow and did not run in the fast suite. CI result not yet checked.
