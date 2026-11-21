"""A cooperative wall-clock budget, checked between slow steps (native calls cannot be interrupted)."""
from __future__ import annotations

import time


class Deadline:
    """A point in time after which optional work is skipped. ``None`` seconds never expires."""

    def __init__(self, seconds: float | None, *, start: float | None = None) -> None:
        """Start counting now (or from ``start``, a ``time.monotonic()`` value)."""
        self.start = time.monotonic() if start is None else start
        self.seconds = seconds

    def elapsed(self) -> float:
        """Seconds since the deadline started."""
        return time.monotonic()-self.start

    def expired(self) -> bool:
        """True once the budget is used up."""
        return self.seconds is not None and self.elapsed() >= self.seconds

    def left(self) -> float:
        """Seconds left (infinite without a budget, never negative)."""
        return float('inf') if self.seconds is None else max(0.0, self.seconds-self.elapsed())

    def stage(self, fraction: float) -> Deadline:
        """A tighter deadline for one stage: the same start, ``fraction`` of the total budget."""
        if self.seconds is None:
            return Deadline(None, start=self.start)
        return Deadline(self.seconds*fraction, start=self.start)


def remaining(deadline: Deadline | None) -> float:
    """Seconds left on an optional deadline (infinite when there is none)."""
    return float('inf') if deadline is None else deadline.left()


def expired(deadline: Deadline | None) -> bool:
    """Tell whether an optional deadline has passed."""
    return deadline is not None and deadline.expired()
