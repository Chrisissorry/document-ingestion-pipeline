from __future__ import annotations

import json
from pathlib import Path

from langgraph.types import Command

import ingest.nodes.extract as extract
from ingest.graph import _route_by_confidence, build_graph, run, thread_config
from ingest.schemas import Invoice

ROOT = Path(__file__).resolve().parent.parent.parent
SAMPLES = ROOT / "samples"
EXPECTED = SAMPLES / "expected"

ENVELOPE_KEYS = {"source", "tier", "doc_type", "confidence", "fields"}

# Fields the stub extractor produces that also appear in the golden file. Stub-only
# values (e.g. invoice_number "STUB-001") are intentionally not asserted against the
# golden; they tighten automatically once a real Haiku extractor replaces the stub.
GOLDEN_STABLE_FIELDS = ("vendor", "date", "total", "currency")


def _golden(name: str) -> dict:
    return json.loads((EXPECTED / name).read_text())


def test_full_graph_output_matches_golden_shape(fake_llm) -> None:
    golden = _golden("sample_invoice.json")
    result = run(golden["source"])  # repo-relative path, matches the golden "source"

    assert ENVELOPE_KEYS == set(result)
    assert result["doc_type"] == golden["doc_type"] == "invoice"
    assert result["source"] == golden["source"]

    # fields validate against the same schema the golden uses
    Invoice.model_validate(result["fields"])
    assert set(result["fields"]) <= set(Invoice.model_fields)

    for key in GOLDEN_STABLE_FIELDS:
        assert result["fields"][key] == golden["fields"][key], key


def test_text_sample_routes_through_text_tier(fake_llm) -> None:
    result = run(str(SAMPLES / "sample_invoice.pdf"))
    assert result["tier"] == "text"


def test_scanned_sample_routes_through_vision_tier(fake_llm) -> None:
    result = run(str(SAMPLES / "sample_invoice_scan.pdf"))
    assert result["tier"] == "vision"


def test_low_confidence_routes_to_human_review() -> None:
    # Routing-level assertion of the HITL branch decision.
    assert _route_by_confidence({"needs_review": True}) == "human_review"
    assert _route_by_confidence({"needs_review": False}) == "persist"


def test_graph_pauses_on_low_confidence_and_resumes_with_corrections(monkeypatch, fake_llm) -> None:
    # Force the invoice extractor below CONFIDENCE_THRESHOLD so validate flags review
    # and the conditional edge routes through human_review, which pauses the graph
    # with a real interrupt instead of writing.
    def _low_confidence_invoice(state):
        out = extract.extract_invoice(state)
        out["confidence"] = 0.1
        return out

    monkeypatch.setattr("ingest.graph.extract_invoice", _low_confidence_invoice)

    graph = build_graph()
    config = thread_config()
    paused = graph.invoke({"path": str(SAMPLES / "sample_invoice.pdf")}, config)
    assert "result" not in paused  # nothing persisted while paused
    payload = paused["__interrupt__"][0].value
    assert payload["confidence"] == 0.1

    final = graph.invoke(Command(resume={"overrides": {"vendor": "Corrected GmbH"}}), config)
    assert final["needs_review"] is False
    assert final["result"]["fields"]["vendor"] == "Corrected GmbH"
