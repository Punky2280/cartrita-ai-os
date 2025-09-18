# AI Instructions: Testing Patterns

## Test Structure

**Location:** `services/ai-orchestrator/tests/`

**Test Organization:**
```
tests/
├── conftest.py                 # Test fixtures and configuration
├── agents/                     # Agent-specific tests
│   ├── test_research_agent.py
│   ├── test_code_agent.py
│   └── test_your_agent.py
├── core/                       # Core system tests
│   ├── test_database.py
│   └── test_state_management.py
├── providers/                  # Provider tests
│   ├── test_openai_provider.py
│   └── test_fallback_provider.py
└── integration/                # End-to-end tests
    ├── test_api_endpoints.py
    └── test_streaming.py
```

## Essential Test Fixtures

**Use fixtures from conftest.py - NEVER hardcode API keys:**

```python
# Available fixtures (from conftest.py)
def test_your_feature(
    mock_api_key_manager,      # Mocked API key manager
    sample_messages,           # Sample conversation messages
    test_conversation,         # Complete conversation object
    mock_openai_client,        # Mocked OpenAI client
    mock_database,             # Mocked database operations
    temp_upload_dir           # Temporary directory for uploads
):
    # Your test implementation
    pass
```

**Environment Setup:**
- Tests automatically run with `TESTING=true`
- All API keys are mocked/fake values
- Database uses SQLite in-memory for speed
- Redis uses test database (DB 15)

## Agent Testing Patterns

**Basic Agent Test Template:**
```python
import pytest
from cartrita.orchestrator.agents.your_domain.agent import YourDomainAgent

class TestYourDomainAgent:

    @pytest.fixture
    def agent(self, mock_api_key_manager):
        return YourDomainAgent(mock_api_key_manager)

    @pytest.mark.asyncio
    async def test_execute_success(self, agent, sample_messages):
        """Test successful agent execution"""
        result = await agent.execute(sample_messages, {}, {})

        # Standard assertions for all agents
        assert "response" in result
        assert "metadata" in result
        assert result["metadata"]["status"] == "success"
        assert result["metadata"]["agent"] == agent.name

        # Domain-specific assertions
        assert len(result["response"]) > 0

    @pytest.mark.asyncio
    async def test_execute_with_context(self, agent):
        """Test agent with specific context"""
        messages = [{"role": "user", "content": "specific request"}]
        context = {"setting": "value"}
        metadata = {"session_id": "test-123"}

        result = await agent.execute(messages, context, metadata)

        # Verify context was used
        assert result["metadata"]["session_id"] == "test-123"

    @pytest.mark.asyncio
    async def test_fallback_behavior(self, agent, mock_failed_openai):
        """Test agent fallback when OpenAI fails"""
        messages = [{"role": "user", "content": "test message"}]

        with mock_failed_openai:
            result = await agent.execute(messages, {}, {})

        # Should still return valid response
        assert "response" in result
        assert result["metadata"]["status"] == "fallback"
        assert "error" in result["metadata"]

    @pytest.mark.asyncio
    async def test_error_handling(self, agent):
        """Test agent error handling"""
        # Test with invalid input
        invalid_messages = None

        result = await agent.execute(invalid_messages, {}, {})

        assert result["metadata"]["status"] == "error"
        assert "error" in result["metadata"]
```

## Provider Testing

**Fallback Provider Tests:**
```python
import pytest
from cartrita.orchestrator.providers.fallback_provider import get_fallback_provider

class TestFallbackProvider:

    @pytest.mark.asyncio
    async def test_openai_success(self, mock_openai_client):
        """Test successful OpenAI call"""
        provider = get_fallback_provider()

        response = await provider.chat_completion(
            messages=[{"role": "user", "content": "test"}],
            max_completion_tokens=100
        )

        assert response
        assert isinstance(response, str)

    @pytest.mark.asyncio
    async def test_fallback_chain(self, mock_failed_openai, mock_huggingface):
        """Test complete fallback chain"""
        provider = get_fallback_provider()

        with mock_failed_openai:
            response = await provider.chat_completion(
                messages=[{"role": "user", "content": "test"}],
                max_completion_tokens=100
            )

        # Should get response from fallback
        assert response
        assert "fallback" in response.lower() or len(response) > 0
```

## API Endpoint Testing

**FastAPI Test Patterns:**
```python
import pytest
from fastapi.testclient import TestClient
from cartrita.orchestrator.main import app

client = TestClient(app)

class TestChatAPI:

    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_chat_endpoint(self, mock_api_key_manager):
        """Test chat endpoint"""
        payload = {
            "message": "Hello, world!",
            "conversation_id": "test-conv-123"
        }

        response = client.post("/chat/send", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "conversation_id" in data

    @pytest.mark.asyncio
    async def test_streaming_endpoint(self):
        """Test SSE streaming endpoint"""
        with client.stream("GET", "/chat/stream/test-conv") as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/plain; charset=utf-8"

            # Read stream chunks
            chunks = []
            for chunk in response.iter_lines():
                if chunk.startswith("data: "):
                    chunks.append(chunk[6:])  # Remove "data: " prefix

            # Should have at least one message and done event
            assert len(chunks) >= 2
            assert any("done" in chunk for chunk in chunks)
```

