# Cartrita AI OS – Copilot Instructions for AI Coding Agents

These instructions help AI agents work productively in this monorepo. Keep edits small, run checks, and follow the project’s conventions.

## Big picture
- System is a hierarchical multi-agent OS.
  - Supervisor orchestrator (Python, LangGraph) decides which specialized agent to run.
  - Agents: Research, Code, Computer Use, Knowledge, Task.
  - Fallback response chain: OpenAI → HuggingFace (lazy) → FSM rules → Emergency templates.
- Services (docker-compose):
  - ai-orchestrator (FastAPI, Python) at `services/ai-orchestrator`.
  - api-gateway (Node/Next.js Fastify) at `services/api-gateway`.
  - frontend (Next.js 15) at `/frontend`.
  - Infra: Postgres (pgvector), Redis, Jaeger, Prometheus, Grafana.
- Observability: OpenTelemetry + Prometheus; JSON structured logs via structlog.

## Where key things live
- Orchestrator core: `services/ai-orchestrator/cartrita/orchestrator/core/`
  - `supervisor.py` (LangGraph StateGraph, state model, routing, error handling)
  - `metrics.py`, `database.py`, `cache.py`
- Agents: `services/ai-orchestrator/cartrita/orchestrator/agents/`
- Providers: `.../providers/`
  - `fallback_provider_v2.py` (lightweight production fallback, async, lazy HF)
  - `fallback_provider.py` (heavier reference version)
- API entry: `services/ai-orchestrator/cartrita/orchestrator/main.py`
- Frontend app: `/frontend` (Next.js 15, Vitest)
- Docs: `/docs` (architecture, research, implementation)
- Compose: `/docker-compose.yml`

## Critical workflows
- Local dev (backend):
  - Install: `cd services/ai-orchestrator && pip install -r requirements.txt`
  - Run: `python -m cartrita.orchestrator.main`
  - Health: `curl http://localhost:8000/health`
- Docker stack: `docker-compose up -d` then check health endpoints.
- Tests (backend):
  - `pytest -q` or with coverage: `pytest --cov=cartrita.orchestrator --cov-report=term-missing`
- Frontend:
  - `cd frontend && npm i && npm run dev` (env expects API at 3001).

## Patterns and conventions
- State handling with LangGraph:
  - LangGraph converts Pydantic state to a dict-like AddableValuesDict. Never assume attribute access; use safe helpers.
  - In `supervisor.py`, use `_safe_get_messages`, `_safe_set_messages`, `_safe_append_message`, and `_normalize_state` before reads/writes.
  - Avoid `state.messages = ...` or `state.messages.append(...)` outside those helpers.
- Loop prevention: `max_total_iterations`, `max_attempts_per_agent`, and `agent_attempts` are enforced in supervisor.
- OpenAI params:
  - Use `max_completion_tokens` (not `max_tokens`). Some models ignore temperature; pass via `model_kwargs` if needed.
- Fallback provider usage:
  - Prefer `fallback_provider_v2.get_fallback_provider()`.
  - Call `await provider.generate_response(message, conversation_id, context)` and expect a plain string.
- Logging: Use `structlog.get_logger(__name__)` with key=value context.
- Types: Pydantic v2 models in orchestrator state/schema.

## Integration points
- DB: PostgreSQL + pgvector. Connection params injected via env in docker-compose.
- Cache: Redis for sessions/caching.
- Observability: `/metrics` (Prometheus), OTLP to Jaeger; keep spans lightweight.
- Frontend streaming: Next.js SSE handler expects assistant messages in order; supervisor must finalize with an assistant message or END.

## Safe-edit checklist for AI agents
1. Search first: understand the target module and all its call sites.
2. For supervisor changes, update only the minimal code paths and keep state-safe helpers.
3. Keep agent public APIs stable: `execute(messages, context, metadata)` returns `{response, metadata}`.
4. After edits, run: lint/type check (if configured) and at least `pytest -q` for smoke.
5. Validate one chat flow manually via the `/api/chat` endpoint or local test.

## Examples
- Append assistant message safely in supervisor:
  - `self._safe_append_message(state, {"role":"assistant","content":text,"timestamp":time.time()})`
- Use fallback in error paths:
  - `text = await self.fallback_provider.generate_response(msg, state.conversation_id, {"purpose":"error_recovery"})`

## Gotchas
- Don’t access `state.messages` directly; use helpers.
- Ensure `ChatOpenAI` uses `max_completion_tokens`.
- Keep fallback provider v2’s async signature; older provider returns dict.
- Respect iteration/attempt limits to avoid infinite loops.

---
If anything here seems outdated or unclear, open a PR to update `.github/copilot-instructions.md` and link to the exact files/lines.
