from __future__ import annotations

from ..state import IngestState


def human_review(state: IngestState) -> dict:
    # TODO (Human-in-the-Loop cluster): replace the print statements with a
    # LangGraph interrupt so the graph pauses and the CLI can collect corrections.
    fields = state.get("fields", {})
    missing = [k for k, v in fields.items() if v is None or v == []]
    print(
        f"[human-review] doc_type={state.get('doc_type')}, "
        f"confidence={state.get('confidence', 0.0):.2f}"
    )
    if missing:
        print(f"[human-review] missing required fields: {missing}")
    print("[human-review] fields would be confirmed via CLI interrupt here")
    return {"needs_review": False}
