from __future__ import annotations

from ..state import IngestState

CONFIDENCE_THRESHOLD = 0.7


def validate(state: IngestState) -> dict:
    # TODO (Validation cluster): check required fields per schema, not just the
    # confidence score. The stub flags review only when confidence is low.
    confidence = state.get("confidence", 0.0)
    return {"needs_review": confidence < CONFIDENCE_THRESHOLD}
