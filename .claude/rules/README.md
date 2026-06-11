# Project rules

Short, single-topic convention files, auto-discovered by Claude Code (recursively).
Files load at launch unless they carry a `paths:` frontmatter filter, in which case
they load only when Claude touches a matching file. Use `paths:` to keep rules
scoped and context cheap.

```markdown
---
paths:
  - "src/**/*.py"
---

# ...rule body...
```

Repo-wide, always-on conventions (English only, no em-dashes, model defaults) live
in the root [`CLAUDE.md`](../../CLAUDE.md), which is always loaded, so they are not
duplicated here.

- [python.md](python.md) — Python conventions, scoped to `src/**` and `scripts/**`.
- [langgraph-nodes.md](langgraph-nodes.md) — Node pure-function pattern, no cross-imports, return dict for state merge. Scoped to `src/ingest/nodes/`.
- [testing.md](testing.md) — Golden-file contract, `fake_llm` fixture usage, smoke test marking. Scoped to `tests/` and `samples/`.
- [anthropic-usage.md](anthropic-usage.md) — LLM calls via `tools.llm.client()`, never instantiate `Anthropic` directly. Scoped to `src/ingest/`.
