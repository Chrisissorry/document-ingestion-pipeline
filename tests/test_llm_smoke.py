from __future__ import annotations

import ingest.tools.llm as llm


def test_fake_llm_returns_deterministic_text(fake_llm):
    response = llm.client().messages.create(model=llm.model_name(), messages=[])
    assert response.content[0].text == '{"doc_type": "invoice"}'
