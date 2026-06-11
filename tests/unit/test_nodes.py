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
    out = ingest({"path": SCAN_PDF})
    assert out["tier"] == "vision"
    assert out["raw_text"] == ""


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


# --- human_review ---------------------------------------------------------


def test_human_review_clears_the_flag() -> None:
    out = human_review({"needs_review": True, "fields": {}})
    assert out["needs_review"] is False


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
