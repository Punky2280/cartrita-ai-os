# Secrets configuration guide

Repository secrets needed:

- EXTERNAL_CODACY_API_TOKEN: Codacy API token used by `.github/workflows/codacy-analysis.yml`.

Optional environment variables (.env/.env.local):

- BACKEND_BASE_URL: Backend URL for Next.js proxies (default <http://localhost:8000>)
- BACKEND_API_KEY or AI_API_KEY: API key injected by Next.js API routes when proxying to backend

How to add EXTERNAL_CODACY_API_TOKEN:

1. Go to GitHub → Settings → Secrets and variables → Actions → New repository secret.
2. Name: EXTERNAL_CODACY_API_TOKEN
3. Value: your Codacy API token (provided out-of-band).
4. Save. CI will use it on next push/PR.
