# Document Ingestion Pipeline — Claude Context

This is a teaching repo for the IU "Aktuelle Themen der Digitalisierung" SS2026 seminar (Chris Tietz, lecturer). Sessions 6, 7, 8 use this repo as a continuous build thread.

## What this project is

An agentic document ingestion pipeline written in Python with LangGraph. PDF in, structured JSON out, human-in-the-loop on low confidence. Built by BA Informatik (Duales Studium) students during a ~4h hackathon in Session 7. The goal is teaching agentic engineering concepts, not shipping a product.

## Audience and constraints

- 14 students enrolled (~9 typically present). Plan for 14.
- Mixed OS (macOS / Windows / Linux). Setup must work on all.
- Shared IU API token against an Azure AI Foundry endpoint that speaks the Anthropic protocol. Quota is a real constraint.
- **Agent runtime (the ingestion pipeline):** default model `claude-haiku-4-5`. Sonnet only when explicitly justified — Vision fallback, schema extraction and other pipeline calls run on Haiku.
- **Development (Claude Code on the host):** default model `claude-sonnet-4-6`. Haiku for tight loops, Opus only when Sonnet is stuck.

## Key architectural decisions (already made)

1. **Two-tier extraction**, not three. Text-Layer (pdfplumber) first, Vision (Haiku) as fallback. OCR / Tesseract was considered and rejected for the critical path — install pain on mixed OS outweighs token savings vs Vision. OCR can live as an optional bonus issue.
2. **LLM extracts fields always.** OCR / text-layer only produce text. Field extraction is always a Haiku call against a pydantic schema.
3. **Haiku 4.5 as default.** Cheap, fast, sufficient for invoices / receipts / simple contracts. Pedagogically right ("smallest model that does the job") and quota-friendly for 14 shared users.
4. **Triage + Router via LangGraph conditional edges.** Classify document type, then route to type-specific extractor.
5. **Human-in-the-Loop via LangGraph interrupts.** When validator reports low confidence or missing required fields, the graph pauses and asks via CLI.
6. **No real customer data.** Workshop uses only fictional sample PDFs. Students who want to apply this at their Praxisunternehmen do so off-platform.
7. **Dev runs in Docker via docker compose.** Python and Postgres run as containers; the host needs only Docker, git, and Claude Code (which runs on the host, editing the mounted repo). Removes Python/uv install pain on mixed OS, which was the main setup risk for 14 students. `uv run` auto-syncs deps at runtime into a named-volume venv, so the skeleton can evolve without image rebuilds.
8. **Persistence target is Postgres 16** (the `[Persist]` node), running as a compose service. Chosen as the ubiquitous teaching default; swappable if needed.

## Curriculum thread

| Session | Date | What happens here |
|---|---|---|
| S6 | Tue 02.06.2026, 16:45-19:15 | Setup sprint (Claude Code + IU token), repo clone, product pitch, post-it work breakdown, students write GitHub issues |
| S7 | Thu 11.06.2026, 09:00-14:00 | The Big Build — 4-5h hackathon implementing the MVP |
| S8 | Tue 16.06.2026, 16:45-19:15 | LLM Security live — prompt-injection attacks against the pipeline they just built |
| S9 | Tue 23.06.2026, 16:45-19:15 | Not this repo. n8n / low-code rebuild of the same flow for comparison. |

## Cluster structure for the work breakdown

Seven planned clusters. Students discover these during post-it session; the list below is a hypothesis to fall back on if facilitation needs structure:

1. Ingestion and I/O
2. Triage and Routing
3. Schemas (pydantic)
4. Extractors (Invoice / Contract / Generic)
5. Validation and Confidence
6. Human-in-the-Loop
7. Test Data and Eval

Plus optional bonus: Tier 1.5 OCR for scans (Tesseract).

## Current state

End-to-end stub runs in Docker. Next steps remaining for setup:

- [x] Docker Compose dev environment (Python + Postgres containers)
- [x] Python project (`pyproject.toml`, hatchling, src layout)
- [x] `src/ingest/` package: `graph.py` (LangGraph wired through all node names), `nodes/` (stub bodies with cluster TODOs), `tools/` (`pdf.py` real pdfplumber, `llm.py` stubbed client), `cli.py`, `schemas.py`, `state.py`
- [x] Minimal end-to-end stub: `docker compose run --rm ingest python -m ingest samples/sample_invoice.pdf` returns dummy JSON (no API call, zero quota). Verified.
- [x] Sample PDFs via `scripts/make_samples.py` (invoice EN/DE, contract, receipt, letter) in `samples/`
- [x] GitHub issue form for cluster tasks (`.github/ISSUE_TEMPLATE/`). Chose a single form over seeded examples: students do the work breakdown and write their own issues in S6. Blank issues disabled so the form is the path.
- [x] Repo created, pushed, clone URL in SETUP.md points to `Chrisissorry/document-ingestion-pipeline`
- [ ] Slide add-on for Session 6 presentation (post-it method, acceptance criteria, graph diagram)

Also added since the original plan: Docker stack, CI on PR (`.github/workflows/ci.yml`), `docs/branching.md` (GitHub Flow), `.claude/rules/` (path-scoped) and `.claude/skills/branch`.

## Working agreements with Chris

- Be decisive. Don't re-hedge a decision that's been made. Speak up if a decision turns out to be wrong, but don't relitigate without new information.
- Lead with the punchline. Detail on demand.
- No em-dashes. Use commas, parentheses, colons.
- Everything in the repo is English (code, README, SETUP, issues, internal notes). It is a shared codebase and code repos stay English. Slides are the only exception: keep them German, since they are presented to the German-speaking seminar.
- For internal artifacts (this file, internal notes): English.
- Default to no comments in code. Only document the non-obvious WHY.

## Related context

- Lecturer / engagement: `~/Documents/projects/millie/crm/engagements/iu-digitalisierung-ss2026/`
- Presentation deck for S6 will live in `~/Documents/projects/presentations/iu-digitalisierung-ss2026-06/` (lazyslides)
- IU IT ticket for token access: ITOPS-172343 (Jens Caasen)
- Endpoint: `https://iu-digitalisierung-seminar.services.ai.azure.com/anthropic`
- Models available: `claude-sonnet-4-6`, `claude-opus-4-8`, `claude-haiku-4-5`
