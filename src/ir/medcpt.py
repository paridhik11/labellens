"""MedCPT dense retrieval (Step 18): an asymmetric bi-encoder pair trained on PubMed search logs.

Unlike bge, MedCPT uses TWO encoders: a query encoder (max 64 tokens) for the query and an
article encoder (max 512 tokens) for each passage. Following the model cards, an article is
encoded from a (title, text) pair, both sides use the [CLS] vector as the embedding, and the
score is the plain inner product (vectors are not normalised). Here the "article" is a corpus
chunk, its title is the section heading.

The model was trained on biomedical literature, not on regulations, so whether it transfers
to CFR text is an open question that the Step 18 CV answers.

Passage embeddings are cached in data/processed (not tracked), keyed by the chunk ids and
content hashes, like the bge cache.
"""
from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from pathlib import Path

import numpy as np

from src.common.schemas import Chunk, Hit

ARTICLE_MODEL = "ncbi/MedCPT-Article-Encoder"
QUERY_MODEL = "ncbi/MedCPT-Query-Encoder"
CACHE_DIR = Path("data/processed")


def _fingerprint(chunks: list[Chunk]) -> str:
    blob = "\n".join(f"{c.chunk_id}:{c.hash}" for c in chunks).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


def cls_encoder(model_name: str, max_length: int, batch_size: int = 16) -> Callable[[list], np.ndarray]:
    """Returns a function mapping texts (or [title, text] pairs) to their [CLS] vectors.

    The model is loaded lazily from the local cache only (never downloaded), and batches are
    kept small because the machine is shared.
    """
    state: dict = {}

    def encode(items: list) -> np.ndarray:
        import os

        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        import torch
        from transformers import AutoModel, AutoTokenizer

        if "model" not in state:
            state["tok"] = AutoTokenizer.from_pretrained(model_name)
            state["model"] = AutoModel.from_pretrained(model_name).eval()
        out = []
        with torch.no_grad():
            for i in range(0, len(items), batch_size):
                enc = state["tok"](items[i:i + batch_size], truncation=True, padding=True,
                                   return_tensors="pt", max_length=max_length)
                out.append(state["model"](**enc).last_hidden_state[:, 0, :].numpy())
        return np.concatenate(out).astype(np.float32)

    return encode


class MedCPTDenseRetriever:
    """Inner-product search over cached MedCPT article embeddings."""

    name = "medcpt"

    def __init__(self, embeddings: np.ndarray, chunk_ids: list[str], texts: list[str],
                 query_encoder: Callable[[list], np.ndarray]) -> None:
        """Args:
            embeddings: one row per chunk (article-encoder [CLS] vectors).
            chunk_ids: chunk id per row.
            texts: chunk text per row (returned in Hit.text).
            query_encoder: maps a list of query strings to their [CLS] vectors.
        """
        self._emb = embeddings
        self._ids = chunk_ids
        self._texts = texts
        self._encode_query = query_encoder

    def search(self, query: str, k: int = 10) -> list[Hit]:
        """Top-k chunks by inner product with the query vector."""
        q = self._encode_query([query])[0]
        scores = self._emb @ q
        order = np.argsort(-scores, kind="stable")[:k]
        return [Hit(doc_id=self._ids[i], score=float(scores[i]), rank=r + 1, text=self._texts[i])
                for r, i in enumerate(order)]

    @classmethod
    def from_chunks(cls, chunks: list[Chunk], cache_dir: Path | None = CACHE_DIR,
                    article_encoder: Callable[[list], np.ndarray] | None = None,
                    query_encoder: Callable[[list], np.ndarray] | None = None) -> "MedCPTDenseRetriever":
        """Builds the retriever, encoding the chunks once and caching the vectors on disk."""
        ids = [c.chunk_id for c in chunks]
        texts = [c.text for c in chunks]
        qenc = query_encoder or cls_encoder(QUERY_MODEL, 64)
        emb = None
        paths = None
        if cache_dir is not None:
            stem = Path(cache_dir) / f"medcpt_cache_{_fingerprint(chunks)}"
            paths = (stem.with_suffix(".npy"), stem.with_suffix(".json"))
            if paths[0].exists() and paths[1].exists() and json.loads(paths[1].read_text(encoding="utf-8")) == ids:
                emb = np.load(str(paths[0]))
        if emb is None:
            aenc = article_encoder or cls_encoder(ARTICLE_MODEL, 512)
            emb = aenc([[c.title, c.text] for c in chunks])
            if paths is not None:
                Path(cache_dir).mkdir(parents=True, exist_ok=True)
                np.save(str(paths[0]), emb)
                paths[1].write_text(json.dumps(ids), encoding="utf-8")
        return cls(emb, ids, texts, qenc)
