from __future__ import annotations

import json
import sys
from typing import Any

from langgraph.types import Command

from .graph import build_graph, thread_config


def _parse_value(raw: str) -> Any:
    # "3050.0" stays a float and '["a", "b"]' a list; anything else is a string.
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def _collect_overrides(payload: dict[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = payload["fields"]
    to_review: list[str] = payload["flagged"] or [k for k in fields if k != "doc_type"]
    print(
        f"[human-review] doc_type={payload['doc_type']}, "
        f"confidence={payload['confidence']:.2f}, "
        f"flagged: {', '.join(to_review)}",
        file=sys.stderr,
    )
    overrides: dict[str, Any] = {}
    for name in to_review:
        raw = input(f"  {name} [{fields.get(name)!r}] (Enter to accept): ").strip()
        if raw:
            overrides[name] = _parse_value(raw)
    return overrides


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print("usage: python -m ingest <pdf-path>", file=sys.stderr)
        return 2
    graph = build_graph()
    config = thread_config()
    state = graph.invoke({"path": argv[0]}, config)
    while "__interrupt__" in state:
        overrides = _collect_overrides(state["__interrupt__"][0].value)
        state = graph.invoke(Command(resume={"overrides": overrides}), config)
    print(json.dumps(state["result"], indent=2, ensure_ascii=False))
    return 0
