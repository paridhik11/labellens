# Step 23e structured output evaluation

Fresh queries: 30 answerable, 10 no_answer, written by the assistant, not used in any earlier selection. Frozen config `data/rag/step23e_config.json`. Faithfulness grades are LLM grades, not human. Each model run once.

## qwen2.5:1.5b-instruct-q4_K_M

- Public (medicine): verified answers on answerable 7/15 = 0.467 [0.248, 0.699]; not answered by cause {'verification/bad_json': 4, 'score_gate': 4}; wrong answers on no_answer 1/5 = 0.200 [0.036, 0.624]
- Professional (device): verified answers on answerable 7/15 = 0.467 [0.248, 0.699]; not answered by cause {'score_gate': 3, 'verification/bad_json': 5}; wrong answers on no_answer 0/5 = 0.000 [0.000, 0.434]
- reached the model: 26 of 40 (the rest stopped at the scope rule or score gate); unparseable JSON: 11
- first failed check among model replies: {'bad_json': 11}
- pooled: verified-answer rate 14/30 = 0.467 [0.302, 0.639]; wrong-answer rate 1/10 = 0.100 [0.018, 0.404]; latency median 30.8 s, p90 38.2 s
- eligible under the frozen rule: False

### Faithfulness, qwen2.5:1.5b-instruct-q4_K_M (LLM-graded, not human)

- sentences graded 34: supported (2) 26/34 = 0.765 [0.600, 0.876]; supported or partly (>= 1) 28/34 = 0.824 [0.665, 0.917]
- query level, every sentence supported: 11/15 = 0.733 [0.480, 0.891]
- second pass, random 20 percent (12 units): exact agreement 12/12 = 1.000 [0.757, 1.000], supported vs not 12/12 = 1.000 [0.757, 1.000]

## qwen2.5:3b-instruct-q4_K_M

- Public (medicine): verified answers on answerable 8/15 = 0.533 [0.301, 0.752]; not answered by cause {'verification/low_overlap': 2, 'no_answer': 1, 'score_gate': 4}; wrong answers on no_answer 0/5 = 0.000 [0.000, 0.434]
- Professional (device): verified answers on answerable 9/15 = 0.600 [0.357, 0.802]; not answered by cause {'score_gate': 3, 'no_answer': 2, 'verification/banned_claim': 1}; wrong answers on no_answer 0/5 = 0.000 [0.000, 0.434]
- reached the model: 26 of 40 (the rest stopped at the scope rule or score gate); unparseable JSON: 0
- first failed check among model replies: {'banned_claim': 1, 'low_overlap': 2}
- pooled: verified-answer rate 17/30 = 0.567 [0.392, 0.726]; wrong-answer rate 0/10 = 0.000 [0.000, 0.278]; latency median 38.6 s, p90 76.9 s
- eligible under the frozen rule: False

### Faithfulness, qwen2.5:3b-instruct-q4_K_M (LLM-graded, not human)

- sentences graded 26: supported (2) 24/26 = 0.923 [0.759, 0.979]; supported or partly (>= 1) 25/26 = 0.962 [0.811, 0.993]
- query level, every sentence supported: 15/17 = 0.882 [0.657, 0.967]
- second pass, random 20 percent (5 units): exact agreement 5/5 = 1.000 [0.566, 1.000], supported vs not 5/5 = 1.000 [0.566, 1.000]

## Selection by the frozen rule

- chosen: none, the extractive default stays
