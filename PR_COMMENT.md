Summary: Deduplicated `llama-3.1-8b` model config, tightened exception handling, sanitized frontend env, and reduced `execute_with_optimal_model` complexity via helper extraction. Logic unchanged; reliability and maintainability improved.

Changes:
- Model config: Removed duplicate entry with conflicting cost/quality.
- Exceptions: Replaced bare catches; narrowed token-estimation and fallback paths.
- Frontend env: Scrubbed `frontend/.env.local`; added `frontend/.env.local.example`.
- Orchestrator: Extracted `_invoke_model`, `_compute_cost`, `_record_success`, `_update_memory`, `_attempt_fallback`.

Tests & Coverage: 85 passed, 8 skipped, 1 xfailed; coverage 40.76% (gate 35%).

Security: Please rotate any previously committed OpenAI and Deepgram API keys immediately. Keep keys server-side only; enable org-wide secret scanning and add a pre-commit secret scan hook.

Codacy: Repo-wide scan via Codacy CLI returned 0 issues across
Semgrep, Pylint, ESLint, PMD, and Trivy. Targeted single-file wrapper
failed in this environment; recommend the standard CLI/container path
for local runs. `.codacyignore` is active to reduce noise.

Env Hygiene: Verified `.gitignore` ignores `.env`, `.env.*`, and allows
`.env.example` while `frontend/.env.local.example` is present for local
setup.

Risk & Rollback: Low; behavior preserved. Rollback point is the orchestrator refactor commit if needed.

Next: Confirm key rotation completion, keep Codacy green on subsequent commits, and optionally reduce residual complexity/NLOC where safe.
