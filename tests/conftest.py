from __future__ import annotations

from unittest.mock import MagicMock

import pytest


def _fake_response(text: str) -> MagicMock:
    block = MagicMock()
    block.type = "text"
    block.text = text
    msg = MagicMock()
    msg.content = [block]
    return msg


def _fake_tool_response(data: dict) -> MagicMock:
    block = MagicMock()
    block.type = "tool_use"
    block.input = data
    msg = MagicMock()
    msg.content = [block]
    return msg


@pytest.fixture
def fake_llm(monkeypatch):
    mock_client = MagicMock()

    def _dispatch(*args, **kwargs):
        if "tools" in kwargs:
            return _fake_tool_response(
                {"doc_type": "generic", "title": "Test document", "summary": "A short summary."}
            )
        return _fake_response(
            '{"doc_type": "invoice", "invoice_number": "INV-2026-0042", '
            '"date": "2026-05-28", "vendor": "ACME Supplies Ltd.", '
            '"currency": "EUR", "total": 1222.80, '
            '"line_items": [{"description": "Consulting services", "amount": 900.0}, '
            '{"description": "Travel expenses", "amount": 119.0}]}'
        )

    mock_client.messages.create.side_effect = _dispatch
    monkeypatch.setattr("ingest.tools.llm.client", lambda: mock_client, raising=False)
    return mock_client
