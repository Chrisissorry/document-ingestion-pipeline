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
