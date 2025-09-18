"""
Test suite for authentication schemas.
Tests Pydantic models for JWT authentication without LangChain dependencies.
"""

import pytest
from datetime import datetime, timedelta
from pydantic import ValidationError

from cartrita.orchestrator.models.auth_schemas import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserResponse,
    CreateUserRequest,
    PasswordChangeRequest,
    APIKeyCreateRequest,
    APIKeyResponse,
    AuthStatusResponse,
)


class TestLoginRequest:
    """Test LoginRequest model."""

    def test_valid_login_request(self):
        """Test valid login request creation."""
        data = {"email": "test@example.com", "password": "securepassword123"}
        request = LoginRequest(**data)
        assert request.email == "test@example.com"
        assert request.password == "securepassword123"

    def test_invalid_email(self):
        """Test invalid email validation."""
        data = {"email": "invalid-email", "password": "securepassword123"}
        with pytest.raises(ValidationError):
            LoginRequest(**data)

    def test_short_password(self):
        """Test password minimum length validation."""
        data = {"email": "test@example.com", "password": "short"}
        with pytest.raises(ValidationError):
            LoginRequest(**data)


class TestTokenResponse:
    """Test TokenResponse model."""

    def test_valid_token_response(self):
        """Test valid token response creation."""
        data = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "expires_in": 3600,
        }
        response = TokenResponse(**data)
        assert response.access_token == data["access_token"]
        assert response.refresh_token == data["refresh_token"]
        assert response.token_type == "bearer"
        assert response.expires_in == 3600

    def test_custom_token_type(self):
        """Test custom token type."""
        data = {
            "access_token": "token123",
            "refresh_token": "refresh123",
            "token_type": "custom",
            "expires_in": 7200,
        }
        response = TokenResponse(**data)
        assert response.token_type == "custom"


