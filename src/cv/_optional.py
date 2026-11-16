"""Delay optional vision imports until an extraction function is actually used."""
from __future__ import annotations

from importlib import import_module
from typing import Any, Callable


class LazyModule:
    """Resolve module attributes on demand without loading native CV dependencies at import."""

    def __init__(self, name: str) -> None:
        """Remember the import path without importing the module."""
        self.name = name

    def __getattr__(self, name: str) -> Any:
        """Load the real module only when a runtime attribute is requested."""
        return getattr(import_module(self.name), name)


def deferred(module: str, name: str) -> Callable[..., Any]:
    """Return a callable that imports an optional implementation only on invocation."""
    def invoke(*args: Any, **kwargs: Any) -> Any:
        """Resolve and call the implementation with the original arguments."""
        return getattr(import_module(module), name)(*args, **kwargs)

    return invoke
