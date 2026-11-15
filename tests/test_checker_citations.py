"""Citations are real chunks with verbatim quotes; no accepted section in the top k means no citation."""
import pytest

from src.checker.citations import CITATION_SPECS, CitationSpec, best_quote, find_citation
from src.checker.retrieval import build_retriever, module_chunks
from src.checker.settings import RetrievalSettings
from src.common.schemas import Chunk, Hit


class FakeRetriever:
    name = "fake"

    def __init__(self, ids: list[str]) -> None:
        self.ids = ids

    def search(self, query: str, k: int = 10) -> list[Hit]:
        return [Hit(doc_id=i, score=1.0, rank=r) for r, i in enumerate(self.ids[:k], start=1)]


def _chunk(cid: str, section: str, text: str) -> Chunk:
    return Chunk(chunk_id=cid, source="FDA", section=section, title="T", url="u", text=text)


def test_best_quote_is_verbatim_and_prefers_query_terms() -> None:
    text = "(a) Unrelated opening words here. (b) The date must be year, month, day with hyphens.\n\n(c) Other."
    quote = best_quote(text, "date year month day hyphens")
    assert quote in text and "hyphens" in quote and len(quote) <= 300


def test_best_quote_truncates_long_segments_at_a_word() -> None:
    text = "word " * 200
    quote = best_quote(text, "word")
    assert len(quote) <= 300 and quote in text


def test_cites_first_accepted_section_with_rank() -> None:
    chunks = {c.chunk_id: c for c in [_chunk("a", "9.9", "noise"), _chunk("b", "801.18", "A date format rule.")]}
    spec = CitationSpec("date format", frozenset({"801.18"}), "direct")
    cite = find_citation(spec, FakeRetriever(["a", "b"]), chunks, k=10)
    assert cite is not None and cite.chunk_id == "b" and cite.rank == 2 and cite.quote in chunks["b"].text


def test_no_citation_when_only_other_sections_retrieved() -> None:
    chunks = {"a": _chunk("a", "9.9", "noise")}
    spec = CitationSpec("date format", frozenset({"801.18"}), "direct")
    assert find_citation(spec, FakeRetriever(["a"]), chunks, k=10) is None


def test_accepted_sections_exist_in_device_corpus() -> None:
    sections = {c.section for c in module_chunks("device").values()}
    for rule_id, spec in CITATION_SPECS.items():
        assert spec.sections <= sections, rule_id


def test_every_rule_query_finds_its_section_with_bm25() -> None:
    """Regression guard on the frozen queries (lexical retriever, so it runs without the dense model)."""
    chunks = module_chunks("device")
    retriever = build_retriever(RetrievalSettings(method="bm25"), chunks)
    for rule_id, spec in CITATION_SPECS.items():
        cite = find_citation(spec, retriever, chunks, k=10)
        assert cite is not None, rule_id
        assert cite.quote in chunks[cite.chunk_id].text


@pytest.mark.slow
def test_every_rule_query_finds_its_section_with_hybrid() -> None:
    chunks = module_chunks("device")
    retriever = build_retriever(RetrievalSettings(), chunks)
    for rule_id, spec in CITATION_SPECS.items():
        assert find_citation(spec, retriever, chunks, k=10) is not None, rule_id
