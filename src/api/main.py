"""FastAPI entry point.

Real endpoints (routes.py) use SQLite. Every other operation of docs/contracts/openapi.yaml serves its mock JSON
with the header `X-Mock: true` (mock_server.py). Run with `uvicorn src.api.main:app`.

Environment: LABELLENS_DB_URL (default sqlite:///data/api/labellens.db), LABELLENS_SEED=0 to skip the demo seed.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.api.db import init_db, make_engine, make_session_factory
from src.api.errors import ApiError
from src.api.extractor import extract_with_cv
from src.api.mock_server import register_mocks
from src.api.quality import DEFAULT as QUALITY_THRESHOLDS
from src.api.quality import assess_photo
from src.api.routes import router
from src.api.seed import seed_demo
from src.api.uploads import MAX_BYTES
from src.checker.settings import CheckerSettings
from src.rag.service import RagService, frozen_threshold

FORM_OVERHEAD = 64 * 1024  # room for the multipart boundaries and the small text fields around the file


def create_app(db_url: str | None = None, seed: bool | None = None) -> FastAPI:
    """Build the app. The database is opened (and seeded) when the app starts, not when this module is imported."""

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = make_engine(db_url)
        init_db(engine)
        app.state.engine = engine
        app.state.session_factory = make_session_factory(engine)
        app.state.extractor = extract_with_cv  # tests replace it with a stub
        app.state.quality_gate = lambda path: assess_photo(path, QUALITY_THRESHOLDS)  # tests replace it
        app.state.quality_thresholds = QUALITY_THRESHOLDS
        app.state.checker_settings = CheckerSettings()  # default retrieval: plain hybrid RRF
        app.state.rag = RagService(threshold=frozen_threshold())  # Step 23: E5b retrieval loads on the first question
        app.state.edit_provider = None  # optional LLM text parser, off by default (src/change/parser.py)
        if seed if seed is not None else os.environ.get("LABELLENS_SEED", "1") != "0":
            with app.state.session_factory() as session:
                seed_demo(session)
        yield
        engine.dispose()

    app = FastAPI(title="LabelLens API", version="0.1.0", lifespan=lifespan)

    @app.middleware("http")
    async def refuse_oversize_upload(request: Request, call_next):  # noqa: ANN001, ANN202
        """Answer a too-large POST /scans from its Content-Length before the body is parsed or stored."""
        if request.method == "POST" and request.url.path == "/scans":
            declared = request.headers.get("content-length", "")
            if declared.isdigit() and int(declared) > MAX_BYTES + FORM_OVERHEAD:
                error = ApiError(422, "file_too_large", f"The upload is larger than {MAX_BYTES // (1024 * 1024)} MB.")
                return JSONResponse(error.body(), status_code=422)
        return await call_next(request)

    @app.exception_handler(ApiError)
    async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(exc.body(), status_code=exc.status)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [{"loc": [str(p) for p in e["loc"]], "message": e["msg"]} for e in exc.errors()]
        body = {"error": "validation_error", "message": "The request is invalid.", "details": {"errors": errors}}
        return JSONResponse(body, status_code=422)

    @app.get("/health", operation_id="getHealth", tags=["common"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(router)
    register_mocks(app)
    return app


app = create_app()
