# SARIF Static Analysis Workflow

This directory contains the baseline and current run outputs for static analysis in SARIF format, plus diff artifacts.

## Components

- `baseline.sarif` – Curated baseline representing the accepted zero-finding state at time of introduction.
- `current.sarif` – Generated on each run by `scripts/sarif/generate_sarif.py`.
- `diff-summary.json` – Machine-readable comparator output.
- `diff-report.md` – Human-readable summary used as CI artifact.

## Scripts

### Generate Unified SARIF

```bash
python scripts/sarif/generate_sarif.py --output sarif/current.sarif
# Include Trivy (slower):
python scripts/sarif/generate_sarif.py --include-trivy
```

### Compare Against Baseline

```bash
python scripts/sarif/compare_sarif.py sarif/baseline.sarif sarif/current.sarif \
  --json-output sarif/diff-summary.json \
  --md-output sarif/diff-report.md

# Optional gating / matching flags:
#   --ignore-column                # tolerate column shifts
#   --fail-on-new-errors           # non-zero exit if any new error-level findings
#   --max-new-warnings N           # fail if new warnings exceed N
#   --max-new-total N              # fail if total new findings exceed N
```

## Classification Logic

Identity key: `(ruleId, level, message.text, firstLocation.uri, line, column)`.

Categories:

- **new** – In current, not in baseline
- **fixed** – In baseline, not in current
- **persisted** – Present in both

## Severity Normalization

Tool-specific severities map to SARIF levels: `error | warning | note | none`.

## CI Non-Blocking Mode

Initial workflow does not fail the build. Threshold-based blocking can be enabled later (e.g., fail if new.error > 0).

Example gated run in CI (future):

```bash
python scripts/sarif/compare_sarif.py sarif/baseline.sarif sarif/current.sarif \
  --fail-on-new-errors --max-new-warnings 5 --max-new-total 15
```

## Updating the Baseline

1. Review `diff-report.md` after a run.
1. If all new findings are accepted (or resolved), regenerate and copy `current.sarif` over `baseline.sarif` in a dedicated PR.
1. Keep baseline diffs small & auditable.

### Recommended Cadence

- Weekly scheduled review (or before release branch cut) of `diff-report.md`.
- Immediate update if only noise from tool rule evolution and vetted as non-actionable.
- Never auto-update baseline in same PR that introduces new findings—require separate approval.

## Future Enhancements

- Fuzzy location matching (ignore column or minor line shifts)
- Rule suppression metadata file
- Threshold-based exit codes
- HTML report renderer
