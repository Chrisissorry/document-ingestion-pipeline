from __future__ import annotations

from pathlib import Path

import pytest

from ingest.nodes.extract import extract_contract, extract_generic, extract_invoice
from ingest.nodes.human_review import human_review
from ingest.nodes.ingest import ingest
from ingest.nodes.persist import persist
from ingest.nodes.triage import triage
from ingest.nodes.validate import CONFIDENCE_THRESHOLD, validate
from ingest.schemas import Contract, GenericDocument, Invoice

SAMPLES = Path(__file__).resolve().parent.parent.parent / "samples"
TEXT_PDF = str(SAMPLES / "sample_invoice.pdf")
SCAN_PDF = str(SAMPLES / "sample_invoice_scan.pdf")

# Same envelope contract asserted by tests/test_golden_files.py.
ENVELOPE_KEYS = {"source", "tier", "doc_type", "confidence", "fields"}


# --- ingest ---------------------------------------------------------------


def test_ingest_text_layer_pdf_routes_to_text_tier() -> None:
    out = ingest({"path": TEXT_PDF})
    assert out["tier"] == "text"
    assert out["raw_text"]


def test_ingest_scanned_pdf_falls_back_to_vision_tier() -> None:
    # OCR is off by default, so a scan falls straight through to the Tier 2 stub.
    out = ingest({"path": SCAN_PDF})
    assert out["tier"] == "vision"
    assert out["raw_text"] == ""


# --- ingest: Tier 1.5 OCR (#57) -------------------------------------------
# OCR is gated by ocr_available(); these patch that gate so the suite never
# depends on the Tesseract binary being installed.


def test_ingest_uses_ocr_when_available(monkeypatch) -> None:
    monkeypatch.setattr("ingest.nodes.ingest.ocr_available", lambda: True)
    monkeypatch.setattr("ingest.nodes.ingest.ocr_first_page", lambda path: "scanned text")
    out = ingest({"path": SCAN_PDF})
    assert out["tier"] == "ocr"
    assert out["raw_text"] == "scanned text"


def test_ingest_falls_through_to_vision_when_ocr_unavailable(monkeypatch) -> None:
    monkeypatch.setattr("ingest.nodes.ingest.ocr_available", lambda: False)
    out = ingest({"path": SCAN_PDF})
    assert out["tier"] == "vision"
    assert out["raw_text"] == ""


def test_ingest_falls_through_to_vision_when_ocr_yields_no_text(monkeypatch) -> None:
    # OCR ran but produced nothing usable: do not claim the "ocr" tier on empty text.
    monkeypatch.setattr("ingest.nodes.ingest.ocr_available", lambda: True)
    monkeypatch.setattr("ingest.nodes.ingest.ocr_first_page", lambda path: "")
    out = ingest({"path": SCAN_PDF})
    assert out["tier"] == "vision"
    assert out["raw_text"] == ""


def test_ingest_text_layer_skips_ocr_even_when_available(monkeypatch) -> None:
    # A PDF with a real text layer must never reach the OCR branch.
    called = False

    def _should_not_run() -> bool:
        nonlocal called
        called = True
        return True

    monkeypatch.setattr("ingest.nodes.ingest.ocr_available", _should_not_run)
    out = ingest({"path": TEXT_PDF})
    assert out["tier"] == "text"
    assert called is False


# --- triage ---------------------------------------------------------------


def test_triage_returns_a_known_doc_type() -> None:
    out = triage({"raw_text": "INVOICE\nTotal: 100 EUR"})
    assert out["doc_type"] in {"invoice", "contract", "generic"}


def test_triage_handles_empty_text() -> None:
    # The stub always returns invoice; the contract is "never crash, always
    # return a routable doc_type" even when the text layer is empty.
    out = triage({"raw_text": ""})
    assert out["doc_type"] in {"invoice", "contract", "generic"}


# --- extractors -----------------------------------------------------------


@pytest.mark.parametrize(
    "extractor,schema",
    [
        (extract_invoice, Invoice),
        (extract_contract, Contract),
        (extract_generic, GenericDocument),
    ],
)
def test_extractor_returns_schema_valid_fields_and_confidence(extractor, schema, fake_llm) -> None:
    out = extractor({"raw_text": "irrelevant for the stub"})
    parsed = schema.model_validate(out["fields"])
    assert parsed.doc_type == schema().doc_type
    assert 0.0 <= out["confidence"] <= 1.0


@pytest.mark.parametrize(
    "extractor,schema",
    [
        (extract_invoice, Invoice),
        (extract_contract, Contract),
        (extract_generic, GenericDocument),
    ],
)
def test_extractor_emits_only_known_field_names(extractor, schema, fake_llm) -> None:
    out = extractor({"raw_text": ""})
    assert set(out["fields"]) <= set(schema.model_fields), "unknown field names"


