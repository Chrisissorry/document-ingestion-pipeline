---
paths:
  - "tests/**/*.py"
  - "samples/**"
---

# Test conventions

## Golden files are test contracts

Every `samples/*.pdf` has a matching `samples/expected/*.json`. The test in
`test_golden_files.py` validates that the pipeline output envelope matches that
file and that `fields` validates against the pydantic schema (strict mode).

When you add or change a schema field, update the affected golden files or the test fails.

## fake_llm fixture

`conftest.py` provides `fake_llm` — it patches `ingest.tools.llm.client` with a
`MagicMock` that returns a configurable JSON string. Use it in any test that would
otherwise make a live API call:

```python
def test_something(fake_llm):
    fake_llm.messages.create.return_value = _fake_response('{"doc_type": "invoice"}')
    ...
```

The fixture patches at `ingest.tools.llm.client`, so it only works when nodes call
`tools.llm.client()` — not a direct `from anthropic import Anthropic`.

## LLM smoke tests

`test_llm_smoke.py` is marked `@pytest.mark.smoke` and skipped unless
`ANTHROPIC_AUTH_TOKEN` is set. Do not make new tests depend on a live API call
unless you mark them `@pytest.mark.smoke`.
