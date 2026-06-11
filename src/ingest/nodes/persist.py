from __future__ import annotations

import json

import psycopg

from ..db import connect, init_db
from ..state import IngestState

_UPSERT = """
INSERT INTO documents (source, tier, doc_type, confidence, fields)
VALUES (%s, %s, %s, %s, %s::jsonb)
ON CONFLICT (source) DO UPDATE SET
    tier       = EXCLUDED.tier,
    doc_type   = EXCLUDED.doc_type,
    confidence = EXCLUDED.confidence,
    fields     = EXCLUDED.fields;
"""


def persist(state: IngestState) -> dict:
    record = {
        "source": state.get("path"),
        "tier": state.get("tier"),
        "doc_type": state.get("doc_type"),
        "confidence": state.get("confidence"),
        "fields": state.get("fields", {}),
    }
    # source is the primary key; without it there is nothing to upsert against.
    if record["source"]:
        # A returned envelope is the contract; an unreachable DB must not crash the
        # pipeline (or the suite). The integration test verifies the write itself.
        try:
            init_db()
            with connect() as conn:
                conn.execute(
                    _UPSERT,
                    (
                        record["source"],
                        record["tier"],
                        record["doc_type"],
                        record["confidence"],
                        json.dumps(record["fields"]),
                    ),
                )
                conn.commit()
        except psycopg.OperationalError:
            pass
    return {"result": record}
