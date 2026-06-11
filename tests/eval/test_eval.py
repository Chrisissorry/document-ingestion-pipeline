from __future__ import annotations

import base64
import json
import os
import re
from pathlib import Path
from typing import Any

import pytest

from ingest.schemas import Contract, GenericDocument, Invoice
from ingest.tools.llm import HAIKU_INPUT_PRICE, HAIKU_OUTPUT_PRICE, client, model_name

GOLDEN_DIR = Path(__file__).parent.parent.parent / "samples" / "expected"
SAMPLES_DIR = Path(__file__).parent.parent.parent / "samples"

SCHEMA_MAP: dict[str, type] = {
    "invoice": Invoice,
    "contract": Contract,
    "generic": GenericDocument,
}

_GOLDEN_FILES = sorted(GOLDEN_DIR.glob("*.json"))


def _score_fields(expected: dict[str, Any], actual: dict[str, Any]) -> dict[str, bool]:
    scores: dict[str, bool] = {}
    for key, exp_val in expected.items():
        if key == "doc_type":
            continue
        act_val = actual.get(key)
        if isinstance(exp_val, list):
            scores[key] = len(act_val or []) == len(exp_val)
        elif isinstance(exp_val, float):
            scores[key] = abs((act_val or 0.0) - exp_val) < 0.02
        else:
            scores[key] = str(act_val or "").strip().lower() == str(exp_val).strip().lower()
    return scores


def _extract_json(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {}


@pytest.fixture(scope="session")
def _report_rows() -> list[dict[str, Any]]:
    return []


@pytest.fixture(scope="session", autouse=True)
def _write_report(_report_rows: list[dict[str, Any]]) -> None:  # type: ignore[return]
    yield
    if not _report_rows:
        return
    total_cost = sum(r["cost"] for r in _report_rows)
    total_in = sum(r["input_tokens"] for r in _report_rows)
    total_out = sum(r["output_tokens"] for r in _report_rows)
    lines = [
        "# Eval Report\n",
        "| File | Doc type | Fields matched | Accuracy | Input tok | Output tok | Cost ($) |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in _report_rows:
        matched = sum(r["field_scores"].values())
        total = len(r["field_scores"])
        acc = matched / total if total else 0.0
        lines.append(
            f"| {r['file']} | {r['doc_type']} | {matched}/{total} | {acc:.0%}"
            f" | {r['input_tokens']} | {r['output_tokens']} | ${r['cost']:.6f} |"
        )
    lines += [
        "",
        f"**Total:** {total_in} input tokens, {total_out} output tokens, **${total_cost:.6f}**",
    ]
    report = Path("eval_report.md")
    report.write_text("\n".join(lines) + "\n")
    print(f"\nEval report written to {report.resolve()}")


@pytest.mark.eval
@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_AUTH_TOKEN"),
    reason="ANTHROPIC_AUTH_TOKEN not set — skipping real-model eval",
)
@pytest.mark.parametrize("golden_path", _GOLDEN_FILES, ids=[f.name for f in _GOLDEN_FILES])
def test_extraction_accuracy(golden_path: Path, _report_rows: list[dict[str, Any]]) -> None:
    golden = json.loads(golden_path.read_text())
    doc_type: str = golden["doc_type"]
    expected_fields: dict[str, Any] = golden["fields"]
    pdf_path = SAMPLES_DIR / Path(golden["source"]).name

    SchemaClass = SCHEMA_MAP[doc_type]
    schema_json = SchemaClass.model_json_schema()
    prompt = (
        "Extract the fields from this document as a JSON object matching this schema:\n"
        f"{json.dumps(schema_json, indent=2)}\n\n"
        "Reply with only the JSON object and nothing else."
    )

    pdf_b64 = base64.standard_b64encode(pdf_path.read_bytes()).decode()

    llm = client()
    response = llm.messages.create(
        model=model_name(),
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_b64,
                    },
                },
                {"type": "text", "text": prompt},
            ],
        }],
    )

    raw_text = response.content[0].text
    raw_dict = _extract_json(raw_text)
    assert raw_dict, f"Could not parse JSON from model response:\n{raw_text}"

    extracted = SchemaClass.model_validate(raw_dict)
    actual_fields = extracted.model_dump(exclude={"doc_type"})
    field_scores = _score_fields(expected_fields, actual_fields)

    input_tokens: int = response.usage.input_tokens
    output_tokens: int = response.usage.output_tokens
    cost = (input_tokens * HAIKU_INPUT_PRICE) + (output_tokens * HAIKU_OUTPUT_PRICE)

    _report_rows.append({
        "file": golden_path.name,
        "doc_type": doc_type,
        "field_scores": field_scores,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost": cost,
    })

    matched = sum(field_scores.values())
    total = len(field_scores)
    accuracy = matched / total if total else 0.0

    print(f"\n{golden_path.name}: {matched}/{total} fields correct ({accuracy:.0%}), ${cost:.6f}")
    for field, ok in field_scores.items():
        status = "OK  " if ok else "FAIL"
        print(f"  {status} {field}: expected={expected_fields.get(field)!r}, got={actual_fields.get(field)!r}")
