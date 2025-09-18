# CLAUDE.md

This file provides comprehensive guidance to Claude Code (claude.ai/code) for working with the Cartrita AI OS codebase. Follow these instructions EXACTLY for rapid feature development while maintaining production quality and security.

## 🚀 PRIORITY DIRECTIVES

1. **ALWAYS** run security checks before modifying code
2. **ALWAYS** use existing base classes for new agents
3. **ALWAYS** run quick tests after changes (`pytest -m "not slow"`)
4. **ALWAYS** generate corresponding test files for new features
5. **NEVER** commit without running linting (ruff --fix then pylint)
6. **NEVER** use eval(), exec(), or unsafe string operations
7. **NEVER** expose API keys or secrets in code or logs

## Overview

Cartrita AI OS is a hierarchical multi-agent AI operating system with 100% uptime guarantee through a 4-level fallback system. Built with Python 3.13 (FastAPI) backend and Next.js 15 frontend, featuring advanced LangGraph orchestration and comprehensive observability.

## 🏗️ Architecture

### Core Technology Stack
- **Python 3.13**: With 11% performance improvements and free-threaded mode
- **FastAPI**: Async patterns with comprehensive middleware
- **PostgreSQL 17 + pgvector 0.8.0**: 3-5x vector query performance
- **Redis 7.4+**: Hash field expiration and clustering
- **Next.js 15 + React 18**: TypeScript, Jotai, TanStack Query
- **Docker**: Multi-stage builds with security hardening

### Agent Hierarchy
```
CartritaOrchestrator (GPT-4.1) - Main Supervisor
├── Research Agent (GPT-5) - Web research and analysis
├── Code Agent (GPT-5) - Complex code generation
├── Computer Use Agent (GPT-4o) - System automation
├── Knowledge Agent (GPT-4.1-mini) - RAG retrieval
├── Task Agent (GPT-4.1-mini) - Planning & decomposition
├── Audio Agent (Deepgram) - Voice processing
└── Advanced Tool Agent (LangGraph) - Math, FS, Web tools
```

### Fallback System (4 Levels)
1. **OpenAI API** (Primary provider)
2. **HuggingFace Local** (Local inference fallback)
3. **Rule-based FSM** (Deterministic fallback)
4. **Emergency Templates** (Static responses)

### Directory Structure
```
/home/robbie/cartrita-ai-os/
├── services/
│   ├── ai-orchestrator/      # Main Python backend
│   ├── api-gateway/          # Node.js routing service
│   └── frontend/             # Next.js application
├── infrastructure/           # Docker & monitoring
├── docs/                    # Comprehensive documentation
└── tests/                   # Test suites
```

## 🛡️ SECURITY WORKFLOWS (MANDATORY)

### Before ANY Code Changes
```bash
# 1. Check for secrets/keys exposure
grep -r "sk-" . --exclude-dir=node_modules --exclude-dir=.git
grep -r "api_key\|secret\|password" . --exclude-dir=node_modules

# 2. Verify environment isolation
cat .env.example  # Use as template, NEVER commit .env

# 3. Run security audit
npm audit --audit-level high
safety check --json
```

### Security Anti-Patterns to AVOID
```python
# NEVER DO THIS:
eval(user_input)                    # Code injection risk
exec(dynamic_code)                  # Arbitrary code execution
os.system(f"command {user_input}")  # Command injection
pickle.loads(untrusted_data)        # Deserialization attack
f"SELECT * FROM {table_name}"       # SQL injection

# ALWAYS DO THIS:
ast.literal_eval(safe_input)        # Safe evaluation
subprocess.run(["command", param])  # Safe command execution
parameterized_queries               # SQL safety
json.loads(data)                   # Safe deserialization
input_validation                    # Validate all inputs
```

### After Code Changes
```bash
# Mandatory security scan sequence
docker scout cve cartrita-ai-orchestrator  # Container vulnerabilities
bandit -r services/ai-orchestrator/         # Python security issues
npm audit fix                               # Auto-fix JS vulnerabilities
pre-commit run --all-files                 # Run all security hooks
```

## 🚀 RAPID DEVELOPMENT COMMANDS

### Quick Start Development
```bash
# Backend Fast Start
cd services/ai-orchestrator
source venv/bin/activate  # If using virtual env
pip install -r requirements.txt
python -m cartrita.orchestrator.main

# Frontend Fast Start
cd frontend
npm install
npm run dev

# Full Stack with Docker (Fastest)
docker-compose up -d
```

