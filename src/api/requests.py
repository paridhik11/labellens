"""Request bodies for the real endpoints (shapes from docs/contracts/openapi.yaml).

Pydantic checks the shape. Business rules (roles, hashes, checks) live in store.py and reviews.py.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SHA256_PATTERN = r"^[0-9a-f]{64}$"


class ProductCreate(BaseModel):
    """POST /products. `udi_di` is whatever the company allocated, or empty. LabelLens never fills it in."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    model: str = ""
    manufacturer: str = ""
    manufacturer_address: str = ""
    udi_di: str = ""
    sterilization: str = ""
    storage: str = ""
    extra: dict[str, str] = Field(default_factory=dict)
    intended_market: list[str] = Field(default_factory=list)


class SizeMm(BaseModel):
    """Label size in millimetres."""

    model_config = ConfigDict(extra="forbid")

    w: float = Field(gt=0)
    h: float = Field(gt=0)


class Slot(BaseModel):
    """One marked slot of a template (TEMPLATE_SPEC.md). Only the shape is checked here, not the layout."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^[A-Za-z][A-Za-z0-9_-]*$")
    type: Literal["text", "symbol", "barcode"]
    field: str
    bbox_mm: tuple[float, float, float, float]
    font: str | None = None
    size_pt: float | None = Field(default=None, gt=0)
    align: Literal["left", "center", "right"] | None = None
    max_lines: int | None = Field(default=None, ge=1)
    symbol_name: Literal["manufacturer", "expiry"] | None = None
    symbology: Literal["GS1_DataMatrix", "GS1-128"] | None = None
    min_size_mm: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def _type_specific_fields(self) -> Slot:
        needed = {"text": "size_pt", "symbol": "symbol_name", "barcode": "symbology"}[self.type]
        if getattr(self, needed) is None:
            raise ValueError(f"a {self.type} slot needs {needed}")
        return self

    def to_json(self) -> dict:
        """Return the slot as a JSON dict without the unset optional keys."""
        out = self.model_dump(exclude_none=True)
        out["bbox_mm"] = list(self.bbox_mm)
        return out


class TemplateCreate(BaseModel):
    """POST /products/{id}/templates. Give `template_id` to add a new version of an existing template."""

    model_config = ConfigDict(extra="forbid")

    template_id: str | None = None
    size_mm: SizeMm
    background: str | None
    min_font_pt: float | None = Field(default=None, gt=0)
    slots: list[Slot] = Field(min_length=1)

    @model_validator(mode="after")
    def _unique_slot_ids(self) -> TemplateCreate:
        ids = [s.id for s in self.slots]
        if len(ids) != len(set(ids)):
            raise ValueError("slot ids must be unique inside a template")
        return self


class FieldEdit(BaseModel):
    """One structured field edit of a change."""

    model_config = ConfigDict(extra="forbid")

    field: str = Field(min_length=1)
    old_value: str | None = None
    new_value: str


class ChangeCreate(BaseModel):
    """POST /changes. Give `edits` (structured) or `raw_text` (parsed by the rules in src/change). Edits win if both."""

    model_config = ConfigDict(extra="forbid")

    product_id: str
    raw_text: str | None = None
    edits: list[FieldEdit] | None = None

    @model_validator(mode="after")
    def _text_or_edits(self) -> ChangeCreate:
        if self.raw_text is None and not self.edits:
            raise ValueError("give raw_text or edits")
        return self


class ImpactDecision(BaseModel):
    """One checklist decision of a confirmation."""

    model_config = ConfigDict(extra="forbid")

    impact_id: str
    user_decision: Literal["confirmed", "dismissed"]


class ChangeConfirmCreate(BaseModel):
    """POST /changes/{id}/confirm. `edits` is in the schema but refused: a changed edit set is a new change."""

    model_config = ConfigDict(extra="forbid")

    parse_confirmed: bool
    edits: list[FieldEdit] | None = None
    decisions: list[ImpactDecision]


class ReviewCreate(BaseModel):
    """POST /label-versions/{id}/reviews. Conditional rules (check_id, comment) give specific codes in reviews.py."""

    model_config = ConfigDict(extra="forbid")

    decision: Literal["approve", "return", "reject"]
    comment: str = ""
    artifact_sha256: str = Field(pattern=SHA256_PATTERN)
    check_id: str | None = None


class RetrievalConfig(BaseModel):
    """RetrievalConfig of the contract. Unset keys mean the checker's default (plain hybrid RRF)."""

    model_config = ConfigDict(extra="forbid")

    method: Literal["hybrid_rrf", "bm25", "tfidf", "dense"] | None = None
    stem: bool | None = None
    prefix: bool | None = None
    rerank: bool = False
    expansion: bool = False

    def overrides(self) -> dict[str, object]:
        """The keys that were set, for the checker. rerank and expansion have no implementation, so they are refused."""
        if self.rerank or self.expansion:
            raise ValueError("rerank and expansion are not available: no reranker or query expansion exists in src/ir")
        return {k: v for k, v in self.model_dump(exclude={"rerank", "expansion"}).items() if v is not None}


class InspectCreate(BaseModel):
    """POST /label-versions/{id}/inspect (optional body)."""

    model_config = ConfigDict(extra="forbid")

    retrieval: RetrievalConfig | None = None


class SearchCreate(BaseModel):
    """POST /search. Module is required and never mixed."""

    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1)
    module: Literal["device", "medicine"]
    k: int = Field(default=10, ge=1, le=50)
    section_level: bool = False
    retrieval: RetrievalConfig | None = None
