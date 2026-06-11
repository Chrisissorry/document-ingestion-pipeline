from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

import psycopg

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    source     TEXT PRIMARY KEY,
    tier       TEXT,
    doc_type   TEXT,
    confidence DOUBLE PRECISION,
    fields     JSONB NOT NULL DEFAULT '{}'::jsonb
);
"""


def _dsn() -> str:
    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        raise RuntimeError("DATABASE_URL is not set")
    return dsn


@contextmanager
def connect() -> Iterator[psycopg.Connection]:
    with psycopg.connect(_dsn()) as conn:
        yield conn


def init_db() -> None:
    """Idempotently create the documents table."""
    with connect() as conn:
        conn.execute(SCHEMA)
        conn.commit()
