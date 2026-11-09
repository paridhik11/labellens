"""Every retrieval system implements this interface so eval can swap them."""
from __future__ import annotations

from typing import Protocol

from src.common.schemas import Hit


class Retriever(Protocol):
    name: str

    def search(self, query: str, k: int = 10) -> list[Hit]:
        ...
