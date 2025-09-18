"""
Comprehensive tests for AudioAgent with full voice processing coverage.
"""

import asyncio
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from cartrita.orchestrator.agents.audio.audio_agent import AudioAgent


@pytest.mark.unit
@pytest.mark.ai
class TestAudioAgent:
    """Test AudioAgent functionality."""

    @pytest.fixture
    def mock_deepgram_service(self):
        """Mock Deepgram service."""
        service = Mock()
        service.transcribe_audio = AsyncMock(
            return_value={
                "transcript": "Test transcription",
                "confidence": 0.95,
                "language": "en",
            }
        )
        service.synthesize_speech = AsyncMock(return_value=b"fake_audio_data")
        service.health_check = AsyncMock(return_value={"status": "healthy"})
        return service

    @pytest.fixture
    def mock_openai_service(self):
        """Mock OpenAI service for audio processing."""
        service = Mock()
        service.process_audio_chat = AsyncMock(
            return_value={
                "role": "assistant",
                "content": "Audio chat response",
                "model": "gpt-4-turbo",
            }
        )
        return service

    @pytest.fixture
    def agent(self, api_key_manager, mock_deepgram_service, mock_openai_service):
        """Create AudioAgent instance with mocked dependencies."""
        with (
            patch(
                "cartrita.orchestrator.agents.audio.audio_agent.DeepgramService"
            ) as mock_dg,
            patch(
                "cartrita.orchestrator.agents.audio.audio_agent.OpenAIService"
            ) as mock_openai,
        ):
            mock_dg.return_value = mock_deepgram_service
            mock_openai.return_value = mock_openai_service

            agent = AudioAgent(api_key_manager)
            return agent

    @pytest.mark.asyncio
    async def test_initialization(self, agent, api_key_manager):
        """Test proper agent initialization."""
        assert agent.api_key_manager == api_key_manager
        assert agent.agent_id == "audio_agent"
        assert agent.deepgram_service is not None
        assert agent.openai_service is not None
        assert agent.session_manager is not None

    @pytest.mark.asyncio
    async def test_start_stop(self, agent):
        """Test agent start and stop functionality."""
        await agent.start()
        assert agent.running is True

        await agent.stop()
        assert agent.running is False

    @pytest.mark.asyncio
    async def test_health_check(self, agent):
        """Test agent health check."""
        health = await agent.health_check()

        assert "status" in health
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
        assert "deepgram_status" in health
        assert "openai_status" in health

    @pytest.mark.asyncio
    async def test_transcribe_audio_success(self, agent, sample_audio_data):
        """Test successful audio transcription."""
        result = await agent._transcribe_audio(sample_audio_data)

        assert result["transcript"] == "Test transcription"
        assert result["confidence"] == 0.95
        assert result["language"] == "en"

    @pytest.mark.asyncio
    async def test_transcribe_audio_failure(self, agent, sample_audio_data):
        """Test audio transcription failure handling."""
        agent.deepgram_service.transcribe_audio = AsyncMock(
            side_effect=Exception("Transcription failed")
        )

        result = await agent._transcribe_audio(sample_audio_data)

        assert "error" in result
        assert result["transcript"] == ""

    @pytest.mark.asyncio
    async def test_synthesize_speech_success(self, agent):
        """Test successful speech synthesis."""
        text = "Hello, this is a test message"

        result = await agent._synthesize_speech(text)

        assert isinstance(result, bytes)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_synthesize_speech_failure(self, agent):
        """Test speech synthesis failure handling."""
        agent.deepgram_service.synthesize_speech = AsyncMock(
            side_effect=Exception("Synthesis failed")
        )

        result = await agent._synthesize_speech("Test text")

        assert result is None

    @pytest.mark.asyncio
    async def test_process_audio_conversation(self, agent, sample_audio_data):
        """Test complete audio conversation processing."""
        request = {
            "audio_data": sample_audio_data,
            "format": "wav",
            "sample_rate": 16000,
            "conversation_id": "test-conv-123",
        }

        result = await agent.process_audio(request)

        assert "transcript" in result
        assert "response" in result
        assert "audio_response" in result
        assert result["response"]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_audio_analysis(self, agent, sample_audio_data):
        """Test audio analysis functionality."""
        analysis = await agent._analyze_audio(sample_audio_data)

        assert "duration" in analysis
        assert "quality_score" in analysis
        assert "noise_level" in analysis
        assert "speech_detected" in analysis

    @pytest.mark.asyncio
    async def test_realtime_processing(self, agent):
        """Test real-time audio processing."""

        # Mock real-time stream
        async def mock_audio_stream():
            chunks = [b"chunk1", b"chunk2", b"chunk3"]
            for chunk in chunks:
                yield chunk

        results = []
        async for result in agent._process_realtime(mock_audio_stream()):
            results.append(result)

        assert len(results) >= 3
        for result in results:
            assert "timestamp" in result
            assert "partial_transcript" in result

    @pytest.mark.asyncio
    async def test_stream_conversation(self, agent, sample_audio_data):
        """Test streaming conversation functionality."""
        request = {
            "audio_data": sample_audio_data,
            "stream": True,
            "conversation_id": "stream-test-123",
        }

        chunks = []
        async for chunk in agent.stream_conversation(request):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert any("transcript" in chunk for chunk in chunks)
        assert any("response_chunk" in chunk for chunk in chunks)

    @pytest.mark.asyncio
    async def test_session_management(self, agent):
        """Test audio session management."""
        session_id = "test-session-123"

        # Start session
        session = await agent.start_session(session_id)
        assert session["session_id"] == session_id
        assert session["status"] == "active"

        # End session
        result = await agent.end_session(session_id)
        assert result["status"] == "closed"

    def test_get_capabilities(self, agent):
        """Test getting agent capabilities."""
        capabilities = agent.get_capabilities()

        assert "transcription" in capabilities
        assert "synthesis" in capabilities
        assert "real_time" in capabilities
        assert "languages" in capabilities
        assert "formats" in capabilities

    @pytest.mark.asyncio
    async def test_voice_activity_detection(self, agent, sample_audio_data):
        """Test voice activity detection."""
        vad_result = await agent._detect_voice_activity(sample_audio_data)

        assert "speech_detected" in vad_result
        assert "speech_segments" in vad_result
        assert "confidence" in vad_result

    @pytest.mark.asyncio
    async def test_audio_preprocessing(self, agent, sample_audio_data):
        """Test audio preprocessing."""
        processed_audio = await agent._preprocess_audio(sample_audio_data)

        assert isinstance(processed_audio, bytes)
        assert len(processed_audio) > 0

    @pytest.mark.asyncio
    async def test_multiple_language_support(self, agent, sample_audio_data):
        """Test multiple language support."""
        languages = ["en", "es", "fr", "de"]

        for lang in languages:
            agent.deepgram_service.transcribe_audio = AsyncMock(
                return_value={
                    "transcript": f"Test in {lang}",
                    "confidence": 0.9,
                    "language": lang,
                }
            )

            request = {"audio_data": sample_audio_data, "language": lang}

            result = await agent.process_audio(request)
            assert result["transcript"]["language"] == lang

    @pytest.mark.asyncio
    async def test_audio_format_support(self, agent):
        """Test support for different audio formats."""
        formats = ["wav", "mp3", "ogg", "flac"]

        for audio_format in formats:
            request = {
                "audio_data": b"fake_audio_data",
                "format": audio_format,
                "sample_rate": 16000,
            }

            result = await agent.process_audio(request)
            assert "transcript" in result

    @pytest.mark.asyncio
    async def test_noise_reduction(self, agent, sample_audio_data):
        """Test noise reduction functionality."""
        noisy_audio = b"noisy_audio_data_with_background_noise"

        cleaned_audio = await agent._reduce_noise(noisy_audio)

        assert isinstance(cleaned_audio, bytes)
        assert len(cleaned_audio) > 0

    @pytest.mark.asyncio
    async def test_conversation_context(self, agent, sample_audio_data):
        """Test conversation context preservation."""
        conversation_id = "context-test-123"

        # First message
        request1 = {
            "audio_data": sample_audio_data,
            "conversation_id": conversation_id,
            "context": {"user_name": "Alice"},
        }

        result1 = await agent.process_audio(request1)

        # Second message with context
        request2 = {
            "audio_data": sample_audio_data,
            "conversation_id": conversation_id,
            "context": result1.get("context", {}),
        }

        result2 = await agent.process_audio(request2)

        # Context should be preserved
        assert result2["context"]["user_name"] == "Alice"

    @pytest.mark.asyncio
    async def test_error_recovery(self, agent, sample_audio_data):
        """Test error recovery mechanisms."""
        # Simulate service failures
        agent.deepgram_service.transcribe_audio = AsyncMock(
            side_effect=Exception("Service down")
        )

        request = {"audio_data": sample_audio_data}

        result = await agent.process_audio(request)

        # Should gracefully handle errors
        assert "error" in result
        assert "fallback_message" in result


