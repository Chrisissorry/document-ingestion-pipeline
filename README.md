# Document Ingestion Pipeline

Hackathon project for the IU seminar "Aktuelle Themen der Digitalisierung" (SS2026), Sessions 6-8.

An agentic pipeline that reads PDF documents, classifies them, extracts structured fields, and persists the result. A human only steps in when the system is unsure.

## Why this project

Every company processes documents manually every day: invoices, contracts, receipts, applications, travel expense reports. Classic OCR solutions break on layout variants, classic RPA templates rot. Agentic AI (LLM + LangGraph + tools) is fundamentally reshaping this market right now. We build a working prototype.

## Architecture

Two-stage escalation, cost-aware:

```
[Ingest PDF]
     |
[Tier 1: Text layer]  pdfplumber, free
     |
     +-- text ok     --> text
     |                     |
     +-- text empty  --> [Tier 2: Haiku Vision] --> text
                                |
                  (both paths converge on text)
                                |
                      [Triage / Classifier]
                                |
          +---------------------+---------------------+
          |                     |                     |
   [InvoiceExtractor]   [ContractExtractor]   [GenericExtractor]   Haiku + pydantic schema
          |                     |                     |
          +----------+----------+---------------------+
                     |
                [Validate]
                     |
          +----------+----------+
          |                     |
     confidence ok        confidence low
          |                     |
   [Persist: Postgres]   [Human Review (CLI)]
                                |
                         [Persist: Postgres]
```

Models via the IU Azure Foundry endpoint. **Pipeline default:** `claude-haiku-4-5` (Sonnet only when explicitly justified). **Development default (Claude Code):** `claude-sonnet-4-6`.

## Tech stack

- Python 3.12+ managed with `uv`
- LangGraph for the state graph
- Anthropic SDK against the Azure Foundry endpoint (`/anthropic/v1/messages`)
- `pdfplumber` for text-layer extraction
- `pydantic` for schemas
- Postgres for persistence
- Docker Compose for the dev environment (Python + Postgres run in containers)
- CLI as the interface, no UI

## Teaching context

| Session | Date | Focus |
|---|---|---|
| S6 | 02.06.2026 | Build prep: setup, repo clone, idea, work breakdown, write issues |
| S7 | 11.06.2026 | The Big Build: 4-5h MVP implementation |
| S8 | 16.06.2026 | LLM Security: prompt-injection attacks against your own code |

## Setup

See [SETUP.md](SETUP.md). Development runs in Docker, so you do not install Python or uv on your machine.

## Backlog

GitHub issues in the repo, grouped by cluster:

1. Ingestion and I/O
2. Triage and Routing
3. Schemas
4. Extractors (Invoice / Contract / Generic)
5. Validation and Confidence
6. Human-in-the-Loop
7. Test Data and Eval

Optional: Tier 1.5 OCR for scanned PDFs (Tesseract), a bonus issue for interested pairs.
