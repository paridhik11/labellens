"""The RAG pipeline of docs/RAG_SPEC.md: scope rule, retrieve, score gate, generate, verify, fall back.

Three outcomes: answered, needs_human_check, out_of_scope. Nothing here says a label complies.
"""
from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from src.checker.citations import best_quote
from src.common.schemas import Chunk
from src.ir.base import Retriever
from src.rag import rerank, selection
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
    "rerank_gate": "No sentence in the closest passages is a strong enough match to answer. A person should check this.",  # noqa: E501
    "no_answer": "The model found that the passages do not answer the question. A person should check this.",
    "verification": "A generated answer did not pass the citation checks, so only the closest passages are shown. A person should check this.",  # noqa: E501
    # Medicine mode: nothing relevant was found, which is not the same as "no language model is running".
    "no_match": "This label doesn't seem to answer that.",
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

    def message(self) -> str:
        """Plain-language reason. In medicine mode a gate miss says the label does not answer the question."""
        cause = self.cause.split(":")[0]
        if self.module == "medicine" and cause in ("score_gate", "rerank_gate", "no_hits"):
            return MESSAGES["no_match"]
        return MESSAGES[cause]

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
            "score": self.score, "threshold": self.threshold, "message": self.message(),
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
    context_filter: Callable[[list[Chunk]], list[Chunk]] | None = None, quote_question: str | None = None,
) -> RagResult:
    """Run the pipeline. Every path returns a RagResult; provider failures never raise.

    context_filter (optional) removes passages that do not apply to one product and repeated sections before
    anything is shown or given to the model. The score gate still reads the unfiltered top hit, so the gate is
    unchanged. With a filter, twice cfg.k hits are retrieved so up to cfg.k remain after filtering.

    quote_question (optional) picks the shown sentences of the extractive passages. Live labels retrieve with an
    expanded query ("... how supplied, store at") but quote with the person's own question, so "how to store it"
    shows the "Store at ..." sentence, not "Tablets are available as follows".
    """
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
    depth = cfg.k * 2 if context_filter else cfg.k
    hits = [h for h in retriever.search(question, k=depth) if h.doc_id in chunks][:depth]
    if not hits:
        result.retrieved = []
        return done("needs_human_check", "no_hits")
    result.score = float(hits[0].score)
    context = [chunks[h.doc_id] for h in hits]
    if context_filter:
        context = context_filter(context)[: cfg.k]
    else:
        context = context[: cfg.k]
    result.retrieved = [c.chunk_id for c in context]
    if not context:
        return done("needs_human_check", "no_hits")
    if threshold is not None and result.score < threshold:
        return done("needs_human_check", "score_gate")

    def fall_back(cause: str) -> RagResult:
        quote_q = quote_question or question
        shown_sentences = reranked_display_sources(quote_q, context) if cfg.rerank_display else []
        result.sources = shown_sentences or extractive_sources(quote_q, context, cfg.fallback_quotes)
        result.mode = "extractive"
        return done("needs_human_check", cause)

    if cfg.output == "rerank":
        return _reranked(result, question, context, cfg, done)
    candidates: list[selection.Candidate] = []
    try:
        if cfg.output == "select":
            candidates = selection.build_candidates(context)
            raw = provider.generate_json(selection.SYSTEM_V4, selection.build_user(question, candidates),
                                         selection.SELECT_SCHEMA, max_tokens=cfg.max_tokens)
            return _selected(result, raw, candidates, context, done, fall_back)
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


def _selected(
    result: RagResult, raw: str, candidates: list[selection.Candidate], context: list[Chunk], done: Any,
    fall_back: Any,
) -> RagResult:
    """Finish selection mode: the answer is the chosen sentences, verbatim, each cited to its chunk."""
    result.raw = raw
    sel = selection.parse_selection(raw, len(candidates))
    if sel.no_answer:
        return done("needs_human_check", "no_answer")
    result.checks = {"ok": not sel.failed, "failed": sel.failed, "detail": sel.detail,
                     "n_sentences": len(sel.numbers), "n_valid_sentences": len(sel.numbers),
                     "n_candidates": len(candidates)}
    if sel.failed:
        return fall_back("verification")
    chosen = [candidates[n - 1] for n in sel.numbers]
    order: list[str] = []
    for c in chosen:
        if c.chunk_id not in order:
            order.append(c.chunk_id)
    chunk_by_id = {ch.chunk_id: ch for ch in context}
    result.sources = [_citation(chunk_by_id[cid], " ".join(c.text for c in chosen if c.chunk_id == cid))
                      for cid in order]
    parts = []
    for c in chosen:
        parts.append(f"{c.text.rstrip()} [{order.index(c.chunk_id) + 1}]")
        result.sentences.append({"text": c.text, "chunk_ids": [c.chunk_id]})
    result.answer = " ".join(parts)
    result.mode = "selected"
    return done("answered", "ok")


def _sentence_sources(shown: list[rerank.Scored], context: list[Chunk]) -> tuple[list[dict[str, str]], list[str]]:
    """Citations (one per chunk, quote = its shown sentences) and the answer parts with chunk markers."""
    chunk_by_id = {ch.chunk_id: ch for ch in context}
    order: list[str] = []
    for s in shown:
        if s.candidate.chunk_id not in order:
            order.append(s.candidate.chunk_id)
    sources = [_citation(chunk_by_id[cid], " ".join(s.candidate.text for s in shown if s.candidate.chunk_id == cid))
               for cid in order]
    parts = [f"{s.candidate.text.rstrip()} [{order.index(s.candidate.chunk_id) + 1}]" for s in shown]
    return sources, parts


def reranked_display_sources(question: str, context: list[Chunk]) -> list[dict[str, str]]:
    """Sources of the default extractive display: top cross-encoder sentences at the frozen T, or [] when the
    cross-encoder is unavailable, no config exists or no sentence reaches T (the caller then shows chunk quotes)."""
    floor = rerank.frozen_threshold()
    if floor is None:
        return []
    try:
        ranked = rerank.rank_sentences(question, context)
    except Exception:  # model not cached, torch missing: the old display is the fallback
        return []
    return _sentence_sources(rerank.top_sentences(ranked, floor), context)[0]


def _reranked(result: RagResult, question: str, context: list[Chunk], cfg: RagSettings, done: Any) -> RagResult:
    """Rerank mode: no provider. The answer is the top cross-encoder sentences at or above the threshold."""
    ranked = rerank.rank_sentences(question, context)
    top = ranked[: rerank.TOP]
    result.checks = {"n_candidates": len(ranked), "scored": [
        {"text": s.candidate.text, "chunk_id": s.candidate.chunk_id, "score": round(s.score, 4)} for s in top]}
    floor = float("-inf") if cfg.rerank_threshold is None else cfg.rerank_threshold
    shown = rerank.top_sentences(ranked, floor)
    if not shown:
        return done("needs_human_check", "rerank_gate")
    result.sources, parts = _sentence_sources(shown, context)
    for s in shown:
        result.sentences.append({"text": s.candidate.text, "chunk_ids": [s.candidate.chunk_id],
                                 "score": round(s.score, 4)})
    result.answer = " ".join(parts)
    result.mode = "reranked"
    return done("answered", "ok")
