# Dependency Layering Strategy (AI Orchestrator)

## Rationale

The `ai-orchestrator` service supports both CPU-only and GPU-accelerated execution paths. Heavy, fast-moving ML dependencies (Torch, Transformers,
Accelerate, Safetensors) are isolated from the stable base runtime to:

- Reduce cold start and image size for non-GPU deployments
- Minimize unrelated churn in the primary lockfile
- Allow targeted rebuilds when ML stack updates are required
- Preserve deterministic reproducibility with hash-locked layers

## File Roles

| File | Purpose |
|------|---------|
| `services/ai-orchestrator/requirements.in` | Human-maintained base (CPU) dependency spec (no ML stack) |
| `services/ai-orchestrator/requirements-gpu.in` | Overlay spec adding GPU/ML packages (pinned) |
| `services/ai-orchestrator/constraints.txt` | Fully resolved, hash-locked base environment |
| `services/ai-orchestrator/constraints-gpu.txt` | Fully resolved, hash-locked superset (base + GPU overlay) |

## Regeneration Workflow

Always regenerate the base first, then the GPU overlay, using the pinned
pip version (24.3.1) to avoid resolver API incompatibilities observed
with newer pip versions.

```bash
# Activate reproducible build virtualenv
source .venv-repro/bin/activate

# 1. Regenerate base constraints (CPU layer)
pip install --upgrade 'pip==24.3.1' pip-tools
pip-compile \
  --generate-hashes \
  --allow-unsafe \
  --output-file services/ai-orchestrator/constraints.txt \
  services/ai-orchestrator/requirements.in

# 2. Regenerate GPU overlay (depends on resolved base)
pip-compile \
  --generate-hashes \
  --allow-unsafe \
  --output-file services/ai-orchestrator/constraints-gpu.txt \
  services/ai-orchestrator/requirements-gpu.in
```

## Verification Steps

1. GPU packages absent from base (should return nothing):

   ```bash
   grep -E '^(torch|transformers|accelerate|safetensors)==' services/ai-orchestrator/constraints.txt
   ```

1. GPU packages present in overlay:

   ```bash
   grep -E '^(torch|transformers|accelerate|safetensors)==' services/ai-orchestrator/constraints-gpu.txt
   ```

1. (Optional) Confirm no unexpected CUDA/nvidia wheels pulled unless explicitly needed.

1. Run Codacy / Trivy scans after changes:

   ```bash
   ./.codacy/cli.sh analyze --format sarif > security/sarif/results.sarif
   ```

## CI Guard

The workflow `.github/workflows/dependency-layering-guard.yml` enforces:

- No ML stack packages in `constraints.txt`
- Required ML stack presence in `constraints-gpu.txt`

## Change Policy

- Do NOT manually edit either constraints file—always recompile.
- Any ML stack version bump must include both: rationale (PR description) + confirmation of successful security scan.
- Keep pip pinned until compatibility with newer versions is validated.

## Future Enhancements

- Add automated PR comment summarizing diff of ML stack upgrades
- Integrate license scanning for overlay separately
- Add SBOM generation step for both layers
