"""Public medicine mode (Step 25a): match a product name to one of the corpus products, show its reference label.

The reference catalog is the ten pinned DailyMed products of `data/medicine/` (loaded with `src.gen.medicine`).
Nothing is invented. A reference field is filled only when a rule finds it in the product's own chunk text, and it
carries that evidence. When no rule finds it the value is null and the field is listed in `not_in_corpus`:
the manufacturer field may carry the sourced SPL labeler, with that role explicitly stated in its evidence.
The labeler may be a repackager or distributor; a physical manufacturing site is not inferred.

Matching reuses the frozen E5b recipe (stemmed BM25 plus bge-large with the BGE query prefix, fused with RRF k=60)
over ten small documents (product name plus the package panel text). RRF scores only say "first in both lists",
so the accept/reject decision uses the bge-large cosine of the top product, with a threshold (`MATCH_THRESHOLD`)
fitted on a handful of names (see `results/step25_medicine_match.md`). Below it the outcome is `no_reference_match`.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from src.common.schemas import Chunk, Hit
from src.gen.medicine import load_medicine_corpus, load_medicine_metadata

MEDICINE_DIR = Path(__file__).resolve().parents[2] / "data" / "medicine"
BANNER = "Authenticity not verified. Based on a reference label match."
MATCH_THRESHOLD = 0.65  # bge-large cosine of the top product: midpoint of worst positive 0.708 and best negative 0.591
REVIEW_BAND = 0.05  # a cosine within this distance of the threshold, or a close second product, asks for review
SECTION_LIMITS = {"summary": 3, "ingredients": 3, "warnings": 6}

# LOINC-style section codes inside Chunk.section ("labelling/34067-9/5"): which group a chunk belongs to.
SUMMARY_CODES = ("34067-9",)  # uses / indications
INGREDIENT_CODES = ("34089-3",)  # description (Rx labels); OTC labels have none, so the package panel stands in
PANEL_CODES = ("51945-4",)  # principal display panel text (carton wording)

DOSAGE_FORMS = (  # most specific first; the first one found in the package panel (or description) wins
    r"delayed[- ]release tablets?", r"oral suspension", r"oral solution", r"inhalation solution",
    r"capsules?", r"caplets?", r"tablets?",
)
SUBSTANCES = (  # lexicon of the substances named in this corpus; a value is used only when the text contains it
    "acetaminophen", "ibuprofen", "loratadine", "omeprazole", "famotidine", "amoxicillin", "metformin hydrochloride",
    "atorvastatin calcium", "levothyroxine sodium", "albuterol sulfate",
)
# up to two words between the count and the unit, never a dose unit (so "20 mg Tablet" is not a pack size)
_FILLER = r"(?:(?!(?:mg|mcg|ml|g)\b)[A-Za-z]+\s+){0,2}?"
PACK_PATTERNS = (
    (re.compile(rf"\b(\d+)(?:'s)?\s+{_FILLER}(tablets?|caplets?|capsules?|vials?)\b", re.I), "count_unit"),
    (re.compile(r"\b(\d+)\s+in\s+1\s+(blister pack|bottle)\b", re.I), "{0} in 1 {1}"),
    (re.compile(r"\b(\d+)\s*mL\s+(bottle)\b", re.I), "{0} mL {1}"),
)


class Searcher(Protocol):
    """Anything with the Retriever `search` method (tests pass a stub)."""

    def search(self, query: str, k: int = 10) -> list[Hit]:
        """Ranked hits."""
        ...


@dataclass
class ReferenceProduct:
    """One corpus product with its derived reference fields and their evidence."""

    product_id: str
    name: str
    setid: str
    version: int
    effective_date: str
    url: str
    fetched: str
    chunk_ids: list[str]
    fields: dict[str, str | None] = field(default_factory=dict)
    evidence: dict[str, dict[str, str]] = field(default_factory=dict)
    aliases: list[str] = field(default_factory=list)

    @property
    def not_in_corpus(self) -> list[str]:
        """Reference fields that no rule could fill from this product's text."""
        return [k for k in ("dosage_form", "active_substance", "pack_size", "manufacturer") if not self.fields.get(k)]


def _section_code(section: str) -> str:
    """'labelling/34067-9/5' -> '34067-9'."""
    parts = section.split("/")
    return parts[1] if len(parts) > 1 else ""


def _first(patterns: tuple[str, ...], text: str) -> str | None:
    """The first of the ordered regular expressions found in the text, as it appears there (lower-cased)."""
    for pattern in patterns:
        found = re.search(pattern, text, re.I)
        if found:
            return found.group(0).lower()
    return None


