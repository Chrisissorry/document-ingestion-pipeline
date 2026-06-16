from __future__ import annotations

from typing import Final

from pydantic import BaseModel, Field


class LineItem(BaseModel):
    description: str
    amount: float


class Invoice(BaseModel):
    doc_type: str = "invoice"
    invoice_number: str | None = None
    date: str | None = None
    vendor: str | None = None
    currency: str | None = None
    total: float | None = None
    line_items: list[LineItem] = Field(default_factory=list)


class Contract(BaseModel):
    doc_type: str = "contract"
    parties: list[str] = Field(default_factory=list)
    effective_date: str | None = None
    term: str | None = None


class GenericDocument(BaseModel):
    doc_type: str = "generic"
    title: str | None = None
    summary: str | None = None


REQUIRED_FIELDS: Final[dict[str, list[str]]] = {
    "invoice": ["invoice_number", "date", "vendor", "total"],
    "contract": ["parties", "effective_date", "term"],
    "generic": ["summary"],
}
