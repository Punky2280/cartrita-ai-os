"""
Secure Test Data Fixtures for Cartrita AI OS
Provides mock secrets and secure test configurations
"""

import os
import pytest
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch
import uuid
import secrets
from datetime import datetime, timedelta
from dataclasses import dataclass
from services.ai_orchestrator.cartrita.orchestrator.services.secrets_manager import (
    get_secrets_manager,
)


@dataclass
class MockSecrets:
    """Mock secrets for testing"""

    # Mock API keys that are clearly test-only
    OPENAI_API_KEY = "mock-sk-test-openai-key-for-unit-tests-only-1234567890"
    ANTHROPIC_API_KEY = "mock-sk-ant-test-anthropic-key-for-unit-tests-only-1234"
    DEEPGRAM_API_KEY = "mock-deepgram-test-key-for-unit-tests-only-32chars"
    TAVILY_API_KEY = "mock-tvly-test-tavily-key-for-unit-tests-only-1234"
    LANGCHAIN_API_KEY = "mock-lsv2-test-langchain-key-for-unit-tests-only-1234"
    HUGGINGFACE_TOKEN = "mock-hf-test-huggingface-token-for-unit-tests-only-1234"

    # Mock JWT and encryption keys
    JWT_SECRET_KEY = (
        "mock-jwt-secret-key-for-testing-only-must-be-at-least-64-chars-long-abcdef"
    )
    ENCRYPTION_KEY = (
        "mock-encryption-key-for-testing-purposes-only-secure-random-string-here"
    )

    # Mock database credentials
    DATABASE_PASSWORD = "mock-test-db-password-secure"
    REDIS_PASSWORD = "mock-test-redis-password-secure"

    # Mock service credentials
    CARTRITA_API_KEY = "mock-cartrita-api-key-for-testing-purposes-only"
    GITHUB_TOKEN = "mock-ghp-test-github-token-for-unit-tests-only-abcdef123456789"

    # Mock URLs
    DATABASE_URL = "postgresql://testuser:testpass@localhost:5433/cartrita_test"
    REDIS_URL = "redis://localhost:6380/0"


class SecureTestEnvironment:
    """Secure test environment manager"""

    def __init__(self):
        self.original_env = {}
        self.mock_secrets = MockSecrets()

    def setup_mock_environment(self):
        """Set up mock environment variables for testing"""
        mock_env_vars = {
            "OPENAI_API_KEY": self.mock_secrets.OPENAI_API_KEY,
            "ANTHROPIC_API_KEY": self.mock_secrets.ANTHROPIC_API_KEY,
            "DEEPGRAM_API_KEY": self.mock_secrets.DEEPGRAM_API_KEY,
            "TAVILY_API_KEY": self.mock_secrets.TAVILY_API_KEY,
            "LANGCHAIN_API_KEY": self.mock_secrets.LANGCHAIN_API_KEY,
            "HUGGINGFACE_TOKEN": self.mock_secrets.HUGGINGFACE_TOKEN,
            "JWT_SECRET_KEY": self.mock_secrets.JWT_SECRET_KEY,
            "ENCRYPTION_KEY": self.mock_secrets.ENCRYPTION_KEY,
            "DATABASE_PASSWORD": self.mock_secrets.DATABASE_PASSWORD,
            "REDIS_PASSWORD": self.mock_secrets.REDIS_PASSWORD,
            "CARTRITA_API_KEY": self.mock_secrets.CARTRITA_API_KEY,
            "GITHUB_TOKEN": self.mock_secrets.GITHUB_TOKEN,
            "DATABASE_URL": self.mock_secrets.DATABASE_URL,
            "REDIS_URL": self.mock_secrets.REDIS_URL,
            # Test-specific configurations
            "ENV": "test",
            "DEBUG": "false",
            "TESTING": "true",
            "LOG_LEVEL": "ERROR",  # Reduce test output
            "DISABLE_AUTH": "true",  # Disable auth for some tests
            "MOCK_EXTERNAL_APIS": "true",
            "SKIP_DB_MIGRATIONS": "true",
            "CACHE_DISABLED": "true",
        }

        # Store original values
        for key, value in mock_env_vars.items():
            self.original_env[key] = os.environ.get(key)
            os.environ[key] = value

    def cleanup_environment(self):
        """Restore original environment variables"""
        for key, original_value in self.original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value
        self.original_env.clear()


