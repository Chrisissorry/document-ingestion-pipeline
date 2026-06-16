from __future__ import annotations

from pathlib import Path

from langgraph.types import Command, interrupt

import ingest.nodes.extract as extract
from ingest.graph import build_graph, run, thread_config

ROOT = Path(__file__).resolve().parent.parent.parent
SAMPLES = ROOT / "samples"

ENVELOPE_KEYS = {"source", "tier", "doc_type", "confidence", "fields"}


def _low_confidence_invoice(state):
    out = extract.extract_invoice(state)
    out["confidence"] = 0.1
    return out


def _interrupting_review(state):
    answer = interrupt({"fields": state.get("fields", {})})
    return {"fields": {**state.get("fields", {}), **answer}, "needs_review": False}


def test_thread_config_uses_given_thread_id() -> None:
    assert thread_config("t-42") == {"configurable": {"thread_id": "t-42"}}


def test_thread_config_generates_unique_thread_ids() -> None:
    a = thread_config()["configurable"]["thread_id"]
    b = thread_config()["configurable"]["thread_id"]
    assert a and b and a != b


def test_interrupt_pauses_and_resumes_on_same_thread(monkeypatch, fake_llm) -> None:
    # build_graph() must compile with a working checkpointer: a node that calls
    # interrupt() pauses the run, and Command(resume=...) on the same thread_id
    # continues it to the end (issue #36 acceptance criterion).
    monkeypatch.setattr("ingest.graph.extract_invoice", _low_confidence_invoice)
    monkeypatch.setattr("ingest.graph.human_review", _interrupting_review)

    graph = build_graph()
    config = thread_config("test-thread")

    paused = graph.invoke({"path": str(SAMPLES / "sample_invoice.pdf")}, config)
    assert "__interrupt__" in paused
    assert "result" not in paused
    assert paused["__interrupt__"][0].value["fields"]

    final = graph.invoke(Command(resume={"vendor": "Corrected GmbH"}), config)
    assert "__interrupt__" not in final
    assert final["result"]["fields"]["vendor"] == "Corrected GmbH"
    assert ENVELOPE_KEYS == set(final["result"])


def test_happy_path_still_runs_unchanged(fake_llm) -> None:
    result = run(str(SAMPLES / "sample_invoice.pdf"))
    assert ENVELOPE_KEYS == set(result)


def test_run_accepts_explicit_thread_id(fake_llm) -> None:
    result = run(str(SAMPLES / "sample_invoice.pdf"), thread_id="cli-thread")
    assert ENVELOPE_KEYS == set(result)
