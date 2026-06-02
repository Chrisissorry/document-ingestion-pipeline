from __future__ import annotations

from ..state import IngestState


def persist(state: IngestState) -> dict:
    record = {
        "source": state.get("path"),
        "tier": state.get("tier"),
        "doc_type": state.get("doc_type"),
        "confidence": state.get("confidence"),
        "fields": state.get("fields", {}),
    }
    # TODO (Persistence): write the record to Postgres using DATABASE_URL. The stub
    # returns it so the CLI can print the JSON.
    return {"result": record}