# --- validate -------------------------------------------------------------


def test_validate_passes_high_confidence() -> None:
    out = validate({"confidence": 0.95})
    assert out["needs_review"] is False


def test_validate_flags_low_confidence() -> None:
    out = validate({"confidence": CONFIDENCE_THRESHOLD - 0.01})
    assert out["needs_review"] is True


def test_validate_flags_missing_confidence() -> None:
    out = validate({})
    assert out["needs_review"] is True


def test_validate_flags_invoice_with_missing_required_field() -> None:
    fields = {
        "doc_type": "invoice",
        "invoice_number": None,
        "date": None,
        "vendor": None,
        "total": None,
    }
    out = validate({"doc_type": "invoice", "confidence": 0.95, "fields": fields})
    assert out["needs_review"] is True


def test_validate_passes_invoice_with_all_required_fields() -> None:
    fields = {
        "doc_type": "invoice",
        "invoice_number": "INV-001",
        "date": "2026-06-11",
        "vendor": "ACME",
        "total": 100.0,
    }
    out = validate({"doc_type": "invoice", "confidence": 0.95, "fields": fields})
    assert out["needs_review"] is False


def test_validate_flags_contract_with_missing_required_field() -> None:
    fields = {"doc_type": "contract", "parties": ["A", "B"], "effective_date": None, "term": None}
    out = validate({"doc_type": "contract", "confidence": 0.95, "fields": fields})
    assert out["needs_review"] is True


def test_validate_flags_contract_with_empty_parties() -> None:
    fields = {
        "doc_type": "contract",
        "parties": [],
        "effective_date": "2026-07-01",
        "term": "12 months",
    }
    out = validate({"doc_type": "contract", "confidence": 0.95, "fields": fields})
    assert out["needs_review"] is True


def test_validate_passes_contract_with_all_required_fields() -> None:
    fields = {
        "doc_type": "contract",
        "parties": ["A", "B"],
        "effective_date": "2026-07-01",
        "term": "12 months",
    }
    out = validate({"doc_type": "contract", "confidence": 0.95, "fields": fields})
    assert out["needs_review"] is False


# --- human_review ---------------------------------------------------------
# human_review pauses with interrupt(), which only works inside a compiled
# graph with a checkpointer, so the unit tests wrap the node in a one-node graph.


def _review_graph():
    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.graph import END, START, StateGraph

    from ingest.state import IngestState

    g = StateGraph(IngestState)
    g.add_node("human_review", human_review)
    g.add_edge(START, "human_review")
    g.add_edge("human_review", END)
    return g.compile(checkpointer=MemorySaver())


def test_human_review_interrupts_with_flagged_fields() -> None:
    graph = _review_graph()
    state = {
        "doc_type": "invoice",
        "confidence": 0.4,
        "needs_review": True,
        "fields": {"doc_type": "invoice", "vendor": None, "total": 100.0},
    }
    paused = graph.invoke(state, {"configurable": {"thread_id": "t"}})
    payload = paused["__interrupt__"][0].value
    assert payload["flagged"] == ["vendor"]
    assert payload["fields"] == state["fields"]
    assert payload["doc_type"] == "invoice"


def test_human_review_applies_overrides_and_clears_the_flag() -> None:
    from langgraph.types import Command

    graph = _review_graph()
    config = {"configurable": {"thread_id": "t"}}
    state = {"needs_review": True, "fields": {"doc_type": "invoice", "vendor": None}}
    graph.invoke(state, config)
    out = graph.invoke(Command(resume={"overrides": {"vendor": "ACME"}}), config)
    assert out["needs_review"] is False
    assert out["fields"] == {"doc_type": "invoice", "vendor": "ACME"}


def test_human_review_accept_all_keeps_fields_unchanged() -> None:
    from langgraph.types import Command

    graph = _review_graph()
    config = {"configurable": {"thread_id": "t"}}
    state = {"needs_review": True, "fields": {"doc_type": "invoice", "vendor": None}}
    graph.invoke(state, config)
    out = graph.invoke(Command(resume={"overrides": {}}), config)
    assert out["needs_review"] is False
    assert out["fields"] == state["fields"]


# --- persist --------------------------------------------------------------


def test_persist_builds_full_envelope() -> None:
    state = {
        "path": "samples/sample_invoice.pdf",
        "tier": "text",
        "doc_type": "invoice",
        "confidence": 0.9,
        "fields": {"doc_type": "invoice"},
    }
    out = persist(state)
    assert ENVELOPE_KEYS == set(out["result"])
    assert out["result"]["source"] == state["path"]


def test_persist_tolerates_missing_optional_state() -> None:
    out = persist({})
    assert ENVELOPE_KEYS == set(out["result"])
    assert out["result"]["fields"] == {}
