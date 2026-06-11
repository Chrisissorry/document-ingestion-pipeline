from __future__ import annotations

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


def build_graph():
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
    g.add_conditional_edges(
        "validate", _route_by_confidence, ["human_review", "persist"]
    )
    g.add_edge("human_review", "persist")
    g.add_edge("persist", END)
    return g.compile()


def run(path: str) -> dict:
    final = build_graph().invoke({"path": path})
    return final["result"]
