# RAG sentence reranker, held-out evaluation

Plan and rule: `reports/rag_rerank_plan.md`, config `data/rag/rag_rerank_config.json` (T = 1, tuned on the 20 dev queries). 20 held-out queries (15 answerable, 5 no_answer), each system run once. Relevance grades are LLM grades (not human), graded blind with systems pooled. Gated and abstained queries count as misses.

## extractive

- All: direct hit rate 8/15 = 0.533 [0.301, 0.752]; units 42, graded >= 1 33/42 = 0.786 [0.641, 0.883], graded 2 8/42 = 0.190 [0.100, 0.333]; shows units on answerable 14/15 = 0.933 [0.702, 0.988]; shows units on no_answer 2/5 = 0.400 [0.118, 0.769]; ungraded 0
- Medicine: direct hit rate 4/7 = 0.571 [0.250, 0.842]; units 21, graded >= 1 16/21 = 0.762 [0.549, 0.894], graded 2 4/21 = 0.190 [0.077, 0.400]; shows units on answerable 7/7 = 1.000 [0.646, 1.000]; shows units on no_answer 1/3 = 0.333 [0.061, 0.792]; ungraded 0
- Device: direct hit rate 4/8 = 0.500 [0.215, 0.785]; units 21, graded >= 1 17/21 = 0.810 [0.600, 0.923], graded 2 4/21 = 0.190 [0.077, 0.400]; shows units on answerable 7/8 = 0.875 [0.529, 0.978]; shows units on no_answer 1/2 = 0.500 [0.095, 0.905]; ungraded 0
- latency over 20: median 0.37 s, p90 0.43 s

## rerank

- All: direct hit rate 9/15 = 0.600 [0.357, 0.802]; units 40, graded >= 1 36/40 = 0.900 [0.769, 0.960], graded 2 15/40 = 0.375 [0.242, 0.530]; shows units on answerable 14/15 = 0.933 [0.702, 0.988]; shows units on no_answer 1/5 = 0.200 [0.036, 0.624]; ungraded 0
- Medicine: direct hit rate 5/7 = 0.714 [0.359, 0.918]; units 19, graded >= 1 17/19 = 0.895 [0.686, 0.971], graded 2 10/19 = 0.526 [0.317, 0.727]; shows units on answerable 7/7 = 1.000 [0.646, 1.000]; shows units on no_answer 1/3 = 0.333 [0.061, 0.792]; ungraded 0
- Device: direct hit rate 4/8 = 0.500 [0.215, 0.785]; units 21, graded >= 1 19/21 = 0.905 [0.711, 0.973], graded 2 5/21 = 0.238 [0.106, 0.451]; shows units on answerable 7/8 = 0.875 [0.529, 0.978]; shows units on no_answer 0/2 = 0.000 [0.000, 0.658]; ungraded 0
- latency over 20: median 1.04 s, p90 1.39 s

## Decision by the frozen rule

- direct hit rate rerank >= extractive: 0.600 >= 0.533: met
- wrong rate on no_answer: 0.200 <= 0.200: met
- median latency over 20 (s): 1.038 < 3.000: met

- **rerank becomes the default extractive display**
