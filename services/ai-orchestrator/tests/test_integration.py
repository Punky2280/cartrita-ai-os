"""
Basic integration test for Cartrita AI OS.
Tests the core functionality without external dependencies.
"""

import sys
from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest


# Mock external dependencies for testing
@pytest.fixture
def mock_dependencies() -> Generator[dict[str, Any]]:
    """Mock all external dependencies."""
    with (
        patch("cartrita.orchestrator.main.DatabaseManager") as mock_db,
        patch("cartrita.orchestrator.main.CacheManager") as mock_cache,
        patch("cartrita.orchestrator.main.MetricsCollector") as mock_metrics,
        patch("cartrita.orchestrator.main.SupervisorOrchestrator") as mock_supervisor,
        patch("cartrita.orchestrator.main.ResearchAgent") as mock_research,
        patch("cartrita.orchestrator.main.CodeAgent") as mock_code,
        patch("cartrita.orchestrator.main.ComputerUseAgent") as mock_computer,
        patch("cartrita.orchestrator.main.KnowledgeAgent") as mock_knowledge,
        patch("cartrita.orchestrator.main.TaskAgent") as mock_task,
    ):

        # Configure mocks
        mock_db_instance = AsyncMock()
        mock_db.return_value = mock_db_instance
        mock_db_instance.connect = AsyncMock()
        mock_db_instance.disconnect = AsyncMock()
        mock_db_instance.health_check = AsyncMock(return_value=True)

        mock_cache_instance = AsyncMock()
        mock_cache.return_value = mock_cache_instance
        mock_cache_instance.connect = AsyncMock()
        mock_cache_instance.disconnect = AsyncMock()
        mock_cache_instance.health_check = AsyncMock(return_value=True)

        mock_metrics_instance = AsyncMock()
        mock_metrics.return_value = mock_metrics_instance
        mock_metrics_instance.start = AsyncMock()
        mock_metrics_instance.stop = AsyncMock()

        mock_supervisor_instance = AsyncMock()
        mock_supervisor.return_value = mock_supervisor_instance
        mock_supervisor_instance.start = AsyncMock()
        mock_supervisor_instance.stop = AsyncMock()
        mock_supervisor_instance.health_check = AsyncMock(return_value=True)

        # Mock agents
        for mock_agent in (
            mock_research,
            mock_code,
            mock_computer,
            mock_knowledge,
            mock_task,
        ):
            mock_agent_instance = AsyncMock()
            mock_agent.return_value = mock_agent_instance
            mock_agent_instance.start = AsyncMock()
            mock_agent_instance.stop = AsyncMock()
            mock_agent_instance.health_check = AsyncMock(return_value=True)

        yield {
            "db": mock_db_instance,
            "cache": mock_cache_instance,
            "metrics": mock_metrics_instance,
            "supervisor": mock_supervisor_instance,
        }


@pytest.mark.asyncio
async def test_application_startup(mock_deps) -> None:
    """Test that the application can start up successfully."""
    from fastapi import FastAPI

    from cartrita.orchestrator.main import lifespan

    app = FastAPI()

    # Test startup
    async with lifespan(app):
        # Application should start without errors
        assert True

    # Verify all components were initialized and started
    mock_deps["db"].connect.assert_called_once()
    mock_deps["cache"].connect.assert_called_once()
    mock_deps["metrics"].start.assert_called_once()
    mock_deps["supervisor"].start.assert_called_once()


@pytest.mark.asyncio
async def test_application_shutdown(mock_deps) -> None:
    """Test that the application shuts down gracefully."""
    from fastapi import FastAPI

    from cartrita.orchestrator.main import lifespan

    app = FastAPI()

    # Test startup and shutdown
    async with lifespan(app):
        pass  # Just test that shutdown happens

    # Verify all components were stopped
    mock_deps["supervisor"].stop.assert_called_once()
    mock_deps["db"].disconnect.assert_called_once()
    mock_deps["cache"].disconnect.assert_called_once()
    mock_deps["metrics"].stop.assert_called_once()


def test_imports() -> None:  # pylint: disable=W0611
    """Test that all modules can be imported."""
    # pylint: disable=C0413,W0611
    try:
        # Test core imports (using _ prefix for intentionally unused imports)
        # Test agent imports
        from cartrita.orchestrator.agents import CodeAgent as _code_agent
        from cartrita.orchestrator.agents import ComputerUseAgent as _computer_use_agent
        from cartrita.orchestrator.agents import KnowledgeAgent as _knowledge_agent
        from cartrita.orchestrator.agents import ResearchAgent as _research_agent
        from cartrita.orchestrator.agents import TaskAgent as _task_agent
        from cartrita.orchestrator.core.cache import CacheManager as _cache_manager
        from cartrita.orchestrator.core.database import DatabaseManager as _db_manager
        from cartrita.orchestrator.core.metrics import (
            MetricsCollector as _metrics_collector,
        )
        from cartrita.orchestrator.core.supervisor import (
            SupervisorOrchestrator as _supervisor,
        )
        from cartrita.orchestrator.main import app as _app

        # Test model imports
        from cartrita.orchestrator.models.schemas import ChatRequest as _chat_request
        from cartrita.orchestrator.models.schemas import ChatResponse as _chat_response

        # Test utility imports
        from cartrita.orchestrator.utils.config import Settings as _settings
        from cartrita.orchestrator.utils.logger import setup_logging as _setup_logging

        # All imports successful
        assert True

    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


@pytest.mark.asyncio
async def test_voice_conversation_flow():
    """Test the voice conversation flow with OpenAI service."""
    try:
        from cartrita.orchestrator.services.openai_service import OpenAIService

        # Mock OpenAI client
        with patch("cartrita.orchestrator.services.openai_service.AsyncOpenAI") as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client

            # Mock streaming response
            mock_response = AsyncMock()
            mock_response.choices = [AsyncMock()]
            mock_response.choices[0].delta = AsyncMock()
            mock_response.choices[0].delta.content = "Hello! How can I help you?"
            mock_response.choices[0].finish_reason = "stop"

            mock_client.chat.completions.create = mock_response

            # Create service instance
            service = OpenAIService()

            # Test voice conversation
            conversation_id = "test-voice-conversation"
            transcribed_text = "Hello, can you help me?"

            chunks = []
            async for chunk in service.process_voice_conversation(
                conversation_id=conversation_id,
                transcribed_text=transcribed_text,
                conversation_history=None
            ):
                chunks.append(chunk)

            # Verify response
            assert len(chunks) > 0
            assert any(chunk["type"] == "content" for chunk in chunks)
            print("✅ Voice conversation test passed")

    except Exception as e:
        pytest.fail(f"Voice conversation test failed: {e}")


if __name__ == "__main__":
    # Run basic smoke test
    print("Running Cartrita AI OS integration tests...")

    try:
        test_imports()
        print("✅ All imports successful")

        # Note: Async tests require pytest-asyncio
        print("ℹ️  Async tests require pytest-asyncio to run")
        print("   Run with: pytest test_integration.py -v")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
