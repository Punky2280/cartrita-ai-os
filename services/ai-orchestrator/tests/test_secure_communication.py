"""
Tests for the secure communication utilities.
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cartrita.orchestrator.utils.secure_communication import (
    CircuitBreaker,
    MessageQueue,
    SecureCommunicator,
    SecureMessage,
    optimized_agent_communication,
)


class TestSecureMessage:
    """Tests for SecureMessage model."""

    def test_secure_message_creation(self):
        """Test creating a secure message."""
        payload = {"test": "data"}
        message = SecureMessage(payload=payload)

        assert message.payload == payload
        assert message.encrypted is False
        assert message.signature is None
        assert isinstance(message.timestamp, float)

    def test_timestamp_validation(self):
        """Test timestamp validation."""
        # Recent timestamp should pass
        payload = {"test": "data"}
        message = SecureMessage(payload=payload, timestamp=time.time())
        assert message.timestamp is not None

        # Old timestamp should fail
        with pytest.raises(ValueError, match="Message timestamp too old"):
            SecureMessage(payload=payload, timestamp=time.time() - 400)


class TestSecureCommunicator:
    """Tests for SecureCommunicator class."""

    def test_init(self):
        """Test SecureCommunicator initialization."""
        communicator = SecureCommunicator("test_secret")
        assert communicator.secret_key == b"test_secret"
        assert communicator.cipher is None
        assert communicator.session is None

    def test_init_with_encryption(self):
        """Test SecureCommunicator with encryption key."""
        # Generate a valid Fernet key (32 bytes base64-encoded)
        from cryptography.fernet import Fernet

        key = Fernet.generate_key()

        communicator = SecureCommunicator("test_secret", key.decode())
        assert communicator.cipher is not None

    def test_signature_generation_and_verification(self):
        """Test HMAC signature generation and verification."""
        communicator = SecureCommunicator("test_secret")
        payload = "test message"

        signature = communicator._generate_signature(payload)
        assert isinstance(signature, str)
        assert len(signature) == 64  # SHA256 hex digest length

        # Verify signature
        assert communicator._verify_signature(payload, signature) is True

        # Wrong signature should fail
        assert communicator._verify_signature(payload, "wrong_sig") is False

    def test_encryption_decryption(self):
        """Test payload encryption and decryption."""
        from cryptography.fernet import Fernet

        key = Fernet.generate_key()

        communicator = SecureCommunicator("test_secret", key.decode())
        payload = {"sensitive": "data", "number": 42}

        encrypted = communicator._encrypt_payload(payload)
        decrypted = communicator._decrypt_payload(encrypted)

        assert decrypted == payload

    def test_create_secure_message(self):
        """Test creating secure messages."""
        communicator = SecureCommunicator("test_secret")
        payload = {"test": "data"}

        message = communicator.create_secure_message(payload)

        assert message.payload == payload
        assert message.signature is not None
        assert message.encrypted is False

    def test_create_secure_message_with_encryption(self):
        """Test creating encrypted secure messages."""
        from cryptography.fernet import Fernet

        key = Fernet.generate_key()

        communicator = SecureCommunicator("test_secret", key.decode())
        payload = {"sensitive": "data"}

        message = communicator.create_secure_message(payload, encrypt=True)

        assert message.encrypted is True
        assert "encrypted_data" in message.payload
        assert message.signature is not None

    def test_verify_secure_message(self):
        """Test verifying secure messages."""
        communicator = SecureCommunicator("test_secret")
        payload = {"test": "data"}

        message = communicator.create_secure_message(payload)

        # Verify valid message
        assert communicator.verify_secure_message(message) is True

        # Tamper with signature
        message.signature = "invalid_signature"
        assert communicator.verify_secure_message(message) is False

    @pytest.mark.asyncio
    async def test_send_secure_request_success(self):
        """Test successful secure request."""
        communicator = SecureCommunicator("test_secret")

        # Mock aiohttp response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"result": "success"})

        # Mock aiohttp session and context manager
        mock_session = AsyncMock()
        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(return_value=mock_response)
        mock_cm.__aexit__ = AsyncMock(return_value=None)
        mock_session.request = MagicMock(return_value=mock_cm)

        communicator.session = mock_session

        payload = {"test": "request"}
        result = await communicator.send_secure_request("http://test.com", payload)

        assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_send_secure_request_retry_on_timeout(self):
        """Test retry logic on timeout."""
        communicator = SecureCommunicator("test_secret")
        communicator.max_retries = 2

        # Mock the session to raise timeout error properly
        mock_session = AsyncMock()
        mock_cm = AsyncMock()
        mock_cm.__aenter__ = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_cm.__aexit__ = AsyncMock(return_value=None)
        mock_session.request = MagicMock(return_value=mock_cm)
        communicator.session = mock_session

        with pytest.raises(Exception):  # Will raise Exception from the retry logic
            await communicator.send_secure_request("http://test.com", {"test": "data"})

        # Should have retried 2 times
        assert mock_session.request.call_count == 2

    @pytest.mark.asyncio
    async def test_send_secure_request_rate_limit_handling(self):
        """Test rate limit handling."""
        communicator = SecureCommunicator("test_secret")

        # First response returns 429
        mock_response_429 = AsyncMock()
        mock_response_429.status = 429
        mock_response_429.headers = {"Retry-After": "1"}

        # Second response succeeds
        mock_response_200 = AsyncMock()
        mock_response_200.status = 200
        mock_response_200.json = AsyncMock(return_value={"success": True})

        # Mock context managers
        mock_cm_429 = AsyncMock()
        mock_cm_429.__aenter__ = AsyncMock(return_value=mock_response_429)
        mock_cm_429.__aexit__ = AsyncMock(return_value=None)

        mock_cm_200 = AsyncMock()
        mock_cm_200.__aenter__ = AsyncMock(return_value=mock_response_200)
        mock_cm_200.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.request = MagicMock(side_effect=[mock_cm_429, mock_cm_200])

        communicator.session = mock_session

        with patch("asyncio.sleep") as mock_sleep:
            result = await communicator.send_secure_request(
                "http://test.com", {"test": "data"}
            )

        assert result == {"success": True}
        mock_sleep.assert_called_once_with(1)


class TestMessageQueue:
    """Tests for MessageQueue class."""

    @pytest.mark.asyncio
    async def test_publish_and_subscribe(self):
        """Test message publishing and subscription."""
        queue = MessageQueue(max_size=10)
        topic = "test_topic"

        # Create test message
        communicator = SecureCommunicator("test_secret")
        message = communicator.create_secure_message({"test": "data"})

        # Start subscriber in background
        messages = []

        async def collect_messages():
            async for msg in queue.subscribe(topic):
                messages.append(msg)
                if len(messages) >= 1:
                    break

        subscriber_task = asyncio.create_task(collect_messages())

        # Give subscriber time to setup
        await asyncio.sleep(0.1)

        # Publish message
        await queue.publish(topic, message)

        # Wait for message to be processed
        await subscriber_task

        assert len(messages) == 1
        assert messages[0].payload == message.payload

    @pytest.mark.asyncio
    async def test_queue_size_limit(self):
        """Test queue size limiting."""
        queue = MessageQueue(max_size=2)
        topic = "test_topic"

        communicator = SecureCommunicator("test_secret")

        # Publish 3 messages (exceeds limit of 2)
        for i in range(3):
            message = communicator.create_secure_message({"msg": i})
            await queue.publish(topic, message)

        # Should only keep last 2 messages
        assert len(queue.queues[topic]) == 2
        assert queue.queues[topic][0].payload["msg"] == 1
        assert queue.queues[topic][1].payload["msg"] == 2


class TestCircuitBreaker:
    """Tests for CircuitBreaker pattern."""

    @pytest.mark.asyncio
    async def test_circuit_breaker_normal_operation(self):
        """Test circuit breaker in normal operation."""
        breaker = CircuitBreaker(failure_threshold=3)

        async def success_func():
            return "success"

        result = await breaker.call(success_func)
        assert result == "success"
        assert breaker.state == "CLOSED"
        assert breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_circuit_breaker_failure_threshold(self):
        """Test circuit breaker opening after failures."""
        breaker = CircuitBreaker(failure_threshold=2)

        async def failing_func():
            raise Exception("Test failure")

        # First failure
        with pytest.raises(Exception):
            await breaker.call(failing_func)
        assert breaker.state == "CLOSED"
        assert breaker.failure_count == 1

        # Second failure - should open circuit
        with pytest.raises(Exception):
            await breaker.call(failing_func)
        assert breaker.state == "OPEN"
        assert breaker.failure_count == 2

        # Further calls should be rejected immediately
        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await breaker.call(failing_func)

    @pytest.mark.asyncio
    async def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery after timeout."""
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)

        async def failing_func():
            raise Exception("Test failure")

        # Fail once to open circuit
        with pytest.raises(Exception):
            await breaker.call(failing_func)
        assert breaker.state == "OPEN"

        # Wait for recovery timeout
        await asyncio.sleep(0.2)

        # Next call should transition to HALF_OPEN
        async def success_func():
            return "recovered"

        result = await breaker.call(success_func)
        assert result == "recovered"
        assert breaker.state == "CLOSED"
        assert breaker.failure_count == 0