### Essential Development Commands
```bash
# Quick Testing (Run after EVERY change)
pytest -m "not slow" -q                    # Fast tests only (~30s)
npm test -- --run                          # Frontend unit tests

# Linting (Run before commit)
ruff check services/ai-orchestrator/ --fix --show-fixes
npm run lint:fix                           # Auto-fix frontend

# Type Checking
npm run type-check                         # TypeScript validation
mypy services/ai-orchestrator/             # Python type hints

# Health Checks
curl http://localhost:8000/health          # Backend
curl http://localhost:3000/health          # Frontend
```

## 🤖 AGENT DEVELOPMENT PATTERNS

### Creating a New Agent (MANDATORY PATTERN)
```python
# ALWAYS extend base classes - NEVER create from scratch
from cartrita.orchestrator.agents.base import CartritaBaseAgent
from cartrita.orchestrator.types import ChatResponse

class CustomAgent(CartritaBaseAgent):
    """Follow exact naming: {purpose}_agent.py"""

    def __init__(self, api_key_manager):
        super().__init__(api_key_manager)
        self.agent_type = "custom"
        self.model_preference = ["gpt-4-turbo-preview", "gpt-3.5-turbo"]

    async def process_request(self, message: str, context: dict) -> ChatResponse:
        """MUST implement full fallback chain"""
        try:
            # Level 1: OpenAI
            response = await self._call_openai(message)
            if response:
                return response
        except Exception as e:
            self.logger.warning(f"OpenAI failed: {e}")

        try:
            # Level 2: HuggingFace
            response = await self._call_huggingface(message)
            if response:
                return response
        except Exception as e:
            self.logger.warning(f"HuggingFace failed: {e}")

        # Level 3: FSM fallback
        return self._fsm_fallback(message)

    def _fsm_fallback(self, message: str) -> ChatResponse:
        """Deterministic fallback logic"""
        # Implement state machine logic
        return ChatResponse(
            role="assistant",
            content="Fallback response",
            model="fsm"
        )
```

### Auto-Generated Test File (REQUIRED)
```python
# tests/test_custom_agent.py - AUTO CREATE THIS
import pytest
from unittest.mock import Mock, patch

@pytest.mark.unit
@pytest.mark.ai
class TestCustomAgent:
    @pytest.fixture
    def agent(self):
        mock_api_manager = Mock()
        return CustomAgent(mock_api_manager)

    @pytest.mark.asyncio
    async def test_process_request_success(self, agent):
        # Test implementation
        pass

    @pytest.mark.asyncio
    async def test_fallback_chain(self, agent):
        # Test all 4 fallback levels
        pass
```

### Update Supervisor Routing (REQUIRED)
```python
# services/ai-orchestrator/cartrita/orchestrator/agents/cartrita_core/orchestrator.py
# Add to route_to_agent method:
elif "custom" in intent.lower():
    agent = CustomAgent(self.api_key_manager)
    return await agent.process_request(message, context)
```

## 🗄️ DATABASE WORKFLOWS

### Database Changes Workflow
```bash
# 1. Modify SQLAlchemy models
vim services/ai-orchestrator/cartrita/models/database.py

# 2. Auto-generate migration
alembic revision --autogenerate -m "Add new feature"

# 3. Create rollback (ALWAYS)
alembic downgrade -1  # Test rollback
alembic upgrade head  # Re-apply

# 4. Update vector indexes for embeddings
psql -d cartrita -c "CREATE INDEX ON embeddings USING ivfflat (vector vector_cosine_ops);"

# 5. Generate TypeScript types
npm run generate:types  # Updates frontend/types/api.ts

# 6. Create seed data
python scripts/seed_database.py --feature custom
```

### Database Backup Before Migrations
```bash
# ALWAYS backup before schema changes
pg_dump cartrita > backup_$(date +%Y%m%d_%H%M%S).sql
redis-cli --rdb /tmp/redis_backup.rdb

# Apply migration
alembic upgrade head

# Verify
psql -d cartrita -c "\dt"  # Check tables
```

## 🧪 TESTING REQUIREMENTS

