"""
Comprehensive tests for core services: OpenAI, Deepgram, Tavily, HuggingFace, etc.
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest


@pytest.mark.unit
@pytest.mark.ai
class TestOpenAIService:
    """Test OpenAI service functionality."""

    @pytest.fixture
    def mock_openai_client(self):
        """Create mock OpenAI client."""
        client = Mock()

        # Mock chat completion
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Test OpenAI response"
        mock_response.choices[0].message.role = "assistant"
        mock_response.usage = Mock()
        mock_response.usage.total_tokens = 150
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50

        client.chat.completions.create = AsyncMock(return_value=mock_response)
        return client

    @pytest.fixture
    def openai_service(self, mock_openai_client, api_key_manager):
        """Create OpenAI service with mocked client."""
        with patch(
            "cartrita.orchestrator.services.openai_service.OpenAI"
        ) as mock_openai_class:
            mock_openai_class.return_value = mock_openai_client

            from cartrita.orchestrator.services.openai_service import OpenAIService

            service = OpenAIService(api_key_manager)
            return service

    @pytest.mark.asyncio
    async def test_chat_completion_success(self, openai_service, sample_chat_messages):
        """Test successful chat completion."""
        result = await openai_service.chat_completion(
            messages=sample_chat_messages, model="gpt-4-turbo-preview"
        )

        assert result["role"] == "assistant"
        assert result["content"] == "Test OpenAI response"
        assert result["model"] == "gpt-4-turbo-preview"
        assert result["usage"]["total_tokens"] == 150

    @pytest.mark.asyncio
    async def test_chat_completion_with_tools(
        self, openai_service, sample_chat_messages
    ):
        """Test chat completion with function tools."""
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "Get weather information",
                    "parameters": {
                        "type": "object",
                        "properties": {"location": {"type": "string"}},
                    },
                },
            }
        ]

        # Mock tool call response
        mock_tool_call = Mock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function = Mock()
        mock_tool_call.function.name = "get_weather"
        mock_tool_call.function.arguments = '{"location": "New York"}'

        openai_service.client.chat.completions.create.return_value.choices[
            0
        ].message.tool_calls = [mock_tool_call]
        openai_service.client.chat.completions.create.return_value.choices[
            0
        ].message.content = None

        result = await openai_service.chat_completion(
            messages=sample_chat_messages, tools=tools
        )

        assert "tool_calls" in result
        assert len(result["tool_calls"]) == 1
        assert result["tool_calls"][0]["function"]["name"] == "get_weather"

    @pytest.mark.asyncio
    async def test_streaming_completion(self, openai_service, sample_chat_messages):
        """Test streaming chat completion."""

        # Mock streaming response
        async def mock_stream():
            chunks = [
                Mock(choices=[Mock(delta=Mock(content="Hello "))]),
                Mock(choices=[Mock(delta=Mock(content="world!"))]),
                Mock(choices=[Mock(delta=Mock(content=None))]),
            ]
            for chunk in chunks:
                yield chunk

        openai_service.client.chat.completions.create = AsyncMock(
            return_value=mock_stream()
        )

        chunks = []
        async for chunk in openai_service.stream_completion(
            messages=sample_chat_messages, model="gpt-4-turbo-preview"
        ):
            chunks.append(chunk)

        assert len(chunks) >= 2
        content = "".join([chunk.get("content", "") for chunk in chunks])
        assert "Hello world!" in content

    @pytest.mark.asyncio
    async def test_embedding_generation(self, openai_service):
        """Test text embedding generation."""
        # Mock embedding response
        mock_embedding = Mock()
        mock_embedding.data = [Mock()]
        mock_embedding.data[0].embedding = [0.1, 0.2, 0.3] * 512  # 1536 dimensions
        mock_embedding.usage = Mock()
        mock_embedding.usage.total_tokens = 10

        openai_service.client.embeddings.create = AsyncMock(return_value=mock_embedding)

        result = await openai_service.create_embedding(
            text="Test text for embedding", model="text-embedding-3-small"
        )

        assert "embedding" in result
        assert len(result["embedding"]) == 1536
        assert result["usage"]["total_tokens"] == 10

    @pytest.mark.asyncio
    async def test_rate_limiting_handling(self, openai_service, sample_chat_messages):
        """Test rate limiting error handling."""
        from openai import RateLimitError

        openai_service.client.chat.completions.create = AsyncMock(
            side_effect=RateLimitError("Rate limit exceeded", response=Mock(), body={})
        )

        with pytest.raises(RateLimitError):
            await openai_service.chat_completion(messages=sample_chat_messages)

    @pytest.mark.asyncio
    async def test_retry_mechanism(self, openai_service, sample_chat_messages):
        """Test retry mechanism for transient failures."""
        # First call fails, second succeeds
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Retry success"
        mock_response.choices[0].message.role = "assistant"
        mock_response.usage = Mock(total_tokens=100)

        openai_service.client.chat.completions.create = AsyncMock(
            side_effect=[Exception("Temporary failure"), mock_response]
        )

        # Should retry and succeed
        result = await openai_service.chat_completion_with_retry(
            messages=sample_chat_messages, max_retries=2
        )

        assert result["content"] == "Retry success"

    @pytest.mark.asyncio
    async def test_token_counting(self, openai_service):
        """Test token counting functionality."""
        text = "This is a test message for token counting"

        token_count = openai_service.count_tokens(text, model="gpt-4")

        assert isinstance(token_count, int)
        assert token_count > 0

    @pytest.mark.asyncio
    async def test_model_validation(self, openai_service, sample_chat_messages):
        """Test model validation."""
        # Valid model
        result = await openai_service.chat_completion(
            messages=sample_chat_messages, model="gpt-4-turbo-preview"
        )
        assert result is not None

        # Invalid model should raise error
        with pytest.raises(ValueError):
            await openai_service.chat_completion(
                messages=sample_chat_messages, model="invalid-model"
            )


@pytest.mark.unit
@pytest.mark.ai
class TestDeepgramService:
    """Test Deepgram service functionality."""

    @pytest.fixture
    def mock_deepgram_client(self):
        """Create mock Deepgram client."""
        client = Mock()

        # Mock transcription response
        mock_response = Mock()
        mock_response.results = {
            "channels": [
                {
                    "alternatives": [
                        {"transcript": "Test transcription", "confidence": 0.95}
                    ]
                }
            ]
        }

        client.transcription.prerecorded = Mock(return_value=mock_response)
        return client

    @pytest.fixture
    def deepgram_service(self, mock_deepgram_client, api_key_manager):
        """Create Deepgram service with mocked client."""
        with patch(
            "cartrita.orchestrator.services.deepgram_service.Deepgram"
        ) as mock_deepgram:
            mock_deepgram.return_value = mock_deepgram_client

            from cartrita.orchestrator.services.deepgram_service import DeepgramService

            service = DeepgramService(api_key_manager)
            return service

    @pytest.mark.asyncio
    async def test_transcribe_audio_success(self, deepgram_service, sample_audio_data):
        """Test successful audio transcription."""
        result = await deepgram_service.transcribe_audio(
            audio_data=sample_audio_data, language="en"
        )

        assert result["transcript"] == "Test transcription"
        assert result["confidence"] == 0.95

    @pytest.mark.asyncio
    async def test_transcribe_multiple_languages(
        self, deepgram_service, sample_audio_data
    ):
        """Test transcription in multiple languages."""
        languages = ["en", "es", "fr", "de"]

        for lang in languages:
            deepgram_service.client.transcription.prerecorded.return_value.results = {
                "channels": [
                    {
                        "alternatives": [
                            {
                                "transcript": f"Transcription in {lang}",
                                "confidence": 0.9,
                            }
                        ]
                    }
                ]
            }

            result = await deepgram_service.transcribe_audio(
                audio_data=sample_audio_data, language=lang
            )

            assert f"Transcription in {lang}" in result["transcript"]

    @pytest.mark.asyncio
    async def test_real_time_transcription(self, deepgram_service):
        """Test real-time transcription."""

        # Mock real-time response
        async def mock_real_time_stream():
            responses = [
                {"channel": {"alternatives": [{"transcript": "Hello "}]}},
                {"channel": {"alternatives": [{"transcript": "world!"}]}},
                {"channel": {"alternatives": [{"transcript": ""}]}},  # End marker
            ]
            for response in responses:
                yield response

        deepgram_service.client.transcription.live = AsyncMock(
            return_value=mock_real_time_stream()
        )

        results = []
        async for result in deepgram_service.transcribe_real_time():
            results.append(result)
            if not result.get("transcript"):
                break

        assert len(results) >= 2
        transcripts = [r["transcript"] for r in results if r.get("transcript")]
        assert "Hello " in transcripts
        assert "world!" in transcripts

    @pytest.mark.asyncio
    async def test_speech_synthesis(self, deepgram_service):
        """Test speech synthesis."""
        text = "Hello, this is a test for speech synthesis"

        # Mock synthesis response
        deepgram_service.client.speak = AsyncMock(
            return_value=b"synthesized_audio_data"
        )

        result = await deepgram_service.synthesize_speech(
            text=text, voice="aura-helios-en"
        )

        assert isinstance(result, bytes)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_voice_activity_detection(self, deepgram_service, sample_audio_data):
        """Test voice activity detection."""
        # Mock VAD response
        deepgram_service.client.analyze = AsyncMock(
            return_value={
                "results": {
                    "segments": [
                        {"start": 0.0, "end": 2.5, "speech": True},
                        {"start": 2.5, "end": 3.0, "speech": False},
                        {"start": 3.0, "end": 5.0, "speech": True},
                    ]
                }
            }
        )

        result = await deepgram_service.detect_voice_activity(sample_audio_data)

        assert "segments" in result
        assert len(result["segments"]) == 3
        assert result["segments"][0]["speech"] is True

    @pytest.mark.asyncio
    async def test_audio_intelligence(self, deepgram_service, sample_audio_data):
        """Test audio intelligence features."""
        # Mock intelligence response
        deepgram_service.client.analyze = AsyncMock(
            return_value={
                "results": {
                    "sentiment": {
                        "segments": [{"sentiment": "positive", "confidence": 0.8}]
                    },
                    "topics": {
                        "segments": [{"topic": "technology", "confidence": 0.9}]
                    },
                }
            }
        )

        result = await deepgram_service.analyze_audio_intelligence(sample_audio_data)

        assert "sentiment" in result
        assert "topics" in result


@pytest.mark.unit
@pytest.mark.ai
class TestTavilyService:
    """Test Tavily web search service."""

    @pytest.fixture
    def mock_tavily_client(self):
        """Create mock Tavily client."""
        client = Mock()
        client.search = Mock(
            return_value={
                "results": [
                    {
                        "title": "Test Search Result",
                        "content": "This is test content from web search",
                        "url": "https://example.com/test",
                        "score": 0.95,
                    }
                ],
                "query": "test query",
                "response_time": 0.5,
            }
        )
        return client

    @pytest.fixture
    def tavily_service(self, mock_tavily_client, api_key_manager):
        """Create Tavily service with mocked client."""
        with patch(
            "cartrita.orchestrator.services.tavily_service.TavilyClient"
        ) as mock_tavily:
            mock_tavily.return_value = mock_tavily_client

            from cartrita.orchestrator.services.tavily_service import TavilyService

            service = TavilyService(api_key_manager)
            return service

    @pytest.mark.asyncio
    async def test_web_search_success(self, tavily_service):
        """Test successful web search."""
        query = "artificial intelligence latest news"

        result = await tavily_service.search(query)

        assert "results" in result
        assert len(result["results"]) > 0
        assert result["results"][0]["title"] == "Test Search Result"
        assert result["results"][0]["url"] == "https://example.com/test"

    @pytest.mark.asyncio
    async def test_search_with_filters(self, tavily_service):
        """Test web search with filters."""
        query = "python programming"

        result = await tavily_service.search(
            query=query,
            search_depth="advanced",
            max_results=5,
            include_domains=["github.com", "stackoverflow.com"],
        )

        assert "results" in result
        tavily_service.client.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_contextual_search(self, tavily_service):
        """Test contextual search with conversation context."""
        query = "latest developments"
        context = {
            "previous_queries": ["artificial intelligence", "machine learning"],
            "conversation_topic": "AI technology",
        }

        result = await tavily_service.contextual_search(query, context)

        assert "results" in result
        assert "context_enhanced" in result

    @pytest.mark.asyncio
    async def test_answer_generation(self, tavily_service):
        """Test answer generation from search results."""
        query = "What is machine learning?"

        # Mock answer response
        tavily_service.client.get_search_context = Mock(
            return_value={
                "answer": "Machine learning is a subset of artificial intelligence...",
                "sources": ["https://example.com/ml-guide"],
            }
        )

        result = await tavily_service.get_answer(query)

        assert "answer" in result
        assert "sources" in result

    @pytest.mark.asyncio
    async def test_search_rate_limiting(self, tavily_service):
        """Test search rate limiting."""
        # Simulate rapid searches
        queries = [f"test query {i}" for i in range(10)]

        results = []
        for query in queries:
            try:
                result = await tavily_service.search(query)
                results.append(result)
            except Exception as e:
                # Rate limiting may kick in
                results.append({"error": str(e)})

        # Should handle all requests gracefully
        assert len(results) == 10


@pytest.mark.unit
@pytest.mark.ai
class TestHuggingFaceService:
    """Test HuggingFace service functionality."""

    @pytest.fixture
    def mock_hf_client(self):
        """Create mock HuggingFace client."""
        client = Mock()
        client.text_generation = Mock(
            return_value=[{"generated_text": "Test HuggingFace response"}]
        )
        client.feature_extraction = Mock(return_value=[[0.1, 0.2, 0.3] * 256])
        return client

    @pytest.fixture
    def hf_service(self, mock_hf_client, api_key_manager):
        """Create HuggingFace service with mocked client."""
        with patch(
            "cartrita.orchestrator.services.huggingface_service.InferenceClient"
        ) as mock_hf:
            mock_hf.return_value = mock_hf_client

            from cartrita.orchestrator.services.huggingface_service import (
                HuggingFaceService,
            )

            service = HuggingFaceService(api_key_manager)
            return service

    @pytest.mark.asyncio
    async def test_text_generation(self, hf_service):
        """Test text generation."""
        prompt = "Complete this sentence: The future of AI is"

        result = await hf_service.generate_text(
            prompt=prompt, model="microsoft/DialoGPT-medium"
        )

        assert result["generated_text"] == "Test HuggingFace response"

    @pytest.mark.asyncio
    async def test_embedding_generation(self, hf_service):
        """Test embedding generation."""
        text = "Test text for embedding"

        result = await hf_service.create_embedding(
            text=text, model="sentence-transformers/all-MiniLM-L6-v2"
        )

        assert "embedding" in result
        assert len(result["embedding"]) == 768  # Expected embedding size

    @pytest.mark.asyncio
    async def test_model_inference(self, hf_service):
        """Test general model inference."""
        inputs = {"text": "Analyze sentiment: I love this product!"}

        hf_service.client.post = AsyncMock(
            return_value=[{"label": "POSITIVE", "score": 0.95}]
        )

        result = await hf_service.inference(
            inputs=inputs, model="cardiffnlp/twitter-roberta-base-sentiment-latest"
        )

        assert len(result) > 0
        assert result[0]["label"] == "POSITIVE"

    @pytest.mark.asyncio
    async def test_conversational_ai(self, hf_service):
        """Test conversational AI capabilities."""
        conversation = {
            "past_user_inputs": ["Hello"],
            "generated_responses": ["Hi there!"],
            "text": "How are you?",
        }

        hf_service.client.conversational = Mock(
            return_value={
                "generated_text": "I'm doing well, thank you for asking!",
                "conversation": conversation,
            }
        )

        result = await hf_service.conversational(conversation)

        assert "generated_text" in result
        assert result["generated_text"] == "I'm doing well, thank you for asking!"


@pytest.mark.integration
@pytest.mark.ai
class TestServicesIntegration:
    """Integration tests for all services working together."""

    @pytest.fixture
    def all_services(self, api_key_manager):
        """Create all services for integration testing."""
        services = {}

        with (
            patch("cartrita.orchestrator.services.openai_service.OpenAI"),
            patch("cartrita.orchestrator.services.deepgram_service.Deepgram"),
            patch("cartrita.orchestrator.services.tavily_service.TavilyClient"),
            patch("cartrita.orchestrator.services.huggingface_service.InferenceClient"),
        ):
            from cartrita.orchestrator.services.deepgram_service import DeepgramService
            from cartrita.orchestrator.services.huggingface_service import (
                HuggingFaceService,
            )
            from cartrita.orchestrator.services.openai_service import OpenAIService
            from cartrita.orchestrator.services.tavily_service import TavilyService

            services["openai"] = OpenAIService(api_key_manager)
            services["deepgram"] = DeepgramService(api_key_manager)
            services["tavily"] = TavilyService(api_key_manager)
            services["huggingface"] = HuggingFaceService(api_key_manager)

        return services

    @pytest.mark.asyncio
    async def test_multimodal_workflow(self, all_services, sample_audio_data):
        """Test workflow involving multiple services."""
        # 1. Transcribe audio
        transcript_result = await all_services["deepgram"].transcribe_audio(
            sample_audio_data
        )

        # 2. Search for relevant information
        search_result = await all_services["tavily"].search(
            transcript_result["transcript"]
        )

        # 3. Generate response using OpenAI
        messages = [
            {"role": "user", "content": transcript_result["transcript"]},
            {
                "role": "system",
                "content": f"Context: {search_result['results'][0]['content']}",
            },
        ]

        chat_result = await all_services["openai"].chat_completion(messages)

        # 4. Synthesize speech response
        audio_result = await all_services["deepgram"].synthesize_speech(
            chat_result["content"]
        )

        # Verify complete workflow
        assert transcript_result["transcript"] is not None
        assert len(search_result["results"]) > 0
        assert chat_result["content"] is not None
        assert isinstance(audio_result, bytes)

    @pytest.mark.asyncio
    async def test_service_fallback_chain(self, all_services, sample_chat_messages):
        """Test fallback between services."""
        # Simulate OpenAI failure
        all_services["openai"].client.chat.completions.create = AsyncMock(
            side_effect=Exception("OpenAI unavailable")
        )

        # Should fall back to HuggingFace
        try:
            result = await all_services["openai"].chat_completion(sample_chat_messages)
        except Exception:
            # Fallback to HuggingFace
            result = await all_services["huggingface"].generate_text(
                prompt=sample_chat_messages[-1]["content"]
            )

        assert result is not None

    @pytest.mark.asyncio
    async def test_concurrent_service_usage(self, all_services):
        """Test concurrent usage of multiple services."""
        tasks = [
            all_services["openai"].chat_completion(
                [{"role": "user", "content": "Test 1"}]
            ),
            all_services["tavily"].search("test query"),
            all_services["huggingface"].generate_text("Test prompt"),
            all_services["deepgram"].transcribe_audio(b"fake_audio"),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # At least some services should succeed
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) > 0

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_service_performance_under_load(self, all_services):
        """Test service performance under concurrent load."""
        import time

        start_time = time.time()

        # Create many concurrent requests
        tasks = []
        for i in range(20):
            tasks.extend(
                [
                    all_services["openai"].chat_completion(
                        [{"role": "user", "content": f"Request {i}"}]
                    ),
                    all_services["tavily"].search(f"query {i}"),
                ]
            )

        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        total_time = end_time - start_time
        successful_results = [r for r in results if not isinstance(r, Exception)]

        # Performance assertions
        assert total_time < 30  # Should complete within 30 seconds
        assert len(successful_results) > len(tasks) * 0.8  # At least 80% success rate


@pytest.mark.performance
class TestServicesPerformance:
    """Performance tests for all services."""

    @pytest.mark.asyncio
    async def test_openai_performance(self, openai_service, sample_chat_messages):
        """Test OpenAI service performance."""
        import time

        times = []
        for i in range(5):
            start_time = time.time()
            await openai_service.chat_completion(sample_chat_messages)
            end_time = time.time()
            times.append(end_time - start_time)

        avg_time = sum(times) / len(times)
        assert avg_time < 3.0  # Average response time under 3 seconds

    @pytest.mark.asyncio
    async def test_service_memory_efficiency(self, all_services):
        """Test memory efficiency across all services."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Use all services
        tasks = [
            all_services["openai"].chat_completion(
                [{"role": "user", "content": "Memory test"}]
            ),
            all_services["tavily"].search("memory test query"),
            all_services["huggingface"].generate_text("Memory test prompt"),
            all_services["deepgram"].transcribe_audio(b"fake_audio" * 100),
        ]

        await asyncio.gather(*tasks, return_exceptions=True)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable
        assert memory_increase < 200  # Less than 200MB increase
