from __future__ import annotations

import json
from pathlib import Path

import pytest

from ingest.schemas import Contract, GenericDocument, Invoice

EXPECTED = Path(__file__).resolve().parent.parent / "samples" / "expected"
SCHEMAS = {"invoice": Invoice, "contract": Contract, "generic": GenericDocument}
ENVELOPE_KEYS = {"source", "tier", "doc_type", "confidence", "fields"}

GOLDEN_FILES = sorted(EXPECTED.glob("*.json"))


def test_every_sample_pdf_has_a_golden_file() -> None:
    samples = Path(__file__).resolve().parent.parent / "samples"
    missing = [
        pdf.name
        for pdf in samples.glob("*.pdf")
        if not (EXPECTED / pdf.with_suffix(".json").name).exists()
    ]
    assert not missing, f"samples without golden files: {missing}"


@pytest.mark.parametrize("path", GOLDEN_FILES, ids=lambda p: p.name)
def test_golden_file_is_valid(path: Path) -> None:
    golden = json.loads(path.read_text())

    assert ENVELOPE_KEYS <= golden.keys(), f"missing keys: {ENVELOPE_KEYS - golden.keys()}"
    assert golden["source"] == f"samples/{path.stem}.pdf"
    assert golden["tier"] in {"text", "vision"}
    assert 0.0 <= golden["confidence"] <= 1.0

    schema = SCHEMAS[golden["doc_type"]]
    parsed = schema.model_validate(golden["fields"], strict=True)
    assert parsed.doc_type == golden["doc_type"]
    assert set(golden["fields"]) <= set(schema.model_fields), "unknown field names"
