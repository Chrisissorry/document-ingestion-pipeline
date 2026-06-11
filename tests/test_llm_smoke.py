from __future__ import annotations

import ingest.tools.llm as llm


def test_fake_llm_returns_deterministic_tool_use(fake_llm):
    response = llm.client().messages.create(model=llm.model_name(), messages=[])
    block = response.content[0]
    assert block.type == "tool_use"
    assert block.input["doc_type"] == "generic"
