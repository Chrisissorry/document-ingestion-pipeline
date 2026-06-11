from __future__ import annotations

from ..schemas import Contract, GenericDocument, Invoice
from ..state import IngestState
from ..tools.llm import extract_structured


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
    g = extract_structured(GenericDocument, state["raw_text"])
    optional_fields = [f for f in GenericDocument.model_fields if f != "doc_type"]
    populated = sum(1 for f in optional_fields if getattr(g, f) is not None)
    confidence = round(populated / len(optional_fields), 2) if optional_fields else 1.0
    return {"fields": g.model_dump(), "confidence": confidence}
