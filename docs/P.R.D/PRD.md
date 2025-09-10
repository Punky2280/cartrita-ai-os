# Cartrita AI OS – Product Requirements Document (PRD)

Version: 1.0 • Date: 2025-09-10 • Status: Active

Owners: Platform Lead (Backend), Platform Lead (Frontend)
Stakeholders: Research, Code, Knowledge, Task, Computer Use agents; DevOps; Security; Product

## 1. background & context

Cartrita AI OS is a hierarchical multi-agent system with a GPT-4.1 supervisor orchestrator and specialized GPT-5 agents (research, code, knowledge, task, computer use). It exposes an SSE-first API with WebSocket fallback and includes a Next.js 15 frontend wired via proxy routes. Observability is provided via Prometheus metrics and structured logging. Infra runs via Docker Compose with Postgres (pgvector) and Redis.

This PRD aligns product outcomes with the implemented architecture in:

- Backend: `services/ai-orchestrator/cartrita/orchestrator/`
- Frontend: `frontend/` (Next.js 15, TypeScript)
- Docs: `docs/` (architecture, streaming, voice, research)

## 2. goals

- Deliver reliable chat and voice interactions with multi-agent orchestration.
- Stream responses via SSE with consistent event semantics and shape.
- Provide WebSocket fallback for bidirectional scenarios.
- Support file uploads and voice features from the UI via Next.js proxies.
- Ensure production-grade observability, security, and performance targets.

## 3. non-goals

- Building custom ASR/TTS engines (use Deepgram and provider SDKs).
- Offline-first storage sync beyond basic retries.
- Complex multi-tenant RBAC (keep token-based auth with basic scoping initially).

## 4. personas

- End user: Chats with the system, uploads files, uses voice mode.
- Developer user: Integrates endpoints, debugs via metrics and logs.
- Admin/SRE: Monitors health/metrics, manages deployments.

## 5. user journeys

1) Chat (text)

- User sends a message.
- Backend supervisor processes; if unavailable, fallback provider responds.
- SSE stream returns a final message payload (token streaming can be expanded later).

1) Voice chat (speech → text → response)

- Browser records audio, transcribes (Deepgram) to text.
- Sends to `/api/chat/voice` (non-stream) or `/api/chat/voice/stream` (SSE) for response text.
- Response can be synthesized to audio via voice speak API.

1) File upload + context

- User uploads files via `/api/upload` or `/api/upload/multiple` (proxied to backend endpoint family).
- Uploaded artifacts can be referenced in chat context.

## 6. functional requirements

FR-1 Chat API

- Non-stream: `POST /api/chat` (JSON body with message, context, agent_override, stream=false)
- Stream: `GET /api/chat/stream` (query: message, optional context JSON string, agent_override)
- Fallback path active when supervisor fails; metadata marks fallback_used.

FR-2 Voice API

- Non-stream: `POST /api/chat/voice` (body with conversationId, transcribedText, conversationHistory, voiceMode)
- Stream: `GET /api/chat/voice/stream` (query: conversationId, transcribedText, optional conversationHistory JSON string)

FR-3 Agents API

- `GET /api/agents` (list agent statuses)
- `GET /api/agents/{agent_id}` (single agent status)

FR-4 WebSocket fallback

- `WS /ws/chat` authenticates, accepts JSON messages, returns responses.

FR-5 Uploads (via Next proxy to backend)

- `POST /api/upload` (multipart form-data)
- `POST /api/upload/multiple`

FR-6 Frontend proxy routes (Next.js 15, http-proxy)

- Implemented: `/api/chat` (POST), `/api/chat/stream` (GET), `/api/chat/voice/stream` (GET), `/api/voice/transcribe` (POST), `/api/voice/speak` (POST), `/api/upload` (POST), `/api/upload/multiple` (POST)
- All proxies inject `X-API-Key` and `Authorization: Bearer <key>`, set CORS, forward with ~70s timeout, and return unified error codes (BACKEND_DOWN, PROXY_ERROR).

FR-7 Authentication

- Token-based (`X-API-Key` and/or `Authorization: Bearer …`). Default dev key: `dev-api-key-2025`. Backend verifies via `verify_api_key`.

FR-8 Observability & health

