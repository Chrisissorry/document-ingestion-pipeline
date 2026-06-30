# Assessment after Session 8

Assessed: 2026-06-30. Branch: `main` at `606d74b`.

## Does it work?

Yes. The end-to-end pipeline runs cleanly:

```
PDF → ingest → triage → extract → validate → [human_review] → persist → JSON out
```

`docker compose run --rm ingest python -m ingest samples/sample_invoice.pdf` returns valid, structured, confidence-scored JSON. The `slurp` CLI entry point works with `--verbose`, `--no-db`, `--thread-id`, and `-o` flags. Human-in-the-loop interrupt and resume are wired and tested.

## What was built

The hackathon (S7) and subsequent PRs produced a functional agentic pipeline:

| Component | Status |
|---|---|
| LangGraph graph, full node wiring | Done |
| PDF text extraction (pdfplumber) | Done |
| Tier 1.5 OCR for scans (Tesseract, opt-in) | Done — gated by `INGEST_ENABLE_OCR=1`, degrades gracefully when absent |
| Triage node (LLM classifies doc_type) | Done |
| Invoice extractor (LLM + schema + confidence score) | Done |
| Contract extractor | Stub — returns hardcoded values, no LLM call |
| Generic extractor (`extract_structured`) | Done |
| Validation + required-field checks | Done |
| Human-in-the-loop (LangGraph interrupt/resume) | Done |
| Postgres persistence | Done |
| CLI (`slurp`) with flags | Done |
| Prompt injection hardening (document tags) | Partial — see below |
| Unit test suite | Done (35+ tests, all pass) |
| Integration tests (DB, graph e2e, HITL) | Done — CI runs DB tests against a real Postgres service |

## What is incomplete

### Contract extractor (`nodes/extract.py`)

`extract_contract` is a hardcoded stub. It returns `Party A / Party B`, a fixed date, and `0.88` confidence for every document, with no LLM call. Any contract run through the pipeline produces identical fictional output.

**Fix:** implement `extract_contract` using `extract_structured(Contract, state["raw_text"])`, the same pattern already used by `extract_generic`.

### Vision tier — Tier 2 (`nodes/ingest.py`)

When pdfplumber finds no text and OCR is disabled (or Tesseract is absent), the pipeline sets `tier=vision` and carries `raw_text=""`. Triage and extraction then operate on empty text. The pipeline does not crash, but produces meaningless output.

Tier 1.5 (OCR) now closes this gap when Tesseract is available. Tier 2 (Haiku Vision — render page to image, send to model) is still a TODO. `render_page_image()` already exists in `tools/pdf.py` as a shared helper; the Vision call itself is the missing piece.

**Fix:** in `ingest.py`, after the OCR branch, call `render_page_image()`, encode the image, and send it to Haiku Vision to produce `raw_text`.

### Prompt injection hardening is inconsistent

`extract_generic` uses `extract_structured`, which wraps document text in `<document>` tags and sets an injection-resistant system prompt. `extract_invoice` and `triage` make raw `messages.create` calls without these protections.

For S8 (LLM Security) this inconsistency is pedagogically useful: attacks against the invoice and triage paths succeed while the generic path resists them. If hardening all paths is the goal after S8, both nodes should be migrated to `extract_structured`.

## Test coverage

`pytest-cov` is not in the dev dependencies, so exact line coverage is not measured. From the test suite structure:

- Unit tests cover all nodes, the CLI, `extract_structured` behavior, and the OCR helpers (patched, no Tesseract binary needed).
- Integration tests cover the graph end-to-end (with `fake_llm`), the HITL interrupt/resume flow, Postgres read/write, and the checkpointer. CI runs these against a real Postgres 16 service.
- Eval tests (`tests/eval/`, `tests/test_llm_smoke.py`) are gated behind `-m eval` and require a live `ANTHROPIC_AUTH_TOKEN`. They do not run in CI.

Coverage gaps: Tier 2 Vision (not yet implemented), the contract extractor stub (covered but not meaningful until replaced).

## Remaining work

One mandatory gap and one optional one:

1. **Contract extractor** — single-node change, implement with `extract_structured`. Good candidate for a student issue.
2. **Tier 2 Vision fallback** — call Haiku Vision when pdfplumber and OCR both yield no text. `render_page_image()` is already in `tools/pdf.py`; the Vision call is the only missing piece.
