from __future__ import annotations

import json

from ..state import IngestState
from ..tools import llm

_SYSTEM = (
    "Classify the document. Reply with JSON only: "
    '{"doc_type": "invoice"}, {"doc_type": "contract"}, or {"doc_type": "generic"}. '
    "Default to generic when the type is unclear."
)

_VALID = {"invoice", "contract", "generic"}


def triage(state: IngestState) -> dict:
    raw_text = (state.get("raw_text") or "").strip()
    if not raw_text:
        return {"doc_type": "generic"}
    try:
        response = llm.client().messages.create(
            model=llm.model_name(),
            max_tokens=32,
            system=_SYSTEM,
            messages=[{"role": "user", "content": raw_text}],
        )
        text = getattr(response.content[0], "text", None)
        if not isinstance(text, str):
            return {"doc_type": "generic"}
        try:
            data = json.loads(text.strip())
            word = str(data.get("doc_type", "generic")).lower()
        except (json.JSONDecodeError, AttributeError, TypeError):
            word = text.strip().lower()
        return {"doc_type": word if word in _VALID else "generic"}
    except Exception:
        return {"doc_type": "generic"}
