"""
Comprehensive tests for CartritaCoreAgent with full fallback chain coverage.
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from cartrita.orchestrator.agents.cartrita_core.api_key_manager import APIKeyManager
from cartrita.orchestrator.agents.cartrita_core.cartrita_agent import CartritaCoreAgent


@pytest.mark.unit
@pytest.mark.ai
class TestCartritaCoreAgent:
    """Test CartritaCoreAgent with mocked dependencies."""

    @pytest.fixture
    def mock_api_key_manager(self):
        """Create mock API key manager."""
        manager = Mock(spec=APIKeyManager)
        manager.request_key_access = AsyncMock(return_value="test-api-key")
        manager.return_key_access = AsyncMock()
        return manager

    @pytest.fixture
    def agent(self, mock_api_key_manager, mock_settings):
        """Create CartritaCoreAgent instance with mocked dependencies."""
        with (
            patch(
                "cartrita.orchestrator.agents.cartrita_core.cartrita_agent.ChatOpenAI"
            ) as mock_openai,
            patch(
                "cartrita.orchestrator.agents.cartrita_core.cartrita_agent.get_fallback_provider"
            ) as mock_fallback,
        ):
            mock_fallback.return_value = Mock()
            mock_fallback.return_value.get_response = Mock(
                return_value="Fallback response"
            )

            agent = CartritaCoreAgent(mock_api_key_manager)
            agent.openai_client = Mock()
            agent.langchain_openai = Mock()
            return agent

    @pytest.mark.asyncio
    async def test_initialization(self, agent, mock_api_key_manager):
        """Test proper agent initialization."""
        assert agent.api_key_manager == mock_api_key_manager
        assert agent.agent_id == "cartrita_core"
        assert not agent.mock_mode
        assert agent.fallback_provider is not None

    @pytest.mark.asyncio
    async def test_process_request_success_openai(self, agent):
        """Test successful request processing with OpenAI."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "OpenAI response"
        mock_response.choices[0].message.role = "assistant"
        mock_response.usage = Mock()
        mock_response.usage.total_tokens = 150

        agent.openai_client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        result = await agent.process_request("Test message", {})

        assert result["role"] == "assistant"
        assert "OpenAI response" in result["content"]
        assert result["model"] == "gpt-4-turbo-preview"
        assert "metadata" in result

    @pytest.mark.asyncio
    async def test_process_request_fallback_chain(self, agent):
        """Test complete fallback chain when OpenAI fails."""
        # Mock OpenAI failure
        agent.openai_client.chat.completions.create = AsyncMock(
            side_effect=Exception("OpenAI failed")
        )

        # Mock LangChain fallback
        mock_langchain_response = Mock()
        mock_langchain_response.content = "LangChain fallback response"
        agent.langchain_openai.ainvoke = AsyncMock(return_value=mock_langchain_response)

        result = await agent.process_request("Test message", {})

        assert result["role"] == "assistant"
        assert "LangChain fallback response" in result["content"]
        assert result["model"] == "langchain-openai"

    @pytest.mark.asyncio
    async def test_process_request_final_fallback(self, agent):
        """Test final fallback when all AI providers fail."""
        # Mock all AI failures
        agent.openai_client.chat.completions.create = AsyncMock(
            side_effect=Exception("OpenAI failed")
        )
        agent.langchain_openai.ainvoke = AsyncMock(
            side_effect=Exception("LangChain failed")
        )

        result = await agent.process_request("Test message", {})

        assert result["role"] == "assistant"
        assert "I'm experiencing technical difficulties" in result["content"]
        assert result["model"] == "fallback"

    @pytest.mark.asyncio
    async def test_stream_response_openai(self, agent):
        """Test streaming response from OpenAI."""

        async def mock_stream():
            chunks = [
                Mock(choices=[Mock(delta=Mock(content="Hello "))]),
                Mock(choices=[Mock(delta=Mock(content="world!"))]),
                Mock(choices=[Mock(delta=Mock(content=None))]),
            ]
            for chunk in chunks:
                yield chunk

        agent.openai_client.chat.completions.create = AsyncMock(
            return_value=mock_stream()
        )

        chunks = []
        async for chunk in agent.stream_response("Test message", {}):
            chunks.append(chunk)

        assert len(chunks) >= 2
        content = "".join([chunk.get("content", "") for chunk in chunks])
        assert "Hello world!" in content

    @pytest.mark.asyncio
    async def test_stream_response_fallback(self, agent):
        """Test streaming fallback when OpenAI streaming fails."""
        agent.openai_client.chat.completions.create = AsyncMock(
            side_effect=Exception("Stream failed")
        )

        # Mock LangChain streaming
        async def mock_langchain_stream():
            chunks = ["Stream ", "fallback ", "response"]
            for chunk in chunks:
                yield Mock(content=chunk)

        agent.langchain_openai.astream = AsyncMock(return_value=mock_langchain_stream())

        chunks = []
        async for chunk in agent.stream_response("Test message", {}):
            chunks.append(chunk)

        assert len(chunks) >= 3
        content = "".join([chunk.get("content", "") for chunk in chunks])
        assert "Stream fallback response" in content

    @pytest.mark.asyncio
    async def test_personality_integration(self, agent):
        """Test that personality traits are integrated into responses."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[
            0
        ].message.content = "¡Hola! I'm excited to help you today."
        mock_response.choices[0].message.role = "assistant"
        mock_response.usage = Mock(total_tokens=100)

        agent.openai_client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        result = await agent.process_request("Hello", {})

        # Check that the response includes personality elements
        assert "¡Hola!" in result["content"]
        assert result["metadata"]["personality_applied"] is True

    @pytest.mark.asyncio
    async def test_get_status(self, agent):
        """Test agent status reporting."""
        status = await agent.get_status()

        assert status["agent_id"] == "cartrita_core"
        assert status["status"] == "active"
        assert "capabilities" in status
        assert "health" in status

    @pytest.mark.asyncio
    async def test_health_check(self, agent):
        """Test agent health check."""
        health = await agent.health_check()

        assert health["status"] in ["healthy", "degraded", "unhealthy"]
        assert "openai_available" in health
        assert "langchain_available" in health
        assert "fallback_available" in health

    @pytest.mark.asyncio
    async def test_context_memory(self, agent):
        """Test context memory functionality."""
        context = {
            "conversation_id": "test-conv-123",
            "user_id": "test-user",
            "previous_messages": [
                {"role": "user", "content": "My name is Alice"},
                {"role": "assistant", "content": "Nice to meet you, Alice!"},
            ],
        }

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Hello again, Alice!"
        mock_response.choices[0].message.role = "assistant"
        mock_response.usage = Mock(total_tokens=100)

        agent.openai_client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        result = await agent.process_request("Hi again", context)

        # Verify that context was used
        call_args = agent.openai_client.chat.completions.create.call_args
        messages = call_args[1]["messages"]
        assert len(messages) >= 3  # System + previous + current

    @pytest.mark.asyncio
    async def test_error_handling(self, agent):
        """Test robust error handling."""
        # Test with malformed input
        result = await agent.process_request("", {})
        assert result["role"] == "assistant"
        assert "error" not in result["content"].lower()

        # Test with None input
        result = await agent.process_request(None, {})
        assert result["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_rate_limiting_compliance(self, agent):
        """Test that agent respects rate limiting."""
        agent.api_key_manager.request_key_access = AsyncMock(
            side_effect=Exception("Rate limited")
        )

        result = await agent.process_request("Test message", {})

        # Should fall back gracefully
        assert result["role"] == "assistant"
        assert result["model"] == "fallback"

    @pytest.mark.asyncio
    async def test_token_usage_tracking(self, agent):
        """Test token usage tracking."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Test response"
        mock_response.choices[0].message.role = "assistant"
        mock_response.usage = Mock()
        mock_response.usage.total_tokens = 250
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 150

        agent.openai_client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        result = await agent.process_request("Test message", {})

        assert result["metadata"]["tokens_used"] == 250
        assert result["metadata"]["prompt_tokens"] == 100
        assert result["metadata"]["completion_tokens"] == 150

    @pytest.mark.asyncio
    async def test_cultural_personality_traits(self, agent):
        """Test that cultural personality traits are preserved."""
        # Test Spanish phrases integration
        message = "How are you today?"

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[
            0
        ].message.content = "¡Muy bien, gracias! I'm doing great today."
        mock_response.choices[0].message.role = "assistant"
        mock_response.usage = Mock(total_tokens=100)

        agent.openai_client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        result = await agent.process_request(message, {})

        # Check for cultural elements
        assert any(phrase in result["content"] for phrase in ["¡", "gracias", "muy"])

    @pytest.mark.asyncio
    async def test_mock_mode(self, agent):
        """Test mock mode functionality."""
        agent.mock_mode = True

        result = await agent.process_request("Test message", {})

        assert result["role"] == "assistant"
        assert result["model"] == "mock"
        assert "mock response" in result["content"].lower()

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, agent):
        """Test handling of concurrent requests."""
        import asyncio

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Concurrent response"
        mock_response.choices[0].message.role = "assistant"
        mock_response.usage = Mock(total_tokens=100)

        agent.openai_client.chat.completions.create = AsyncMock(
            return_value=mock_response
        )

        # Send multiple concurrent requests
        tasks = [agent.process_request(f"Message {i}", {}) for i in range(5)]

        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        for result in results:
            assert result["role"] == "assistant"
            assert "Concurrent response" in result["content"]


