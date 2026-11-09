from src.ir.bm25 import BM25Retriever, InvertedIndex, TfidfRetriever

DOCS = [
    ("d1", "sterile symbol and sterilization method"),
    ("d2", "expiry date format on the label"),
    ("d3", "storage temperature limits"),
]


def test_bm25_ranks_matching_doc_first():
    ix = InvertedIndex().build(DOCS)
    hits = BM25Retriever(ix).search("sterilization method", k=3)
    assert hits[0].doc_id == "d1"
    assert hits[0].rank == 1


def test_tfidf_ranks_matching_doc_first():
    ix = InvertedIndex().build(DOCS)
    hits = TfidfRetriever(ix).search("storage temperature", k=3)
    assert hits[0].doc_id == "d3"


def test_unknown_terms_return_empty():
    ix = InvertedIndex().build(DOCS)
    assert BM25Retriever(ix).search("zzzz", k=3) == []


def test_save_load_roundtrip(tmp_path):
    ix = InvertedIndex().build(DOCS)
    p = tmp_path / "ix.json"
    ix.save(p)
    ix2 = InvertedIndex.load(p)
    a = [h.doc_id for h in BM25Retriever(ix).search("expiry date", k=3)]
    b = [h.doc_id for h in BM25Retriever(ix2).search("expiry date", k=3)]
    assert a == b
