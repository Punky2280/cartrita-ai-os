# Cartrita AI OS - Hierarchical Multi-Agent System

A production-ready hierarchical multi-agent AI operating system built with GPT-4.1 orchestration and GPT-5 specialized agents.

## 🚀 Features

- **Hierarchical Architecture**: GPT-4.1 supervisor orchestrator with specialized GPT-5 agents
- **Multi-Agent System**: Research, Code, Computer Use, Knowledge, and Task agents
- **Production Ready**: Docker orchestration, monitoring, and enterprise-grade architecture
- **Advanced Observability**: OpenTelemetry tracing, Prometheus metrics, Jaeger distributed tracing
- **Vector Database**: PostgreSQL with pgvector for semantic search and RAG
- **Real-time Communication**: WebSocket support with streaming responses
- **Comprehensive Testing**: Full test suite with integration and performance tests

## 🏗️ Architecture

```md
┌─────────────────┐    ┌─────────────────┐
│   GPT-4.1       │    │   GPT-5 Agents  │
│ Supervisor      │◄──►│                 │
│ Orchestrator    │    │ • Research      │
└─────────────────┘    │ • Code          │
                       │ • Computer Use  │
┌─────────────────┐    │ • Knowledge     │
│   Core Services │    │ • Task          │
│                 │    └─────────────────┘
│ • Database      │
│ • Cache         │    ┌─────────────────┐
│ • Metrics       │    │   MCP Protocol  │
└─────────────────┘    │                 │
                       │ • Dynamic Agent │
                       │ • Communication │
                       └─────────────────┘
```

## 🛠️ Technology Stack

### Backend

- **Python 3.13**: Core runtime with advanced async features
- **FastAPI**: High-performance API framework
- **LangChain/LangGraph**: Agent orchestration framework
- **PostgreSQL + pgvector**: Vector database for embeddings
- **Redis**: High-performance caching and session management
- **OpenAI GPT-4.1/GPT-5**: AI models for orchestration and specialized tasks

### Observability

- **OpenTelemetry**: Comprehensive tracing and metrics
- **Prometheus**: Metrics collection and alerting
- **Jaeger**: Distributed tracing visualization
- **Grafana**: Dashboard and visualization
- **Structured Logging**: JSON logging with context

### DevOps

- **Docker Compose**: Multi-service orchestration
- **Health Checks**: Comprehensive service health monitoring
- **Graceful Shutdown**: Proper resource cleanup
- **Configuration Management**: Environment-based configuration

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.13+
- OpenAI API keys for GPT-4.1 and GPT-5

### Environment Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd cartrita-ai-os
   ```

2. **Set environment variables**

   ```bash
   export OPENAI_API_KEY="your-gpt4.1-api-key"
   export GPT5_API_KEY="your-gpt5-api-key"
   export CARTRITA_API_KEY="dev-api-key-2025"
   ```

3. **Start the system**

   ```bash
   docker-compose up -d
   ```

4. **Check health**

   ```bash
   curl http://localhost:8000/health
   ```

### Manual Setup (Development)

1. **Install dependencies**

   ```bash
   cd services/ai-orchestrator
   pip install -r requirements.txt
   ```

2. **Run the application**

   ```bash
   python -m cartrita.orchestrator.main
   ```

## 📡 API Usage

### Chat Endpoint

```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-2025" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello, can you help me with a coding task?"}
    ],
    "user_id": "user123"
  }'
```

### Streaming Chat

```bash
curl -X POST "http://localhost:8000/api/chat/stream" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-2025" \
  -d '{
    "messages": [
      {"role": "user", "content": "Explain quantum computing"}
    ]
  }'
```

### WebSocket Connection

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat/conversation-123');

ws.onopen = () => {
  ws.send(JSON.stringify({
    api_key: 'dev-api-key-2025',
    messages: [{ role: 'user', content: 'Hello!' }]
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | GPT-4.1 API key | Required |
| `GPT5_API_KEY` | GPT-5 API key | Required |
| `CARTRITA_API_KEY` | API authentication key | `dev-api-key-2025` |
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql://user:pass@localhost:5432/cartrita` |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` |
| `AI_ORCHESTRATOR_PORT` | Service port | `8000` |

### Docker Services

- **ai-orchestrator**: Main FastAPI application (port 8000)
- **database**: PostgreSQL with pgvector (port 5432)
- **redis**: Redis cache (port 6379)
- **jaeger**: Distributed tracing (port 16686)
- **prometheus**: Metrics collection (port 9090)
- **grafana**: Dashboard (port 3000)

## 🧪 Testing

### Run Tests

```bash
# Unit tests
pytest tests/ -v

# Integration tests
pytest tests/test_integration.py -v

# With coverage (project-wide)
pytest --cov --cov-report=term-missing
```

### Coverage Policy (Ratchet)

We enforce an incremental coverage ratchet to improve quality safely:

| Phase | Minimum Coverage | Status |
|-------|------------------|--------|
| 1     | 25%              | Complete |
| 2     | 30%              | Pending (next after new service tests) |
| 3     | 35%              | Planned |

Legacy/backup agent modules are excluded via `.coveragerc` to avoid denominator distortion while they await archival or refactor. Exclusions are explicitly documented for transparency.

Raise sequence: add targeted tests → validate stable > threshold + buffer (≥ +4%) → bump `--cov-fail-under`.

### Runtime Policy

All services target Python `>=3.13,<3.14`. Local development should use the pinned patch in `.python-version`. CI and Docker images are aligned to `python:3.13-slim` for determinism. Earlier versions (3.11/3.12) are no longer tested.

### Test Categories

- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end functionality
- **Performance Tests**: Load and stress testing
- **Agent Tests**: Specialized agent functionality

## 📊 Monitoring

### Health Checks

- `/health`: Overall system health
- `/metrics`: Prometheus metrics
- `/api/agents/status`: Agent status overview

### Dashboards

- **Grafana**: <http://localhost:3000>
- **Jaeger**: <http://localhost:16686>
- **Prometheus**: <http://localhost:9090>

## 🔒 Security

- API key authentication
- Input validation and sanitization
- Rate limiting and abuse protection
- Secure configuration management
- Audit logging

## 📚 Documentation

### API Documentation

- **Swagger UI**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>

### Architecture Documentation

- See `docs/` directory for detailed architecture docs
- Agent specifications and communication protocols
- Deployment and scaling guides

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Development Guidelines

- Follow PEP 8 style guidelines
- Add comprehensive tests
- Update documentation
- Use type hints
- Follow the established architecture patterns

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for GPT-4.1 and GPT-5 models
- LangChain community for orchestration frameworks
- FastAPI community for the excellent web framework
- All contributors and the open-source community

---

**Cartrita AI OS** - Building the future of hierarchical multi-agent AI systems.

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/19effc69e3c54f548927869d28656546)](https://app.codacy.com?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)
