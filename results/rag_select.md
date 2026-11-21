# RAG selection mode, fresh 40-query evaluation

Plan and rule: `reports/rag_select_plan.md`, config `data/rag/rag_select_config.json`. 30 answerable, 10 no_answer, each mode run once. Relevance and faithfulness are LLM grades (not human), relevance graded blind with modes pooled. Abstentions and gated queries count as misses.

## extractive

- All: direct hit rate 21/30 = 0.700 [0.521, 0.833]; units shown 78, graded >= 1 64/78 = 0.821 [0.721, 0.890], graded 2 28/78 = 0.359 [0.261, 0.470]; answered 0/30 = 0.000 [0.000, 0.114]; wrong on no_answer 0/10 = 0.000 [0.000, 0.278]; ungraded units 0
- Public (medicine): direct hit rate 11/15 = 0.733 [0.480, 0.891]; units shown 42, graded >= 1 34/42 = 0.810 [0.667, 0.900], graded 2 16/42 = 0.381 [0.250, 0.532]; answered 0/15 = 0.000 [0.000, 0.204]; wrong on no_answer 0/5 = 0.000 [0.000, 0.434]; ungraded units 0
- Professional (device): direct hit rate 10/15 = 0.667 [0.417, 0.848]; units shown 36, graded >= 1 30/36 = 0.833 [0.681, 0.921], graded 2 12/36 = 0.333 [0.202, 0.497]; answered 0/15 = 0.000 [0.000, 0.204]; wrong on no_answer 0/5 = 0.000 [0.000, 0.434]; ungraded units 0
- latency over all 40: median 4.7 s, p90 22.1 s; median over queries that reached the model 6.4 s
- shows quotes on answerable 26/30 = 0.867 [0.703, 0.947]; shows quotes on no_answer 5/10 = 0.500 [0.237, 0.763] (irrelevant quotes shown)

## select

- All: direct hit rate 14/30 = 0.467 [0.302, 0.639]; units shown 47, graded >= 1 40/47 = 0.851 [0.723, 0.926], graded 2 26/47 = 0.553 [0.412, 0.686]; answered 16/30 = 0.533 [0.361, 0.698]; wrong on no_answer 0/10 = 0.000 [0.000, 0.278]; ungraded units 0
- Public (medicine): direct hit rate 8/15 = 0.533 [0.301, 0.752]; units shown 27, graded >= 1 22/27 = 0.815 [0.633, 0.918], graded 2 14/27 = 0.519 [0.340, 0.693]; answered 9/15 = 0.600 [0.357, 0.802]; wrong on no_answer 0/5 = 0.000 [0.000, 0.434]; ungraded units 0
- Professional (device): direct hit rate 6/15 = 0.400 [0.198, 0.643]; units shown 20, graded >= 1 18/20 = 0.900 [0.699, 0.972], graded 2 12/20 = 0.600 [0.387, 0.781]; answered 7/15 = 0.467 [0.248, 0.699]; wrong on no_answer 0/5 = 0.000 [0.000, 0.434]; ungraded units 0
- latency over all 40: median 36.3 s, p90 48.3 s; median over queries that reached the model 38.2 s
- faithfulness, sentences graded 47: supported (2) 45/47 = 0.957 [0.858, 0.988]; supported or partly 47/47 = 1.000 [0.924, 1.000]
- second pass on 9 units: exact agreement 9/9 = 1.000 [0.701, 1.000]

## generative

- All: direct hit rate 18/30 = 0.600 [0.423, 0.754]; units shown 49, graded >= 1 45/49 = 0.918 [0.808, 0.968], graded 2 27/49 = 0.551 [0.413, 0.681]; answered 21/30 = 0.700 [0.521, 0.833]; wrong on no_answer 0/10 = 0.000 [0.000, 0.278]; ungraded units 0
- Public (medicine): direct hit rate 8/15 = 0.533 [0.301, 0.752]; units shown 29, graded >= 1 25/29 = 0.862 [0.694, 0.945], graded 2 15/29 = 0.517 [0.344, 0.686]; answered 11/15 = 0.733 [0.480, 0.891]; wrong on no_answer 0/5 = 0.000 [0.000, 0.434]; ungraded units 0
- Professional (device): direct hit rate 10/15 = 0.667 [0.417, 0.848]; units shown 20, graded >= 1 20/20 = 1.000 [0.839, 1.000], graded 2 12/20 = 0.600 [0.387, 0.781]; answered 10/15 = 0.667 [0.417, 0.848]; wrong on no_answer 0/5 = 0.000 [0.000, 0.434]; ungraded units 0
- latency over all 40: median 38.3 s, p90 57.9 s; median over queries that reached the model 40.2 s
- faithfulness, sentences graded 37: supported (2) 33/37 = 0.892 [0.753, 0.957]; supported or partly 36/37 = 0.973 [0.862, 0.995]
- second pass on 7 units: exact agreement 6/7 = 0.857 [0.487, 0.974]

## Decision by the frozen rule

- direct hit rate select >= extractive: 0.467 >= 0.700: NOT met
- unit precision (>= 1) select >= extractive: 0.851 >= 0.821: met
- median latency over all 40 (s): 36.306 < 30.000: NOT met
- answered rate on answerable: 0.533 >= 0.600: NOT met
- wrong-answer rate on no_answer: 0.000 <= 0.200: met
- supported sentence rate: 0.957 >= 0.800: met

- **current default and AI mode stay**
