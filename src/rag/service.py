"""What the API holds for asking questions: retrievers, chunks, a provider and the frozen threshold.

Retrieval is the frozen E5b system (src/ir/step18_config). It loads lazily on the first question, so the API
starts fast, and a missing embedding cache or a changed corpus raises ``RetrievalUnavailable`` instead of
silently using another retriever.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.common.schemas import Chunk
from src.ir.base import Retriever
from src.rag.applicability import chunk_filter
from src.rag.pipeline import RagResult, answer_question
from src.rag.provider import NullProvider, Provider, provider_from_env
from src.rag.settings import RagSettings

CONFIG_PATH = Path(__file__).resolve().parents[2] / "data" / "rag" / "rag_config.json"
CORPUS_PATH = Path(__file__).resolve().parents[2] / "data" / "processed" / "regs.jsonl"


class RetrievalUnavailable(RuntimeError):
    """The frozen retrieval system cannot be built (cache missing, corpus changed)."""


def frozen_threshold(path: Path = CONFIG_PATH) -> float | None:
    """The score-gate threshold written at freeze time, or None when no config exists yet."""
    if not path.exists():
        return None
    value = json.loads(path.read_text(encoding="utf-8")).get("threshold")
    return None if value is None else float(value)


class RagService:
    """Answers one question for one module. Tests pass stub retrievers, chunks and a fake provider."""

    def __init__(
        self, provider: Provider | None = None, settings: RagSettings | None = None, threshold: float | None = None,
        retrievers: dict[str, Retriever] | None = None, chunks: dict[str, dict[str, Chunk]] | None = None,
    ) -> None:
        self.settings = settings or RagSettings()
        self.provider = provider if provider is not None else provider_from_env(self.settings)
        self.threshold = threshold
        self._retrievers = retrievers
        self._chunks = chunks or {}

    def _load(self) -> dict[str, Retriever]:
        if self._retrievers is None:
            try:
                from src.ir.step18_config import load_system
                from src.rag import indexes

                indexes.pull()  # copy built indexes from the shared store, so nothing is rebuilt
                self._retrievers = load_system()
                indexes.push()
            except Exception as error:  # cache missing, config hash mismatch, model not installed
                raise RetrievalUnavailable(f"frozen retrieval is not available: {error}") from error
        return self._retrievers

    def chunks(self, module: str) -> dict[str, Chunk]:
        """Chunks of one module by id (read from the corpus once)."""
        if module not in self._chunks:
            from src.checker.retrieval import module_chunks

            self._chunks[module] = module_chunks(module, CORPUS_PATH)
        return self._chunks[module]

    def ask(
        self, question: str, module: str, provider: Provider | None = None, settings: RagSettings | None = None,
        product_text: str | None = None,
    ) -> RagResult:
        """Run the pipeline in one module. Never mixes modules. A provider or settings can be given for one call.

        product_text (device module): the product record as text. Passages of sections that do not apply to
        this product are dropped and each section shows once, also in what the model sees.
        """
        retriever = self._load()[module]
        context_filter = chunk_filter(product_text) if product_text is not None else None
        return answer_question(question, module, retriever, self.chunks(module), provider or self.provider,
                               settings or self.settings, self.threshold, context_filter=context_filter)

    @property
    def mode(self) -> str:
        """generated when a provider is configured, otherwise extractive."""
        return "extractive" if isinstance(self.provider, NullProvider) else "generated"
