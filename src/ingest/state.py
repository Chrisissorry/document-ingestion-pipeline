from __future__ import annotations

from typing import Any, TypedDict


class IngestState(TypedDict, total=False):
    path: str
    raw_text: str
    tier: str  # "text" (Tier 1) or "vision" (Tier 2)
    doc_type: str  # "invoice" | "contract" | "generic"
    fields: dict[str, Any]
    confidence: float
    needs_review: bool
    skip_db: bool
    result: dict[str, Any]
