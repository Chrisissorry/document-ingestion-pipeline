#!/usr/bin/env bash
# Claude Code Stop-hook gate: deterministically verify the agent's work before
# it is allowed to declare itself done.
#
# Mirrors the `smoke` job in .github/workflows/ci.yml 1:1 so anything that would
# fail CI fails here first, before a red PR burns shared CI minutes.
#
# WHERE THIS RUNS: hooks run on the HOST, where Claude Code lives. Per the repo's
# Docker-only contract (CLAUDE.md decision #7) the host has no Python/uv, so the
# checks are shipped into the `ingest` container, exactly like SETUP.md tells
# students to run them.
#
# Contract with the Stop hook:
#   exit 0  -> checks passed, or were skipped (clean tree / Docker down).
#   exit 2  -> blocking: stderr is fed back to the agent to fix and retry.
#              (Claude Code treats Stop-hook exit code 2 as "do not stop".)
#
# It blocks on RED CHECKS (something the agent can fix), never on a missing
# ENVIRONMENT (Docker down) -- a hook that wedges the loop on something the
# student can't fix in two seconds gets disabled, and then it protects nothing.
set -uo pipefail

cd "$(git rev-parse --show-toplevel)" || exit 0

# --- Dirty-tree gate -------------------------------------------------------
# No staged/unstaged/untracked changes => nothing to verify. Keeps pure Q&A and
# read-only turns instant.
if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
  exit 0
fi

# --- Pick how to reach the container ---------------------------------------
# Three-step fallback:
#   1. Docker not running        -> warn, exit 0 (degrade gracefully, CI still gates).
#   2. `ingest` already running   -> exec into it (fast; exec SKIPS the image
#                                    ENTRYPOINT, so call `uv run` explicitly).
#   3. otherwise                  -> run --rm --no-deps (throwaway; the ENTRYPOINT
#                                    is `uv run`, so DON'T repeat it; --no-deps
#                                    skips the Postgres healthcheck wait the
#                                    lint/type/test checks don't need).
if ! docker info >/dev/null 2>&1; then
  echo "WARNING [agent-gate]: Docker is not running; skipping verification." >&2
  echo "  Checks were NOT run. Start Docker Desktop to re-enable the gate (CI still enforces them)." >&2
  exit 0
fi

if docker compose ps --status running --services 2>/dev/null | grep -qx ingest; then
  dc() { docker compose exec -T ingest uv run "$@"; }
else
  dc() { docker compose run --rm --no-deps --quiet-pull ingest "$@"; }
fi

# Compose prints its own lifecycle chatter (Creating/Created, the pgdata volume
# warning, time= lines) on stderr. Strip it so the failure feedback the agent
# sees is just the ruff/mypy/pytest output, not Docker noise.
_strip_noise() {
  grep -vE '^(time=|.*Container .*(Creating|Created|Starting|Started|Running)|.*volume .*already exists)' || true
}

# --- Run the gates ---------------------------------------------------------
# Collect failures instead of failing fast, so the agent gets the full picture
# in one round-trip rather than fixing one thing only to hit the next.
failures=""
run() {
  local name="$1"; shift
  # Capture combined output with compose noise stripped, but take the exit status
  # from `dc` (PIPESTATUS[0]), not from the grep filter -- otherwise a passing
  # filter would mask a failing check.
  out="$(dc "$@" 2>&1 | _strip_noise; exit "${PIPESTATUS[0]}")"
  if [ $? -ne 0 ]; then
    failures+=$'\n'"### ${name} failed:"$'\n'"${out}"$'\n'
  fi
}

run "ruff check"        ruff check .
run "ruff format check" ruff format --check .
run "mypy"              mypy src
# -m "not eval": eval tests hit the real IU endpoint and cost shared quota.
# They never gate the agent (they run in .github/workflows/eval.yml).
run "pytest"            pytest -m "not eval" -q

if [ -n "$failures" ]; then
  {
    echo "Work is NOT complete: deterministic checks failed. Fix these before stopping."
    echo "$failures"
  } >&2
  exit 2
fi

exit 0
