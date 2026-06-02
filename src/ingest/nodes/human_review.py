from __future__ import annotations

from ..state import IngestState


def human_review(state: IngestState) -> dict:
    # TODO (Human-in-the-Loop cluster): pause the graph with a LangGraph interrupt
    # and ask on the CLI to confirm or correct the low-confidence fields. The stub
    # just clears the flag so the smoke test stays non-interactive.
    print("[human-review] low confidence; fields would be confirmed on the CLI here")
    return {"needs_review": False}
