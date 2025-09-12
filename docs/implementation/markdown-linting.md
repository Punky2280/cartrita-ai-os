# Markdown Linting Standards & Workflow

This repository enforces consistent Markdown quality to keep documentation navigable, diff-friendly, and automation-ready.

## Ruleset

Configured in `.markdownlint.jsonc`. Key enforced behaviors:

- Headings increment sequentially (no jumps)
- Blank lines: before/after headings, lists, fenced code blocks
- Ordered lists use `1.` style uniformly
- Indentation: 2 spaces for nested list content
- Line length soft cap: 140 (code blocks & tables excluded)
- No hard tabs; no trailing double-space line breaks
- Fenced code blocks surrounded by blank lines and consistently fenced
- Minimal consecutive blank lines (collapses >1)

Relaxations (intentional):

- Inline HTML allowed (expandable details, diagrams)
- First line heading not mandatory (some index/meta files)
- Required heading set not enforced (flexible document structures)

## CLI Usage

Run a full repository scan:

```bash
npm run lint:md
```

Run against a subset (example):

```bash
npx markdownlint-cli2 docs/streaming/**/*.md
```

## Pre-Commit Hook

A pre-commit hook script lives at `.githooks/pre-commit` and lints only staged Markdown files. Enable it locally:

```bash
git config core.hooksPath .githooks
chmod +x .githooks/pre-commit
```

To bypass for an emergency (rare):

```bash
git commit --no-verify -m "..."
```

## Fixing Common Issues

| Symptom | Likely Rule | Fix |
|---------|-------------|-----|
| Heading stuck to previous paragraph | MD022 / MD032 | Add blank line before heading |
| List renders as paragraph | MD032 | Ensure blank line before list start |
| Inconsistent ordered list numbers | MD029 | Make every line `1.` (auto-renumber in render) |
| Code block flagged | MD031 | Add blank line before and after fenced block |
| Tab / weird indent | MD010 / MD007 | Replace tab with spaces (2) |

## Adding New Docs

When creating a new Markdown file:

1. Start with a level-1 `#` heading (unless index/meta file)
1. Keep lines under ~140 chars for readability
1. Use fenced code blocks with language specifiers (e.g., `bash` after opening fence)
1. Prefer relative links; verify after moves with `grep` searches
1. Use `1.` style for ordered lists (automatic numbering)

## Automation & CI

Future enhancement: integrate markdown lint run into CI pipeline to prevent regressions in pull requests.

## Troubleshooting

If the hook reports failures but local `npm run lint:md` passes, ensure your staged set matches working tree (`git add -u`). Re-stage after edits.

If `npx markdownlint-cli2` fails with module not found:

```bash
npm install --include=dev
```

If using a different package manager, adapt accordingly (e.g., `pnpm dlx`, `yarn dlx`).

## Change Control

Adjust `.markdownlint.jsonc` only with justification (diff noise, rendering problems, or needed rule expansion). Document rationale
in commit messages.
