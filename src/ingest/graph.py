from __future__ import annotations

from typing import Any
from uuid import uuid4

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from .nodes.extract import extract_contract, extract_generic, extract_invoice
from .nodes.human_review import human_review
from .nodes.ingest import ingest
from .nodes.persist import persist
from .nodes.triage import triage
from .nodes.validate import validate
from .state import IngestState


def _route_by_type(state: IngestState) -> str:
    return {
        "invoice": "extract_invoice",
        "contract": "extract_contract",
    }.get(state.get("doc_type", "generic"), "extract_generic")


def _route_by_confidence(state: IngestState) -> str:
    return "human_review" if state.get("needs_review") else "persist"


def build_graph(checkpointer: BaseCheckpointSaver | None = None) -> Any:
    g = StateGraph(IngestState)
    g.add_node("ingest", ingest)
    g.add_node("triage", triage)
    g.add_node("extract_invoice", extract_invoice)
    g.add_node("extract_contract", extract_contract)
    g.add_node("extract_generic", extract_generic)
    g.add_node("validate", validate)
    g.add_node("human_review", human_review)
    g.add_node("persist", persist)

    g.add_edge(START, "ingest")
    g.add_edge("ingest", "triage")
    g.add_conditional_edges(
        "triage",
        _route_by_type,
        ["extract_invoice", "extract_contract", "extract_generic"],
    )
    for extractor in ("extract_invoice", "extract_contract", "extract_generic"):
        g.add_edge(extractor, "validate")
    g.add_conditional_edges("validate", _route_by_confidence, ["human_review", "persist"])
    g.add_edge("human_review", "persist")
    g.add_edge("persist", END)
    # MemorySaver is the dev default; interrupt() needs a checkpointer to pause and
    # resume. Pass a Postgres-backed saver here once persistence of paused runs matters.
    return g.compile(checkpointer=checkpointer or MemorySaver())


def thread_config(thread_id: str | None = None) -> dict[str, Any]:
    return {"configurable": {"thread_id": thread_id or uuid4().hex}}


def run(path: str, thread_id: str | None = None) -> dict:
    final = build_graph().invoke({"path": path}, thread_config(thread_id))
    return final["result"]
