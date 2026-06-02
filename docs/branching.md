# Branching and Pull Requests

We use **GitHub Flow** (lightweight), not the heavyweight Gitflow with long-lived
`develop` and `release` branches. For a 4-5 hour hackathon with seven pairs working
in parallel, short branches off `main` plus pull requests are the right amount of
process: enough to keep `main` working, not so much that it slows the build.

## The rules

1. `main` is always green. CI runs on every pull request and must pass before merge.
2. One issue, one branch, one pull request.
3. Never commit directly to `main`. Always branch.

## Branch names

`<type>/<issue-number>-<short-slug>`, for example:

- `feat/12-invoice-extractor`
- `fix/19-empty-text-layer`
- `docs/4-setup-windows-paths`

Types: `feat`, `fix`, `docs`, `chore`, `test`.

## Workflow

```bash
git switch main
git pull

git switch -c feat/12-invoice-extractor
# work, commit in small steps
git add -p
git commit -m "feat: invoice extractor calls Haiku with the Invoice schema"

git push -u origin feat/12-invoice-extractor
# then open a pull request on GitHub
```

## Pull requests

- Keep them small: one issue's worth of change.
- Link the issue in the description with `Closes #<n>` so it closes automatically on merge.
- CI (`.github/workflows/ci.yml`) runs the pipeline smoke test on the PR. It must be green before merge.
- At least one teammate reviews. Pair review counts.
- **Squash merge** into `main` to keep history linear and readable.

## Commit messages

Short, imperative, with a conventional-commit prefix: `feat:`, `fix:`, `docs:`,
`chore:`, `test:`. One line is usually enough. Add a body only when the WHY is not
obvious from the change.

## During the hackathon

Branches live hours, not days. Open a draft PR early so CI and your teammates can
see the work in progress, and merge as soon as the issue's acceptance criteria are met.