class TestOptimizedAgentCommunication:
    """Tests for optimized agent communication function."""

    @pytest.mark.asyncio
    async def test_successful_agent_communication(self):
        """Test successful agent communication."""
        with patch(
            "cartrita.orchestrator.utils.secure_communication.SecureCommunicator"
        ) as mock_comm_class:
            mock_communicator = AsyncMock()
            mock_communicator.send_secure_request = AsyncMock(
                return_value={"response": "success", "agent": "research"}
            )
            mock_comm_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_communicator
            )
            mock_comm_class.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await optimized_agent_communication(
                "research", {"query": "test query"}
            )

            assert result["response"] == "success"
            assert result["agent"] == "research"

    @pytest.mark.asyncio
    async def test_agent_communication_fallback(self):
        """Test agent communication fallback on failure."""
        with patch(
            "cartrita.orchestrator.utils.secure_communication.SecureCommunicator"
        ) as mock_comm_class:
            mock_communicator = AsyncMock()
            mock_communicator.send_secure_request = AsyncMock(
                side_effect=Exception("Connection failed")
            )
            mock_comm_class.return_value.__aenter__ = AsyncMock(
                return_value=mock_communicator
            )
            mock_comm_class.return_value.__aexit__ = AsyncMock(return_value=None)

            result = await optimized_agent_communication(
                "code", {"query": "test query"}
            )

            assert result["error"] == "Service temporarily unavailable"
            assert result["agent_type"] == "code"
            assert result["fallback"] is True


@pytest.mark.asyncio
async def test_integration_secure_workflow():
    """Integration test for complete secure communication workflow."""
    # Test the full workflow with encryption, signing, and verification
    from cryptography.fernet import Fernet

    key = Fernet.generate_key()

    sender = SecureCommunicator("shared_secret", key.decode())
    receiver = SecureCommunicator("shared_secret", key.decode())

    original_payload = {"confidential": "data", "transaction_id": 12345}

    # Sender creates and signs encrypted message
    secure_msg = sender.create_secure_message(original_payload, encrypt=True)

    # Simulate transmission (serialize/deserialize)
    transmitted_data = secure_msg.dict()
    received_msg = SecureMessage(**transmitted_data)

    # Receiver verifies and decrypts
    is_valid = receiver.verify_secure_message(received_msg)

    assert is_valid is True
    assert received_msg.payload == original_payload
    assert received_msg.encrypted is False  # Should be decrypted after verification