def derive_fields(chunks: list[Chunk]) -> tuple[dict[str, str | None], dict[str, dict[str, str]]]:
    """Reference fields from the product's chunks, with evidence ({chunk_id, quote}) for every value found.

    Dosage form and pack size come from the package panel text (title and text); the description is the fallback
    for the dosage form. Pack size is given only when the panels agree on one value (a product with several carton
    sizes gets null). The manufacturer is never filled: it is not in the corpus.
    """
    panels = [c for c in chunks if _section_code(c.section) in PANEL_CODES]
    description = [c for c in chunks if _section_code(c.section) in INGREDIENT_CODES]
    values: dict[str, str | None] = {"dosage_form": None, "active_substance": None, "pack_size": None,
                                     "manufacturer": None}
    evidence: dict[str, dict[str, str]] = {}
    for source in (panels, description):
        for chunk in source:
            if values["dosage_form"] is None:
                found = _first(DOSAGE_FORMS, f"{chunk.title} {chunk.text}")
                if found:
                    values["dosage_form"] = found
                    evidence["dosage_form"] = {"chunk_id": chunk.chunk_id, "quote": found}
    for chunk in panels + description:
        low = f"{chunk.title} {chunk.text}".lower()
        hit = next((s for s in SUBSTANCES if s in low), None)
        if hit and values["active_substance"] is None:
            values["active_substance"] = hit
            evidence["active_substance"] = {"chunk_id": chunk.chunk_id, "quote": hit}
    packs: dict[str, tuple[str, str]] = {}
    for chunk in panels:
        text = f"{chunk.title} {chunk.text}"
        for pattern, template in PACK_PATTERNS:
            found = pattern.search(text)
            if found:
                groups = [g.lower() for g in found.groups()]
                if template == "count_unit":
                    unit = groups[1].rstrip("s")
                    value = f"{groups[0]} {unit if groups[0] == '1' else unit + 's'}"
                else:
                    value = template.format(*groups)
                packs.setdefault(value, (chunk.chunk_id, found.group(0)))
                break
    if len(packs) == 1:
        value, (chunk_id, quote) = next(iter(packs.items()))
        values["pack_size"] = value
        evidence["pack_size"] = {"chunk_id": chunk_id, "quote": quote}
    return values, evidence


class MedicineCatalog:
    """Pinned reference products and sourced metadata, read once from the separate medicine corpus."""

    def __init__(self, directory: Path = MEDICINE_DIR) -> None:
        self.chunks: dict[str, Chunk] = {c.chunk_id: c for c in load_medicine_corpus(directory / "corpus.jsonl")}
        self.products: dict[str, ReferenceProduct] = {}
        metadata = load_medicine_metadata(directory)
        for row in json.loads((directory / "products.json").read_text(encoding="utf-8")):
            ids = [cid for s in row["sections"] for cid in s["chunk_ids"]]
            product = ReferenceProduct(
                product_id=f"med_{row['setid'][:8]}", name=row["product_name"], setid=row["setid"],
                version=row["version"], effective_date=row["effective_date"], url=row["url"],
                fetched=row["fetched"], chunk_ids=ids)
            product.fields, product.evidence = derive_fields([self.chunks[i] for i in ids])
            sourced = metadata.get(row['setid'], {})
            product.aliases = list(dict.fromkeys(v['value'] for v in sourced.get('aliases', [])))
            labelers = sourced.get('labelers', [])
            if len({v['value'] for v in labelers}) == 1:
                value = labelers[0]
                product.fields['manufacturer'] = value['value']
                product.evidence['manufacturer'] = {
                    'chunk_id': '', 'quote': value['value'], 'url': value['url'],
                    'role': 'SPL labeler; physical manufacturer not established', 'source_type': 'spl_metadata',
                    'xpath': value['xpath'], 'xml_sha256': value['xml_sha256']}
            self.products[product.product_id] = product

    def product_chunks(self, product_id: str) -> dict[str, Chunk]:
        """The chunks of one product by id (KeyError for an unknown product)."""
        return {i: self.chunks[i] for i in self.products[product_id].chunk_ids}

    def match_documents(self) -> list[Chunk]:
        """One small document per product for the matcher: its name plus the package panel text."""
        docs = []
        for product in self.products.values():
            panels = [self.chunks[i].text for i in product.chunk_ids
                      if _section_code(self.chunks[i].section) in PANEL_CODES]
            text = f"{product.name}. {'; '.join(product.aliases)}. {panels[0] if panels else ''}".strip()[:600]
            docs.append(Chunk(chunk_id=product.product_id, source="DailyMed", title=product.name, text=text,
                              module="medicine"))
        return docs


