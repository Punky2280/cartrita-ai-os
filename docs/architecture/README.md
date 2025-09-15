# Cartrita AI OS Architecture Documentation

## Overview

This directory contains comprehensive architectural documentation for the Cartrita AI OS project, a hierarchical multi-agent AI operating system built with modern 2025 technologies.

## Documentation Structure

### Core Technology Research

- **[2025-technology-research.md](../2025-technology-research.md)** - Comprehensive research on all technologies used in the project
- **[openai-streaming-analysis.md](../openai-streaming-analysis.md)** - Detailed analysis of OpenAI streaming capabilities (SSE vs WebSocket)

### Architecture Components

#### Multi-Agent System

The Cartrita AI OS implements a hierarchical multi-agent architecture with:

- **GPT-4.1 Supervisor Orchestrator**: Main coordination layer
- **Specialized GPT-5 Agents**: Research, Code, Computer Use, Knowledge, Task agents
- **LangGraph Orchestration**: State management and workflow control
- **MCP Protocol Integration**: Standardized tool and context integration

#### Technology Stack (2025)

- **Backend**: Python 3.13, FastAPI, LangChain/LangGraph
- **Database**: PostgreSQL 17 + pgvector 0.8.0
- **Cache**: Redis 7.4/8.0
- **Containers**: Docker with modern security practices
- **Monitoring**: OpenTelemetry, Prometheus, Jaeger, Grafana

#### Communication Patterns

- **SSE Streaming**: For AI response streaming and status updates
- **WebSocket**: For real-time collaboration and interactive features
- **MCP Protocol**: For standardized AI tool integration
- **REST API**: For standard CRUD operations

## Key Architectural Decisions

### Real-Time Communication Strategy

1. **Server-Sent Events (SSE)** for unidirectional AI streaming
2. **WebSocket.io** for bidirectional interactive features
3. **Hybrid approach** based on use case requirements

### Security Framework

1. **Container Security**: Non-root users, read-only filesystems
2. **API Security**: Token-based auth, rate limiting, input validation
3. **Network Security**: TLS everywhere, network segmentation
4. **Data Protection**: Vector database encryption, audit logging

### Performance Optimization

1. **Python 3.13**: 11% performance improvement over 3.11
2. **pgvector 0.8.0**: 3-5× query throughput improvement
3. **Redis 8.0**: 30+ performance optimizations
4. **Binary Quantization**: 32× memory reduction with 95% accuracy

## Implementation Guidelines

### Development Workflow

1. Follow modern Docker best practices (2025)
2. Implement comprehensive testing (unit, integration, e2e)
3. Use structured logging with OpenTelemetry
4. Maintain type safety with Python 3.13 type hints

### Deployment Strategy

1. Container-first architecture with health checks
2. Zero-downtime deployments with rolling updates
3. Multi-environment support (dev, staging, production)
4. Monitoring and alerting integration

### Code Quality Standards

1. **Linting**: pylint with 10/10 target score
2. **Type Checking**: mypy (planned strict adoption) using Python 3.13 typing features
3. **Testing**: pytest with incremental coverage ratchet (25% → 30% → 35% → higher) toward long-term >90%
4. **Documentation**: Comprehensive docstrings and README files kept in sync with architectural changes

### Runtime & Coverage Enforcement

| Aspect | Policy |
|--------|--------|
| Python Runtime | `>=3.13,<3.14` pinned across Docker, CI, local `.python-version` |
| Determinism | Single-version CI to eliminate cross-version drift |
| Coverage Exclusions | Legacy / backup agent modules (marked for deprecation) via `.coveragerc` |
| Ratchet Strategy | Raise threshold only after focused tests + ≥4% safety buffer |
| Transparency | All exclusions documented here + root README |

Rationale: enforcing a single modern runtime reduces matrix flakiness, ensures consistent async/typing behavior, and accelerates adoption of Python 3.13 performance and language improvements.

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.13+
- OpenAI API keys (GPT-4.1, GPT-5)
- PostgreSQL 17 with pgvector
- Redis 7.4/8.0

### Quick Start

```bash
# Clone and setup
git clone <repository-url>
cd cartrita-ai-os

# Install dependencies
pip install -e .

# Start services
docker-compose up -d

# Verify health
curl http://localhost:8000/health
```

### Configuration

See `.env` files for environment-specific configuration:

- **Development**: `.env`
- **Production**: `.env.production`
- **Testing**: `.env.test`

## Contributing

### Code Standards

1. Follow PEP 8 style guidelines
2. Add comprehensive tests for new features
3. Update documentation for architectural changes
4. Use structured commit messages
5. Implement proper error handling and logging

### Pull Request Process

1. Create feature branch from main
2. Implement changes with tests
3. Update documentation
4. Ensure all checks pass
5. Submit PR with detailed description

## Support and Resources

### Documentation Links

 **OpenAI Platform**: https://platform.openai.com/docs/
 **LangChain Docs**: https://docs.langchain.com/
 **FastAPI Docs**: https://fastapi.tiangolo.com/
 **Docker Best Practices**: https://docs.docker.com/develop/dev-best-practices/

### Community Resources

- **Issues**: GitHub Issues for bug reports and feature requests
- **Discussions**: GitHub Discussions for community questions
- **Discord**: Community Discord server for real-time chat

---
*Cartrita AI OS - Building the future of hierarchical multi-agent AI systems*
*Last Updated: September 2025*
