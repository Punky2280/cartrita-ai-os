# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Cartrita AI OS is a hierarchical multi-agent AI operating system built with Python FastAPI backend and Next.js frontend. It implements a 4-level fallback system ensuring 100% uptime and features a supervisor orchestrator that routes tasks to specialized AI agents.

## Architecture

### Core Components
- **AI Orchestrator** (`/services/ai-orchestrator/`): Main Python FastAPI backend with LangGraph-based supervisor
- **Frontend** (`/frontend/`): Next.js 15 + React 18 with TypeScript, using Jotai + TanStack Query
- **API Gateway** (`/services/api-gateway/`): Node.js service for request routing
- **Infrastructure** (`/infrastructure/`): Docker configs and monitoring stack

### Agent Hierarchy
The system uses a Supervisor Orchestrator (GPT-4.1) that routes to specialized agents:
- Research Agent (GPT-5) - web research and information gathering
- Code Agent (GPT-5) - code generation and analysis
- Computer Use Agent (GPT-5) - system interactions
- Knowledge Agent (GPT-5) - knowledge base operations
- Task Agent (GPT-5) - general task execution

### Fallback System
4-level reliability architecture:
1. OpenAI API (Primary)
2. HuggingFace Local inference
3. Rule-based FSM
4. Emergency templates

## Development Commands

### Backend (AI Orchestrator)
```bash
cd services/ai-orchestrator

# Setup
pip install -r requirements.txt

# Development
python -m cartrita.orchestrator.main

# Testing
pytest -q                                    # Quick test run
pytest --cov=cartrita --cov-report=term-missing  # With coverage

# Health check
curl http://localhost:8000/health
```

### Frontend
```bash
cd frontend

# Setup
npm install

# Development
npm run dev

# Testing
npm test
npm run test:coverage
npm run type-check

# Linting
npm run lint
```

### Full Stack
```bash
# Start entire stack
docker-compose up -d

# Health checks
curl http://localhost:8000/health  # AI Orchestrator
curl http://localhost:3000/health  # Frontend
```

### Linting
- **Python**: `ruff check services/ai-orchestrator/ --fix` (auto-fixes most issues)
- **Python**: `pylint services/ai-orchestrator/` (quality scoring)
- **Markdown**: `npm run lint:md` (markdownlint)

## Key Architectural Patterns

### LangGraph State Management
The supervisor uses LangGraph with safety helpers:
- Always use `_safe_get_messages()` for message retrieval
- State updates must be immutable
- Error handling through fallback chains

### Streaming Architecture
SSE-first design for real-time responses:
- All agent interactions support streaming
- Frontend uses EventSource for SSE consumption
- Structured logging with request context

### Fallback Provider Integration
When adding new AI providers:
- Implement in `/services/ai-orchestrator/cartrita/orchestrator/providers/`
- Follow fallback chain pattern with graceful degradation
- Include health check endpoints
- Add to supervisor routing logic

### Container Security
Containers use security hardening:
- Non-root users
- Read-only filesystems where possible
- Minimal base images
- Security scanning in CI/CD

## Database & Vector Operations
- **Primary DB**: PostgreSQL 17 with pgvector extension
- **Vector DBs**: ChromaDB and FAISS for embeddings
- **Cache**: Redis 7.4+ for session and response caching
- **ORM**: SQLAlchemy 2.0 with async patterns

## Observability Stack
Full OpenTelemetry integration:
- **Metrics**: Prometheus + Grafana dashboards
- **Tracing**: Jaeger for distributed tracing
- **Logging**: Structured JSON logs with correlation IDs
- **Health**: Kubernetes-style health checks at `/health`

## Testing Strategy
- **Backend**: pytest with async support, 90%+ coverage requirement
- **Frontend**: Vitest + Testing Library for components
- **Integration**: Full stack tests with Docker Compose
- **E2E**: Playwright tests for critical user flows

## Documentation
Comprehensive docs in `/docs/` directory:
- **Architecture**: `/docs/architecture/` - system design documents
- **Implementation**: `/docs/implementation/` - technical details
- **API**: `/docs/api/` - OpenAPI schemas and examples
- **Research**: `/docs/research/` - technology evaluation reports

Key files:
- `/docs/INDEX.md` - Documentation navigation
- `/docs/implementation/IMPLEMENTATION_SUMMARY.md` - Technical overview
- `/docs/build-completion-report.md` - Current project status

## Agent Development
When creating new agents:
- Extend base classes in `/services/ai-orchestrator/cartrita/orchestrator/agents/`
- Implement required interfaces for supervisor integration
- Add fallback logic for reliability
- Include comprehensive error handling
- Follow LangChain integration patterns

## Voice Integration
Deepgram SDK integration for real-time voice:
- WebRTC streaming for low latency
- Voice Activity Detection (VAD)
- Streaming transcription with interim results
- TTS integration for voice responses

## Security Considerations
- API keys managed through environment variables
- No secrets in code or commits
- Container security scanning
- Input validation and sanitization
- CORS and security headers configured
- Rate limiting implemented
