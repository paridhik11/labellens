# Evaluation plan

Principle: every claim in the report is backed by a number from a command anyone can rerun.

## 1. Retrieval (main section)
| Set | Queries | Documents | Labels |
|---|---|---|---|
| T1 requirement | 62 queries (44 device, 18 medicine) in `data/eval/queries_t1.tsv` | regulatory chunks | graded 0, 1, 2 by Pari, 30% re-graded by Parth |
| T2 product match | 50+ OCR strings from synthetic and public labels | product records | one correct record |
| T3 impact | 30+ product changes | label versions | set of affected labels |

Pooling: top 10 from each of tfidf, bm25, dense, hybrid within the right module, shuffled, graded blind. Rubric in `docs/QRELS_GUIDE.md`. Queries of type `no_answer` are excluded from main averages and reported separately as an abstention test.

Systems: TF-IDF, BM25 (own), dense, hybrid RRF, then query expansion, LTR, relevance feedback.
Metrics: nDCG@10, Recall@20, MRR, MAP at chunk level and section level, paired bootstrap against BM25.
Ablations: RRF k, fusion weights, stemming, BGE query prefix, chunk size and overlap, module filter on and off, clean vs OCR-noisy queries, BM25 k1 and b.
Failure analysis: 10 queries where hybrid lost to BM25, with reasons.
Caveat: a system added after pooling can be penalised for unjudged results, so report unjudged rate.

## 2. Error detection
Synthetic labels with injected errors (wrong field, missing symbol, missing warning, barcode mismatch, stale text, date format). Precision, recall, F1 per type, false alarms per clean label. Plus 20 to 30 real public labels checked by hand.

## 3. Computer vision
OCR character and word error rate, barcode decode rate, symbol recall and precision, all per condition (clean, scan, photo).

## 4. RAG
Citation precision, faithfulness (manual check on 50 outputs), abstention on unanswerable queries, refusal on medical-advice questions.

## 5. Generation
Self-check pass rate on 30+ synthetic change requests, barcode round-trip success, conditional barcode correctness (kept when unchanged, regenerated when changed), field fidelity (CER of rendered text), overflow and layout violation rate, draft creation time.

## 6. Print verification
Detection of injected print errors, false alarm rate on correct prints, decode rate and field CER by condition (flat scan, phone photo, blur, glare, skew), rate of correctly asking for a clearer scan.

## 7. Public medicine module (separate tables)
Product match accuracy at 1 and 3, summary faithfulness, chatbot citation precision, refusal rate, behavior on blurry photos.

## 8. Reviewer task study (if time)
3 to 5 classmates, 10 labels each, with and without LabelLens. Time per label, errors caught. State the small sample honestly.

## 9. Results table template
| System | nDCG@10 | Recall@20 | MRR | MAP | Latency (ms) |
|---|---|---|---|---|---|
| TF-IDF | | | | | |
| BM25 | | | | | |
| Dense | | | | | |
| Hybrid RRF | | | | | |
