# Step 23 RAG evaluation

All faithfulness grades are LLM grades (claude-sonnet-5-5), not human grades. Frozen config: `data/rag/rag_config.json`. Retrieval: frozen E5b. Run once per condition. Not a fresh test: the ab queries and q45 to q61 were used in earlier abstention work and in selecting E5b.

Primary condition: A1. Threshold used: 0.0315136476426799 (dev AUROC of the E5b top score 0.933, gate usable: True).

## Condition A1 (qwen2.5:1.5b-instruct-q4_K_M)

### Public (medicine)

- answered rate on answerable: 0/27 = 0.000 [0.000, 0.125]
  - not answered, by cause: {'needs_human_check:no_answer': 2, 'needs_human_check:verification': 23, 'needs_human_check:score_gate': 2}
- wrong-answer rate on no_answer (answered): 0/10 = 0.000 [0.000, 0.278]
  - no_answer queries answered: none
  - no_answer queries that showed extractive quotes: 0 of 10
  - dev half: answered 0 of 5
  - test half: answered 0 of 5
- citation validity, answer level (all generated answers pass verification): 0/23 = 0.000 [0.000, 0.143]
- citation validity, sentence level (marker present and in the retrieved set): 0/27 = 0.000 [0.000, 0.125]
  - first failed check among generated answers: {'empty_sentence': 18, 'marker_missing': 5}
- citation relevance (cited chunk has LLM qrels grade >= 1; unjudged excluded): n/a (n=0), unjudged cited chunks 0
- extractive passages shown on answerable queries: relevant (qrels grade >= 1) 53/69 = 0.768 [0.656, 0.852], unjudged 0
- latency seconds, median 15.7, 90th percentile 23.4

### Professional (device)

- answered rate on answerable: 0/20 = 0.000 [0.000, 0.161]
  - not answered, by cause: {'needs_human_check:verification': 16, 'needs_human_check:score_gate': 3, 'needs_human_check:no_answer': 1}
- wrong-answer rate on no_answer (answered): 0/4 = 0.000 [0.000, 0.490]
  - no_answer queries answered: none
  - no_answer queries that showed extractive quotes: 1 of 4
- citation validity, answer level (all generated answers pass verification): 0/17 = 0.000 [0.000, 0.184]
- citation validity, sentence level (marker present and in the retrieved set): 0/19 = 0.000 [0.000, 0.168]
  - first failed check among generated answers: {'empty_sentence': 13, 'marker_missing': 4}
- citation relevance (cited chunk has LLM qrels grade >= 1; unjudged excluded): n/a (n=0), unjudged cited chunks 0
- extractive passages shown on answerable queries: relevant (qrels grade >= 1) 27/48 = 0.562 [0.423, 0.693], unjudged 0
- latency seconds, median 17.3, 90th percentile 22.9

### Scope rule (public)

- recall on advice queries: 10/10 = 1.000 [0.722, 1.000]
  - advice queries missed: none
- false scope triggers on the other 61 queries: 0 

### Faithfulness, condition A1 (LLM-graded, not human)

- no answered responses, nothing to grade

### Exploratory, condition A1: accept a marker at the start of a sentence (post hoc, not frozen)

- generated answers that would pass verification: 9/40 = 0.225 [0.123, 0.375]. Not faithfulness-graded.

## Condition A2 (qwen2.5:3b-instruct-q4_K_M)

### Public (medicine)

- answered rate on answerable: 0/27 = 0.000 [0.000, 0.125]
  - not answered, by cause: {'needs_human_check:no_answer': 6, 'needs_human_check:verification': 19, 'needs_human_check:score_gate': 2}
- wrong-answer rate on no_answer (answered): 0/10 = 0.000 [0.000, 0.278]
  - no_answer queries answered: none
  - no_answer queries that showed extractive quotes: 0 of 10
  - dev half: answered 0 of 5
  - test half: answered 0 of 5