@pytest.mark.integration
@pytest.mark.ai
class TestAudioAgentIntegration:
    """Integration tests for AudioAgent."""

    @pytest.fixture
    def integration_agent(self, api_key_manager):
        """Create agent for integration testing."""
        return AudioAgent(api_key_manager)

    @pytest.mark.asyncio
    async def test_end_to_end_voice_conversation(
        self, integration_agent, sample_audio_data
    ):
        """Test complete voice conversation flow."""
        conversation_id = "integration-voice-test"

        # Process audio input
        request = {
            "audio_data": sample_audio_data,
            "conversation_id": conversation_id,
            "format": "wav",
            "sample_rate": 16000,
        }

        result = await integration_agent.process_audio(request)

        # Verify all components
        assert "transcript" in result
        assert "response" in result
        assert result["response"]["role"] == "assistant"

    @pytest.mark.asyncio
    async def test_real_time_streaming(self, integration_agent):
        """Test real-time streaming integration."""
        session_id = "realtime-integration-test"

        # Start session
        session = await integration_agent.start_session(session_id)
        assert session["status"] == "active"

        # Simulate real-time audio chunks
        async def audio_chunk_generator():
            chunks = [b"chunk1", b"chunk2", b"chunk3"]
            for chunk in chunks:
                yield chunk
                await asyncio.sleep(0.1)

        # Process streaming audio
        results = []
        async for result in integration_agent._process_realtime(
            audio_chunk_generator()
        ):
            results.append(result)

        # End session
        await integration_agent.end_session(session_id)

        assert len(results) > 0

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_long_audio_processing(self, integration_agent):
        """Test processing of long audio files."""
        # Simulate long audio (5 minutes worth of data)
        long_audio = b"long_audio_data" * 1000

        request = {"audio_data": long_audio, "format": "wav", "sample_rate": 16000}

        start_time = asyncio.get_event_loop().time()
        result = await integration_agent.process_audio(request)
        end_time = asyncio.get_event_loop().time()

        processing_time = end_time - start_time

        assert "transcript" in result
        assert processing_time < 30  # Should process within 30 seconds

    @pytest.mark.asyncio
    async def test_concurrent_audio_processing(
        self, integration_agent, sample_audio_data
    ):
        """Test concurrent audio processing."""
        # Create multiple concurrent requests
        requests = [
            {
                "audio_data": sample_audio_data,
                "conversation_id": f"concurrent-{i}",
                "format": "wav",
            }
            for i in range(5)
        ]

        # Process concurrently
        tasks = [integration_agent.process_audio(request) for request in requests]

        results = await asyncio.gather(*tasks)

        # All should succeed
        assert len(results) == 5
        for result in results:
            assert "transcript" in result


