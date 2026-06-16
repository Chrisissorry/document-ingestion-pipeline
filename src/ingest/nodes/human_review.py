from __future__ import annotations

from typing import Any

from langgraph.types import interrupt

from ..state import IngestState


def human_review(state: IngestState) -> dict:
    fields = state.get("fields", {})
    # Same missing-field notion as validate(): None means missing. An empty
    # list (e.g. line_items) is a valid extraction, not a flag.
    flagged = [k for k, v in fields.items() if v is None]
    # The resume payload is wrapped ({"overrides": {...}}) because a falsy resume
    # value (empty dict = "accept everything") re-pauses instead of resuming.
    answer: dict[str, Any] = interrupt(
        {
            "doc_type": state.get("doc_type"),
            "confidence": state.get("confidence", 0.0),
            "fields": fields,
            "flagged": flagged,
        }
    )
    overrides = answer.get("overrides", {})
    return {"fields": {**fields, **overrides}, "needs_review": False}