# Global test environment instance
test_env = SecureTestEnvironment()


@pytest.fixture(scope="session", autouse=True)
def secure_test_environment():
    """Automatically set up secure test environment for all tests"""
    test_env.setup_mock_environment()
    yield
    test_env.cleanup_environment()


@pytest.fixture
def mock_secrets():
    """Fixture providing mock secrets"""
    return MockSecrets()


@pytest.fixture
def mock_secrets_manager():
    """Fixture providing a mock secrets manager"""
    with patch(
        "services.ai_orchestrator.cartrita.orchestrator.services.secrets_manager.get_secrets_manager"
    ) as mock:
        manager_instance = Mock()

        # Configure the mock to return test values
        def get_secret_side_effect(secret_name, service_override=None):
            mock_secrets = MockSecrets()
            return getattr(mock_secrets, secret_name, f"mock-{secret_name}-value")

        manager_instance.get_secret.side_effect = get_secret_side_effect
        manager_instance.set_secret.return_value = True
        manager_instance.validate_all_secrets.return_value = {"all_secrets": True}

        mock.return_value = manager_instance
        yield manager_instance


@pytest.fixture
def mock_api_responses():
    """Fixture providing mock API responses"""
    return {
        "openai": {
            "choices": [
                {"message": {"content": "Mock OpenAI response", "role": "assistant"}}
            ],
            "usage": {"total_tokens": 10},
        },
        "anthropic": {
            "content": [{"text": "Mock Anthropic response"}],
            "usage": {"input_tokens": 5, "output_tokens": 5},
        },
        "deepgram": {
            "results": {
                "channels": [
                    {"alternatives": [{"transcript": "Mock Deepgram transcript"}]}
                ]
            }
        },
        "tavily": {
            "results": [
                {
                    "title": "Mock Result",
                    "content": "Mock search content",
                    "url": "https://example.com",
                }
            ]
        },
    }


@pytest.fixture
def mock_database_session():
    """Fixture providing a mock database session"""
    with patch("sqlalchemy.orm.sessionmaker") as mock_sessionmaker:
        mock_session = Mock()
        mock_sessionmaker.return_value = lambda: mock_session

        # Configure common database operations
        mock_session.query.return_value.filter.return_value.first.return_value = None
        mock_session.query.return_value.all.return_value = []
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.rollback.return_value = None

        yield mock_session


@pytest.fixture
def mock_redis_client():
    """Fixture providing a mock Redis client"""
    with patch("redis.Redis") as mock_redis:
        client = Mock()

        # Configure common Redis operations
        client.get.return_value = None
        client.set.return_value = True
        client.delete.return_value = 1
        client.exists.return_value = False
        client.ping.return_value = True
        client.hget.return_value = None
        client.hset.return_value = 1

        mock_redis.return_value = client
        yield client


@pytest.fixture
def temporary_test_key():
    """Generate a temporary test API key that expires"""
    test_key = f"test-key-{uuid.uuid4().hex[:16]}"
    created_at = datetime.utcnow()
    expires_at = created_at + timedelta(minutes=30)

    return {
        "key": test_key,
        "created_at": created_at,
        "expires_at": expires_at,
        "is_valid": lambda: datetime.utcnow() < expires_at,
    }


@pytest.fixture
def secure_random_string():
    """Generate a secure random string for testing"""
    return secrets.token_urlsafe(32)


class MockHTTPResponse:
    """Mock HTTP response for API testing"""

    def __init__(self, json_data: Dict[str, Any], status_code: int = 200):
        self.json_data = json_data
        self.status_code = status_code
        self.text = str(json_data)

    def json(self):
        return self.json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


