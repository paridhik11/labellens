# UI notes for the optional AI answer (for Ishanvi)

Applies to the public Ask screen (P3) and the professional evidence screen. Contract: `docs/contracts/openapi.yaml` (CR-21). Mocks: `src/api/mock/*/ask/ai_*.json`. Limits: `docs/AI_ANSWER.md`.

1. **Panel 1, "Extractive answer (instant)".** Call `POST /public/ask` (or `/ask`) with no `mode`. Show the cited passages, or the abstain message, immediately. This panel is always shown first and is the default.
2. **Button "Ask AI (about 40 s)".** Calls the same endpoint with `?mode=ai`. It answers 202 with a Job. Poll `GET /jobs/{job_id}` every 2 s. Show a progress state from `progress` and `message` (the message says what the job is doing). The user can keep reading panel 1 while waiting. Stop polling at `done` or `failed`, and give up politely after 120 s.
3. **Panel 2, "AI answer" (when `done`).** Show `result.answer` the same way as panel 1, plus the note "AI-generated, supported by the cited text only. Check the quotes." Never say a label complies.
4. **Fallback message.** If `result.fallback_reason` is set, do not show an error. Show the passages in panel 2 with a notice by reason: `model_unavailable` "The AI model is not available here. Showing the closest passages.", `timeout` "The AI took too long. Showing the closest passages.", `verification_failed` "The AI answer did not pass the citation checks. Showing the closest passages." If `model_used` is true and the answer is abstained, show the abstain message.
5. **Failed job.** Only `error: retrieval_unavailable` ends a job `failed`. Show "Search is not available right now" and keep panel 1.
6. The public screen keeps the banner constant. The professional screen has no banner.

Mock states for development: `?mock_state=ai_accepted`, `ai_done`, `ai_fallback_timeout`.
