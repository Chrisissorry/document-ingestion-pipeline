# Setup

Step-by-step so you have a working environment after Session 6.

Development runs in Docker. Python and Postgres run in containers, so you do **not** install Python or uv on your machine. On the host you only need Docker, git, and Claude Code. Claude Code runs on the host and edits the files that are mounted into the container.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (macOS or Windows)
- Git
- GitHub account (send your username to Chris in the session)
- IU Azure API token (you get it in Session 6)

No local Python, no local uv. Those live in the container.

## 1. Clone the repo

Pick a folder where you keep your repos.

**macOS / Linux**

```bash
mkdir -p ~/projects && cd ~/projects
git clone https://github.com/Chrisissorry/document-ingestion-pipeline.git
cd document-ingestion-pipeline
```

**Windows (PowerShell)**

```powershell
mkdir $env:USERPROFILE\projects -Force; cd $env:USERPROFILE\projects
git clone https://github.com/Chrisissorry/document-ingestion-pipeline.git
cd document-ingestion-pipeline
```

## 2. Install Claude Code (on the host)

**macOS / Linux**

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

**Windows (PowerShell)**

```powershell
irm https://claude.ai/install.ps1 | iex
```

Check:

```bash
claude --version
```

## 3. Configure the IU token

In Session 6 you get the API key from Chris. It is needed in two places: by the container (via `.env`) and by Claude Code on the host (via shell environment).

The endpoint is Microsoft Foundry's Anthropic-compatible passthrough. Three models are available:

| Model | When to use |
|---|---|
| `claude-sonnet-4-6` | **Default for Claude Code (development).** Best price/performance for coding. |
| `claude-haiku-4-5` | **Default for the pipeline (agent runtime in `.env`).** Cheap, fast — right for bulk document calls. Also good for tight Claude Code loops. |
| `claude-opus-4-8` | Highest capability. Use only when Sonnet is stuck. |

So the split: Claude Code (development on the host) runs on Sonnet, the container (pipeline runtime) runs on Haiku. This is deliberate. The repo ships `.claude/settings.json`, which points Claude Code at the IU endpoint and pins the model IDs (Sonnet as the default), so on the host you only provide the token. The container reads its endpoint and Haiku model from `.env`.

**Why Claude Code may still ask for a login method:** Claude Code authenticates from your shell environment (plus the shipped `.claude/settings.json`). It does not read the project `.env`, that file only feeds the Docker container. So filling in `.env` alone is not enough for Claude Code on the host. When `ANTHROPIC_AUTH_TOKEN` is present in the shell before you start `claude`, the bearer token is detected and the "Select login method" chooser is skipped. If it is missing, Claude Code falls back to that interactive prompt.

