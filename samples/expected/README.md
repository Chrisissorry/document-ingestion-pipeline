# Golden expected outputs

One JSON per sample PDF in `samples/`, holding the ground-truth pipeline output.
The integration test and the eval harness assert accuracy against these files.

## Format

Each file mirrors the pipeline's result envelope:

| Key | Meaning |
|---|---|
| `source` | Path of the sample PDF, relative to the repo root |
| `tier` | Extraction tier expected to succeed: `text` (pdfplumber) or `vision` (Haiku) |
| `doc_type` | Routed document type: `invoice`, `contract`, or `generic` |
| `confidence` | Indicative confidence; treat as a lower bound, not an exact-match target |
| `fields` | The extracted fields, shaped by the pydantic schemas in `src/ingest/schemas.py` |

`fields` must validate against the schema matching `doc_type` (`Invoice`,
`Contract`, or `GenericDocument`). `tests/test_golden_files.py` enforces this.

For `generic` documents, `title` and `summary` are free-form: evals should score
them by similarity or key facts, not byte equality.

## Provenance

- `sample_*.json`: hand-authored against the checked-in `sample_*.pdf` files.
- Generated variants (`invoice_0001.json`, ...): written by
  `scripts/make_samples.py` alongside their PDFs.
