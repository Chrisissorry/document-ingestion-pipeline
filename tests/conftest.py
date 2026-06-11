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


@pytest.fixture
def fake_llm(monkeypatch):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _fake_response(
        '{"doc_type": "invoice"}'
    )
    monkeypatch.setattr("ingest.tools.llm.client", lambda: mock_client, raising=False)
    return mock_client
