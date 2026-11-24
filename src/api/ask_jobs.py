"""The optional AI answer (Step 24c): a 202 job around the Step 23 pipeline with the structured-output model.

Extractive stays the default of askPublic and askProfessional. `mode=ai` starts a job. The job never ends
in a failure the user can do nothing about: a missing Ollama, a slow model (90 s) or an answer that fails
verification all end `done` with the extractive passages and a `fallback_reason`. The one exception is a
retrieval system that cannot be built at all, because then there are no passages to show either.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.api.checks import advance_job
from src.api.db import utcnow
from src.api.models import AskResult
from src.rag.pipeline import RagResult
from src.rag.provider import NullProvider, OllamaProvider, Provider
from src.rag.service import RetrievalUnavailable
from src.rag.settings import AI_MODEL, AI_SETTINGS

FALLBACK_REASONS = {
    "provider_off": "model_unavailable",
    "provider_error": "model_unavailable",
    "provider_timeout": "timeout",
    "verification": "verification_failed",
}
PUBLIC_BASED_ON = "21 CFR Parts 201, 208 and 211 (no product label text is used yet)"


def build_payload(
    result: RagResult, module: str, product_id: str | None, fallback: str | None = None, based_on: str | None = None,
) -> dict[str, Any]:
    """The contract AskJobResult for one finished pipeline run."""
    if module == "medicine":
        answer = result.to_wire(based_on=based_on or f"{PUBLIC_BASED_ON}; product {product_id}")
    else:
        answer = result.to_wire(banner=False)
    out: dict[str, Any] = {
        "answer": answer, "model": AI_MODEL,
        "model_used": result.mode == "generated" or result.cause == "no_answer",
        "latency_s": result.latency_s,
    }
    reason = fallback or FALLBACK_REASONS.get(result.cause)
    if reason:
        out["fallback_reason"] = reason
    return out


def stored_result(session: Session, job_id: str) -> dict[str, Any] | None:
    """The stored AskJobResult of a finished ask job, or None."""
    row = session.scalars(select(AskResult).where(AskResult.job_id == job_id)).first()
    return row.payload if row else None


def _ask(app: Any, question: str, module: str, product_id: str | None, provider: Provider,
         product_text: str | None = None) -> RagResult:
    """The pipeline for one job: a reference medicine product answers from its own chunks (CR-23), else as before."""
    service = app.state.medicine
    if module == "medicine" and app.state.live.knows(product_id):  # CR-28: a label fetched live
        result, _label = app.state.live.ask(question, product_id, provider, AI_SETTINGS, gated=False)
        return result
    if module == "medicine" and service.knows(product_id):
        return service.ask(question, product_id, provider, AI_SETTINGS)
    if module == "device" and product_text is not None:  # CR-29: only passages that apply to the product
        return app.state.rag.ask(question, module, provider, AI_SETTINGS, product_text=product_text)
    return app.state.rag.ask(question, module, provider, AI_SETTINGS)


def _based_on(app: Any, module: str, product_id: str | None) -> str | None:
    """`based_on` text for a reference product, None for any other id."""
    service = app.state.medicine
    if module == "medicine" and app.state.live.knows(product_id):
        return app.state.live.based_on(app.state.live.load(product_id))
    if module == "medicine" and service.knows(product_id):
        from src.api.medicine import based_on

        return based_on(service.catalog.products[product_id])
    return None


def _attach_live(app: Any, payload: dict[str, Any], product_id: str | None) -> None:
    """Put the live label info on the answer of a label fetched live (CR-28)."""
    if product_id and app.state.live.knows(product_id):
        payload["answer"]["live"] = app.state.live.load(product_id).live_info()


def run_ask_job(
    app: Any, job_id: str, question: str, module: str, product_id: str | None, product_text: str | None = None,
) -> None:
    """Background body of a 202 ask: run the model, verify, fall back to extractive, store the result."""
    with app.state.session_factory() as session:
        try:
            advance_job(session, job_id, "processing", 0.1, "retrieving passages")
            provider: Provider = app.state.ai_provider or OllamaProvider(AI_MODEL, AI_SETTINGS)
            advance_job(session, job_id, "processing", 0.3, "asking the model (the first run loads it, about a minute)")
            try:
                result = _ask(app, question, module, product_id, provider, product_text)
                payload = build_payload(result, module, product_id, based_on=_based_on(app, module, product_id))
            except RetrievalUnavailable:
                raise
            except Exception:  # anything unexpected in the model path: show the passages instead
                result = _ask(app, question, module, product_id, NullProvider(), product_text)
                payload = build_payload(
                    result, module, product_id, "model_unavailable", _based_on(app, module, product_id))
            _attach_live(app, payload, product_id)
            session.add(AskResult(job_id=job_id, payload=payload, created_at=utcnow()))
            session.commit()
            advance_job(session, job_id, "done", 1.0, "done")
        except RetrievalUnavailable as error:
            advance_job(session, job_id, "failed", 1.0, error={"error": "retrieval_unavailable", "message": str(error)})
        except Exception as error:  # a job must end in a state a client can read
            advance_job(session, job_id, "failed", 1.0, error={
                "error": "ask_failed", "message": f"{type(error).__name__}: {error}"})
