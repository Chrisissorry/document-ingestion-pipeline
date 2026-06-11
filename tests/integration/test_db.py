from __future__ import annotations

import os
import uuid

import psycopg
import pytest

from ingest.db import connect, init_db


def test_init_db_insert_and_query_back() -> None:
    # Runs by default (-m "not eval"); skips when there is no database to reach so
    # tokenless CI (no DATABASE_URL) and the agent-gate without a db do not fail.
    if not os.environ.get("DATABASE_URL"):
        pytest.skip("DATABASE_URL is not set")
    try:
        init_db()
    except psycopg.OperationalError as exc:
        pytest.skip(f"Postgres unreachable: {exc}")

    source = f"test://{uuid.uuid4()}"
    with connect() as conn:
        conn.execute(
            "INSERT INTO documents (source, tier, doc_type, confidence, fields) "
            "VALUES (%s, %s, %s, %s, %s)",
            (source, "text", "invoice", 0.91, '{"vendor": "ACME"}'),
        )
        conn.commit()

        row = conn.execute(
            "SELECT source, tier, doc_type, confidence, fields FROM documents WHERE source = %s",
            (source,),
        ).fetchone()

    assert row is not None
    assert row[0] == source
    assert row[1] == "text"
    assert row[2] == "invoice"
    assert row[3] == pytest.approx(0.91)
    assert row[4] == {"vendor": "ACME"}