def passage(chunk: Chunk, limit: int = 1200) -> dict[str, str]:
    """A Citation (source_type label_section) for a whole short chunk; the quote is a verbatim prefix of the text."""
    return {"source_type": "label_section", "chunk_id": chunk.chunk_id, "source": chunk.source,
            "section": chunk.section, "title": chunk.title, "url": chunk.url, "quote": chunk.text[:limit]}


def reference_sections(catalog: MedicineCatalog, product_id: str) -> dict[str, Any]:
    """Summary, ingredients, warnings (as Citations) and sources (the pinned DailyMed document) of one product."""
    product = catalog.products[product_id]
    chunks = [catalog.chunks[i] for i in product.chunk_ids]

    def pick(codes: tuple[str, ...]) -> list[Chunk]:
        return [c for c in chunks if _section_code(c.section) in codes]

    ingredients = pick(INGREDIENT_CODES)
    out: dict[str, Any] = {
        "summary": [passage(c) for c in pick(SUMMARY_CODES)[: SECTION_LIMITS["summary"]]],
        "ingredients": [passage(c) for c in (ingredients or pick(PANEL_CODES))[: SECTION_LIMITS["ingredients"]]],
        "warnings": [passage(c) for c in chunks if c.section.startswith("warnings/")][: SECTION_LIMITS["warnings"]],
        "sources": [{"source": "DailyMed", "url": product.url, "setid": product.setid, "version": product.version,
                     "effective_date": product.effective_date, "fetched": product.fetched,
                     "chunk_ids": product.chunk_ids}],
    }
    out["ingredients_note"] = ("Description section of the label." if ingredients else
                               "This label has no description section in the corpus; the package panel text is shown.")
    return out


def cosine_of(dense: Searcher, query: str, product_id: str, n: int) -> float:
    """The dense (cosine) score of one product for a query, 0.0 when it is not among the top n."""
    for hit in dense.search(query, k=n):
        if hit.doc_id == product_id:
            return float(hit.score)
    return 0.0


class ProductMatcher:
    """E5b-style ranking over the product documents plus a cosine decision. Tests pass `ranker` and `dense` stubs."""

    def __init__(self, catalog: MedicineCatalog, ranker: Searcher | None = None, dense: Searcher | None = None,
                 threshold: float = MATCH_THRESHOLD) -> None:
        self.catalog, self.threshold = catalog, threshold
        self._ranker, self._dense = ranker, dense

    def _load(self) -> None:
        if self._ranker is None:
            from src.ir.step18_config import e5b
            from src.ir.step18_systems import MODELS, Context18, sentence_model

            # Small pinned catalog: avoid native MPS crashes while preserving E5b/model/threshold.
            sentence_model(MODELS['large']).to('cpu')
            context = Context18(self.catalog.match_documents())
            self._ranker = context.build(e5b())
            self._dense = context._dense_part(*e5b().dense[0])

    def match(self, product_name: str, k: int = 3) -> dict[str, Any]:
        """`outcome` is matched, needs_review or no_reference_match, with up to k ranked candidates and scores."""
        self._load()
        assert self._ranker is not None and self._dense is not None
        n = len(self.catalog.products)
        ranked = [h.doc_id for h in self._ranker.search(product_name, k=n)][:k]
        scored = [(pid, cosine_of(self._dense, product_name, pid, n)) for pid in ranked]
        top = scored[0][1] if scored else 0.0
        if not scored or top < self.threshold:
            outcome = "no_reference_match"
        elif top < self.threshold + REVIEW_BAND or (len(scored) > 1 and top - scored[1][1] < 0.02):
            outcome = "needs_review"
        else:
            outcome = "matched"
        return {"outcome": outcome, "score_name": "bge_large_cosine", "score": round(top, 4),
                "threshold": self.threshold, "candidates": scored if outcome != "no_reference_match" else []}


