"""RAG settings in one object (docs/RAG_SPEC.md). Echoed in reports so a run can be repeated."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RagSettings:
    """k chunks in the context, answer length, grounding guard and provider limits."""

    k: int = 5
    prompt: str = "v1"  # v1 is the frozen run. v2 is an unused experiment (failed a 6-query dev check, spec section 14)
    max_sentences: int = 4
    min_overlap: float = 0.40  # a guess made before any run, frozen in the spec
    fallback_quotes: int = 3
    max_tokens: int = 220
    timeout_s: float = 120.0
    ollama_url: str = "http://localhost:11434"

    def echo(self) -> dict[str, object]:
        """The settings as a dict, for reports."""
        return dict(self.__dict__)
