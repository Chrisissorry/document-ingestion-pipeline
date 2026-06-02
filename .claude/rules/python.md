---
paths:
  - "src/**/*.py"
  - "scripts/**/*.py"
---

# Python conventions

- Python 3.12+, type hints on function signatures.
- pydantic models are the single source of truth for extracted document schemas.
- Default model is `claude-haiku-4-5`. Use Sonnet or Opus only with explicit
  justification: the IU token and its quota are shared across the whole seminar.
- No comments unless they explain a non-obvious WHY.
- Keep graph nodes small: one node, one responsibility.
