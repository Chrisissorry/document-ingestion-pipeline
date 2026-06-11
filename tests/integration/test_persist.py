from __future__ import annotations

import uuid

import psycopg
import pytest

from ingest.db import connect, init_db
from ingest.nodes.persist import persist


def _cleanup(source: str) -> None:
    with connect() as conn:
        conn.execute("DELETE FROM documents WHERE source = %s", (source,))
        conn.commit()


def test_persist_upserts_exactly_one_row() -> None:
    source = f"samples/test_persist_{uuid.uuid4().hex}.pdf"
    state = {
        "path": source,
        "tier": "text",
        "doc_type": "invoice",
        "confidence": 0.9,
        "fields": {"doc_type": "invoice", "total": "100.00"},
    }
    try:
        init_db()
    except psycopg.OperationalError:
        pytest.skip("Postgres is unreachable")

    try:
        persist(state)
        persist({**state, "confidence": 0.5})  # same source, must not duplicate

        with connect() as conn:
            row = conn.execute(
                "SELECT source, tier, doc_type, confidence, fields FROM documents "
                "WHERE source = %s",
                (source,),
            ).fetchall()

        assert len(row) == 1
        src, tier, doc_type, confidence, fields = row[0]
        assert src == source
        assert tier == "text"
        assert doc_type == "invoice"
        assert confidence == 0.5  # second upsert won
        assert fields == {"doc_type": "invoice", "total": "100.00"}
    finally:
        _cleanup(source)
