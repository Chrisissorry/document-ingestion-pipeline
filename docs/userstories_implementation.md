# Implementation User Stories

User stories per cluster, in recommended implementation order.

---

## 1. LLM Client (dependency for all other clusters)

**As a pipeline operator, I want the system to connect to the IU Azure endpoint and call Haiku, so that downstream nodes receive real LLM responses instead of hardcoded dummy values.**

Acceptance criteria:
- `tools/llm.py` exposes a configured `Anthropic` client using `ANTHROPIC_AUTH_TOKEN` and `ANTHROPIC_BASE_URL` from the environment.
- The model defaults to `claude-haiku-4-5` via `ANTHROPIC_MODEL` (already implemented in `model_name()`).
- A call to the client with a minimal prompt succeeds against the IU endpoint.

---

## 2. Triage

**As a pipeline operator, I want the system to automatically classify an incoming PDF as `invoice`, `contract`, or `generic`, so that the correct extractor runs without manual routing.**

Acceptance criteria:
- `nodes/triage.py` sends `state["raw_text"]` to Haiku and receives one of the three labels.
- The returned `doc_type` matches what a human would classify the sample PDFs as.
- Unknown or ambiguous documents fall back to `generic`.

---

## 3. Invoice Extraction

**As an accountant, I want the system to extract invoice number, date, vendor, currency, total amount, and line items from a PDF invoice, so that I do not have to re-type them manually.**

Acceptance criteria:
- `nodes/extract.py` (`extract_invoice`) sends `state["raw_text"]` to Haiku and returns a populated `Invoice` pydantic model.
- All fields present in the PDF are filled; optional fields are `None` when absent.
- `confidence` reflects how completely the fields were filled.

---

## 4. Contract Extraction

**As a legal administrator, I want the system to extract parties, effective date, and contract term from a PDF contract, so that contract data is available in structured form.**

Acceptance criteria:
- `extract_contract` returns a populated `Contract` model.
- `parties` is a list of all named parties.
- Missing fields are `None`, not empty strings.

---

## 5. Generic Extraction

**As a document manager, I want unrecognized documents to be summarized with a title and short summary, so that even unclassifiable PDFs produce useful structured output.**

Acceptance criteria:
- `extract_generic` returns a populated `GenericDocument` model.
- `summary` is a one- to two-sentence description of the document content.

---

## 6. Validation

**As a pipeline operator, I want the system to flag documents with missing required fields per schema (not only low confidence), so that incomplete extractions are caught before persisting.**

Acceptance criteria:
- `nodes/validate.py` checks that all non-optional fields of the active schema are populated.
- `needs_review` is `True` when required fields are missing OR confidence is below the threshold.
- The threshold remains configurable via `CONFIDENCE_THRESHOLD`.

---

## 7. Human-in-the-Loop

**As a clerk, I want the system to pause and ask me to confirm or correct fields when confidence is low or required fields are missing, so that incorrect data is not saved without review.**

Acceptance criteria:
- `nodes/human_review.py` uses a LangGraph `interrupt()` to pause the graph.
- The CLI displays the current field values and prompts the user to accept or override each flagged field.
- After the user responds, the graph resumes and `needs_review` is cleared.

---

## 8. Persistence

**As a pipeline operator, I want extracted document data to be saved to Postgres, so that results are available for later retrieval and analysis.**

Acceptance criteria:
- `nodes/persist.py` inserts the record into Postgres using `DATABASE_URL` from the environment.
- The table schema matches the fields in `IngestState` (source, tier, doc_type, confidence, fields).
- The node is idempotent: re-running the same file does not create duplicate rows (upsert on source path).

---

## 9. Vision Fallback — Tier 2 (nice-to-have)

**As a pipeline operator, I want scanned PDFs without a text layer to be processed via Haiku Vision, so that scans produce structured output without requiring Tesseract.**

Acceptance criteria:
- When `extract_text()` returns an empty string, `nodes/ingest.py` renders the first page to an image and sends it to Haiku Vision.
- `state["tier"]` is set to `"vision"` for this path.
- Extraction and validation work identically to the text-layer path.

---

## 10. Test Data and Eval

**As a developer, I want a sample PDF for each document type, so that I can test the pipeline end-to-end without using real customer data.**

Acceptance criteria:
- Sample files exist in `samples/` for invoice (EN + DE), contract, receipt, and letter.
- Running the full pipeline against each sample produces a non-empty `result` dict.
- A smoke-test script or pytest fixture covers the happy path for each type.
