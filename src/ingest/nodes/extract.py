from __future__ import annotations

from ..schemas import Contract, GenericDocument, Invoice
from ..state import IngestState

# TODO (Extractors cluster): replace the hardcoded values with a Haiku call that
# fills the pydantic schema from state["raw_text"]. The stub returns fixed fields
# and a confidence so the graph runs without touching the API.


def extract_invoice(state: IngestState) -> dict:
    inv = Invoice(
        invoice_number="STUB-001",
        date="2026-05-28",
        vendor="ACME Supplies Ltd.",
        currency="EUR",
        total=1222.80,
    )
    return {"fields": inv.model_dump(), "confidence": 0.91}


def extract_contract(state: IngestState) -> dict:
    c = Contract(
        parties=["Party A", "Party B"],
        effective_date="2026-06-11",
        term="12 months",
    )
    return {"fields": c.model_dump(), "confidence": 0.88}


def extract_generic(state: IngestState) -> dict:
    g = GenericDocument(title="Stub document", summary="Placeholder summary.")
    return {"fields": g.model_dump(), "confidence": 0.75}
