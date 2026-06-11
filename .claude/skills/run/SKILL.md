---
name: run
description: Run the ingestion pipeline inside Docker. Use when asked to run the pipeline, test a PDF, or confirm a change works.
---

# Run the ingestion pipeline

Run a single PDF through the pipeline inside the Docker container:

```bash
docker compose run --rm ingest python -m ingest <pdf-path>
```

## Common invocations

- Default smoke test (text-layer path):
  ```bash
  docker compose run --rm ingest python -m ingest samples/sample_invoice.pdf
  ```
- Vision fallback path (scanned PDF):
  ```bash
  docker compose run --rm ingest python -m ingest samples/sample_invoice_scan.pdf
  ```
- Both CI variants back-to-back:
  ```bash
  docker compose run --rm ingest python -m ingest samples/sample_invoice.pdf
  docker compose run --rm ingest python -m ingest samples/sample_invoice_scan.pdf
  ```

## What to observe

Output is JSON on stdout. A working pipeline returns a structured document with `document_type`, extracted fields, and a `confidence` score. Errors surface as Python tracebacks.

If the user provides a PDF path as an argument, run that path. If not, default to `samples/sample_invoice.pdf`.
