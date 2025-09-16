"""
Secure communication utilities for inter-service communication.
Implements secure patterns for API Gateway <-> AI Orchestrator communication.
"""

import asyncio
import hashlib
import hmac
import json
import os
import time
from typing import Any, Dict, List, Optional, AsyncIterator
from pydantic import BaseModel, Field, validator
import aiohttp
from cryptography.fernet import Fernet
import structlog

logger = structlog.get_logger(__name__)


class SecureMessage(BaseModel):
    """Secure message format for inter-service communication."""

    payload: Dict[str, Any] = Field(..., description="The actual message payload")
    timestamp: float = Field(default_factory=time.time)
    signature: Optional[str] = Field(None, description="HMAC signature for integrity")
    encrypted: bool = Field(False, description="Whether payload is encrypted")

    @validator('timestamp')
    def validate_timestamp(cls, v):
        """Ensure timestamp is recent (within 5 minutes)."""
        if abs(time.time() - v) > 300:  # 5 minutes
            raise ValueError("Message timestamp too old or invalid")
        return v


class SecureCommunicator:
    """Handles secure communication between services."""

    def __init__(self, secret_key: str, encryption_key: Optional[str] = None):
        self.secret_key = secret_key.encode()
        self.cipher = Fernet(encryption_key.encode()) if encryption_key else None
        self.session: Optional[aiohttp.ClientSession] = None
        self.request_timeout = 30
        self.max_retries = 3

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.request_timeout),
            headers={
                'User-Agent': 'Cartrita-AI-OS/2.0',
                'Content-Type': 'application/json'
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    def _generate_signature(self, payload: str) -> str:
        """Generate HMAC signature for message integrity."""
        return hmac.new(
            self.secret_key,
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

    def _verify_signature(self, payload: str, signature: str) -> bool:
        """Verify HMAC signature."""
        expected = self._generate_signature(payload)
        return hmac.compare_digest(expected, signature)

    def _encrypt_payload(self, payload: Dict[str, Any]) -> str:
        """Encrypt payload if cipher is available."""
        if not self.cipher:
            return json.dumps(payload)

        payload_str = json.dumps(payload)
        encrypted = self.cipher.encrypt(payload_str.encode())
        return encrypted.decode()

    def _decrypt_payload(self, encrypted_payload: str) -> Dict[str, Any]:
        """Decrypt payload if cipher is available."""
        if not self.cipher:
            return json.loads(encrypted_payload)

        decrypted = self.cipher.decrypt(encrypted_payload.encode())
        return json.loads(decrypted.decode())

    def create_secure_message(
        self,
        payload: Dict[str, Any],
        encrypt: bool = False
    ) -> SecureMessage:
        """Create a secure message with optional encryption and signature."""

        if encrypt and self.cipher:
            encrypted_payload = self._encrypt_payload(payload)
            message_payload = {"encrypted_data": encrypted_payload}
            encrypted_flag = True
        else:
            message_payload = payload
            encrypted_flag = False

        # Create message without signature first
        message = SecureMessage(
            payload=message_payload,
            encrypted=encrypted_flag
        )

        # Generate signature for the entire message
        message_str = json.dumps(message_payload, sort_keys=True)
        signature = self._generate_signature(message_str)
        message.signature = signature

        return message

    def verify_secure_message(self, message: SecureMessage) -> bool:
        """Verify message signature and decrypt if needed."""
        try:
            # Verify signature
            if message.signature:
                message_str = json.dumps(message.payload, sort_keys=True)
                if not self._verify_signature(message_str, message.signature):
                    logger.warning("Message signature verification failed")
                    return False

            # Decrypt if encrypted
            if message.encrypted and "encrypted_data" in message.payload:
                decrypted = self._decrypt_payload(message.payload["encrypted_data"])
                message.payload = decrypted
                message.encrypted = False

            return True

        except Exception as e:
            logger.error(f"Message verification failed: {e}")
            return False

    async def send_secure_request(
        self,
        url: str,
        payload: Dict[str, Any],
        method: str = "POST",
        encrypt: bool = False,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Send a secure request with retries and error handling."""

        if not self.session:
            raise RuntimeError("Communication session not initialized")

        # Create secure message
        secure_msg = self.create_secure_message(payload, encrypt=encrypt)

        # Prepare headers
        request_headers = headers or {}
        request_headers.update({
            'X-Secure-Message': 'true',
            'X-Message-Timestamp': str(secure_msg.timestamp)
        })

        # Retry logic
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Sending secure request to {url} (attempt {attempt + 1})")

                async with self.session.request(
                    method,
                    url,
                    json=secure_msg.dict(),
                    headers=request_headers
                ) as response:

                    if response.status == 200:
                        response_data = await response.json()

                        # If response is also a secure message, verify it
                        if response_data.get('signature'):
                            response_msg = SecureMessage(**response_data)
                            if self.verify_secure_message(response_msg):
                                return response_msg.payload
                            else:
                                logger.warning("Response message verification failed")
                                return response_data

                        return response_data

                    elif response.status == 429:  # Rate limited
                        retry_after = int(response.headers.get('Retry-After', 60))
                        logger.warning(f"Rate limited, waiting {retry_after} seconds")
                        await asyncio.sleep(retry_after)
                        continue

                    else:
                        error_msg = await response.text()
                        logger.error(f"Request failed with status {response.status}: {error_msg}")
                        raise aiohttp.ClientError(f"HTTP {response.status}: {error_msg}")

            except asyncio.TimeoutError as e:
                logger.warning(f"Request timeout (attempt {attempt + 1})")
                last_exception = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff

            except Exception as e:
                logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                last_exception = e
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)

        raise last_exception or Exception("All retry attempts failed")


class MessageQueue:
    """In-memory message queue for async communication patterns."""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.queues: Dict[str, List[SecureMessage]] = {}
        self.subscribers: Dict[str, List[asyncio.Event]] = {}

    async def publish(self, topic: str, message: SecureMessage):
        """Publish message to topic."""
        if topic not in self.queues:
            self.queues[topic] = []
            self.subscribers[topic] = []

        # Add message to queue
        self.queues[topic].append(message)

        # Limit queue size
        if len(self.queues[topic]) > self.max_size:
            self.queues[topic] = self.queues[topic][-self.max_size:]

        # Notify subscribers
        for event in self.subscribers[topic]:
            event.set()

        logger.info(f"Published message to topic '{topic}'")

    async def subscribe(self, topic: str) -> AsyncIterator[SecureMessage]:
        """Subscribe to topic and yield messages."""
        if topic not in self.subscribers:
            self.subscribers[topic] = []
            self.queues[topic] = []

        event = asyncio.Event()
        self.subscribers[topic].append(event)

        try:
            while True:
                # Wait for new messages
                await event.wait()
                event.clear()

                # Yield all available messages
                while self.queues[topic]:
                    message = self.queues[topic].pop(0)
                    yield message

        finally:
            # Clean up subscription
            if event in self.subscribers[topic]:
                self.subscribers[topic].remove(event)


# Global message queue instance
message_queue = MessageQueue()


class CircuitBreaker:
    """Circuit breaker pattern for service resilience."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN

    def _is_failure_threshold_reached(self) -> bool:
        return self.failure_count >= self.failure_threshold

    def _is_timeout_expired(self) -> bool:
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )

    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""

        if self.state == 'OPEN':
            if self._is_timeout_expired():
                self.state = 'HALF_OPEN'
                logger.info("Circuit breaker moving to HALF_OPEN state")
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)

            # Success - reset failure count and close circuit
            if self.state == 'HALF_OPEN':
                self.state = 'CLOSED'
                self.failure_count = 0
                logger.info("Circuit breaker CLOSED after successful call")

            return result

        except self.expected_exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self._is_failure_threshold_reached():
                self.state = 'OPEN'
                logger.error(f"Circuit breaker OPENED after {self.failure_count} failures")

            raise e


# Example usage patterns
async def optimized_agent_communication(
    agent_type: str,
    request_data: Dict[str, Any],
    timeout: int = 30
) -> Dict[str, Any]:
    """Optimized communication pattern for agent requests."""

    # Use circuit breaker for resilience
    circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)

    async with SecureCommunicator(
        secret_key=os.getenv('API_KEY_SECRET', 'default_secret'),
        encryption_key=os.getenv('ENCRYPTION_KEY')
    ) as communicator:

        async def make_request():
            agent_url = f"http://localhost:8000/agents/{agent_type}/process"
            return await communicator.send_secure_request(
                agent_url,
                request_data,
                encrypt=True
            )

        try:
            return await circuit_breaker.call(make_request)
        except Exception as e:
            logger.error(f"Agent communication failed: {e}")
            # Fallback to basic response
            return {
                "error": "Service temporarily unavailable",
                "agent_type": agent_type,
                "fallback": True
            }
