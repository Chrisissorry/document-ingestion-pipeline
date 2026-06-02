# Code conventions

- Python 3.12+, type hints on function signatures.
- pydantic models are the single source of truth for extracted document schemas.
- Default model is `claude-haiku-4-5`. Use Sonnet or Opus only with explicit
  justification: the IU token and its quota are shared across the whole seminar.
- No comments unless they explain a non-obvious WHY.
- Everything in the repo is English. (Slides, which live outside the repo, stay German.)
- No em-dashes in prose. Use commas, parentheses, colons.
- Keep graph nodes small: one node, one responsibility.
- Branching and PR conventions live in [docs/branching.md](../../docs/branching.md).
