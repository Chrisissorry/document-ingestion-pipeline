---
name: lint
description: Run ruff (check + format) and mypy inside Docker. Use when asked to lint, format, type-check, or fix code quality issues.
---

# Lint and type-check

## Default: check only (no auto-fix)

```bash
docker compose run --rm ingest uv run ruff check .
docker compose run --rm ingest uv run ruff format --check .
docker compose run --rm ingest uv run mypy src
```

Run all three and report the combined result. Stop after the first failure unless the user asks for all results.

## Auto-fix (when user asks to fix, format, or clean up)

```bash
docker compose run --rm ingest uv run ruff check --fix .
docker compose run --rm ingest uv run ruff format .
```

Note: mypy errors must be fixed manually; ruff cannot fix type errors.

## Single-tool variants

- Lint only: `docker compose run --rm ingest uv run ruff check .`
- Format only: `docker compose run --rm ingest uv run ruff format --check .`
- Type-check only: `docker compose run --rm ingest uv run mypy src`

Interpret the user's intent from context: "lint" → check only; "fix lint" or "format" → auto-fix; "type check" → mypy only.
