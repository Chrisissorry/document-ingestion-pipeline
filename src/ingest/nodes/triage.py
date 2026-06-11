from __future__ import annotations

from anthropic.types import TextBlock

from ..state import IngestState
from ..tools.llm import client, model_name

_SYSTEM = (
    "Classify the document into one of three types: invoice, contract, or generic. "
    "Reply with exactly one word. When uncertain, reply: generic."
)

_VALID = {"invoice", "contract", "generic"}


def triage(state: IngestState) -> dict:
    raw_text = (state.get("raw_text") or "").strip()
    if not raw_text:
        return {"doc_type": "generic"}
    try:
        response = client().messages.create(
            model=model_name(),
            max_tokens=10,
            system=_SYSTEM,
            messages=[{"role": "user", "content": raw_text}],
        )
        block = response.content[0]
        if not isinstance(block, TextBlock):
            return {"doc_type": "generic"}
        word = block.text.strip().lower()
        return {"doc_type": word if word in _VALID else "generic"}
    except Exception:
        return {"doc_type": "generic"}
