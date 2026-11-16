"""RAG settings in one object (docs/RAG_SPEC.md). Echoed in reports so a run can be repeated."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RagSettings:
    """k chunks in the context, answer length, grounding guard and provider limits."""

    k: int = 5
    prompt: str = "v1"  # v1 is the frozen run. v2 is an unused experiment (failed a 6-query dev check, spec section 14)
    output: str = "text"  # "text" (markers in prose, Step 23) or "json" (structured outputs, Step 23e)
    max_sentences: int = 4
    min_overlap: float = 0.40  # a guess made before any run, frozen in the spec
    fallback_quotes: int = 3
    max_tokens: int = 220
    timeout_s: float = 120.0
    ollama_url: str = "http://localhost:11434"

    def echo(self) -> dict[str, object]:
        """The settings as a dict, for reports."""
        return dict(self.__dict__)


# Step 24c: the optional AI answer. Same model, prompt, schema and token cap as the frozen Step 23e run
# (tests/test_ai_mode.py checks the two stay equal), with the 90 s limit of the API.
AI_MODEL = "qwen2.5:3b-instruct-q4_K_M"
AI_TIMEOUT_S = 90.0
AI_SETTINGS = RagSettings(output="json", prompt="v3", max_tokens=300, timeout_s=AI_TIMEOUT_S)
