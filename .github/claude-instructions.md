# Cartrita AI OS – Claude Instructions for AI Assistant

These instructions help Claude work effectively with the Cartrita AI OS project, understanding its architecture, conventions, and best practices for maintenance and development.

## 🎯 Project Overview

Cartrita AI OS is a **hierarchical multi-agent AI system** with the following architecture:

### Core Components
- **Supervisor Orchestrator**: GPT-4.1 powered LangGraph system that routes requests to specialized agents
- **Specialized Agents**: Research, Code, Computer Use, Knowledge, and Task agents (each using GPT-5)
- **Fallback Provider**: 4-level fallback system ensuring 100% uptime
- **Frontend**: Next.js 15 with SSE-first streaming architecture
- **Infrastructure**: Docker-composed services with observability stack

### System Philosophy
- **Reliability First**: Multiple fallback layers ensure service never fails
- **Agent Specialization**: Each agent optimized for specific task domains  
- **Modern Architecture**: SSE streaming, async patterns, containerized deployment
- **Observability**: Comprehensive monitoring with OpenTelemetry, Prometheus, Grafana

## 📁 Project Structure

```
cartrita-ai-os/
├── frontend/                          # Next.js 15 frontend application
│   ├── src/components/                # React components with TypeScript
│   ├── src/services/                  # API clients and streaming services
│   ├── src/pages/api/                 # Next.js API routes (proxy layer)
│   └── src/hooks/                     # React hooks for state management
├── services/
│   ├── ai-orchestrator/               # Main Python FastAPI backend
│   │   ├── cartrita/orchestrator/
│   │   │   ├── core/                  # Core supervisor and state management
│   │   │   ├── agents/                # Specialized AI agents
│   │   │   ├── providers/             # Fallback and external providers
│   │   │   └── main.py               # FastAPI application entry point
│   │   └── requirements.txt          # Python dependencies
│   └── api-gateway/                   # Node.js gateway (if present)
├── docs/                             # Comprehensive project documentation
├── docker-compose.yml               # Container orchestration
└── .github/                         # CI/CD and instruction files
```

## 🔧 Key Technologies & Versions

- **Backend**: Python 3.13, FastAPI, LangGraph, LangChain, OpenAI GPT-4.1/GPT-5
- **Frontend**: Next.js 15, React 18, TypeScript, Jotai (state), TanStack Query
- **Database**: PostgreSQL 17 + pgvector 0.8.0 for vector operations
- **Cache**: Redis 7.4+ with performance optimizations
- **Containerization**: Docker with multi-stage builds, security hardening
- **Observability**: OpenTelemetry, Prometheus, Jaeger, Grafana, structured logging

## 🎛️ Fallback Provider System

The **4-level fallback system** ensures chat responses are always available:

1. **Level 1: OpenAI API** (Primary) - GPT-4.1/GPT-5 via official API
2. **Level 2: HuggingFace Local** - Local inference with transformers
3. **Level 3: Rule-based FSM** - Finite state machine with pattern matching
4. **Level 4: Emergency Templates** - Static template responses

### Integration Points
- Integrated into `/api/chat` and `/api/chat/stream` endpoints
- Health check reports fallback provider status
- Graceful degradation with metadata tracking
- Context-aware responses at all levels

## ⚡ Development Workflows

### Backend Development
```bash
# Setup
cd services/ai-orchestrator
pip install -r requirements.txt

# Run locally
python -m cartrita.orchestrator.main

# Health check
curl http://localhost:8000/health

# Run tests
pytest -q
pytest --cov=cartrita.orchestrator --cov-report=term-missing
```

### Frontend Development
```bash
# Setup
cd frontend
npm install

# Development server
npm run dev

# Linting and type checking
npm run lint
npm run type-check

# Tests
npm test
```

### Docker Stack
```bash
# Full stack
docker compose up -d

# Check all services
curl http://localhost:8000/health  # AI Orchestrator
curl http://localhost:3000/health  # Frontend/API Gateway
```

## 🔐 Security & Best Practices

### Container Security
- Non-root users in all containers
- Multi-stage builds for minimal attack surface
- Resource limits and health checks
- TLS-ready configuration

### API Security  
- API key authentication (`X-API-Key` header)
- Rate limiting and input validation
- Structured error responses
- CORS configuration for frontend integration

### Development Security
- No secrets in code (use environment variables)
- Comprehensive input sanitization
- SQL injection prevention via parameterized queries
- XSS protection in frontend components

## 📝 Code Conventions & Patterns

### Python (Backend)
- **State Management**: Use LangGraph-safe helpers in `supervisor.py`
  - `_safe_get_messages(state)` - Safe message retrieval
  - `_safe_set_messages(state, messages)` - Safe message setting
  - `_safe_append_message(state, message)` - Safe message appending
  - Never directly access `state.messages`
- **Async Patterns**: All I/O operations must be async
- **Error Handling**: Structured exceptions with proper fallback chains
- **Logging**: Use `structlog.get_logger(__name__)` with structured context
- **Types**: Pydantic v2 models for all data structures

