#!/usr/bin/env bash
set -euo pipefail

# Standardized Codacy coverage + finalization wrapper.
# Requirements:
#   - Environment variable CODACY_PROJECT_TOKEN must be exported by caller (do NOT hardcode secrets).
#   - Python dependencies installed; pytest + coverage configured.
#   - Generates coverage.xml if missing, submits report, then performs final step.

if [[ -z "${CODACY_PROJECT_TOKEN:-}" ]]; then
  echo "ERROR: CODACY_PROJECT_TOKEN not set" >&2
  exit 1
fi

echo "[codacy] Starting analysis wrapper"

# Run tests with coverage if report not present (idempotent)
if [[ ! -f coverage.xml ]]; then
  echo "[codacy] coverage.xml not found – running pytest with coverage"
  pytest --maxfail=1 --disable-warnings -q --cov=. --cov-report=xml
else
  echo "[codacy] Using existing coverage.xml"
fi

# Submit coverage (report step) – ignore non‑zero to allow final step attempt
echo "[codacy] Submitting coverage report"
bash <(curl -Ls https://coverage.codacy.com/get.sh) report -r coverage.xml || echo "[codacy] coverage report step failed (continuing)"

# Finalize
echo "[codacy] Finalizing coverage submission"
bash <(curl -Ls https://coverage.codacy.com/get.sh) final

echo "[codacy] Completed"
