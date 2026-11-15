"""One error type for the API, matching the contract shape {error, message, details?}."""

from __future__ import annotations

from typing import Any


class ApiError(Exception):
    """A rule violation the API reports to the client.

    `status` is the HTTP status, `code` the short machine code (for example
    `self_approval_forbidden`), `message` a plain sentence for people.
    """

    def __init__(self, status: int, code: str, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(f"{code}: {message}")
        self.status = status
        self.code = code
        self.message = message
        self.details = details

    def body(self) -> dict[str, Any]:
        """Return the JSON body of the error response."""
        out: dict[str, Any] = {"error": self.code, "message": self.message}
        if self.details:
            out["details"] = self.details
        return out
