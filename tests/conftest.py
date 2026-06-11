from __future__ import annotations

from unittest.mock import MagicMock

import pytest


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
    mock_client.messages.create.return_value = _fake_tool_response(
        {"doc_type": "generic", "title": "Test Document", "summary": "A short test summary."}
    )
    monkeypatch.setattr("ingest.tools.llm.client", lambda: mock_client, raising=False)
    return mock_client
