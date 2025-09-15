# Codacy Analysis & Coverage Workflow

This project standardizes Codacy invocation to ensure consistent local and CI behavior.

## Required Environment

- `CODACY_PROJECT_TOKEN` must be exported in the shell session (never commit this secret).
- Network egress allowed to `coverage.codacy.com` and GitHub releases for the CLI wrapper.

## Standard Command Pattern

The user‑approved invocation style:

```bash
export CODACY_PROJECT_TOKEN=***** && bash <(curl -Ls https://coverage.codacy.com/get.sh) final
```

Because we also want coverage reporting (XML) before the final step, the repository provides a wrapper that:

1. Generates `coverage.xml` with pytest (if missing)
1. Submits the coverage via `report`
1. Executes `final`

## Wrapper Script

Script path: `scripts/codacy/run_codacy.sh`

Run manually:

```bash
export CODACY_PROJECT_TOKEN=*****
bash scripts/codacy/run_codacy.sh
```

## Direct SARIF Analysis (Temporary Workaround)

When the MCP layer forces an unsupported `wsl` prefix or per‑file analysis fails,
run the Codacy CLI directly to generate a SARIF for comparator workflows:

```bash
export CODACY_PROJECT_TOKEN=*****
./.codacy/cli.sh analyze --format sarif > security/sarif/results.sarif
```

Then run the SARIF comparator (example):

```bash
python scripts/codacy/compare_sarif.py \
  --baseline security/sarif/baseline.sarif \
  --current security/sarif/results.sarif \
  --out security/sarif/comparison.json
```

Do not overwrite the baseline until manual review confirms only expected reductions.

## CI Integration (Planned)

In a future CI job (pre-baseline enforcement), steps will:

1. Restore dependencies
1. Run test suite with coverage (optional if relying on wrapper)
1. Invoke wrapper
1. Archive SARIF output + coverage artifacts

## Security Notes

- Never echo the raw token in logs.
- Avoid adding the token to shell history: prefix export with a space or use CI secret store.
- Remote script execution is restricted to Codacy’s official coverage script; review periodically.

## Baseline & SARIF

`security/sarif/baseline.sarif` remains the baseline for comparator gating. After significant issue remediation, regenerate and commit intentionally.

## Local Troubleshooting

| Symptom | Likely Cause | Action |
| ------- | ------------ | ------ |
| 403 during final | Invalid / revoked token | Re-issue project token |
| Empty coverage on Codacy | coverage.xml missing or zeroed | Re-run wrapper; confirm pytest executed |
| Network timeout | Corporate proxy / firewall | Configure proxy vars (`HTTP_PROXY`) |

## Next Steps

- Wire a GitHub Actions job to call the wrapper.
- Integrate SARIF comparator gating after issue count stabilizes.
