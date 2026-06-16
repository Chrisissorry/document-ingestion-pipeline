from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

import ingest.tools.llm as llm


class _SimpleSchema(BaseModel):
    doc_type: str = "generic"
    title: str = ""


def _fake_tool_response(data: dict) -> MagicMock:
    block = MagicMock()
    block.type = "tool_use"
    block.input = data
    msg = MagicMock()
    msg.content = [block]
    return msg


def test_extract_structured_wraps_text_in_document_tags() -> None:
    raw_text = "INVOICE\nTotal: 100 EUR"
    captured: list[dict] = []

    def _fake_create(**kwargs):
        captured.append(kwargs)
        return _fake_tool_response({"doc_type": "generic", "title": "test"})

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = _fake_create

    with patch("ingest.tools.llm.client", return_value=mock_client):
        llm.extract_structured(_SimpleSchema, raw_text)

    messages = captured[0]["messages"]
    assert len(messages) == 1
    content = messages[0]["content"]
    assert content.startswith("<document>"), "document text must start with <document> tag"
    assert content.endswith("</document>"), "document text must end with </document> tag"
    assert raw_text in content, "original text must be preserved inside the tags"


def test_extract_structured_always_sets_system_prompt() -> None:
    def _fake_create(**kwargs):
        return _fake_tool_response({"doc_type": "generic", "title": "test"})

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = _fake_create

    with patch("ingest.tools.llm.client", return_value=mock_client):
        llm.extract_structured(_SimpleSchema, "some text")

    call_kwargs = mock_client.messages.create.call_args.kwargs
    assert "system" in call_kwargs, "system prompt must always be set"
    assert "<document>" in call_kwargs["system"], "system prompt must reference <document> tags"


def test_extract_structured_preserves_caller_system_prompt() -> None:
    caller_system = "Only extract fields in German."
    captured: list[dict] = []

    def _fake_create(**kwargs):
        captured.append(kwargs)
        return _fake_tool_response({"doc_type": "generic", "title": "test"})

    mock_client = MagicMock()
    mock_client.messages.create.side_effect = _fake_create

    with patch("ingest.tools.llm.client", return_value=mock_client):
        llm.extract_structured(_SimpleSchema, "text", system=caller_system)

    system = captured[0]["system"]
    assert caller_system in system, "caller system prompt must be appended, not discarded"