### Testing Workflow (MANDATORY)
```bash
# After ANY Python changes
pytest -m "not slow" -q                    # Quick suite (30s)
pytest tests/test_specific.py -v           # Specific test

# After frontend changes
npm test -- --run                          # Unit tests
npm run test:hooks                         # Hook tests

# Before marking feature complete
docker-compose -f docker-compose.test.yml up
pytest -m integration                      # Integration suite

# Coverage requirements
pytest --cov=cartrita --cov-fail-under=35  # Backend minimum
npm run test:coverage                      # Frontend coverage
```

### Test Markers for Organization
```python
@pytest.mark.unit          # Fast, isolated tests
@pytest.mark.integration   # Cross-component tests
@pytest.mark.e2e          # Full flow tests
@pytest.mark.slow         # Long-running tests (skip in quick run)
@pytest.mark.ai           # AI-dependent tests
@pytest.mark.gpu          # GPU-required tests
@pytest.mark.asyncio      # Async test functions
```

## 📊 MONITORING & OBSERVABILITY

### Development Monitoring
```bash
# Metrics endpoints
curl http://localhost:8000/metrics         # Prometheus metrics
curl http://localhost:9090                 # Prometheus UI
curl http://localhost:3002                 # Grafana (admin:admin)
curl http://localhost:16686                # Jaeger tracing

# Real-time logs
docker-compose logs -f ai-orchestrator
docker-compose logs -f --tail=100 frontend

# Performance monitoring
docker stats                               # Resource usage
ab -n 1000 -c 10 http://localhost:8000/   # Load test
```

### Structured Logging Pattern
```python
import structlog
logger = structlog.get_logger()

# ALWAYS include correlation IDs
logger.info("Processing request",
    request_id=request_id,
    agent_type="custom",
    user_id=user_id,
    metrics={"latency_ms": 250}
)
```

## 🚢 PRODUCTION DEPLOYMENT

### Pre-Deployment Checklist
```bash
# 1. Security scan
docker scout cve --only-severity critical,high
safety check --json
npm audit --audit-level high

# 2. Full test suite
pytest  # All tests including slow
npm run test:e2e

# 3. Linting & formatting
ruff check . --fix
pylint services/ai-orchestrator/ --fail-under=8.0
npm run lint

# 4. Build verification
docker-compose build --no-cache
docker-compose up --abort-on-container-exit

# 5. Performance validation
python scripts/load_test.py --concurrent 100
```

### Container Production Build
```dockerfile
# Multi-stage build pattern (ALWAYS USE)
FROM python:3.13-slim AS builder
# Build stage with full toolchain

FROM python:3.13-slim AS runtime
# Runtime with minimal dependencies
USER nonroot:nonroot
# Security hardening
```

## 🔧 ENVIRONMENT CONFIGURATION

### Required Environment Variables
```bash
# AI Providers (REQUIRED)
OPENAI_API_KEY=sk-proj-...                 # Primary AI
ANTHROPIC_API_KEY=sk-ant-...               # Fallback AI
DEEPGRAM_API_KEY=...                       # Voice processing
TAVILY_API_KEY=tvly-...                    # Web search
LANGCHAIN_API_KEY=lsv2_pt_...              # Observability

# Database (REQUIRED)
DATABASE_URL=postgresql://user:pass@localhost:5433/cartrita
REDIS_URL=redis://localhost:6380
VECTOR_DB_PATH=/data/chromadb

# Security (REQUIRED)
JWT_SECRET_KEY=$(openssl rand -hex 32)
CARTRITA_API_KEY=dev-api-key-2025
CORS_ORIGINS=["http://localhost:3000"]

# Monitoring (OPTIONAL)
PROMETHEUS_MULTIPROC_DIR=/tmp
JAEGER_AGENT_HOST=localhost
GRAFANA_API_KEY=...
```

## 🛠️ ADVANCED FEATURES

### MCP Protocol Integration
```python
from cartrita.orchestrator.agents.cartrita_core.mcp_protocol import CartritaMCPProtocol

# Model Context Protocol for agent communication
protocol = CartritaMCPProtocol()
await protocol.register_agent(agent_instance)
```

### LangGraph State Management
```python
# ALWAYS use safe helpers
from cartrita.orchestrator.state import _safe_get_messages

messages = _safe_get_messages(state)  # Never access directly
# State must be immutable
new_state = {**state, "messages": updated_messages}
```

