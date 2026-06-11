from __future__ import annotations

import json
import re

from ..schemas import Contract, GenericDocument, Invoice
from ..state import IngestState
from ..tools import llm


def _parse_llm_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {}


def extract_invoice(state: IngestState) -> dict:
    raw_text = state.get("raw_text", "")
    schema_json = json.dumps(Invoice.model_json_schema(), indent=2)

    response = llm.client().messages.create(
        model=llm.model_name(),
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": (
                    "Extract the invoice fields from the document below as a JSON object "
                    f"matching this schema:\n{schema_json}\n\n"
                    "Use null for absent fields. Reply with only the JSON object.\n\n"
                    f"Document:\n{raw_text}"
                ),
            }
        ],
    )

    text_block = next(b for b in response.content if b.type == "text")
    raw = _parse_llm_json(text_block.text)  # type: ignore[union-attr]
    inv = Invoice.model_validate(raw)

    scored_fields = ["invoice_number", "date", "vendor", "currency", "total"]
    filled = sum(1 for f in scored_fields if getattr(inv, f) is not None)
    if inv.line_items:
        filled += 1
    confidence = round(filled / (len(scored_fields) + 1), 2)

    return {"fields": inv.model_dump(), "confidence": confidence}


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
