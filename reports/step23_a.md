# Step 23a report: RAG spec (plan only)

1. What I did. Created worktree `../labellens-rag` on branch `step23-rag` from origin/main (8336bd2). Read the contract, checker citations and retrieval, the E5b config, Step 16 and 18 abstention results and the query files. Wrote `docs/RAG_SPEC.md`: pipeline, provider interface, verification, three outcomes, evaluation with frozen rubric and targets. No code written, nothing run.
2. Files. `docs/RAG_SPEC.md` (new), `reports/step23_a.md` (this). Not committed (23a is not approved yet).
3. Pipeline in one line: scope rule, E5b top 5, score gate, numbered context, LLM (Ollama, fake in tests, or off), verify every marker, else extractive quotes marked needs_human_check.
4. Verified. Only that files exist and the spec has no em dashes (grep count 0). Facts checked: model sizes from ollama.com tag pages (qwen2.5:3b-instruct-q4_K_M 1.9 GB, llama3.2:3b 2.0 GB, gemma3:4b 3.4 GB); chunks max 200 words, mean 168; CPU Core Ultra 7 155U, 12 cores, 31 GB, no discrete GPU.
5. Check yourself. (a) Section 5: below-threshold maps to needs_human_check, not low_confidence, to keep your three outcomes. (b) Section 7: targets and rubric, and that Wilson on 10 no_answer queries is very wide. (c) Section 9: CR-18 and CR-19 are contract changes.
6. Unsure / not done.
- **Speed not measured.** Ollama is not installed and I did not download without your yes.
- **bge-large cache missing.** It is not in this checkout, so 23b must rebuild it (about 37 min CPU) before E5b runs.
- **Contract gaps.** The contract has no professional ask operation, and the abstain shape cannot carry extractive quotes. Both need approval (CR-18, CR-19).
- **Not clean data.** The ab11 to ab20 and q45 to q61 queries were used in earlier selection and abstention work, so the final run is not a fresh test.
- **Untested guesses.** The E5b top score is untested as an abstention score, and the 0.40 overlap guard is a guess.