def candidate_json(catalog: MedicineCatalog, product_id: str, confidence: float, read_name: str) -> dict[str, Any]:
    """One contract MedicineMatch. Null reference fields are omitted and named in `not_in_corpus` (CR-23)."""
    product = catalog.products[product_id]
    fields = {k: v for k, v in product.fields.items() if v}
    out: dict[str, Any] = {
        "product_id": product_id, "product_name": product.name, "match_confidence": max(0.0, min(1.0, confidence)),
        "read_from_photo": {"Product name": read_name},
        "from_reference_label": {"Product name": product.name,
                                 **{k.replace("_", " ").capitalize(): v for k, v in fields.items()}},
        "not_in_corpus": product.not_in_corpus, "reference_label_url": product.url,
        "evidence": product.evidence,
    }
    out.update(fields)
    return out


def match_result(catalog: MedicineCatalog, matcher: ProductMatcher, product_name: str) -> dict[str, Any]:
    """The contract PublicMatchResult (CR-23): candidates with reference fields, sections of the best one, outcome."""
    found = matcher.match(product_name)
    out: dict[str, Any] = {
        "banner": BANNER, "outcome": found["outcome"], "score_name": found["score_name"], "score": found["score"],
        "threshold": found["threshold"],
        "candidates": [candidate_json(catalog, pid, score, product_name) for pid, score in found["candidates"]],
    }
    if found["candidates"]:
        best = found["candidates"][0][0]
        sections = reference_sections(catalog, best)
        keys = ("summary", "ingredients", "warnings", "sources", "ingredients_note")
        out["sections"] = {k: sections[k] for k in keys}
        product = catalog.products[best]
        out["summary"] = f"{product.name}: reference label from DailyMed set {product.setid}."
        out["sources"] = sections["summary"][:1] or sections["ingredients"][:1]
    else:
        out["message"] = "No reference match. This product is not one of the reference labels, so no summary is shown."
    return out


class ProductScopedRetriever:
    """Restricts a retriever over all product chunks to the chunks of one product (askPublic with a product_id)."""

    name = "product-scoped"

    def __init__(self, inner: Searcher, allowed: set[str], pool: int) -> None:
        self.inner, self.allowed, self.pool = inner, allowed, pool

    def search(self, query: str, k: int = 10) -> list[Hit]:
        """The inner ranking filtered to the allowed chunks, best first, re-ranked 1..k."""
        hits = [h for h in self.inner.search(query, k=self.pool) if h.doc_id in self.allowed][:k]
        return [h.model_copy(update={"rank": i}) for i, h in enumerate(hits, start=1)]


def based_on(product: ReferenceProduct) -> str:
    """The `based_on` text of a product-scoped answer."""
    return (f"DailyMed label of {product.name} (set id {product.setid}, version {product.version}, "
            f"effective {product.effective_date}); product {product.product_id}")


class MedicineService:
    """What the API holds for the public medicine mode. Everything loads on first use; tests pass stubs."""

    def __init__(self, catalog: MedicineCatalog | None = None, matcher: ProductMatcher | None = None,
                 scoped: Searcher | None = None) -> None:
        self._catalog, self._matcher, self._scoped = catalog, matcher, scoped

    @property
    def catalog(self) -> MedicineCatalog:
        """The ten reference products (read from data/medicine on first use)."""
        if self._catalog is None:
            self._catalog = MedicineCatalog()
        return self._catalog

    @property
    def matcher(self) -> ProductMatcher:
        """The name matcher (the bge-large model loads on its first match)."""
        if self._matcher is None:
            self._matcher = ProductMatcher(self.catalog)
        return self._matcher

    def knows(self, product_id: str | None) -> bool:
        """True when `product_id` names one of the reference products."""
        return bool(product_id) and product_id in self.catalog.products

    def scoped_retriever(self, product_id: str) -> ProductScopedRetriever:
        """The E5b retriever over all product chunks (built once), restricted to one product."""
        if self._scoped is None:
            from src.ir.step18_config import e5b
            from src.ir.step18_systems import Context18

            self._scoped = Context18(list(self.catalog.chunks.values())).build(e5b())
        return ProductScopedRetriever(self._scoped, set(self.catalog.products[product_id].chunk_ids),
                                      pool=len(self.catalog.chunks))

    def ask(self, question: str, product_id: str, provider: Any, settings: Any) -> Any:
        """Answer from the chunks of one reference product only (no score gate: rank scores are not comparable here).

        Returns a RagResult whose sources are marked `label_section`. Extractive passages when the provider is off.
        """
        from src.rag.pipeline import answer_question

        result = answer_question(question, "medicine", self.scoped_retriever(product_id),
                                 self.catalog.product_chunks(product_id), provider, settings, None)
        for source in result.sources:
            source["source_type"] = "label_section"
        return result