- citation validity, answer level (all generated answers pass verification): 0/19 = 0.000 [0.000, 0.168]
- citation validity, sentence level (marker present and in the retrieved set): n/a (n=0)
  - first failed check among generated answers: {'empty_sentence': 19}
- citation relevance (cited chunk has LLM qrels grade >= 1; unjudged excluded): n/a (n=0), unjudged cited chunks 0
- extractive passages shown on answerable queries: relevant (qrels grade >= 1) 46/57 = 0.807 [0.687, 0.889], unjudged 0
- latency seconds, median 33.3, 90th percentile 41.3

### Professional (device)

- answered rate on answerable: 0/20 = 0.000 [0.000, 0.161]
  - not answered, by cause: {'needs_human_check:verification': 15, 'needs_human_check:score_gate': 3, 'needs_human_check:no_answer': 2}
- wrong-answer rate on no_answer (answered): 0/4 = 0.000 [0.000, 0.490]
  - no_answer queries answered: none
  - no_answer queries that showed extractive quotes: 0 of 4
- citation validity, answer level (all generated answers pass verification): 0/15 = 0.000 [0.000, 0.204]
- citation validity, sentence level (marker present and in the retrieved set): n/a (n=0)
  - first failed check among generated answers: {'empty_sentence': 15}
- citation relevance (cited chunk has LLM qrels grade >= 1; unjudged excluded): n/a (n=0), unjudged cited chunks 0
- extractive passages shown on answerable queries: relevant (qrels grade >= 1) 26/45 = 0.578 [0.433, 0.710], unjudged 0
- latency seconds, median 28.8, 90th percentile 45.8

### Scope rule (public)

- recall on advice queries: 10/10 = 1.000 [0.722, 1.000]
  - advice queries missed: none
- false scope triggers on the other 61 queries: 0 

### Faithfulness, condition A2 (LLM-graded, not human)

- no answered responses, nothing to grade

### Exploratory, condition A2: accept a marker at the start of a sentence (post hoc, not frozen)

- generated answers that would pass verification: 0/34 = 0.000 [0.000, 0.102]. Not faithfulness-graded.

## Condition B (provider off, extractive)

### Public (medicine)

- answered rate on answerable: 0/27 = 0.000 [0.000, 0.125]
  - not answered, by cause: {'needs_human_check:provider_off': 25, 'needs_human_check:score_gate': 2}
- wrong-answer rate on no_answer (answered): 0/10 = 0.000 [0.000, 0.278]
  - no_answer queries answered: none
  - no_answer queries that showed extractive quotes: 2 of 10
  - dev half: answered 0 of 5
  - test half: answered 0 of 5
- citation relevance (cited chunk has LLM qrels grade >= 1; unjudged excluded): n/a (n=0), unjudged cited chunks 0
- extractive passages shown on answerable queries: relevant (qrels grade >= 1) 58/75 = 0.773 [0.667, 0.853], unjudged 0
- latency seconds, median 0.3, 90th percentile 0.3

### Professional (device)

- answered rate on answerable: 0/20 = 0.000 [0.000, 0.161]
  - not answered, by cause: {'needs_human_check:provider_off': 17, 'needs_human_check:score_gate': 3}
- wrong-answer rate on no_answer (answered): 0/4 = 0.000 [0.000, 0.490]
  - no_answer queries answered: none
  - no_answer queries that showed extractive quotes: 1 of 4
- citation relevance (cited chunk has LLM qrels grade >= 1; unjudged excluded): n/a (n=0), unjudged cited chunks 0
- extractive passages shown on answerable queries: relevant (qrels grade >= 1) 27/51 = 0.529 [0.395, 0.659], unjudged 0
- latency seconds, median 0.3, 90th percentile 0.4

### Scope rule (public)

- recall on advice queries: 10/10 = 1.000 [0.722, 1.000]
  - advice queries missed: none
- false scope triggers on the other 61 queries: 0 