Reference: [Claude Code on Microsoft Foundry](https://code.claude.com/docs/en/microsoft-foundry#3-configure-claude-code).

### 3a. `.env` for the container

Copy the template, then open `.env` and paste your token into `ANTHROPIC_AUTH_TOKEN`. The other values are prefilled.

**macOS / Linux**

```bash
cp .env.example .env
```

**Windows (PowerShell)**

```powershell
Copy-Item .env.example .env
```

`.env` is gitignored. Never commit it.

### 3b. Token for Claude Code on the host

**macOS / Linux**

```bash
read -s ANTHROPIC_AUTH_TOKEN && export ANTHROPIC_AUTH_TOKEN
# paste token, press Enter
export ANTHROPIC_BASE_URL="https://iu-digitalisierung-seminar.services.ai.azure.com/anthropic"
```

The model is not exported here: Claude Code picks up Sonnet from the committed
`.claude/settings.json`. Confirm the token is visible in this shell before launching `claude`:

```bash
[ -n "$ANTHROPIC_AUTH_TOKEN" ] && echo "token set" || echo "TOKEN MISSING, claude will ask for a login method"
```

For permanent use, store the token in the macOS Keychain instead of plain text:

```bash
security add-generic-password -a "$USER" -s iu-azure-key -w
# type the token once, then in ~/.zshrc:
export ANTHROPIC_AUTH_TOKEN="$(security find-generic-password -a "$USER" -s iu-azure-key -w)"
```

**Windows (PowerShell)**

```powershell
$env:ANTHROPIC_AUTH_TOKEN = "<paste-token>"
$env:ANTHROPIC_BASE_URL = "https://iu-digitalisierung-seminar.services.ai.azure.com/anthropic"
```

The model is not set here: Claude Code picks up Sonnet from the committed
`.claude/settings.json`. Confirm the token is visible in this shell before launching `claude`:

```powershell
if ($env:ANTHROPIC_AUTH_TOKEN) { "token set" } else { "TOKEN MISSING, claude will ask for a login method" }
```

To persist across sessions, add the same two lines to your PowerShell profile (`notepad $PROFILE`).

## 4. Build the container

Same command on macOS and Windows:

```bash
docker compose build
```

## 5. Start Postgres

```bash
docker compose up -d db
docker compose ps
```

`db` should report `healthy`.

## 6. Smoke test against the endpoint

**macOS / Linux**

```bash
curl -X POST "$ANTHROPIC_BASE_URL/v1/messages" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ANTHROPIC_AUTH_TOKEN" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-sonnet-4-6",
    "max_tokens": 200,
    "messages": [{"role": "user", "content": "Reply with one word: ping"}]
  }'
```

**Windows (PowerShell)** — use `curl.exe` (not the `curl` alias):

```powershell
curl.exe -X POST "$env:ANTHROPIC_BASE_URL/v1/messages" `
  -H "Content-Type: application/json" `
  -H "Authorization: Bearer $env:ANTHROPIC_AUTH_TOKEN" `
  -H "anthropic-version: 2023-06-01" `
  -d '{\"model\":\"claude-sonnet-4-6\",\"max_tokens\":200,\"messages\":[{\"role\":\"user\",\"content\":\"Reply with one word: ping\"}]}'
```

The response should contain `"content": [{"type": "text", "text": "pong"}]` or similar.

**If you get "No such file or directory":** a copy-paste may have inserted an invisible character (U+200B) before `curl`. Retype the command, or check with `echo -n "curl" | xxd`.

## 7. Test Claude Code against the endpoint

```bash
claude
```

In the chat: "Write a Python one-liner that prints 'hello'." If that works, you are ready for Session 7.

## 8. Smoke test the pipeline (in the container)

```bash
docker compose run --rm ingest python -m ingest samples/sample_invoice.pdf
```

This starts Postgres (via `depends_on`), runs the pipeline inside the container, and prints JSON (stub data at first, depending on how far the skeleton is built).

## Development tools

Run inside the container:

| Task | Command |
|------|---------|
| Lint check | `docker compose run --rm ingest uv run ruff check .` |
| Format check | `docker compose run --rm ingest uv run ruff format --check .` |
| Auto-fix lint | `docker compose run --rm ingest uv run ruff check --fix .` |
| Auto-format | `docker compose run --rm ingest uv run ruff format .` |

## Troubleshooting

- **Claude Code shows "Select login method":** the token is not in the shell you launched `claude` from. Claude Code reads the shell environment (and `.claude/settings.json`), not the project `.env`. Run the step 3b export in that same terminal, or persist it in your shell profile, then relaunch `claude`. Also make sure `claude --version` is recent.
- **Docker Desktop not running:** start it before any `docker compose` command.
- **Port 5432 already in use:** you have a local Postgres running. Stop it, or change the host port mapping in `docker-compose.yml` (e.g. `"5433:5432"`).
- **Tesseract / OCR errors:** Tier 1.5 OCR is optional and not in the MVP path. Ignore OCR-related errors.
- **Token quota reached:** we share the IU endpoint. On `429`, back off briefly and consider switching to a smaller model (`/model claude-haiku-4-5` inside Claude Code) before retrying.
- **Wrong model name:** Foundry exposes Anthropic model IDs as-is. Valid values: `claude-sonnet-4-6`, `claude-haiku-4-5`, `claude-opus-4-8`. A 404 on the model usually means a typo.
- **PDF not read:** make sure the PDF is in `samples/` and not password protected.
