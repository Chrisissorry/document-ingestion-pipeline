#!/usr/bin/env bash
# Claude Code Stop-hook gate: deterministically verify the agent's work before
# it is allowed to declare itself done.
#
# Mirrors the `smoke` job in .github/workflows/ci.yml 1:1 so anything that would
# fail CI fails here first, locally, on the developer's machine -- saving shared
# CI minutes and the round-trip of a red PR.
#
# Contract with the Stop hook:
#   exit 0  -> checks passed (or skipped); the agent may stop.
#   exit 2  -> blocking error; stderr is fed back to the agent so it can fix and
#              retry. (Claude Code treats Stop-hook exit code 2 as "do not stop".)
#
# Dirty-tree gate: if the working tree has no changes vs HEAD, there is nothing
# to verify -- skip everything so pure Q&A / read-only turns stay instant.
set -uo pipefail

cd "$(git rev-parse --show-toplevel)" || exit 0

# --- Dirty-tree gate -------------------------------------------------------
# No tracked-file changes and no new untracked files => nothing to check.
if git diff --quiet && git diff --cached --quiet && [ -z "$(git ls-files --others --exclude-standard)" ]; then
  exit 0
fi

# --- Run the gates ---------------------------------------------------------
# Collect failures instead of failing fast, so the agent gets the full picture
# in one round-trip rather than fixing one thing only to hit the next.
failures=""
run() {
  local name="$1"; shift
  if ! out="$("$@" 2>&1)"; then
    failures+=$'\n'"### ${name} failed:"$'\n'"${out}"$'\n'
  fi
}

run "ruff check"        uv run ruff check .
run "ruff format check" uv run ruff format --check .
run "mypy"              uv run mypy src
# -m "not eval": eval tests hit the real IU endpoint and cost shared quota.
# They never gate the agent (they run in .github/workflows/eval.yml).
run "pytest"            uv run pytest -m "not eval" -q

if [ -n "$failures" ]; then
  {
    echo "Work is NOT complete: deterministic checks failed. Fix these before stopping."
    echo "$failures"
  } >&2
  exit 2
fi

exit 0
