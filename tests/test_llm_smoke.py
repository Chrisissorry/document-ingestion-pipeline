from __future__ import annotations

import json

import ingest.tools.llm as llm


def test_fake_llm_returns_deterministic_text(fake_llm) -> None:
    response = llm.client().messages.create(model=llm.model_name(), messages=[])
    data = json.loads(response.content[0].text)
    assert data["doc_type"] == "invoice"
    assert data["vendor"] == "ACME Supplies Ltd."
