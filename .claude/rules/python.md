---
paths:
  - "src/**/*.py"
  - "scripts/**/*.py"
---

# Python conventions

- Python 3.12+, type hints on function signatures.
- pydantic models are the single source of truth for extracted document schemas.
- Default model **for pipeline LLM calls** is `claude-haiku-4-5`. Use Sonnet or
  Opus only with explicit justification: the IU endpoint quota is shared across
  the whole seminar. (Development inside Claude Code defaults to Sonnet — that
  rule is separate from runtime model selection.)
- No comments unless they explain a non-obvious WHY.
- Keep graph nodes small: one node, one responsibility.
