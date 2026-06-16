from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from langgraph.types import Command

from .graph import build_graph, thread_config


def _parse_value(raw: str) -> Any:
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


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="slurp",
        description="Extract structured data from a PDF using an agentic LangGraph pipeline.",
    )
    parser.add_argument("pdf", help="path to the PDF file to process")
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="print triage result, tier, and confidence to stderr",
    )
    parser.add_argument(
        "--no-db",
        action="store_true",
        help="skip persisting the result to Postgres",
    )
    parser.add_argument(
        "--thread-id",
        metavar="ID",
        default=None,
        help="resume a paused human-review session by thread ID",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="FILE",
        default=None,
        help="write JSON output to FILE instead of stdout",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    graph = build_graph()
    config = thread_config(args.thread_id)

    initial: dict[str, Any] = {"path": args.pdf}
    if args.no_db:
        initial["skip_db"] = True

    state = graph.invoke(initial, config)

    while "__interrupt__" in state:
        overrides = _collect_overrides(state["__interrupt__"][0].value)
        state = graph.invoke(Command(resume={"overrides": overrides}), config)

    if args.verbose:
        print(
            f"[slurp] tier={state.get('tier')}  "
            f"doc_type={state.get('doc_type')}  "
            f"confidence={state.get('confidence', 0.0):.2f}",
            file=sys.stderr,
        )

    result = json.dumps(state["result"], indent=2, ensure_ascii=False)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(result + "\n")
    else:
        print(result)

    return 0
