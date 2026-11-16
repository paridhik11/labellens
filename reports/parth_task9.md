# Parth Task 9: separate medicine corpus

## 1. What I did
Built a pinned ten-product DailyMed medicine corpus. Extracted source section text without generating advice. Kept medicine separate from device regulations, images and evaluation. Retrieval code was not changed.

## 2. Files created or changed
- `scripts/real/build_medicine_corpus.py`: bounded downloads, SPL identity/date/hash checks, deterministic chunking and offline rebuild.
- `tests/test_medicine_corpus.py`: nine offline tests for provenance, nested sections, invalid sources, caching and archive handling.
- `data/medicine/SOURCES.md`: pinned catalog, source URLs, effective dates and rights notes.
- `data/medicine/corpus.jsonl`, `products.json`, `manifest.json`: text chunks, source metadata and corpus fingerprint. Original XML remains local.
- Learning log: executed results and limitations.

## 3. How it works
A chunk is a short source passage. Each row uses exactly the shared Chunk fields, with module=medicine. Ten products produced 147 unique chunks: labelling 32, warnings 79, dosage 36. Product metadata maps every chunk to its SPL version and effective date. Windows contain at most 200 words with 25-word overlap. Nested section bodies are retained once.

## 4. How I verified it
Actual commands and output:
```text
/opt/anaconda3/envs/labellens-cv/bin/python -m scripts.real.build_medicine_corpus --offline
{"chunks": 147, "corpus_sha256": "2b9dd48d230ee52938c564700d61d6db19ebe68eee4beb285c2c74b601aa018f", "module": "medicine", "products": 10, "retrieval_evaluation": "NOT_RUN"}
```
The online command without --offline downloaded all ten pinned sources first. The offline rebuild returned the same fingerprint.
```text
/opt/anaconda3/envs/labellens-cv/bin/python -m pytest -q -p no:cacheprovider -m "not slow"
436 passed, 3 deselected in 158.85s (0:02:38)

/opt/anaconda3/envs/labellens-cv/bin/python -m ruff check --no-cache src tests scripts/real scripts/cv_experiments/eval_perspective.py
All checks passed!
```

## 5. What you should check yourself
Compare one source passage and its effective date. Confirm module=medicine and matching Chunk keys. Rebuild before integrating retrieval.

## 6. What I am unsure about or assumed
Labelling includes indications, description and principal display panels, not every possible SPL section. This small selected corpus is not clinical validation or comprehensive drug coverage. Pari owns retrieval integration; no src/ir change was made. Photo extraction remains deferred at 1/10 name, 0/10 lot, 0/10 expiry; human spot-check deferred, NOT_RUN.
