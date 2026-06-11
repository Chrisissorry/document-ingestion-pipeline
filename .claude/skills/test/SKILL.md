---
name: test
description: Run the test suite (pytest) inside Docker. Use when asked to run tests, check if tests pass, or verify a code change.
---

# Run tests

```bash
docker compose run --rm ingest uv run pytest -q
```

## Options

- Verbose output with short tracebacks on failure:
  ```bash
  docker compose run --rm ingest uv run pytest -q --tb=short
  ```
- Run a specific test file or pattern (pass as args):
  ```bash
  docker compose run --rm ingest uv run pytest -q tests/test_golden_files.py
  ```
- Include the LLM smoke test (skipped by default unless `ANTHROPIC_AUTH_TOKEN` is set):
  ```bash
  docker compose run --rm ingest uv run pytest -q -m smoke
  ```

## What the tests cover

- **test_golden_files.py** — validates that pipeline output matches the expected JSON in `samples/expected/`
- **test_llm_smoke.py** — a live LLM call; skipped unless token is available

Report pass/fail count and any failures clearly.
