# Evaluation plan

Principle: every claim in the report is backed by a number from a script anyone can rerun.

## 1. Retrieval (main section)

### Test collections
| Set | Queries | Documents | Labeling |
|---|---|---|---|
| T1 requirement | 100 to 150 label fields or claims | regulatory chunks | graded 0 to 2, two annotators on 30% for agreement (Cohen's kappa) |
| T2 product match | 50+ OCR strings from synthetic and public labels | product records | single correct record |
| T3 impact | 30+ product changes | label versions | set of affected labels |

Build qrels by pooling: take the top 10 from each system, annotate the union. Store as TREC style `qrels_t1.tsv`.

### Systems compared
1. TF-IDF (cosine)
2. BM25 (own implementation, tuned k1 and b)
3. Dense (bge or e5)
4. Hybrid RRF
5. Hybrid weighted
6. Hybrid plus cross-encoder rerank
7. Hybrid plus rerank plus query expansion

### Metrics
nDCG@10, Recall@20, MRR, MAP. Report means and a paired significance test (paired t-test or bootstrap) between systems.

### Ablations
- Chunk size (128, 256, 512 tokens) and overlap
- Field-aware queries vs raw OCR text queries
- OCR noise level (clean text vs real OCR output vs synthetic noise)
- k1 and b sweeps for BM25
- Fusion weight sweep

Failure analysis: pick 10 queries where hybrid lost to BM25 and explain why.

## 2. Error detection

Generate synthetic labels from product records, then inject errors:

| Error type | Example |
|---|---|
| Wrong field | model number changed |
| Missing symbol | sterile symbol removed |
| Missing warning | warning block dropped |
| Barcode mismatch | barcode encodes another GTIN |
| Stale revision | old storage text left in |
| Date format | wrong expiry format |

Report precision, recall and F1 per type, plus false alarms per clean label. Add a small set (20 to 30) of real public labels checked by hand.

## 3. Computer vision
- OCR: character error rate and word error rate on synthetic ground truth, split by clean, scanned, photographed (blur, skew, glare)
- Barcode: decode success rate by condition
- Symbols: mAP@0.5 and per-class recall on a held-out synthetic set and a small real set
- Image diff: precision of flagged changed regions against known edits

## 4. RAG
- Citation precision: share of cited passages that truly support the claim
- Faithfulness: share of statements supported by retrieved text (manual check on 50 outputs)
- Abstention: does it refuse when evidence is weak (queries with no answer in the corpus)

## 5. Generation (draft barcode and artwork)
- Self-check pass rate on 30+ synthetic change requests (zero critical flags after round trip)
- Barcode round-trip success (decode equals intended payload)
- Field fidelity: CER between intended text and OCR of rendered artwork
- Symbol round-trip recall
- Overflow and layout violation rate
- Draft creation time

## 5b. Public medicine module (separate tables)
- Product match accuracy@1 and @3 on 50+ photos of packs
- Summary faithfulness and chatbot citation precision (manual check on 50 answers)
- Refusal rate on unanswerable questions and on questions asking for medical advice
- Behaviour on blurry photos (does it ask for a clearer image)

## 6. Reviewer task study
Small study, 3 to 5 classmates, 10 labels each, with and without LabelLens. Measure time per label, errors caught, errors missed. Be honest about the small sample.

## 7. Results table template

| System | nDCG@10 | Recall@20 | MRR | Latency (ms) |
|---|---|---|---|---|
| TF-IDF | | | | |
| BM25 | | | | |
| Dense | | | | |
| Hybrid RRF | | | | |
| Hybrid + rerank | | | | |