### Streaming SSE Responses
```python
# FastAPI SSE pattern
from sse_starlette.sse import EventSourceResponse

async def stream_response():
    async for chunk in agent.stream_process(message):
        yield {
            "event": "message",
            "data": json.dumps({"content": chunk})
        }

return EventSourceResponse(stream_response())
```

### Voice Integration (Deepgram)
```python
from deepgram import Deepgram

dg = Deepgram(api_key)
# WebRTC streaming
await dg.transcription.live({
    "punctuate": True,
    "interim_results": True,
    "vad_events": True
})
```

## 🚨 TROUBLESHOOTING

### Common Issues & Solutions

#### Docker Container Failures
```bash
docker-compose down -v          # Clean volumes
docker system prune -a          # Full cleanup
docker-compose up --build       # Rebuild
```

#### Database Connection Issues
```bash
# Check PostgreSQL with pgvector
psql -U postgres -h localhost -p 5433
\dx  # Check pgvector extension

# Redis connectivity
redis-cli -p 6380 ping
```

#### Agent Timeout Issues
```python
# Increase timeout in agent config
async with timeout(30):  # 30 second timeout
    response = await agent.process_request(message)
```

#### Frontend SSE Connection Drops
```typescript
// Implement reconnection logic
const eventSource = new EventSource(url);
eventSource.onerror = () => {
    setTimeout(() => reconnect(), 5000);
};
```

## 📝 COMMIT WORKFLOW

### Pre-Commit Checklist
```bash
# 1. Run tests
pytest -m "not slow" -q

# 2. Fix linting
ruff check . --fix
npm run lint:fix

# 3. Security scan
pre-commit run --all-files

# 4. Stage changes
git add -A

# 5. Commit with conventional format
git commit -m "feat(agents): add custom agent with full fallback chain"
```

### Conventional Commit Format
```
feat: New feature
fix: Bug fix
docs: Documentation
style: Formatting
refactor: Code restructuring
test: Test additions
chore: Maintenance
perf: Performance improvement
```

## 🎯 QUICK REFERENCE

### Most Used Commands
```bash
# Start development
docker-compose up -d

# Quick test after changes
pytest -m "not slow" -q && npm test -- --run

# Fix all linting
ruff check . --fix && npm run lint:fix

# Full health check
curl http://localhost:8000/health && curl http://localhost:3000/health

# View logs
docker-compose logs -f ai-orchestrator

# Database migration
alembic upgrade head

# Security scan
docker scout cve && npm audit
```

### Critical Files to Know
```
/services/ai-orchestrator/cartrita/orchestrator/main.py          # Entry point
/services/ai-orchestrator/cartrita/orchestrator/agents/base.py   # Base classes
/frontend/src/app/page.tsx                                       # Main UI
/docker-compose.yml                                              # Stack config
/.env.example                                                    # Env template
/docs/INDEX.md                                                  # Documentation hub
```

## ⚡ PERFORMANCE OPTIMIZATION

### Python 3.13 Optimizations
```python
# Use free-threaded mode for CPU-bound tasks
import sys
sys.flags.gil = 0  # Disable GIL where safe

# Leverage match statements (faster than if-elif)
match agent_type:
    case "research": return ResearchAgent()
    case "code": return CodeAgent()
```

### Database Query Optimization
```sql
-- Vector similarity search optimization
SET ivfflat.probes = 10;  -- Tune for speed/accuracy
SELECT * FROM embeddings
ORDER BY vector <-> query_vector
LIMIT 10;
```

### Frontend Performance
```typescript
// Use React.memo for expensive components
const ExpensiveComponent = React.memo(({ data }) => {
    // Component logic
});

// Implement virtual scrolling for lists
import { VirtualList } from '@tanstack/react-virtual';
```

## 🔄 CONTINUOUS INTEGRATION

### GitHub Actions Workflow
```yaml
# Runs on every push
- Security scanning (Codacy, Snyk)
- Unit tests (pytest, npm test)
- Integration tests (Docker Compose)
- Coverage reports (Codecov)
- Container scanning (Trivy)
```

### Local CI Simulation
```bash
# Run same checks as CI
act -j test  # Using GitHub Actions locally
```

---

**REMEMBER**: This is a production system. Always prioritize security, test thoroughly, and maintain the fallback chain integrity. When in doubt, run the quick test suite and security scans.