- `GET /health` returns composite status (db, cache, supervisor, fallback)
- `GET /metrics` returns Prometheus metrics
- Structured logs with context (structlog)

## 7. non-functional requirements

NFR-1 Performance targets (based on repo docs)

- P95 first token (SSE) ≤ 350 ms (budget when token streaming is enabled)
- P95 non-stream request ≤ 1200 ms
- WebSocket first frame ≤ 400 ms

NFR-2 Reliability

- Graceful supervisor/fallback switchover; degraded mode acceptable if fallback provider is active.
- SSE must close with terminal event and no resource leaks.

NFR-3 Security

- TrustedHost allowlist enforced (localhost, domain variants)
- CORS restricted to local dev and expected domains
- Token validation on all endpoints; rate limiting can be added at gateway.

NFR-4 Observability

- Prometheus metrics for request counts, latency, errors; health statuses.
- Error handler emits structured JSON with codes.

NFR-5 Compatibility

- SSE-first (GET) standardization for streaming. WebSocket fallback supported.

## 8. api & event contracts (summary)

SSE Endpoints (GET):

- `/api/chat/stream` → emits one or more `data: {…}` messages; ends with `data: [DONE]`.
- `/api/chat/voice/stream` → emits response payload with voiceMode=true, ends with `[DONE]`.

Non-stream (POST):

- `/api/chat` → returns ChatResponse JSON
- `/api/chat/voice` → returns ChatResponse JSON

Error shape (HTTP JSON):

- `{ error: string, code: string, details?: object }` with 4xx/5xx status codes.

Note: Frontend proxies preserve streaming semantics and error codes.

## 9. data model (high level)

- Message: `{ role: user|assistant|system, content: string }`
- ChatResponse: `{ response: string, conversation_id: string, agent_used?: string, agent_type?: string, timestamp?: int, messages?: Message[], context?: object, metadata?: object, processing_time?: float, token_usage?: object }`
- HealthResponse: `{ status: healthy|unhealthy, version: string, services: { database, cache, supervisor, fallback_provider }, timestamp: float }`

## 10. telemetry & metrics

- HTTP middleware captures method, path, status, duration.
- Metrics summary endpoint aggregates counters/histograms.
- Error tracking hooks available for integration.

## 11. dependencies & environment

- Backend: Python, FastAPI, structlog, Pydantic v2, LangGraph, Redis, Postgres/pgvector
- Providers: OpenAI (primary), HF/others via fallback provider
- Voice: Deepgram for ASR and TTS
- Frontend: Next.js 15, TypeScript, http-proxy-based API routes
- Infra: Docker Compose; services include orchestrator, DB, cache, observability stack

## 12. acceptance criteria

- Non-stream and stream chat endpoints work end-to-end via frontend proxies.
- Voice chat (non-stream + stream) returns responses via proxies.
- Upload endpoints accessible via frontend and forward to backend.
- SSE endpoints always close with terminal event; no stalled connections.
- Health endpoint shows healthy when core services are up; metrics endpoint returns Prometheus text when enabled.

## 13. milestones & roadmap

M1: Connect missing proxies (upload, voice) and verify end-to-end flows.
M2: Standardize SSE streaming on GET across docs and UI; deprecate POST streaming references.
M3: Codacy analysis in CI with action items tracked and fixed.
M4: Enable token-level streaming in supervisor path; emit richer SSE events.
M5: Expand agent task progress events and frontend visualizations.

## 14. risks & mitigations

- Provider outages → Mitigation: fallback provider with multiple backends.
- SSE disconnects in some networks → Mitigation: reconnect logic and WebSocket fallback where needed.
- Latency regression → Mitigation: performance budgets, metrics alarms, profiling.
- Inconsistent API contracts → Mitigation: align PRD, code, and docs; enforce in CI.

## 15. open questions

- Finalize auth strategy for admin endpoints (beyond simple token).
- RAG/embedding provider selection and quotas for production.
- Rate limiting/burst control placement (gateway vs app).

## 16. release notes (initial)

- SSE-first streaming standardized on GET for chat and voice.
- Next.js proxies added for chat, voice, and uploads with unified error handling.
- Health/metrics endpoints provide service status and Prometheus metrics.

---
This PRD reflects the current implementation and near-term roadmap for Cartrita AI OS, harmonizing backend, frontend, and documentation into a single source of product truth.
