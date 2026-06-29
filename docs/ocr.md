# Tier 1.5: optional OCR for scans

Scanned PDFs have no text layer, so Tier 1 (`pdfplumber`) returns an empty string.
The pipeline's default fallback for scans is Tier 2 (Haiku Vision). Tier 1.5 adds an
**optional** local OCR step (Tesseract) that turns a scan into text without an API
call, saving quota on the shared seminar token.

This is a bonus, not part of the critical path (CLAUDE.md decision #1). OCR was kept
off the required path because the Tesseract binary is install pain on mixed OS. The
pipeline runs end to end whether or not Tesseract is present:

- **Enabled and working:** scans get `tier == "ocr"` and `raw_text` from Tesseract.
- **Not installed / not enabled:** scans fall through to the Tier 2 Vision path, exactly
  as before. Nothing crashes.

## Enabling it

Two things are needed: the Python package (`ocr` extra) and the Tesseract binary.

1. Install the Python extra:

   ```bash
   uv sync --extra ocr
   ```

2. Install the Tesseract binary (see per-OS below).

3. Set the flag (it is off by default):

   ```bash
   export INGEST_ENABLE_OCR=1
   ```

   In Docker, add it to your `.env` so the `ingest` service picks it up:

   ```
   INGEST_ENABLE_OCR=1
   ```

If the flag is unset, or either piece is missing, OCR silently stays off and the
pipeline behaves as if this tier did not exist.

## Installing Tesseract per OS

### macOS

```bash
brew install tesseract
```

### Windows

Install the UB Mannheim build (includes an installer and adds Tesseract to `PATH`):
<https://github.com/UB-Mannheim/tesseract/wiki>. Reopen your shell afterwards so
`PATH` is refreshed.

### Linux (Debian / Ubuntu)

```bash
sudo apt-get update && sudo apt-get install -y tesseract-ocr
```

### Docker

The image is `python:3.12-slim` and does not ship Tesseract. To use OCR inside the
container, add it to the `Dockerfile`:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*
```

then rebuild (`docker compose build ingest`). This is intentionally left out of the
default image to keep the build light, since OCR is opt-in.

## Verifying

With Tesseract installed and the flag set, a scanned sample should report the OCR tier:

```bash
INGEST_ENABLE_OCR=1 uv run python -c \
  "from ingest.nodes.ingest import ingest; \
   r = ingest({'path': 'samples/sample_invoice_scan.pdf'}); \
   print(r['tier'], len(r['raw_text']))"
# -> ocr 244
```
