"""Dense retrieval using sentence-transformer embeddings and FAISS ANN index.

WHAT IS AN EMBEDDING?
An embedding is a list of numbers that captures the meaning of a piece of text.
Two sentences with the same meaning get vectors that are numerically close to
each other; unrelated sentences get vectors that are far apart.

Tiny worked example (dimensions abbreviated):
  model.encode("Labeling must include net weight.")         -> [0.12, -0.44, 0.09, ...]
  model.encode("The net quantity statement is required.")  -> [0.14, -0.41, 0.07, ...]
  model.encode("Investigational devices need an IDE.")     -> [-0.31, 0.80, -0.52, ...]

The first two vectors are close (cosine similarity ~ 0.9) because they say the
same thing in different words. BM25 misses this because the words do not
overlap; a dense retriever finds it.

CACHING
Embeddings are expensive to recompute. After the first encode, vectors are
saved to disk as a NumPy array (.npy) and an ID list (.json). On subsequent
calls the cache is loaded if the corpus fingerprint (SHA-256 of all
chunk_id:content_hash pairs) matches. Including the content hash ensures the
cache is invalidated when a chunk's text changes even if its ID stays the same.

FAISS
FAISS is a library for fast nearest-neighbour search over large vector
collections. We use IndexFlatIP (inner product) which equals cosine similarity
after L2 normalisation.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import faiss
import numpy as np

from src.common.schemas import Chunk, Hit

MODEL_NAME = "BAAI/bge-small-en-v1.5"
CACHE_DIR = Path("data/processed")


def _corpus_fingerprint(chunk_keys: list[str]) -> str:
    """Returns a short hash of the ordered list of 'chunk_id:content_hash' keys.

    Including content hashes (not just IDs) ensures the cache is invalidated
    when a chunk's text changes even if its chunk_id remains the same.
    """
    blob = "\n".join(chunk_keys).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


def _cache_paths(fingerprint: str, model_tag: str, cache_dir: Path = CACHE_DIR) -> tuple[Path, Path]:
    """Returns (embeddings .npy path, metadata .json path) for the given fingerprint."""
    stem = f"dense_cache_{model_tag}_{fingerprint}"
    return Path(cache_dir) / f"{stem}.npy", Path(cache_dir) / f"{stem}.json"


class DenseRetriever:
    """Retriever that encodes queries with a sentence-transformer and searches a FAISS index.

    Satisfies the Retriever protocol defined in src.ir.base.
    """

    name = "dense"

    def __init__(
        self,
        embeddings: np.ndarray,
        chunk_ids: list[str],
        texts: list[str],
        model_name: str = MODEL_NAME,
        model: object | None = None,
    ) -> None:
        """Stores normalised embeddings and builds a FAISS flat inner-product index."""
        self._model_name = model_name
        self._chunk_ids = chunk_ids
        self._texts = texts
        self._model = model

        # L2-normalise so inner product equals cosine similarity.
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1.0, norms)
        normed = (embeddings / norms).astype(np.float32)

        d = normed.shape[1]
        self._index = faiss.IndexFlatIP(d)
        self._index.add(normed)

    def _encode_query(self, query: str) -> np.ndarray:
        """Encodes a single query string to a normalised float32 vector."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer  # lazy import

            self._model = SentenceTransformer(self._model_name)
        vec = self._model.encode([query], normalize_embeddings=True, show_progress_bar=False)
        return vec.astype(np.float32)

    def search(self, query: str, k: int = 10) -> list[Hit]:
        """Returns top-k chunks by cosine similarity to the query embedding."""
        q_vec = self._encode_query(query)
        scores, indices = self._index.search(q_vec, k)
        hits: list[Hit] = []
        for idx, score in zip(indices[0], scores[0], strict=True):
            if idx < 0 or idx >= len(self._chunk_ids):
                continue
            hits.append(Hit(
                doc_id=self._chunk_ids[idx],
                score=float(score),
                rank=len(hits) + 1,
                text=self._texts[idx],
            ))
        return hits

    @classmethod
    def from_chunks(
        cls,
        chunks: list[Chunk],
        model_name: str = MODEL_NAME,
        cache_dir: Path | None = CACHE_DIR,
        force_recompute: bool = False,
        model: object | None = None,
    ) -> "DenseRetriever":
        """Builds a DenseRetriever from a list of Chunk objects, using disk cache if available.

        Args:
            chunks: Corpus chunks to encode.
            model_name: Sentence-transformer model identifier.
            cache_dir: Directory for the embedding cache. Pass None to skip caching.
            force_recompute: If True, ignore existing cache and re-encode.
            model: Optional pre-loaded (or fake) encoder. If None, loads model_name.
                   Injecting a fake encoder makes tests fast without a network call.
        """
        chunk_ids = [c.chunk_id for c in chunks]
        texts = [c.text for c in chunks]
        # Build fingerprint from id+content_hash pairs so that text changes
        # (without id changes) also invalidate the cache.
        chunk_keys = [f"{c.chunk_id}:{c.hash}" for c in chunks]
        fp = _corpus_fingerprint(chunk_keys)
        model_tag = model_name.replace("/", "_")

        if cache_dir is not None:
            emb_path, meta_path = _cache_paths(fp, model_tag, Path(cache_dir))
            if not force_recompute and emb_path.exists() and meta_path.exists():
                print(f"[DenseRetriever] Loading cached embeddings from {emb_path}")
                embeddings = np.load(str(emb_path))
                cached_ids = json.loads(meta_path.read_text(encoding="utf-8"))
                if cached_ids == chunk_ids:
                    return cls(embeddings, chunk_ids, texts, model_name=model_name, model=model)
                print("[DenseRetriever] Cache mismatch -- recomputing.")

        print(f"[DenseRetriever] Encoding {len(chunks)} chunks with {model_name} ...")
        if model is None:
            from sentence_transformers import SentenceTransformer  # lazy import
            model = SentenceTransformer(model_name)
        embeddings = model.encode(
            texts,
            batch_size=64,
            show_progress_bar=True,
            normalize_embeddings=True,
        ).astype(np.float32)

        if cache_dir is not None:
            Path(cache_dir).mkdir(parents=True, exist_ok=True)
            emb_path, meta_path = _cache_paths(fp, model_tag, Path(cache_dir))
            np.save(str(emb_path), embeddings)
            meta_path.write_text(json.dumps(chunk_ids), encoding="utf-8")
            print(f"[DenseRetriever] Embeddings cached to {emb_path}")

        return cls(embeddings, chunk_ids, texts, model_name=model_name, model=model)

    @classmethod
    def from_jsonl(
        cls,
        corpus_path: str | Path,
        model_name: str = MODEL_NAME,
        cache_dir: Path | None = CACHE_DIR,
        force_recompute: bool = False,
    ) -> "DenseRetriever":
        """Convenience loader: reads a regs.jsonl corpus and calls from_chunks."""
        chunks = []
        for line in Path(corpus_path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                chunks.append(Chunk.model_validate_json(line))
        return cls.from_chunks(
            chunks,
            model_name=model_name,
            cache_dir=cache_dir,
            force_recompute=force_recompute,
        )
