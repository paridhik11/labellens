"""LLM providers. Ollama is the default; the fake provider keeps tests and CI free of any model."""
from __future__ import annotations

import os
from typing import Protocol

from src.rag.settings import RagSettings


class ProviderError(RuntimeError):
    """The provider failed (timeout, bad reply). The pipeline falls back to extractive quotes."""


class ProviderUnavailable(ProviderError):
    """No provider is configured (the model is off)."""


class Provider(Protocol):
    """Anything that turns a system and a user prompt into text."""

    name: str

    def generate(self, system: str, user: str, *, max_tokens: int) -> str:
        """Return the model text, or raise ProviderError."""
        ...


class NullProvider:
    """Provider off. Always raises ProviderUnavailable, so the API runs in extractive mode."""

    name = "off"

    def generate(self, system: str, user: str, *, max_tokens: int) -> str:
        """Always raises."""
        raise ProviderUnavailable("no language model configured")


class FakeProvider:
    """Returns canned replies in order (the last one repeats). A reply that is an Exception is raised."""

    name = "fake"

    def __init__(self, *replies: str | Exception) -> None:
        self.replies = list(replies) or ["NO_ANSWER"]
        self.calls: list[tuple[str, str]] = []

    def generate(self, system: str, user: str, *, max_tokens: int) -> str:
        """Record the call and return or raise the next canned reply."""
        self.calls.append((system, user))
        reply = self.replies[min(len(self.calls) - 1, len(self.replies) - 1)]
        if isinstance(reply, Exception):
            raise reply
        return reply


class OllamaProvider:
    """Local Ollama server, temperature 0 and a fixed seed so a run repeats on the same model build."""

    def __init__(self, model: str, settings: RagSettings | None = None) -> None:
        self.model = model
        self.settings = settings or RagSettings()
        self.name = f"ollama:{model}"

    def generate(self, system: str, user: str, *, max_tokens: int) -> str:
        """POST /api/chat. Any HTTP or format problem becomes ProviderError."""
        import httpx

        body = {
            "model": self.model, "stream": False, "keep_alive": "30m",
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "options": {"temperature": 0, "seed": 42, "num_ctx": 4096, "num_predict": max_tokens},
        }
        try:
            reply = httpx.post(f"{self.settings.ollama_url}/api/chat", json=body, timeout=self.settings.timeout_s)
            reply.raise_for_status()
            return str(reply.json()["message"]["content"])
        except (httpx.HTTPError, KeyError, ValueError) as error:
            raise ProviderError(f"ollama call failed: {error}") from error


def provider_from_env(settings: RagSettings | None = None) -> Provider:
    """LABELLENS_LLM=ollama:<tag> selects Ollama. Unset or anything else means off."""
    value = os.environ.get("LABELLENS_LLM", "").strip()
    if value.startswith("ollama:") and len(value) > len("ollama:"):
        return OllamaProvider(value.split(":", 1)[1], settings)
    return NullProvider()