@pytest.fixture
def mock_http_client():
    """Fixture providing a mock HTTP client"""
    with patch("requests.Session") as mock_session:
        session = Mock()

        # Configure successful responses by default
        session.get.return_value = MockHTTPResponse({"message": "success"})
        session.post.return_value = MockHTTPResponse({"message": "created"}, 201)
        session.put.return_value = MockHTTPResponse({"message": "updated"})
        session.delete.return_value = MockHTTPResponse({"message": "deleted"}, 204)

        mock_session.return_value = session
        yield session


def generate_mock_jwt_token(payload: Optional[Dict[str, Any]] = None) -> str:
    """Generate a mock JWT token for testing"""
    import base64
    import json

    if payload is None:
        payload = {
            "sub": "test-user",
            "iat": int(datetime.utcnow().timestamp()),
            "exp": int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
            "aud": "cartrita-test",
            "iss": "cartrita-test",
        }

    # Create a mock JWT (not cryptographically signed, for testing only)
    header = {"alg": "HS256", "typ": "JWT"}

    header_b64 = (
        base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    )
    payload_b64 = (
        base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    )
    signature = "mock-signature-for-testing-only"

    return f"{header_b64}.{payload_b64}.{signature}"


@pytest.fixture
def mock_jwt_token():
    """Fixture providing a mock JWT token"""
    return generate_mock_jwt_token()


def assert_no_real_secrets_in_test(test_function_name: str, **kwargs):
    """
    Assert that no real secrets are being used in tests

    Args:
        test_function_name: Name of the test function
        **kwargs: Variables to check for real secrets
    """
    dangerous_patterns = [
        r"^sk-[a-zA-Z0-9]{48,}$",  # Real OpenAI keys
        r"^sk-ant-[a-zA-Z0-9\-_]{40,}$",  # Real Anthropic keys
        r"^hf_[a-zA-Z0-9]{34,}$",  # Real HuggingFace tokens
        r"^ghp_[a-zA-Z0-9]{36,}$",  # Real GitHub tokens
        r"^lsv2_pt_[a-zA-Z0-9_]{40,}$",  # Real LangChain keys
    ]

    for name, value in kwargs.items():
        if isinstance(value, str):
            for pattern in dangerous_patterns:
                import re

                if re.match(pattern, value):
                    raise ValueError(
                        f"SECURITY VIOLATION in {test_function_name}: "
                        f"Real secret detected in {name}. Use mock values only!"
                    )


# Security validation decorators
def require_mock_secrets(func):
    """Decorator to ensure tests only use mock secrets"""

    def wrapper(*args, **kwargs):
        # Check environment variables for real secrets
        env_vars_to_check = [
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "DEEPGRAM_API_KEY",
            "TAVILY_API_KEY",
            "LANGCHAIN_API_KEY",
            "GITHUB_TOKEN",
        ]

        for env_var in env_vars_to_check:
            value = os.environ.get(env_var, "")
            if value and not value.startswith("mock-"):
                pytest.skip(
                    f"Skipping test: Real {env_var} detected. Use MOCK_EXTERNAL_APIS=true"
                )

        return func(*args, **kwargs)

    return wrapper


def skip_if_no_api_key(key_name: str):
    """Decorator to skip tests if API key is missing (for optional integration tests)"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            if (
                not os.environ.get(key_name)
                or os.environ.get("MOCK_EXTERNAL_APIS", "").lower() == "true"
            ):
                pytest.skip(
                    f"Skipping test: {key_name} not available or mocking enabled"
                )
            return func(*args, **kwargs)

        return wrapper

    return decorator


# Export main fixtures and utilities
__all__ = [
    "MockSecrets",
    "SecureTestEnvironment",
    "secure_test_environment",
    "mock_secrets",
    "mock_secrets_manager",
    "mock_api_responses",
    "mock_database_session",
    "mock_redis_client",
    "mock_http_client",
    "mock_jwt_token",
    "temporary_test_key",
    "secure_random_string",
    "generate_mock_jwt_token",
    "assert_no_real_secrets_in_test",
    "require_mock_secrets",
    "skip_if_no_api_key",
]