### TypeScript (Frontend)
- **React Patterns**: Functional components with hooks
- **State Management**: Jotai atoms for global state
- **API Integration**: TanStack Query for server state
- **Streaming**: SSE-first with WebSocket fallback
- **Type Safety**: Strict TypeScript with comprehensive typing

### Agent Development
- **Standardized Interface**: All agents implement `execute(messages, context, metadata)`
- **Return Format**: `{response: string, metadata: dict}`
- **Error Resilience**: Graceful failure with supervisor fallback
- **Specialization**: Each agent focused on specific domain expertise

## 🔄 State Management Patterns

### LangGraph State (Critical)
```python
# ❌ NEVER do this - LangGraph converts to AddableValuesDict
state.messages = new_messages
state.messages.append(message)

# ✅ ALWAYS use safe helpers
self._safe_set_messages(state, new_messages)
self._safe_append_message(state, message)
messages = self._safe_get_messages(state)
```

### Loop Prevention
- `max_total_iterations`: Global iteration limit
- `max_attempts_per_agent`: Per-agent attempt limit  
- `agent_attempts`: Counter tracking attempts
- Enforced in supervisor to prevent infinite loops

## 🌐 API Endpoints & Integration

### Core Endpoints
- `POST /api/chat` - Standard chat with fallback integration
- `GET /api/chat/stream` - SSE streaming with fallback
- `GET /api/agents` - List available agents
- `GET /api/agents/{id}` - Get agent status
- `GET /health` - Comprehensive health check
- `GET /metrics` - Prometheus metrics

### Streaming Architecture
- **Primary**: Server-Sent Events (SSE) for AI responses
- **Fallback**: WebSocket for bidirectional communication
- **Proxy Layer**: Next.js API routes add authentication
- **Error Handling**: Graceful degradation with informative messages

## 🧪 Testing Strategy

### Backend Testing
```bash
# Unit tests
pytest tests/ -v

# Integration tests
pytest tests/integration/ -v

# Coverage reporting
pytest --cov=cartrita.orchestrator --cov-report=html
```

### Frontend Testing
```bash
# Component tests
npm run test

# E2E tests (if configured)
npm run test:e2e

# Type checking
npm run type-check
```

### Manual Testing
- Test chat endpoint: `curl -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" -H "X-API-Key: dev-api-key-2025" -d '{"message": "Hello"}'`
- Test streaming: Access `/api/chat/stream?message=test` via frontend
- Test fallback levels by disabling OpenAI API key

## 🎯 Claude-Specific Guidelines

### When Working with This Project
1. **Always Use TodoWrite**: Track progress with the TodoWrite tool for complex tasks
2. **Safety First**: Read files before editing, especially `supervisor.py`
3. **Fallback Integration**: When modifying chat endpoints, ensure fallback provider integration
4. **Error Handling**: Provide informative error messages for users
5. **Documentation**: Update relevant docs when making architectural changes

### Debugging Approach
1. **Check Health Endpoints**: Start with `/health` to verify service status
2. **Review Logs**: Structured logs provide detailed error context
3. **Test Fallback Levels**: Verify fallback provider works at all levels
4. **Frontend/Backend Separation**: Isolate whether issues are client or server-side

### Common Tasks
- **Adding New Agents**: Follow the standardized agent interface in `/agents/`
- **Modifying Chat Flow**: Update supervisor routing logic safely
- **Frontend Components**: Maintain TypeScript strict typing
- **Container Updates**: Test both local development and Docker environments

## 🚨 Critical Gotchas

### Backend
- **LangGraph State**: Never directly access `state.messages` or `state` attributes
- **OpenAI API**: Use `max_completion_tokens` (not `max_tokens`)
- **Async/Await**: All I/O operations must be properly awaited
- **Agent Loop Limits**: Respect iteration limits to prevent infinite loops

### Frontend  
- **SSE Streaming**: Handle connection failures gracefully
- **API Proxy**: Frontend calls Next.js API routes, not backend directly
- **Type Safety**: Maintain strict TypeScript compliance
- **Error Boundaries**: Implement proper error handling for streaming

### Integration
- **Fallback Provider**: Always integrate fallback into new chat endpoints
- **Health Checks**: Include new services in health monitoring
- **Container Ports**: Ensure port consistency across docker-compose and frontend config

## 📚 Key Documentation

- **Architecture**: `/docs/agents/agent-architecture.md`
- **Implementation**: `/docs/implementation/IMPLEMENTATION_SUMMARY.md`
- **Build Status**: `/docs/build-completion-report.md`
- **Technology Research**: Various files in `/docs/technology/`

## 🎉 Success Metrics

When working with Cartrita AI OS, successful task completion includes:
- ✅ All services pass health checks
- ✅ Chat responses work with fallback integration
- ✅ No TypeScript or Python linting errors
- ✅ Tests pass (backend and frontend)
- ✅ Streaming functionality works correctly
- ✅ Error messages are user-friendly and actionable

---

**Remember**: This is a production-ready system with real users. Always test changes thoroughly and maintain the high reliability standards established by the fallback provider system.

*Last updated: Based on comprehensive project analysis and copilot instructions*