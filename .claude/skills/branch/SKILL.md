---
name: branch
description: Start work on a GitHub issue with a correctly named branch and open its pull request, following this repo's GitHub Flow. Use when beginning a new issue, creating a feature branch, or opening a PR. Enforces branch naming, "Closes #n", squash merge, and CI-green-before-merge.
---

# Branch and PR workflow

This repo uses GitHub Flow. The full rules live in `docs/branching.md`; this skill
executes them. Keep `docs/branching.md` as the source of truth: if it changes, follow it.

## Starting an issue

1. Make sure `main` is current:
   ```bash
   git switch main && git pull
   ```
2. Create a branch named `<type>/<issue-number>-<short-slug>`:
   - types: `feat`, `fix`, `docs`, `chore`, `test`
   - example: `feat/12-invoice-extractor`
   ```bash
   git switch -c <branch>
   ```
3. If the issue number or type is unclear, ask before creating the branch.

## While working

- Commit in small steps with a conventional-commit prefix: `feat:`, `fix:`, `docs:`, `chore:`, `test:`.
- One line is enough; add a body only when the WHY is not obvious.
- Keep the change scoped to the one issue.

## Opening the PR

1. Push the branch:
   ```bash
   git push -u origin <branch>
   ```
2. Open the PR with `gh`, linking the issue so it closes on merge:
   ```bash
   gh pr create --base main --title "<type>: <summary>" --body "Closes #<n>

   <what and why>"
   ```
3. CI (`.github/workflows/ci.yml`) runs the smoke test on the PR. It must be green before merge.
4. Get one teammate review. Pair review counts.
5. Squash merge into `main`:
   ```bash
   gh pr merge --squash
   ```

## Don'ts

- Never commit directly to `main`.
- Don't bundle multiple issues into one branch or PR.
