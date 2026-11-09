"""FastAPI entry point. Extend with upload, analyze, decision, change and report routes."""
from fastapi import FastAPI

app = FastAPI(title="LabelLens API", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
