from __future__ import annotations

import os

from anthropic import Anthropic

# Claude Haiku 4.5 — $1.00/MTok input, $5.00/MTok output
HAIKU_INPUT_PRICE = 1.00 / 1_000_000
HAIKU_OUTPUT_PRICE = 5.00 / 1_000_000

IU_BASE_URL = "https://iu-digitalisierung-seminar.services.ai.azure.com/anthropic"


def model_name() -> str:
    return os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5")


def client() -> Anthropic:
    # TODO (Extractors cluster): use this client in nodes/extract.py once stubs are replaced
    return Anthropic(
        api_key=os.environ["ANTHROPIC_AUTH_TOKEN"],
        base_url=os.environ.get("ANTHROPIC_BASE_URL", IU_BASE_URL),
    )
