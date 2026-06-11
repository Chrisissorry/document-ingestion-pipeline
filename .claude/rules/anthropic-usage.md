---
paths:
  - "src/ingest/**/*.py"
---

# LLM call pattern

All LLM calls go through `tools.llm`, not the `anthropic` SDK directly:

```python
from ..tools.llm import client, model_name

def extract_invoice(state: IngestState) -> dict:
    response = client().messages.create(
        model=model_name(),
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    text = response.content[0].text
    ...
```

`model_name()` returns the value of `ANTHROPIC_MODEL` env var (default `claude-haiku-4-5`).
`client()` constructs an `Anthropic` instance pointed at the IU Azure Foundry endpoint
(`ANTHROPIC_BASE_URL`). Do NOT hardcode the model string or instantiate `Anthropic` yourself.

For schema-driven extraction, pass the pydantic schema in the prompt:

```python
import json
schema_json = json.dumps(Invoice.model_json_schema())
```
