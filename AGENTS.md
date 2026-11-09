# Rules for the coding agent (Antigravity)

Project: LabelLens, a course project where information retrieval is the core. Read README.md and docs/WORKFLOW.md before doing anything.

## Ground rules
1. Work on one task per session. Stay inside the files the task names.
2. Make small, targeted changes. Do not refactor unrelated code.
3. Before writing code, write a short plan and list the files you will touch.
4. Every new function has type hints, a docstring and at least one test in `tests/`.
5. Run `pytest` before finishing. Do not say it passes unless you ran it.
6. Never invent metrics, results or dataset sizes. If something was not run, say so.
7. Never hard-code API keys. Use `.env` and `src/common/config.py`.
8. Use the schemas in `src/common/schemas.py`. Change them only when the task says so.
9. Do not add a dependency without saying why and updating `requirements.txt`.
10. Do not use em dashes in docs or comments.

## IR specific
- The inverted index and BM25 must be our own implementation in `src/ir/`. A library version is only for comparison tests.
- All retrieval systems expose the same interface: `search(query: str, k: int) -> list[Hit]`.
- Any change to retrieval must be followed by `python -m src.ir.eval` and the numbers pasted in the PR.
- Fixed random seeds. Results must be reproducible from one command.

## CV specific
- Keep preprocessing steps as separate, testable functions.
- Report OCR and detection results per condition (clean, scan, photo), never one blended number.

## RAG specific
- Generated text may only use retrieved passages. Every claim carries a passage id.
- If evidence is weak, output `NEEDS_HUMAN_REVIEW` with the reason. Do not guess.

## Done means
Tests pass, lint clean, docs updated, metrics line written, and a short summary of what changed and what is not done yet.

## Generation specific
- Barcodes and artwork come from deterministic templates. Never use an image generation model for label artwork.
- Never invent GTIN or UDI-DI values. If one is needed and missing, raise `IdentifierRequired`.
- Every generated draft carries a DRAFT watermark, a change log and a self-check result.
- Nothing is published without an approval record from an authorized reviewer.

## Module separation
- Public medicine module and professional device module share `src/ir`, `src/cv`, auth and storage.
- They do not share datasets, rules or result tables. Keep them in separate folders and report them separately.

## Working agreement
Work in numbered steps, one step at a time. After each step, stop and wait for the user to say "continue".
After every step, provide a Step Report in exactly this format:
1. What I did (plain English, 3 to 5 sentences, no jargon without a definition)
2. Files created or changed (with a one line reason each)
3. How it works (a small worked example or analogy, and define every new term)
4. How I verified it (the exact command and the REAL output pasted, never summarized)
5. What you should check yourself (2 or 3 specific things to look at in the diff)
6. What I am unsure about or assumed
7. Two questions to test if I understood
Also append the same report, shortened, to docs/LEARNING_LOG.md.

