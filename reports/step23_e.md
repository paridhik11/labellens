# Step 23e report: structured JSON output

**Result: no model passes the frozen rule. Extractive stays the default, the model stays off by default.**

**Format fix works.** Ollama structured outputs (JSON schema in `format`, `{no_answer, sentences:[{text, sources}]}`) removed the marker problem of Step 23. The verifier works on the parsed JSON with the same rules (valid ids, no empty sources, banned claims, overlap guard, `no_answer`). Tests: 11 added, fast suite passes.

**Fresh run** (40 queries written by me, 30 answerable and 10 no_answer, config committed first at 48f0caf, each model once, 300 token cap):

| model | verified answers (answerable) | wrong answers (no_answer) | median / p90 s | unparseable JSON | supported sentences (LLM) |
|---|---|---|---|---|---|
| qwen2.5 1.5b | 14/30 = 0.47 [0.30, 0.64] | 1/10 | 30.8 / 38.2 | 11 of 26 | 26/34 = 0.77 [0.60, 0.88] |
| qwen2.5 3b | 17/30 = 0.57 [0.39, 0.73] | 0/10 | 38.6 / 76.9 | 0 of 26 | 24/26 = 0.92 [0.76, 0.98] |

Public and professional rows are in `results/step23e_structured.md`. Neither model is eligible (rule: median < 30 s, answered >= 0.60, wrong <= 0.20). 3b misses the answered target by one query and the speed target by 8 s. The 1.5b failures are all output cut off at the token cap, so a larger cap might help but would be slower. Faithfulness was graded for both for information only; second pass on 17 units agreed 17/17 (same grader, so consistency, not correctness).

**Read the faithfulness with care.** Most answers are verbatim copies of the cited chunk, which is supported but not always relevant to the question. Failures: wrong chunk cited (e26, e40), a statement not in the cited text (e16).

**Not run (speed):** llama3.2 3b and gemma3 4b had pilot medians of 70 and 72 s on three smoke queries, over my 60 s cut. Not tested on the fresh set.

**Caveats.** LLM grades only, 40 queries, wide intervals, this CPU. 14 of 40 queries stop at the score gate. A faster machine or GPU could change the speed result.
