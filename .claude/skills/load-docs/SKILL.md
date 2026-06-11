---
name: load-docs
description: Read project documentation (README + docs/) before starting implementation. Use at the beginning of any feature work, when context about architecture or user stories is needed, or when implementing an issue for the first time.
---

# Load project documentation context

Read the following files in order before writing any code. After reading, state in one sentence what is relevant to the current task, then proceed.

## Files to read

1. `README.md` — project overview and architecture
2. Everything in `docs/` — list the directory and read each file found there

## What to do with what you read

- Identify the cluster (Ingestion, Triage, Schemas, Extractors, Validation, HitL, Test Data) the current task belongs to.
- Flag any architectural constraint that the implementation must respect (model choice, Haiku default, no OCR on the critical path, Postgres as persistence target).
- Then implement. Do not re-read the docs during implementation unless something is ambiguous.

## After implementation

Once the code is done, evaluate the docs:

- Does any file in `docs/` describe behaviour that has now changed? Update it.
- Is there a concept, workflow, or architectural decision introduced that is not yet documented? Create a new file in `docs/`.
- Does `README.md` need to reflect the change (architecture diagram, setup steps, new node in the graph)?

If no update is needed, state that explicitly so the reviewer knows it was checked.

## When this skill is NOT needed

- Documentation-only changes (no code touched)
- Hotfixes where the problem and fix are already clear