class TestRefreshTokenRequest:
    """Test RefreshTokenRequest model."""

    def test_valid_refresh_request(self):
        """Test valid refresh token request."""
        data = {"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
        request = RefreshTokenRequest(**data)
        assert request.refresh_token == data["refresh_token"]


class TestUserResponse:
    """Test UserResponse model."""

    def test_valid_user_response(self):
        """Test valid user response creation."""
        created_time = datetime.now()
        login_time = datetime.now()

        data = {
            "user_id": "user123",
            "email": "test@example.com",
            "permissions": ["read", "write"],
            "created_at": created_time,
            "last_login": login_time,
        }
        response = UserResponse(**data)
        assert response.user_id == "user123"
        assert response.email == "test@example.com"
        assert response.permissions == ["read", "write"]
        assert response.created_at == created_time
        assert response.last_login == login_time

    def test_minimal_user_response(self):
        """Test user response with minimal fields."""
        data = {
            "user_id": "user123",
            "email": "test@example.com",
            "created_at": datetime.now(),
        }
        response = UserResponse(**data)
        assert response.permissions == []
        assert response.last_login is None


class TestCreateUserRequest:
    """Test CreateUserRequest model."""

    def test_valid_create_user(self):
        """Test valid create user request."""
        data = {
            "email": "newuser@example.com",
            "password": "securepassword123",
            "permissions": ["read"],
        }
        request = CreateUserRequest(**data)
        assert request.email == "newuser@example.com"
        assert request.password == "securepassword123"
        assert request.permissions == ["read"]

    def test_minimal_create_user(self):
        """Test create user with minimal fields."""
        data = {"email": "newuser@example.com", "password": "securepassword123"}
        request = CreateUserRequest(**data)
        assert request.permissions == []


class TestPasswordChangeRequest:
    """Test PasswordChangeRequest model."""

    def test_valid_password_change(self):
        """Test valid password change request."""
        data = {"current_password": "oldpassword123", "new_password": "newpassword456"}
        request = PasswordChangeRequest(**data)
        assert request.current_password == "oldpassword123"
        assert request.new_password == "newpassword456"

    def test_short_new_password(self):
        """Test new password minimum length validation."""
        data = {"current_password": "oldpassword123", "new_password": "short"}
        with pytest.raises(ValidationError):
            PasswordChangeRequest(**data)


class TestAPIKeyCreateRequest:
    """Test APIKeyCreateRequest model."""

    def test_valid_api_key_create(self):
        """Test valid API key creation request."""
        data = {
            "name": "Production API Key",
            "permissions": ["read", "write"],
            "expires_days": 90,
        }
        request = APIKeyCreateRequest(**data)
        assert request.name == "Production API Key"
        assert request.permissions == ["read", "write"]
        assert request.expires_days == 90

    def test_minimal_api_key_create(self):
        """Test API key creation with minimal fields."""
        data = {"name": "Test Key"}
        request = APIKeyCreateRequest(**data)
        assert request.name == "Test Key"
        assert request.permissions == []
        assert request.expires_days is None

    def test_invalid_name_length(self):
        """Test API key name length validation."""
        # Empty name
        with pytest.raises(ValidationError):
            APIKeyCreateRequest(name="")

        # Too long name
        with pytest.raises(ValidationError):
            APIKeyCreateRequest(name="x" * 101)

    def test_invalid_expires_days(self):
        """Test expires_days validation."""
        # Zero days
        with pytest.raises(ValidationError):
            APIKeyCreateRequest(name="Test", expires_days=0)

        # Too many days
        with pytest.raises(ValidationError):
            APIKeyCreateRequest(name="Test", expires_days=366)


class TestAPIKeyResponse:
    """Test APIKeyResponse model."""

    def test_valid_api_key_response(self):
        """Test valid API key response."""
        created_time = datetime.now()
        expires_time = created_time + timedelta(days=30)
        used_time = created_time + timedelta(days=1)

        data = {
            "key_id": "key123",
            "name": "Production Key",
            "key": "sk-1234567890abcdef",
            "permissions": ["read", "write"],
            "created_at": created_time,
            "expires_at": expires_time,
            "last_used": used_time,
            "is_active": True,
        }
        response = APIKeyResponse(**data)
        assert response.key_id == "key123"
        assert response.name == "Production Key"
        assert response.key == "sk-1234567890abcdef"
        assert response.permissions == ["read", "write"]
        assert response.created_at == created_time
        assert response.expires_at == expires_time
        assert response.last_used == used_time
        assert response.is_active is True

    def test_minimal_api_key_response(self):
        """Test API key response with minimal fields."""
        data = {
            "key_id": "key123",
            "name": "Test Key",
            "permissions": [],
            "created_at": datetime.now(),
        }
        response = APIKeyResponse(**data)
        assert response.key is None
        assert response.expires_at is None
        assert response.last_used is None
        assert response.is_active is True


class TestAuthStatusResponse:
    """Test AuthStatusResponse model."""

    def test_authenticated_status(self):
        """Test authenticated status response."""
        expires_time = datetime.now() + timedelta(hours=1)

        data = {
            "authenticated": True,
            "user_id": "user123",
            "permissions": ["read", "write", "admin"],
            "token_expires_at": expires_time,
            "auth_method": "jwt",
        }
        response = AuthStatusResponse(**data)
        assert response.authenticated is True
        assert response.user_id == "user123"
        assert response.permissions == ["read", "write", "admin"]
        assert response.token_expires_at == expires_time
        assert response.auth_method == "jwt"

    def test_unauthenticated_status(self):
        """Test unauthenticated status response."""
        data = {"authenticated": False, "auth_method": "none"}
        response = AuthStatusResponse(**data)
        assert response.authenticated is False
        assert response.user_id is None
        assert response.permissions == []
        assert response.token_expires_at is None
        assert response.auth_method == "none"

    def test_api_key_auth(self):
        """Test API key authentication status."""
        data = {
            "authenticated": True,
            "user_id": "service_account",
            "permissions": ["read"],
            "auth_method": "api_key",
        }
        response = AuthStatusResponse(**data)
        assert response.auth_method == "api_key"
        assert response.token_expires_at is None
