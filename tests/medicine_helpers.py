"""Stubs for the public medicine mode tests: the real data/medicine catalog, no embedding model."""
from __future__ import annotations

from src.api.medicine import MedicineCatalog, MedicineService, ProductMatcher
from src.common.schemas import Hit


class NameRanker:
    """Ranks products by the words they share with the query; the cosine stand-in is a function of that overlap."""

    def __init__(self, catalog: MedicineCatalog) -> None:
        self.names = {pid: set(p.name.lower().split()) for pid, p in catalog.products.items()}

    def search(self, query: str, k: int = 10) -> list[Hit]:
        """Products best first, score 0.5 to 0.9."""
        words = set(query.lower().split())
        scored = sorted(((len(words & n) / max(len(n), 1), pid) for pid, n in self.names.items()), reverse=True)
        return [Hit(doc_id=pid, score=0.5 + 0.4 * s, rank=i) for i, (s, pid) in enumerate(scored[:k], start=1)]


class Broken:
    """A ranker whose models cannot be loaded."""

    def search(self, query: str, k: int = 10) -> list[Hit]:
        """Always fails."""
        raise RuntimeError("model files are missing")


def stub_medicine(broken: bool = False) -> MedicineService:
    """A MedicineService with stub matching (or, with broken=True, matching that fails with a 503)."""
    catalog = MedicineCatalog()
    ranker = Broken() if broken else NameRanker(catalog)
    return MedicineService(catalog, ProductMatcher(catalog, ranker, ranker, threshold=0.62))