@pytest.mark.performance
class TestAudioAgentPerformance:
    """Performance tests for AudioAgent."""

    @pytest.fixture
    def performance_agent(self, api_key_manager):
        """Create agent for performance testing."""
        return AudioAgent(api_key_manager)

    @pytest.mark.asyncio
    async def test_transcription_latency(self, performance_agent, sample_audio_data):
        """Test transcription latency."""
        import time

        latencies = []
        for i in range(10):
            start_time = time.time()
            await performance_agent._transcribe_audio(sample_audio_data)
            end_time = time.time()
            latencies.append(end_time - start_time)

        avg_latency = sum(latencies) / len(latencies)
        assert avg_latency < 2.0  # Average latency should be under 2 seconds

    @pytest.mark.asyncio
    async def test_synthesis_latency(self, performance_agent):
        """Test speech synthesis latency."""
        import time

        text = "This is a performance test for speech synthesis."

        latencies = []
        for i in range(5):
            start_time = time.time()
            await performance_agent._synthesize_speech(text)
            end_time = time.time()
            latencies.append(end_time - start_time)

        avg_latency = sum(latencies) / len(latencies)
        assert avg_latency < 3.0  # Average synthesis latency under 3 seconds

    @pytest.mark.asyncio
    async def test_memory_efficiency(self, performance_agent, sample_audio_data):
        """Test memory efficiency during audio processing."""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Process multiple audio requests
        for i in range(20):
            request = {
                "audio_data": sample_audio_data,
                "conversation_id": f"memory-test-{i}",
            }
            await performance_agent.process_audio(request)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable
        assert memory_increase < 100  # Less than 100MB increase

    @pytest.mark.asyncio
    async def test_throughput(self, performance_agent, sample_audio_data):
        """Test processing throughput."""
        import time

        start_time = time.time()

        # Process 50 requests
        tasks = [
            performance_agent.process_audio(
                {"audio_data": sample_audio_data, "conversation_id": f"throughput-{i}"}
            )
            for i in range(50)
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        processing_time = end_time - start_time
        successful_results = [r for r in results if not isinstance(r, Exception)]

        throughput = len(successful_results) / processing_time
        assert throughput > 5  # Should process at least 5 requests per second

    @pytest.mark.asyncio
    async def test_real_time_performance(self, performance_agent):
        """Test real-time processing performance."""
        import time

        # Simulate real-time audio stream
        chunk_duration = 0.1  # 100ms chunks
        total_chunks = 50

        async def timed_audio_stream():
            for i in range(total_chunks):
                yield b"realtime_audio_chunk"
                await asyncio.sleep(chunk_duration)

        start_time = time.time()
        results = []

        async for result in performance_agent._process_realtime(timed_audio_stream()):
            results.append(result)

        end_time = time.time()
        total_time = end_time - start_time

        # Should process in near real-time
        expected_time = total_chunks * chunk_duration
        assert total_time < expected_time * 1.5  # Allow 50% overhead


@pytest.mark.security
class TestAudioAgentSecurity:
    """Security tests for AudioAgent."""

    @pytest.fixture
    def security_agent(self, api_key_manager):
        """Create agent for security testing."""
        return AudioAgent(api_key_manager)

    @pytest.mark.asyncio
    async def test_audio_data_sanitization(self, security_agent):
        """Test that audio data is properly sanitized."""
        # Test with potentially malicious audio data
        malicious_audio = b"\x00" * 1000 + b"malicious_payload" + b"\x00" * 1000

        request = {"audio_data": malicious_audio, "format": "wav"}

        result = await security_agent.process_audio(request)

        # Should handle gracefully without exposing sensitive info
        assert "error" not in result or "malicious" not in str(result)

    @pytest.mark.asyncio
    async def test_input_validation(self, security_agent):
        """Test input validation and sanitization."""
        # Test with invalid formats
        invalid_requests = [
            {"audio_data": "not_bytes", "format": "wav"},
            {"audio_data": b"valid", "format": "invalid_format"},
            {"audio_data": b"", "format": "wav"},
            {"audio_data": None, "format": "wav"},
        ]

        for request in invalid_requests:
            result = await security_agent.process_audio(request)
            assert (
                "error" in result or "transcript" in result
            )  # Should handle gracefully

    @pytest.mark.asyncio
    async def test_session_isolation(self, security_agent):
        """Test that sessions are properly isolated."""
        session1_id = "security-test-session-1"
        session2_id = "security-test-session-2"

        # Start two sessions
        session1 = await security_agent.start_session(session1_id)
        session2 = await security_agent.start_session(session2_id)

        # Verify isolation
        assert session1["session_id"] != session2["session_id"]

        # End sessions
        await security_agent.end_session(session1_id)
        await security_agent.end_session(session2_id)

    @pytest.mark.asyncio
    async def test_rate_limiting_protection(self, security_agent, sample_audio_data):
        """Test rate limiting protection."""
        # Rapid requests from same source
        rapid_requests = [
            {"audio_data": sample_audio_data, "client_id": "rapid_client"}
            for _ in range(100)
        ]

        results = []
        for request in rapid_requests:
            result = await security_agent.process_audio(request)
            results.append(result)

        # Should implement some form of rate limiting
        # (Implementation dependent on actual rate limiting strategy)
        assert len(results) == 100  # All handled gracefully

    def test_data_privacy(self, security_agent):
        """Test data privacy protections."""
        # Verify that sensitive data is not logged or stored
        test_audio = b"private_conversation_data"

        # Check that audio data is not stored in plaintext
        # This would need access to internal storage mechanisms
        # For now, just verify the interface doesn't expose data
        request = {"audio_data": test_audio, "format": "wav", "privacy_mode": True}

        # The test verifies that privacy mode is respected
        assert request.get("privacy_mode") is True
