from __future__ import annotations

import json
from pathlib import Path

import ingest.nodes.extract as extract
from ingest.cli import _parse_value, main

ROOT = Path(__file__).resolve().parent.parent.parent
SAMPLES = ROOT / "samples"
INVOICE_PDF = str(SAMPLES / "sample_invoice.pdf")


def test_parse_value_keeps_json_types() -> None:
    assert _parse_value("3050.0") == 3050.0
    assert _parse_value('["a", "b"]') == ["a", "b"]
    assert _parse_value("ACME GmbH") == "ACME GmbH"


def test_cli_without_args_prints_usage(capsys) -> None:
    assert main([]) == 2
    assert "usage" in capsys.readouterr().err


def test_cli_happy_path_prints_result_json(capsys, fake_llm) -> None:
    assert main([INVOICE_PDF]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["source"] == INVOICE_PDF
    assert result["doc_type"] == "invoice"


def _force_low_confidence(monkeypatch) -> None:
    def _low_confidence_invoice(state):
        out = extract.extract_invoice(state)
        out["confidence"] = 0.1
        return out

    monkeypatch.setattr("ingest.graph.extract_invoice", _low_confidence_invoice)


def test_cli_review_accept_keeps_extracted_values(monkeypatch, capsys, fake_llm) -> None:
    _force_low_confidence(monkeypatch)
    monkeypatch.setattr("builtins.input", lambda prompt: "")

    assert main([INVOICE_PDF]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["fields"]["vendor"] == "ACME Supplies Ltd."


def test_cli_review_override_persists_corrected_value(monkeypatch, capsys, fake_llm) -> None:
    _force_low_confidence(monkeypatch)
    answers = {"vendor": "Corrected GmbH", "total": "999.99"}
    monkeypatch.setattr(
        "builtins.input",
        lambda prompt: next((v for k, v in answers.items() if prompt.strip().startswith(k)), ""),
    )

    assert main([INVOICE_PDF]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["fields"]["vendor"] == "Corrected GmbH"
    assert result["fields"]["total"] == 999.99
