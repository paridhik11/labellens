# Optional AI answer (Step 24c)

Extractive passages stay the default of `askPublic` and `askProfessional`: instant, no model, verbatim quotes. `?mode=ai` adds an optional AI answer as a 202 job (contract change CR-21).

## How it works
1. `POST /public/ask?mode=ai` or `POST /ask?mode=ai` answers 202 with a `Job` of kind `ask`.
2. The job runs the Step 23 pipeline (scope rule, E5b retrieval of 5 passages, score gate) with qwen2.5 3b (`qwen2.5:3b-instruct-q4_K_M`, Ollama structured outputs, prompt v3, temperature 0, 300 token cap, the same settings as the frozen Step 23e run). The reply is JSON `{no_answer, sentences:[{text, sources}]}` and the verifier checks it: valid source ids, no empty sources, banned claims, overlap with the cited text.
3. Poll `GET /jobs/{job_id}`. When `state` is `done`, `result` holds `answer` (the same body the extractive call returns), `model`, `model_used`, `latency_s` and, on a fallback, `fallback_reason`.

## The request never fails because of the model
| Situation | Result |
|---|---|
| Ollama missing, not running, model not pulled, HTTP error | `done`, extractive passages, `fallback_reason: model_unavailable` |
| No reply within 170 s (the pages wait 180 s) | `done`, extractive passages, `fallback_reason: timeout` |
| Reply is not valid JSON or fails the citation checks | `done`, extractive passages, `fallback_reason: verification_failed` |
| The model says the passages do not answer | `done`, abstained without passages, no `fallback_reason` |
| Scope rule or score gate stops it before the model | `done`, abstained as in the extractive call, `model_used: false` |
| The retrieval system cannot be built | `failed`, `error: retrieval_unavailable` (there are no passages to show) |

## Exact limits (read before showing it to anyone)
- **Evidence is small and LLM-graded.** The evaluation used 40 fresh queries (30 answerable, 10 not) written by the assistant. Faithfulness grades come from an LLM (claude-sonnet-5-5), not a human. Reports: `reports/step23_e.md`, `results/step23e_structured.md`.
- **Only 57 percent of answerable queries get a verified answer** (17 of 30, Wilson interval 0.39 to 0.73). The rest stop at the score gate, the model's own no-answer, or the checks.
- **Slow on the development CPU.** Median 38.6 s, 90th percentile 76.9 s. The limit was 90 s in that run; it is now 170 s so a cold model (about a minute to load) can still answer. `scripts/run_demo.py` loads the model at start when Ollama runs. A faster machine or a GPU would change this.
- **Faithfulness means "supported by the cited text".** 24 of 26 sentences were graded supported. It does not mean the answer is complete, current, relevant to the exact question, or medical or compliance advice. Many sentences are close copies of the passage. The system never says a label complies.
- The model did not pass the acceptance rule of Step 23e (median under 30 s, answered rate 0.60). That is why the AI answer is optional and the extractive answer is the default.

## Tests
`tests/test_ai_mode.py` uses a fake provider only, so CI never needs Ollama. It covers success, every fallback, the closed-port case (no Ollama), mode validation, append-only storage, and that the settings equal the frozen Step 23e run.