## Database Testing

**Database Test Patterns:**
```python
import pytest
from cartrita.orchestrator.core.database import DatabaseManager

class TestDatabase:

    @pytest.mark.asyncio
    async def test_conversation_storage(self, mock_database):
        """Test storing conversations"""
        conversation_data = {
            "id": "test-conv-123",
            "messages": [{"role": "user", "content": "test"}],
            "metadata": {}
        }

        async with DatabaseManager() as db:
            result = await db.store_conversation(conversation_data)

        assert result["id"] == "test-conv-123"

    @pytest.mark.asyncio
    async def test_conversation_retrieval(self, mock_database, test_conversation):
        """Test retrieving conversations"""
        async with DatabaseManager() as db:
            conversation = await db.get_conversation(test_conversation["id"])

        assert conversation["id"] == test_conversation["id"]
        assert len(conversation["messages"]) > 0
```

## Integration Testing

**End-to-End Test Example:**
```python
import pytest
from fastapi.testclient import TestClient
from cartrita.orchestrator.main import app

client = TestClient(app)

class TestIntegration:

    @pytest.mark.integration
    def test_complete_chat_flow(self, mock_api_key_manager):
        """Test complete chat flow from request to response"""
        # 1. Send initial message
        response = client.post("/chat/send", json={
            "message": "Create a Python function to calculate fibonacci",
            "agent": "code"
        })

        assert response.status_code == 200
        data = response.json()
        conversation_id = data["conversation_id"]

        # 2. Verify response contains code
        assert "def" in data["response"]
        assert "fibonacci" in data["response"].lower()

        # 3. Send follow-up message
        response = client.post("/chat/send", json={
            "message": "Add error handling to that function",
            "conversation_id": conversation_id
        })

        assert response.status_code == 200
        follow_up = response.json()

        # 4. Verify context was maintained
        assert follow_up["conversation_id"] == conversation_id
        assert "error" in follow_up["response"].lower()
```

## Performance Testing

**Load Testing Pattern:**
```python
import pytest
import asyncio
from concurrent.futures import ThreadPoolExecutor

class TestPerformance:

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, mock_api_key_manager):
        """Test handling multiple concurrent requests"""
        from cartrita.orchestrator.agents.research.agent import ResearchAgent

        agent = ResearchAgent(mock_api_key_manager)

        async def send_request(i):
            messages = [{"role": "user", "content": f"Request {i}"}]
            return await agent.execute(messages, {}, {})

        # Send 10 concurrent requests
        tasks = [send_request(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        # All should succeed
        assert len(results) == 10
        for result in results:
            assert "response" in result
            assert result["metadata"]["status"] in ["success", "fallback"]
```

## Test Commands

**Quick Tests (after code changes):**
```bash
# Run fast tests only
pytest -m "not slow" -q

# Run specific test file
pytest tests/agents/test_your_agent.py -v

# Run tests with coverage
pytest --cov=cartrita --cov-report=html
```

**Full Test Suite:**
```bash
# Run all tests
pytest

# Include slow/integration tests
pytest -m "slow or integration"

# Parallel execution for speed
pytest -n auto
```

**Test Categories:**
- Default: Fast unit tests
- `@pytest.mark.slow`: Performance/load tests
- `@pytest.mark.integration`: End-to-end tests
- `@pytest.mark.asyncio`: Async test functions

## Mocking Best Practices

**Mock External APIs:**
```python
@pytest.fixture
def mock_external_api():
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = {"data": "mocked"}
        mock_get.return_value.status_code = 200
        yield mock_get

def test_with_external_api(mock_external_api):
    # Test code that calls external API
    result = your_function_that_calls_api()

    # Verify API was called
    mock_external_api.assert_called_once()
    assert result["data"] == "mocked"
```

**Mock Database Operations:**
```python
@pytest.fixture
def mock_db_operations():
    with patch("cartrita.orchestrator.core.database.DatabaseManager") as mock_db:
        # Configure mock responses
        mock_db.return_value.__center__.return_value.store_conversation.return_value = {
            "id": "test-id"
        }
        yield mock_db
```

## Quality Thresholds

**Minimum Coverage Requirements:**
- Agent classes: 90% coverage
- Core system: 95% coverage
- API endpoints: 85% coverage
- Providers: 90% coverage

**Performance Benchmarks:**
- Agent execution: < 5 seconds
- API response: < 2 seconds
- Database operations: < 500ms
- Memory usage: < 2GB per worker
