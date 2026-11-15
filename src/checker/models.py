"""Result types. ``Finding`` is a shared ``Flag`` plus citations (schemas.py is not edited)."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from src.checker.citations import Citation
from src.common.schemas import Flag

Outcome = Literal["pass", "fail", "needs_human", "not_applicable", "not_checked"]


class Finding(Flag):
    """A Flag with the rule that raised it, the field it is about and its regulation citations."""

    rule_id: str = ""
    field: str = ""
    citations: list[Citation] = Field(default_factory=list)


class RuleOutcome(BaseModel):
    """What one rule concluded. Listed beside the findings so a missing flag never reads as 'checked and fine'."""

    rule_id: str
    outcome: Outcome
    reason: str = ""


class CheckerResult(BaseModel):
    """Findings (problems only), coverage (one entry per rule) and the retrieval config used."""

    findings: list[Finding]
    coverage: list[RuleOutcome]
    retrieval_config: dict[str, object]

    @property
    def critical_count(self) -> int:
        """Number of critical findings."""
        return sum(f.severity == "critical" for f in self.findings)

    @property
    def review_count(self) -> int:
        """Number of review findings."""
        return sum(f.severity == "review" for f in self.findings)

    @property
    def info_count(self) -> int:
        """Number of info findings (the checker raises none today)."""
        return sum(f.severity == "info" for f in self.findings)

    @property
    def needs_human_count(self) -> int:
        """Coverage entries that need a person, including a symbol detection nobody has confirmed."""
        return sum(o.outcome == "needs_human" for o in self.coverage)

    @property
    def passed(self) -> bool:
        """Zero critical findings (the contract rule). It does not mean the label is compliant."""
        return self.critical_count == 0
