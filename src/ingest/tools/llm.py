from __future__ import annotations

import os


def model_name() -> str:
    return os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5")


# TODO (Extractors cluster): build the Anthropic client against the IU Azure
# Foundry endpoint and call it with a pydantic schema. The stub does not hit the
# API, so the smoke test costs no quota.
#
# from anthropic import Anthropic
#
# def client() -> Anthropic:
#     return Anthropic(
#         api_key=os.environ["ANTHROPIC_AUTH_TOKEN"],
#         base_url=os.environ["ANTHROPIC_BASE_URL"],
#     )
