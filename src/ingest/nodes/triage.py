from __future__ import annotations

from ..state import IngestState


def triage(state: IngestState) -> dict:
    # TODO (Triage cluster): classify with Haiku into invoice | contract | generic
    # based on state["raw_text"]. The stub always returns invoice so the happy
    # path runs end to end.
    return {"doc_type": "invoice"}
