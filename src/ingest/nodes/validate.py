from __future__ import annotations

from ..schemas import REQUIRED_FIELDS
from ..state import IngestState

CONFIDENCE_THRESHOLD = 0.7


def validate(state: IngestState) -> dict:
    if state.get("confidence", 0.0) < CONFIDENCE_THRESHOLD:
        return {"needs_review": True}
    required_fields = REQUIRED_FIELDS.get(str(state.get("doc_type", "")), [])
    fields = state.get("fields", {})
    if any(fields.get(field) in (None, "", []) for field in required_fields):
        return {"needs_review": True}
    return {"needs_review": False}