@pytest.mark.integration
@pytest.mark.ai
class TestCartritaCoreAgentIntegration:
    """Integration tests for CartritaCoreAgent."""

    @pytest.fixture
    def agent(self, api_key_manager, mock_settings):
        """Create agent for integration testing."""
        with (
            patch(
                "cartrita.orchestrator.agents.cartrita_core.cartrita_agent.ChatOpenAI"
            ),
            patch(
                "cartrita.orchestrator.agents.cartrita_core.cartrita_agent.get_fallback_provider"
            ),
        ):
            return CartritaCoreAgent(api_key_manager)

    @pytest.mark.asyncio
    async def test_end_to_end_conversation(self, agent):
        """Test end-to-end conversation flow."""
        conversation_context = {
            "conversation_id": "integration-test-123",
            "user_id": "test-user",
            "session_data": {},
        }

        # First message
        result1 = await agent.process_request(
            "Hello, I'm new here", conversation_context
        )
        assert result1["role"] == "assistant"

        # Follow-up message with context
        conversation_context["previous_messages"] = [
            {"role": "user", "content": "Hello, I'm new here"},
            {"role": "assistant", "content": result1["content"]},
        ]

        result2 = await agent.process_request(
            "What can you help me with?", conversation_context
        )
        assert result2["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_performance_under_load(self, agent):
        """Test agent performance under load."""
        import asyncio
        import time

        start_time = time.time()

        # Send 10 concurrent requests
        tasks = [
            agent.process_request(f"Performance test message {i}", {})
            for i in range(10)
        ]

        results = await asyncio.gather(*tasks)
        end_time = time.time()

        # Check that all requests completed
        assert len(results) == 10
        for result in results:
            assert result["role"] == "assistant"

        # Check performance metrics
        total_time = end_time - start_time
        assert total_time < 30  # Should complete within 30 seconds

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_long_conversation_memory(self, agent):
        """Test memory retention in long conversations."""
        context = {
            "conversation_id": "long-conv-test",
            "user_id": "test-user",
            "previous_messages": [],
        }

        # Simulate a long conversation
        messages = [
            "My name is Alice and I work as a software engineer",
            "I'm working on a Python project about AI",
            "I need help with async programming",
            "Can you remember my name and profession?",
            "What project did I mention earlier?",
        ]

        for i, message in enumerate(messages):
            result = await agent.process_request(message, context)

            # Add to conversation history
            context["previous_messages"].extend(
                [
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": result["content"]},
                ]
            )

            # On the last two messages, check for memory retention
            if i >= 3:
                content_lower = result["content"].lower()
                if "alice" in message.lower():
                    assert "alice" in content_lower
                if "python" in message.lower() or "project" in message.lower():
                    assert any(
                        term in content_lower for term in ["python", "ai", "project"]
                    )


@pytest.mark.performance
class TestCartritaCoreAgentPerformance:
    """Performance tests for CartritaCoreAgent."""

    @pytest.fixture
    def agent(self, api_key_manager, mock_settings):
        """Create agent for performance testing."""
        with (
            patch(
                "cartrita.orchestrator.agents.cartrita_core.cartrita_agent.ChatOpenAI"
            ),
            patch(
                "cartrita.orchestrator.agents.cartrita_core.cartrita_agent.get_fallback_provider"
            ),
        ):
            return CartritaCoreAgent(api_key_manager)

    @pytest.mark.asyncio
    async def test_response_time_benchmark(self, agent):
        """Benchmark response times."""
        import time

        times = []
        for i in range(5):
            start_time = time.time()
            await agent.process_request(f"Benchmark message {i}", {})
            end_time = time.time()
            times.append(end_time - start_time)

        avg_time = sum(times) / len(times)
        assert avg_time < 2.0  # Average response time should be under 2 seconds

    @pytest.mark.asyncio
    async def test_memory_usage(self, agent):
        """Test memory usage remains reasonable."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Process multiple requests
        for i in range(10):
            await agent.process_request(f"Memory test {i}", {})

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 100MB for 10 requests)
        assert memory_increase < 100

    @pytest.mark.asyncio
    async def test_streaming_performance(self, agent):
        """Test streaming response performance."""
        import time

        start_time = time.time()
        chunks = []

        async for chunk in agent.stream_response("Test streaming performance", {}):
            chunks.append(chunk)

        end_time = time.time()

        assert len(chunks) > 0
        assert end_time - start_time < 5.0  # Should complete streaming within 5 seconds
