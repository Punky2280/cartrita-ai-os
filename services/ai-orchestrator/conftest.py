"""
Test configuration and fixtures for Cartrita AI OS.
"""

import asyncio
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Set test environment variables
os.environ["TESTING"] = "true"
os.environ["CARTRITA_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite:///test_cartrita.db"
os.environ["REDIS_URL"] = "redis://localhost:6380/15"  # Test database
os.environ["OPENAI_API_KEY"] = "sk-test-key"
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-test-key"
os.environ["DEEPGRAM_API_KEY"] = "test-deepgram-key"
os.environ["TAVILY_API_KEY"] = "tvly-test-key"
os.environ["LANGCHAIN_API_KEY"] = "lsv2_pt_test-key"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-32-chars-min"
os.environ["CARTRITA_API_KEY"] = "test-api-key-2025"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    from unittest.mock import MagicMock

    mock_ai = MagicMock()
    mock_ai.openai_api_key = MagicMock()
    mock_ai.openai_api_key.get_secret_value.return_value = "sk-test-key"
    mock_ai.anthropic_api_key = MagicMock()
    mock_ai.anthropic_api_key.get_secret_value.return_value = "sk-ant-test-key"
    mock_ai.deepgram_api_key = MagicMock()
    mock_ai.deepgram_api_key.get_secret_value.return_value = "test-deepgram-key"
    mock_ai.tavily_api_key = MagicMock()
    mock_ai.tavily_api_key.get_secret_value.return_value = "tvly-test-key"
    mock_ai.langchain_api_key = MagicMock()
    mock_ai.langchain_api_key.get_secret_value.return_value = "lsv2_pt_test-key"

    mock_settings = MagicMock()
    mock_settings.ai = mock_ai
    mock_settings.database = MagicMock()
    mock_settings.database.url = "sqlite:///test_cartrita.db"
    mock_settings.redis = MagicMock()
    mock_settings.redis.url = "redis://localhost:6380/15"
    mock_settings.security = MagicMock()
    mock_settings.security.jwt_secret_key = "test-jwt-secret-key-32-chars-min"
    mock_settings.security.cartrita_api_key = "test-api-key-2025"

    return mock_settings


@pytest.fixture(autouse=True)
def patch_settings(mock_settings):
    """Auto-patch settings for all tests."""
    with patch(
        "cartrita.orchestrator.utils.config.get_settings", return_value=mock_settings
    ):
        yield mock_settings


@pytest.fixture
def api_key_manager():
    """Create a mock API key manager."""
    from cartrita.orchestrator.agents.cartrita_core.api_key_manager import APIKeyManager

    manager = APIKeyManager()
    # Mock the secure vault to avoid encryption in tests
    manager.vault.store_key = Mock(return_value="test-key-id")
    manager.vault.retrieve_key = Mock(return_value="test-api-key")
    manager.vault.list_keys = Mock(return_value=["test-key-id"])
    return manager


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message = Mock()
    mock_response.choices[0].message.content = "Test response"
    mock_response.choices[0].message.role = "assistant"
    mock_response.usage = Mock()
    mock_response.usage.total_tokens = 100

    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    return mock_client


@pytest.fixture
def mock_langchain_openai():
    """Mock LangChain OpenAI for testing."""
    mock_llm = Mock()
    mock_llm.ainvoke = AsyncMock(return_value=Mock(content="Test LangChain response"))
    mock_llm.astream = AsyncMock()

    # Mock streaming response
    async def mock_stream():
        chunks = ["Test ", "streaming ", "response"]
        for chunk in chunks:
            yield Mock(content=chunk)

    mock_llm.astream.return_value = mock_stream()
    return mock_llm


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_chat_messages():
    """Sample chat messages for testing."""
    return [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there! How can I help you?"},
        {"role": "user", "content": "What's the weather like?"},
    ]


@pytest.fixture
def sample_audio_data():
    """Sample audio data for testing."""
    return b"fake_audio_data_for_testing" * 100  # Simulate audio bytes


@pytest.fixture
def mock_database():
    """Mock database for testing."""
    mock_db = Mock()
    mock_db.execute = AsyncMock(return_value=Mock(fetchall=Mock(return_value=[])))
    mock_db.commit = AsyncMock()
    mock_db.rollback = AsyncMock()
    mock_db.close = AsyncMock()
    return mock_db


@pytest.fixture
def mock_redis():
    """Mock Redis client for testing."""
    mock_redis = Mock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock(return_value=True)
    mock_redis.delete = AsyncMock(return_value=1)
    mock_redis.exists = AsyncMock(return_value=False)
    mock_redis.expire = AsyncMock(return_value=True)
    mock_redis.ping = AsyncMock(return_value=True)
    return mock_redis


@pytest.fixture
def mock_fallback_provider():
    """Mock fallback provider for testing."""
    mock_provider = Mock()
    mock_provider.get_response = Mock(return_value="Fallback response")
    mock_provider.is_available = Mock(return_value=True)
    mock_provider.process_request = AsyncMock(
        return_value={
            "role": "assistant",
            "content": "Fallback response",
            "model": "fallback",
        }
    )
    return mock_provider


@pytest.fixture
def mock_deepgram_client():
    """Mock Deepgram client for testing."""
    mock_client = Mock()
    mock_transcription = Mock()
    mock_transcription.get = Mock(
        return_value={
            "results": {
                "channels": [{"alternatives": [{"transcript": "Test transcription"}]}]
            }
        }
    )
    mock_client.transcription.prerecorded = mock_transcription
    return mock_client


@pytest.fixture
def mock_huggingface_client():
    """Mock HuggingFace client for testing."""
    mock_client = Mock()
    mock_client.text_generation = Mock(
        return_value=[{"generated_text": "Test HuggingFace response"}]
    )
    return mock_client


@pytest.fixture
def mock_tavily_client():
    """Mock Tavily client for testing."""
    mock_client = Mock()
    mock_client.search = Mock(
        return_value={
            "results": [
                {
                    "title": "Test Result",
                    "content": "Test content",
                    "url": "https://example.com",
                }
            ]
        }
    )
    return mock_client


@pytest.fixture
def test_file_content():
    """Sample file content for testing."""
    return {
        "text": "This is a test document with sample content.",
        "pdf": b"%PDF-1.4 fake pdf content for testing",
        "image": b"\x89PNG fake image data for testing",
        "json": '{"test": "data", "value": 123}',
    }


@pytest.fixture
def mock_session():
    """Mock HTTP session for testing."""
    mock_session = Mock()
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json = Mock(return_value={"test": "response"})
    mock_response.text = "Test response text"
    mock_response.content = b"Test response content"
    mock_session.get = AsyncMock(return_value=mock_response)
    mock_session.post = AsyncMock(return_value=mock_response)
    mock_session.put = AsyncMock(return_value=mock_response)
    mock_session.delete = AsyncMock(return_value=mock_response)
    return mock_session


@pytest.fixture
def performance_metrics():
    """Sample performance metrics for testing."""
    return {
        "response_time": 0.5,
        "tokens_per_second": 50,
        "memory_usage": 100.0,
        "cpu_usage": 25.0,
        "error_rate": 0.01,
    }


# Test markers for organization
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.e2e = pytest.mark.e2e
pytest.mark.slow = pytest.mark.slow
pytest.mark.ai = pytest.mark.ai
pytest.mark.gpu = pytest.mark.gpu
pytest.mark.security = pytest.mark.security
pytest.mark.performance = pytest.mark.performance


@pytest.fixture
def chat_response_schema():
    """Expected chat response schema for validation."""
    return {
        "role": str,
        "content": str,
        "model": str,
        "timestamp": str,
        "metadata": dict,
    }


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances between tests."""
    # Clear any cached instances that might interfere with tests
    yield
    # Reset any global state here if needed


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "e2e: mark test as an end-to-end test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "ai: mark test as requiring AI services")
    config.addinivalue_line("markers", "gpu: mark test as requiring GPU")
    config.addinivalue_line("markers", "security: mark test as security-related")
    config.addinivalue_line("markers", "performance: mark test as performance-related")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add markers based on test file paths
        if "test_integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "test_performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        elif "test_security" in str(item.fspath):
            item.add_marker(pytest.mark.security)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        else:
            item.add_marker(pytest.mark.unit)


@pytest.fixture
def mock_agent_response():
    """Mock agent response for testing."""
    return {
        "role": "assistant",
        "content": "Test agent response",
        "model": "test-model",
        "timestamp": "2025-09-17T04:00:00Z",
        "metadata": {"agent_type": "test", "processing_time": 0.5, "tokens_used": 100},
    }
