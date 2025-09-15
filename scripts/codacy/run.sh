#!/usr/bin/env bash
set -euo pipefail
IMAGE_TAG="5cc54a75f9ad88159bb54046196d920e40e367a5" # aligns with action v4.3.0
IMAGE="codacy/codacy-analysis-cli:latest"
OUT="results.sarif"
if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required for local Codacy analysis" >&2
  exit 2
fi
# Note: IMAGE_TAG kept as reference; the codacy CLI image currently not tag-aligned with action commit.
# Consider pinning a digest once published for supply-chain parity.
docker run --rm \
  -v "$(pwd)":/src \
  -w /src \
  -e CODACY_API_TOKEN="${CODACY_API_TOKEN:-}" \
  "$IMAGE" analyze --directory . --format sarif --output "$OUT" "$@"
echo "Codacy SARIF written to $OUT"
