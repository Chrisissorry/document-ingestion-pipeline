---
name: load-docs
description: Read project documentation (README + docs/) before starting implementation. Use at the beginning of any feature work, when context about architecture or user stories is needed, or when implementing an issue for the first time.
---

# Load project documentation context

Read the following files in order before writing any code. After reading, state in one sentence what is relevant to the current task, then proceed.

## Files to read

1. `README.md` — architecture overview, two-tier extraction model, LangGraph graph flow
2. `docs/branching.md` — workflow and PR rules (cross-check with the `/branch` skill)

## What to do with what you read

- Identify the cluster (Ingestion, Triage, Schemas, Extractors, Validation, HitL, Test Data) the current task belongs to.
- Flag any architectural constraint from README.md that the implementation must respect (model choice, Haiku default, no OCR on the critical path, Postgres as persistence target).
- Then implement. Do not re-read the docs during implementation unless something is ambiguous.

## When this skill is NOT needed

- Documentation-only changes (no code touched)
- Hotfixes where the problem and fix are already clear
