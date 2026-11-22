# Release v1.1

Tag `v1.1` on commit 1c6b44a (origin/main). Fresh clone into an empty folder, Python 3.12.10 venv from `requirements-demo.txt`, prebuilt indexes from the shared store (`LABELLENS_INDEX_DIR`), demo server on port 8041 started with `python scripts/run_demo.py --port 8041 --fresh`. No code changes were needed.

| Check | Result |
|---|---|
| Fast tests (`pytest -m "not slow"`) | 1036 passed, 8 skipped, 5 deselected |
| `ruff check src tests` | all checks passed |
| UI states, mock mode (`check_screens.cjs`) | 67 states, 0 failed; 11 click-throughs, 0 failed |
| UI states, api mode | 67 states, 0 failed; 11 click-throughs, 0 failed (11 expected fallback HTTP errors ignored) |
| Live flows (`live_flows.cjs`) | 13 flows, 0 FAIL |
| e2e_golden (inside live flows) | 9/9 stages PASS |
| `demo_e2e.py` | 20 passed, 0 fallback, 0 failed, no mock stages |
| `camera_check.cjs` | ALL PASSED |
| `confirm_check.cjs` | ALL PASSED |

Notes: the AI answer stage (19) fell back to extractive (`verification_failed`, 52.6 s), which is the documented behaviour and counts as PASS. Playwright 1.65.1 was installed outside the repo to match the cached Chromium. Limitations are unchanged (see README "Known limits").
