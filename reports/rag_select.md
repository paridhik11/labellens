# RAG selection mode: result (branch rag-select)

Rule, queries and config were committed before the run (`reports/rag_select_plan.md`, `data/rag/rag_select_config.json`). Full tables: `results/rag_select.md`. LLM grades only (claude-sonnet-5-5), 40 fresh queries (30 answerable, 15 per module, 10 no_answer), each mode run once.

| | extractive (default) | select | generative 3b |
|---|---|---|---|
| direct hit rate (answerable) | 0.700 [0.521, 0.833] | 0.467 [0.302, 0.639] | 0.600 [0.423, 0.754] |
| units graded >= 1 | 0.821 | 0.851 | 0.918 |
| answered rate | n/a (always quotes) | 0.533 | 0.700 |
| wrong answers on no_answer | 0/10 | 0/10 | 0/10 |
| supported sentences | n/a | 0.957 (45/47) | 0.892 (33/37) |
| median latency, all 40 | 4.7 s | 36.3 s | 38.3 s |

Decision: select fails three conditions (hit rate, answered rate 0.533 < 0.60, median 36.3 s > 30 s). The extractive default and the current AI mode stay. Select is merged as code only (`output="select"`, off by default, not wired to the API).

What went wrong: on 10 of 30 answerable queries the 3b model said no_answer although retrieved sentences answered them; 4 more were stopped by the score gate. Latency is token generation on CPU (about 4 tokens/s), not prompt size. Faithfulness is near 1 by construction; the two select sentences below 2 are truncated fragments.

Limits: one LLM grader, 40 queries, wide intervals, the second pass is the same grader (select 9/9, generative 6/7 agreement). Splitter quirk found after the run, not fixed: merging a short piece joins with a space, so a joined sentence may not be a byte-exact substring of the chunk (1 of 47). Cross-encoder not tried.
