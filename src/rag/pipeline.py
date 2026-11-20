"""The RAG pipeline of docs/RAG_SPEC.md: scope rule, retrieve, score gate, generate, verify, fall back.

Three outcomes: answered, needs_human_check, out_of_scope. Nothing here says a label complies.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from src.checker.citations import best_quote
from src.common.schemas import Chunk
from src.ir.base import Retriever
from src.rag.prompt import ANSWER_SCHEMA, PROMPTS, build_user
from src.rag.provider import Provider, ProviderError, ProviderTimeout, ProviderUnavailable
from src.rag.scope import out_of_scope
from src.rag.settings import RagSettings
from src.rag.verify import NO_ANSWER, parse_structured, verify, verify_structured

BANNER = "Authenticity not verified. Based on a reference label match."
SCORE_NAME = "e5b_top_score"
MESSAGES = {
    "scope": "I can only explain what the regulation text says. I cannot give medical advice. Please ask a pharmacist or doctor.",  # noqa: E501
    "score_gate": "The closest passages are not a strong enough match to answer. A person should check this.",
    "no_hits": "No passages were found. A person should check this.",
    "no_answer": "The model found that the passages do not answer the question. A person should check this.",
    "verification": "A generated answer did not pass the citation checks, so only the closest passages are shown. A person should check this.",  # noqa: E501
    "provider_off": "No language model is running, so only the closest passages are shown. No answer was generated or verified.",  # noqa: E501
    "provider_timeout": "The language model took too long, so only the closest passages are shown. No answer was generated or verified.",  # noqa: E501
    "provider_error": "The language model failed, so only the closest passages are shown. No answer was generated or verified.",  # noqa: E501
}


@dataclass
class RagResult:
    """One question's result. `cause` is internal detail for reports; the wire shape uses outcome and reason."""

    outcome: str
    cause: str
    question: str
    module: str
    answer: str | None = None
    sources: list[dict[str, str]] = field(default_factory=list)
    score: float | None = None
    threshold: float | None = None
    score_name: str = SCORE_NAME
    mode: str = "none"  # generated | extractive | none
    provider: str = "off"
    sentences: list[dict[str, Any]] = field(default_factory=list)
    raw: str = ""
    retrieved: list[str] = field(default_factory=list)
    checks: dict[str, Any] = field(default_factory=dict)
    latency_s: float = 0.0

    @property
    def reason(self) -> str | None:
        """Contract reason for an abstained outcome, None when answered."""
        return None if self.outcome == "answered" else self.outcome

    def to_wire(self, based_on: str = "", banner: bool = True) -> dict[str, Any]:
        """The contract AnswerResponse (public) or its professional twin (no banner, no based_on)."""
        extra: dict[str, Any] = {"banner": BANNER} if banner else {}
        if self.outcome == "answered":
            out: dict[str, Any] = {"abstained": False, "answer": self.answer, "sources": self.sources}
            if banner:
                out["based_on"] = based_on
            return {**out, **extra}
        out = {
            "abstained": True, "reason": self.outcome, "score_name": "scope_rule" if self.cause == "scope" else self.score_name,  # noqa: E501
            "score": self.score, "threshold": self.threshold, "message": MESSAGES[self.cause.split(":")[0]],
        }
        if self.sources:
            out["sources"] = self.sources
        return {**out, **extra}


def _citation(chunk: Chunk, quote: str) -> dict[str, str]:
    """Contract Citation for one chunk with a verbatim quote."""
    return {
        "source_type": "cfr", "chunk_id": chunk.chunk_id, "source": chunk.source, "section": chunk.section,
        "title": chunk.title, "url": chunk.url, "quote": quote,
    }


def extractive_sources(question: str, chunks: list[Chunk], n: int) -> list[dict[str, str]]:
    """Top n chunks as verbatim quotes. Quotes are copied, never reworded."""
    return [_citation(c, best_quote(c.text, question)) for c in chunks[:n]]


def answer_question(
    question: str, module: str, retriever: Retriever, chunks: dict[str, Chunk], provider: Provider,
    settings: RagSettings | None = None, threshold: float | None = None,
) -> RagResult:
    """Run the pipeline. Every path returns a RagResult; provider failures never raise."""
    cfg = settings or RagSettings()
    started = time.perf_counter()
    result = RagResult(outcome="needs_human_check", cause="", question=question, module=module,
                       provider=provider.name, threshold=threshold)

    def done(outcome: str, cause: str) -> RagResult:
        result.outcome, result.cause = outcome, cause
        result.latency_s = round(time.perf_counter() - started, 3)
        return result

    if out_of_scope(question, module):
        result.score = result.threshold = None
        return done("out_of_scope", "scope")
    hits = [h for h in retriever.search(question, k=cfg.k) if h.doc_id in chunks][: cfg.k]
    result.retrieved = [h.doc_id for h in hits]
    if not hits:
        return done("needs_human_check", "no_hits")
    context = [chunks[h.doc_id] for h in hits]
    result.score = float(hits[0].score)
    if threshold is not None and result.score < threshold:
        return done("needs_human_check", "score_gate")

    def fall_back(cause: str) -> RagResult:
        result.sources = extractive_sources(question, context, cfg.fallback_quotes)
        result.mode = "extractive"
        return done("needs_human_check", cause)

    try:
        user = build_user(question, context, cfg.prompt)
        if cfg.output == "json":
            raw = provider.generate_json(PROMPTS[cfg.prompt][0], user, ANSWER_SCHEMA, max_tokens=cfg.max_tokens)
        else:
            raw = provider.generate(PROMPTS[cfg.prompt][0], user, max_tokens=cfg.max_tokens)
    except ProviderUnavailable:
        return fall_back("provider_off")
    except ProviderTimeout:
        return fall_back("provider_timeout")
    except ProviderError:
        return fall_back("provider_error")
    result.raw = raw
    if cfg.output == "json":
        parsed = parse_structured(raw)
        if parsed.no_answer and not parsed.failed:
            return done("needs_human_check", "no_answer")
        check = verify_structured(parsed, context, max_sentences=cfg.max_sentences, min_overlap=cfg.min_overlap)
    else:
        if NO_ANSWER in raw.upper():  # also catches "NO_ANSWER [1]" and "No_ANSWER"
            return done("needs_human_check", "no_answer")
        check = verify(raw, context, max_sentences=cfg.max_sentences, min_overlap=cfg.min_overlap)
    result.checks = {"ok": check.ok, "failed": check.failed, "detail": check.detail,
                     "n_sentences": check.n_sentences, "n_valid_sentences": check.n_valid_sentences}
    if not check.ok:
        return fall_back("verification")
    order: list[int] = []
    for s in check.sentences:
        for m in s.markers:
            if m not in order:
                order.append(m)
    quotes = {m: best_quote(context[m - 1].text, " ".join(s.text for s in check.sentences if m in s.markers))
              for m in order}
    result.sources = [_citation(context[m - 1], quotes[m]) for m in order]
    shown = {m: i for i, m in enumerate(order, start=1)}
    parts = []
    for s in check.sentences:
        marks = "".join(f"[{shown[m]}]" for m in dict.fromkeys(s.markers))
        parts.append(f"{s.text.rstrip()} {marks}")
        result.sentences.append({"text": s.text, "chunk_ids": [context[m - 1].chunk_id for m in dict.fromkeys(s.markers)]})  # noqa: E501
    result.answer = " ".join(parts)
    result.mode = "generated"
    return done("answered", "ok")
