from __future__ import annotations

import os
from typing import Any

from anthropic import Anthropic
from pydantic import BaseModel

# Claude Haiku 4.5 — $1.00/MTok input, $5.00/MTok output
HAIKU_INPUT_PRICE = 1.00 / 1_000_000
HAIKU_OUTPUT_PRICE = 5.00 / 1_000_000

IU_BASE_URL = "https://iu-digitalisierung-seminar.services.ai.azure.com/anthropic"


def model_name() -> str:
    return os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5")


def client() -> Anthropic:
    return Anthropic(
        api_key=os.environ["ANTHROPIC_AUTH_TOKEN"],
        base_url=os.environ.get("ANTHROPIC_BASE_URL", IU_BASE_URL),
    )


def extract_structured(
    schema: type[BaseModel],
    text: str,
    *,
    system: str | None = None,
) -> BaseModel:
    tool: dict[str, Any] = {
        "name": "extract",
        "description": "Extract structured fields from the document text.",
        "input_schema": schema.model_json_schema(),
    }
    create_kwargs: dict[str, Any] = {
        "model": model_name(),
        "max_tokens": 1024,
        "tools": [tool],
        "tool_choice": {"type": "tool", "name": "extract"},
        "messages": [{"role": "user", "content": text}],
    }
    if system:
        create_kwargs["system"] = system

    response = client().messages.create(**create_kwargs)

    tool_use = next((b for b in response.content if b.type == "tool_use"), None)
    if tool_use is None:
        raise ValueError(f"Model did not call the extract tool. Response: {response.content}")

    return schema.model_validate(tool_use.input)
