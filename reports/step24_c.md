# Step 24c report: optional AI answer

`askPublic` and `askProfessional` take `?mode=ai` (CR-21, additive). Default stays the instant extractive 200. With `ai` they answer 202 with a Job of kind `ask`; poll `getJob`, whose finished `result` holds the answer, `model_used` and `fallback_reason`.

The job uses qwen2.5 3b with the frozen Step 23e structured-output settings and never fails because of the model: Ollama missing gives `model_unavailable`, no reply in 90 s gives `timeout`, a reply failing the checks gives `verification_failed`, each ending `done` with the extractive passages. Only an unbuildable retrieval system ends `failed`.

Added: `src/api/ask_jobs.py`, `ProviderTimeout`, an append-only `ask_results` table, contract schemas, four mocks, `tests/test_ai_mode.py` (13 tests, fake provider, closed port for the no-Ollama case). Fast suite 698 passed, ruff clean. A live run with real Ollama returned a verified answer (31 s model time).

Limits are in `docs/AI_ANSWER.md`: LLM-graded, 40 fresh queries, 57 percent verified, median 38.6 s on this CPU, faithfulness means supported by the cited text.

UI needs for Ishanvi are in `docs/UI_NOTES_AI_ANSWER.md`. No session for Ishanvi was reachable from here, so please pass that file on.
