# Codacy Integration Remediation & Hardening

This document captures required follow-up actions to stabilize and harden the Codacy analysis integration.

## Findings

1. Workflow `.github/workflows/codacy-analysis.yml` now pinned to immutable commit:
  `codacy/codacy-analysis-cli-action@5cc54a75f9ad88159bb54046196d920e40e367a5`
  (release tag `v4.3.0`).
1. No local Codacy CLI invocation script present; analysis entirely GitHub Action–based.
1. Token logic: `EXTERNAL_CODACY_API_TOKEN` (preferred) with fallback to `CARTRITA_AI_OS_2025` secret.
1. SARIF uploaded to GitHub code scanning; no baseline suppression file present.

## Required Remediations

1. Pin Action to Immutable Commit (COMPLETED)

   - Applied: `5cc54a75f9ad88159bb54046196d920e40e367a5` (maps to tags `v4.3` &
     `v4.3.0`).
   - Verification method:
     `git ls-remote https://github.com/codacy/codacy-analysis-cli-action.git | grep v4.3.0`.

1. Add Execution Integrity Comment

  - Immediately above the action step: rationale for pin + date.

1. Introduce Fail-Fast Policy

   - Add `continue-on-error: false` (default) but explicitly ensure non‑zero exit
     surfaces failure.

1. Add Output Artifact Archival

Upload `results.sarif` as build artifact for historical diffing.

1. Secret Validation Guard

   - Add a step to echo (masked) presence of token:
     `[INFO] Codacy token present: ${{ env.CODACY_TOKEN != '' }}`.

1. Tool Version Drift Monitoring (COMPLETED)

Weekly cron present: `23 4 * * 1`.

1. Quality Gate Aggregation (NEW)

   - Added `quality-gate` job requiring both `codacy` and `markdownlint` success.
   - Fails pipeline early if either analysis or linting fails to enforce minimum
     quality standard pre-merge (enable via branch protection).

1. Optional: Baseline Handling

   - If initial flood of issues is large, consider storing first SARIF and
     filtering new ones. Current policy: show all for rapid remediation.

## Proposed Workflow Additions (Patch Outline)

```yaml
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '17 3 * * 1'

jobs:
  codacy:
    steps:
      - name: Verify Codacy token presence
        run: |
          if [ -n "${CODACY_TOKEN}" ]; then echo "Token status: PRESENT"; else echo "Token status: MISSING"; fi
      - name: Archive SARIF
        uses: actions/upload-artifact@v4
        with:
          name: codacy-sarif
          path: results.sarif
```

## Local Developer Guidance

Local execution intentionally avoided to prevent version drift; rely on action’s containerized toolchain. If a local preview is essential:

```bash
docker run --rm \
  -v "$PWD":/src \
  -w /src \
  codacy/codacy-analysis-cli:latest \
  analyze --directory . --format sarif --output results.sarif
```

Do not commit this workflow change until hash verified.

## Next Steps Checklist

- [x] Identify and verify latest digest for v4 action
- [x] Patch workflow with pinned digest & schedule
- [x] Add artifact upload step
- [x] Communicate remediation in CHANGELOG (Security / QA section)
- [ ] Add branch protection requiring `quality-gate` (manual repo setting)
- [ ] (Optional) Introduce SARIF baseline filtering strategy once issue backlog reduced

## Local Execution Script (Planned)

Introduce `scripts/codacy/run.sh` to provide consistent local Docker-based invocation:

```bash
#!/usr/bin/env bash
set -euo pipefail
IMAGE="codacy/codacy-analysis-cli:latest"
OUT="results.sarif"
docker run --rm \
  -v "$(pwd)":/src \
  -w /src \
  -e CODACY_API_TOKEN="${CODACY_API_TOKEN:-}" \
  "$IMAGE" analyze --directory . --format sarif --output "$OUT" "$@"
echo "SARIF written to $OUT"
```

Rationale: Enables pre-push inspection without relying on locally installed CLI
binary. Keep image tag aligned with pinned action release (`v4.3.0` currently).

## Security Considerations

- Pinned digest prevents supply-chain drift.
- Schedule ensures detection of latent dependency CVEs even without code changes.
- Dual secret fallback may hide misconfiguration; recommend enforcing single canonical secret.
