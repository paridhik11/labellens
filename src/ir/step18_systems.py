"""Systems for the Step 18c experiments: enrichment, bigger embedders, ensembles, MedCPT.

A system is an RRF fusion of a BM25 list and one or more dense lists:
  bm25 part   (stem, enrich)             stem: light-stemmed index; enrich: heading prepended
  dense parts (model, prefix, enrich)    model small, base or large (bge v1.5); prefix: BGE query
                                         instruction; enrich: heading prepended
  medcpt                                 MedCPT query and article encoders as one more dense list
With bm25 plain and one small dense part this is exactly plain hybrid, and with bm25 stemmed
plus small+prefix it is hybrid+stem+prefix; check_baselines() proves both on all queries.

HEADING ENRICHMENT ("for indexing only")
For indexing, the text of a chunk becomes
    "21 CFR Part 801, section 801.109: <section heading>. <chunk text>"
so a query that names a topic or a part can match the heading words that the chunk text does
not repeat. Chunk ids stay the same, results are scored by id, and Hit text shown to people
(and the unjudged CSV) is the original chunk text.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from src.common.schemas import Chunk
from src.ir.base import Retriever
from src.ir.bm25 import BM25Retriever, InvertedIndex
from src.ir.dense import BGE_QUERY_PREFIX, DenseRetriever
from src.ir.fusion import FusionRetriever
from src.ir.medcpt import MedCPTDenseRetriever
from src.ir.partboost import part_of

MODELS = {"small": "BAAI/bge-small-en-v1.5", "base": "BAAI/bge-base-en-v1.5", "large": "BAAI/bge-large-en-v1.5"}
_ST_MODELS: dict[str, object] = {}


def enrich_chunk(chunk: Chunk) -> Chunk:
    """Copy of a chunk whose text starts with its part, section and heading (new content hash)."""
    part = part_of(chunk.chunk_id).removeprefix("21cfr")
    text = f"21 CFR Part {part}, section {chunk.section}: {chunk.title}. {chunk.text}"
    return chunk.model_copy(update={"text": text, "hash": hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]})


def sentence_model(name: str) -> object:
    """Loads a sentence-transformer once per process, from the local cache only."""
    import os

    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    if name not in _ST_MODELS:
        from sentence_transformers import SentenceTransformer

        _ST_MODELS[name] = SentenceTransformer(name)
    return _ST_MODELS[name]


@dataclass(frozen=True)
class Sys18:
    """One fused system (see the module docstring)."""

    bm25: tuple[bool, bool] | None = (False, False)  # (stem, enrich); None = no BM25 list
    dense: tuple[tuple[str, bool, bool], ...] = (("small", False, False),)  # (model, prefix, enrich)
    medcpt: bool = False

    @property
    def name(self) -> str:
        parts = []
        if self.bm25 is not None:
            parts.append("bm25" + ("+stem" if self.bm25[0] else "") + ("+head" if self.bm25[1] else ""))
        for model, prefix, enrich in self.dense:
            parts.append(model + ("+prefix" if prefix else "") + ("+head" if enrich else ""))
        if self.medcpt:
            parts.append("medcpt")
        return "rrf[" + ", ".join(parts) + "]"


PLAIN_HYBRID = Sys18()
STEM_PREFIX_HYBRID = Sys18(bm25=(True, False), dense=(("small", True, False),))


class Context18:
    """Everything one module needs to build any Sys18 (indexes and embeddings are built once)."""

    def __init__(self, chunks: list[Chunk]) -> None:
        self.chunks = chunks
        self.enriched = [enrich_chunk(c) for c in chunks]
        self._bm25: dict[tuple[bool, bool], Retriever] = {}
        self._dense: dict[tuple[str, bool, bool], Retriever] = {}
        self._medcpt: Retriever | None = None
        self._built: dict[Sys18, Retriever] = {}

    def _bm25_part(self, stem: bool, enrich: bool) -> Retriever:
        key = (stem, enrich)
        if key not in self._bm25:
            src = self.enriched if enrich else self.chunks
            ix = InvertedIndex(stem=stem).build([(c.chunk_id, c.text) for c in src])
            self._bm25[key] = BM25Retriever(ix)
        return self._bm25[key]

    def _dense_part(self, model: str, prefix: bool, enrich: bool) -> Retriever:
        key = (model, prefix, enrich)
        if key not in self._dense:
            src = self.enriched if enrich else self.chunks
            self._dense[key] = DenseRetriever.from_chunks(
                src, model_name=MODELS[model], model=sentence_model(MODELS[model]),
                query_prefix=BGE_QUERY_PREFIX if prefix else "")
        return self._dense[key]

    def _medcpt_part(self) -> Retriever:
        if self._medcpt is None:
            self._medcpt = MedCPTDenseRetriever.from_chunks(self.chunks)
        return self._medcpt

    def build(self, system: Sys18) -> Retriever:
        """The fused retriever for a system."""
        if system not in self._built:
            parts: list[Retriever] = []
            if system.bm25 is not None:
                parts.append(self._bm25_part(*system.bm25))
            parts += [self._dense_part(*d) for d in system.dense]
            if system.medcpt:
                parts.append(self._medcpt_part())
            self._built[system] = FusionRetriever(parts, name=system.name)
        return self._built[system]


def experiments() -> list[tuple[str, str, str, Sys18]]:
    """The 18c retrieval experiments as (id, title, what changed, system).

    E2: heading and part number prepended for indexing, on both first stages.
    E3: bge-base and bge-large as the dense list, and two-embedder ensembles.
    E4: MedCPT bi-encoder as the dense list or as an extra list (E4d and E4e, the MedCPT
        cross-encoder, are run by src.ir.step18_rerank).
    """
    s = ("small", False, False)
    sp = ("small", True, False)
    out = [
        ("E2a", "heading prepended, BM25 side, plain hybrid", "BM25 index text gets part, section and heading",
         Sys18(bm25=(False, True), dense=(s,))),
        ("E2b", "heading prepended, dense side, plain hybrid", "bge-small embeds heading plus text",
         Sys18(bm25=(False, False), dense=(("small", False, True),))),
        ("E2c", "heading prepended, both sides, plain hybrid", "BM25 and bge-small both index heading plus text",
         Sys18(bm25=(False, True), dense=(("small", False, True),))),
        ("E2d", "heading prepended, BM25 side, stem+prefix hybrid", "as E2a on the stem+prefix hybrid",
         Sys18(bm25=(True, True), dense=(sp,))),
        ("E2e", "heading prepended, dense side, stem+prefix hybrid", "as E2b on the stem+prefix hybrid",
         Sys18(bm25=(True, False), dense=(("small", True, True),))),
        ("E2f", "heading prepended, both sides, stem+prefix hybrid", "as E2c on the stem+prefix hybrid",
         Sys18(bm25=(True, True), dense=(("small", True, True),))),
        ("E3a", "bge-base as the dense list, plain hybrid", "dense list is bge-base, no prefix, plain BM25",
         Sys18(bm25=(False, False), dense=(("base", False, False),))),
        ("E3b", "bge-base as the dense list, stem+prefix", "bge-base with the query prefix, stemmed BM25",
         Sys18(bm25=(True, False), dense=(("base", True, False),))),
        ("E3c", "bge-large as the dense list, plain hybrid", "dense list is bge-large, no prefix, plain BM25",
         Sys18(bm25=(False, False), dense=(("large", False, False),))),
        ("E3d", "bge-large as the dense list, stem+prefix", "bge-large with the query prefix, stemmed BM25",
         Sys18(bm25=(True, False), dense=(("large", True, False),))),
        ("E3e", "ensemble bge-small + bge-base (+ stemmed BM25)",
         "three-list RRF: stemmed BM25, small+prefix, base+prefix",
         Sys18(bm25=(True, False), dense=(sp, ("base", True, False)))),
        ("E3f", "ensemble bge-small + bge-large (+ stemmed BM25)",
         "three-list RRF: stemmed BM25, small+prefix, large+prefix",
         Sys18(bm25=(True, False), dense=(sp, ("large", True, False)))),
        ("E4a", "MedCPT bi-encoder as the dense list, plain BM25", "dense list is MedCPT (query and article encoders)",
         Sys18(bm25=(False, False), dense=(), medcpt=True)),
        ("E4b", "MedCPT bi-encoder as the dense list, stemmed BM25", "as E4a with stemmed BM25",
         Sys18(bm25=(True, False), dense=(), medcpt=True)),
        ("E4c", "ensemble bge-small + MedCPT (+ stemmed BM25)", "three-list RRF: stemmed BM25, small+prefix, MedCPT",
         Sys18(bm25=(True, False), dense=(sp,), medcpt=True)),
    ]
    return out


def check_baselines(rows: list, ctxs: dict[str, Context18], reference: dict[str, dict[str, list[str]]]) -> list[str]:
    """Rows where a Context18 baseline disagrees with the Step 17 retrievers (empty when identical)."""
    bad = []
    for name, system in (("hybrid", PLAIN_HYBRID), ("hybrid+stem+prefix", STEM_PREFIX_HYBRID)):
        for r in rows:
            got = [h.doc_id for h in ctxs[r.module].build(system).search(r.query, k=50)]
            if got != reference[name][r.qid]:
                bad.append(f"{name} {r.qid}")
    return bad
