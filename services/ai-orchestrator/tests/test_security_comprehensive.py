"""
Comprehensive tests for security middleware, authentication, and authorization.
"""

import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import bcrypt
import jwt
import pytest


@pytest.mark.unit
@pytest.mark.security
class TestJWTAuthentication:
    """Test JWT authentication service."""

    @pytest.fixture
    def jwt_service(self, mock_settings):
        """Create JWT service with mocked settings."""
        from cartrita.orchestrator.services.jwt_auth import JWTAuthService

        return JWTAuthService()

    def test_generate_token_success(self, jwt_service):
        """Test successful JWT token generation."""
        user_data = {
            "user_id": "test-user-123",
            "email": "test@example.com",
            "role": "user",
        }

        token = jwt_service.generate_token(user_data)

        assert isinstance(token, str)
        assert len(token) > 0

        # Verify token can be decoded
        decoded = jwt_service.verify_token(token)
        assert decoded["user_id"] == "test-user-123"
        assert decoded["email"] == "test@example.com"

    def test_verify_token_success(self, jwt_service):
        """Test successful token verification."""
        user_data = {"user_id": "verify-test", "role": "admin"}
        token = jwt_service.generate_token(user_data)

        decoded = jwt_service.verify_token(token)

        assert decoded["user_id"] == "verify-test"
        assert decoded["role"] == "admin"
        assert "exp" in decoded
        assert "iat" in decoded

    def test_verify_expired_token(self, jwt_service):
        """Test verification of expired token."""
        user_data = {"user_id": "expired-test"}

        # Generate token with short expiry
        token = jwt_service.generate_token(user_data, expires_in=1)

        # Wait for expiration
        time.sleep(2)

        with pytest.raises(jwt.ExpiredSignatureError):
            jwt_service.verify_token(token)

    def test_verify_invalid_token(self, jwt_service):
        """Test verification of invalid token."""
        invalid_tokens = [
            "invalid.token.format",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.invalid",
            "",
            None,
        ]

        for invalid_token in invalid_tokens:
            with pytest.raises((jwt.InvalidTokenError, AttributeError, TypeError)):
                jwt_service.verify_token(invalid_token)

    def test_refresh_token(self, jwt_service):
        """Test token refresh functionality."""
        user_data = {"user_id": "refresh-test", "role": "user"}
        original_token = jwt_service.generate_token(user_data)

        # Refresh token
        new_token = jwt_service.refresh_token(original_token)

        assert new_token != original_token
        assert isinstance(new_token, str)

        # Verify new token contains same user data
        decoded = jwt_service.verify_token(new_token)
        assert decoded["user_id"] == "refresh-test"

    def test_token_blacklisting(self, jwt_service):
        """Test token blacklisting functionality."""
        user_data = {"user_id": "blacklist-test"}
        token = jwt_service.generate_token(user_data)

        # Verify token is valid
        assert jwt_service.verify_token(token) is not None

        # Blacklist token
        jwt_service.blacklist_token(token)

        # Verify token is now invalid
        with pytest.raises(jwt.InvalidTokenError):
            jwt_service.verify_token(token)

    def test_role_based_claims(self, jwt_service):
        """Test role-based claims in tokens."""
        admin_data = {
            "user_id": "admin-test",
            "role": "admin",
            "permissions": ["read", "write", "delete"],
        }
        user_data = {"user_id": "user-test", "role": "user", "permissions": ["read"]}

        admin_token = jwt_service.generate_token(admin_data)
        user_token = jwt_service.generate_token(user_data)

        admin_decoded = jwt_service.verify_token(admin_token)
        user_decoded = jwt_service.verify_token(user_token)

        assert admin_decoded["role"] == "admin"
        assert "delete" in admin_decoded["permissions"]

        assert user_decoded["role"] == "user"
        assert "delete" not in user_decoded["permissions"]


@pytest.mark.unit
@pytest.mark.security
class TestPasswordSecurity:
    """Test password hashing and verification."""

    @pytest.fixture
    def password_service(self):
        """Create password service."""
        from cartrita.orchestrator.services.auth import PasswordService

        return PasswordService()

    def test_hash_password(self, password_service):
        """Test password hashing."""
        password = "secure_password_123"

        hashed = password_service.hash_password(password)

        assert isinstance(hashed, str)
        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt format

    def test_verify_password_correct(self, password_service):
        """Test password verification with correct password."""
        password = "test_password_456"
        hashed = password_service.hash_password(password)

        assert password_service.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self, password_service):
        """Test password verification with incorrect password."""
        correct_password = "correct_password"
        wrong_password = "wrong_password"
        hashed = password_service.hash_password(correct_password)

        assert password_service.verify_password(wrong_password, hashed) is False

    def test_password_strength_validation(self, password_service):
        """Test password strength validation."""
        weak_passwords = ["123456", "password", "abc", "11111111"]

        strong_passwords = ["SecurePass123!", "MyStr0ngP@ssw0rd", "C0mpl3x!P@ssw0rd"]

        for weak_pass in weak_passwords:
            assert password_service.validate_password_strength(weak_pass) is False

        for strong_pass in strong_passwords:
            assert password_service.validate_password_strength(strong_pass) is True

    def test_password_history_check(self, password_service):
        """Test password history checking."""
        user_id = "history-test-user"
        old_passwords = ["OldPass123!", "PrevPass456@", "LastPass789#"]

        # Store password history
        for old_pass in old_passwords:
            hashed = password_service.hash_password(old_pass)
            password_service.add_to_history(user_id, hashed)

        # Try to reuse old password
        assert password_service.check_password_history(user_id, "OldPass123!") is False

        # Try new password
        assert password_service.check_password_history(user_id, "NewPass999$") is True


@pytest.mark.unit
@pytest.mark.security
class TestAPIKeyAuthentication:
    """Test API key authentication."""

    @pytest.fixture
    def api_auth_service(self, api_key_manager):
        """Create API authentication service."""
        from cartrita.orchestrator.services.auth import APIKeyAuthService

        return APIKeyAuthService(api_key_manager)

    def test_validate_api_key_success(self, api_auth_service):
        """Test successful API key validation."""
        valid_key = "cartrita-api-key-12345"

        # Mock key validation
        api_auth_service.key_manager.validate_key = Mock(
            return_value={
                "valid": True,
                "key_id": "test-key-id",
                "permissions": ["read", "write"],
            }
        )

        result = api_auth_service.validate_api_key(valid_key)

        assert result["valid"] is True
        assert result["key_id"] == "test-key-id"
        assert "read" in result["permissions"]

    def test_validate_api_key_invalid(self, api_auth_service):
        """Test invalid API key validation."""
        invalid_key = "invalid-api-key"

        api_auth_service.key_manager.validate_key = Mock(
            return_value={"valid": False, "error": "Invalid API key"}
        )

        result = api_auth_service.validate_api_key(invalid_key)

        assert result["valid"] is False
        assert "error" in result

    def test_api_key_rate_limiting(self, api_auth_service):
        """Test API key rate limiting."""
        api_key = "rate-limited-key"

        # Setup rate limiting
        api_auth_service.set_rate_limit(api_key, max_requests=5, window_seconds=60)

        # Make requests up to limit
        for i in range(5):
            result = api_auth_service.check_rate_limit(api_key)
            assert result["allowed"] is True

        # Exceed limit
        result = api_auth_service.check_rate_limit(api_key)
        assert result["allowed"] is False
        assert "rate_limited" in result

    def test_api_key_permissions(self, api_auth_service):
        """Test API key permission checking."""
        api_key = "permissions-test-key"

        # Mock key with specific permissions
        api_auth_service.key_manager.get_permissions = Mock(
            return_value=["agents:read", "agents:write", "files:read"]
        )

        # Check allowed permissions
        assert api_auth_service.check_permission(api_key, "agents:read") is True
        assert api_auth_service.check_permission(api_key, "agents:write") is True

        # Check denied permissions
        assert api_auth_service.check_permission(api_key, "files:write") is False
        assert api_auth_service.check_permission(api_key, "admin:all") is False


@pytest.mark.unit
@pytest.mark.security
class TestSecurityMiddleware:
    """Test security middleware functionality."""

    @pytest.fixture
    def security_middleware(self):
        """Create security middleware."""
        from cartrita.orchestrator.middleware.security import SecurityMiddleware

        return SecurityMiddleware()

    @pytest.mark.asyncio
    async def test_cors_headers(self, security_middleware):
        """Test CORS headers are properly set."""
        mock_request = Mock()
        mock_request.headers = {"Origin": "https://localhost:3000"}
        mock_request.method = "POST"

        mock_response = Mock()
        mock_response.headers = {}

        await security_middleware.add_cors_headers(mock_request, mock_response)

        assert "Access-Control-Allow-Origin" in mock_response.headers
        assert "Access-Control-Allow-Methods" in mock_response.headers
        assert "Access-Control-Allow-Headers" in mock_response.headers

    @pytest.mark.asyncio
    async def test_csp_headers(self, security_middleware):
        """Test Content Security Policy headers."""
        mock_response = Mock()
        mock_response.headers = {}

        security_middleware.add_security_headers(mock_response)

        assert "Content-Security-Policy" in mock_response.headers
        assert "X-Frame-Options" in mock_response.headers
        assert "X-Content-Type-Options" in mock_response.headers

    @pytest.mark.asyncio
    async def test_input_sanitization(self, security_middleware):
        """Test input sanitization."""
        dangerous_inputs = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
        ]

        for dangerous_input in dangerous_inputs:
            sanitized = security_middleware.sanitize_input(dangerous_input)
            assert "<script>" not in sanitized
            assert "javascript:" not in sanitized
            assert "onerror=" not in sanitized

    @pytest.mark.asyncio
    async def test_rate_limiting(self, security_middleware):
        """Test request rate limiting."""
        client_ip = "192.168.1.100"

        # Set aggressive rate limit
        security_middleware.set_rate_limit(client_ip, max_requests=3, window_seconds=60)

        # Make requests up to limit
        for i in range(3):
            allowed = security_middleware.check_rate_limit(client_ip)
            assert allowed is True

        # Exceed limit
        allowed = security_middleware.check_rate_limit(client_ip)
        assert allowed is False

    @pytest.mark.asyncio
    async def test_sql_injection_protection(self, security_middleware):
        """Test SQL injection protection."""
        sql_injection_attempts = [
            "1' OR '1'='1",
            "1; DROP TABLE users;",
            "' UNION SELECT * FROM passwords --",
            "1' OR 1=1 --",
        ]

        for attempt in sql_injection_attempts:
            is_safe = security_middleware.validate_sql_input(attempt)
            assert is_safe is False

        safe_inputs = ["john_doe", "user@example.com", "123456", "normal text input"]

        for safe_input in safe_inputs:
            is_safe = security_middleware.validate_sql_input(safe_input)
            assert is_safe is True

    @pytest.mark.asyncio
    async def test_xss_protection(self, security_middleware):
        """Test XSS protection."""
        xss_attempts = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<iframe src='javascript:alert(\"xss\")'></iframe>",
        ]

        for attempt in xss_attempts:
            sanitized = security_middleware.prevent_xss(attempt)
            assert "<script>" not in sanitized
            assert "javascript:" not in sanitized
            assert "onerror=" not in sanitized

    @pytest.mark.asyncio
    async def test_csrf_protection(self, security_middleware):
        """Test CSRF protection."""
        # Generate CSRF token
        token = security_middleware.generate_csrf_token("session-123")
        assert isinstance(token, str)
        assert len(token) > 0

        # Validate CSRF token
        is_valid = security_middleware.validate_csrf_token("session-123", token)
        assert is_valid is True

        # Invalid token
        is_valid = security_middleware.validate_csrf_token(
            "session-123", "invalid-token"
        )
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_file_upload_security(self, security_middleware):
        """Test file upload security."""
        # Test allowed file types
        allowed_files = [
            ("document.pdf", b"%PDF-1.4"),
            ("image.jpg", b"\xff\xd8\xff"),
            ("text.txt", b"plain text content"),
        ]

        for filename, content in allowed_files:
            is_safe = security_middleware.validate_file_upload(filename, content)
            assert is_safe is True

        # Test dangerous file types
        dangerous_files = [
            ("malware.exe", b"MZ\x90\x00"),
            ("script.js", b"alert('xss')"),
            ("shell.sh", b"#!/bin/bash\nrm -rf /"),
        ]

        for filename, content in dangerous_files:
            is_safe = security_middleware.validate_file_upload(filename, content)
            assert is_safe is False


@pytest.mark.unit
@pytest.mark.security
class TestAdminAuthentication:
    """Test admin authentication and authorization."""

    @pytest.fixture
    def admin_auth_service(self):
        """Create admin authentication service."""
        from cartrita.orchestrator.services.admin_auth import AdminAuthService

        return AdminAuthService()

    @pytest.mark.asyncio
    async def test_admin_login_success(self, admin_auth_service):
        """Test successful admin login."""
        # Mock valid admin credentials
        admin_auth_service.validate_credentials = AsyncMock(
            return_value={
                "valid": True,
                "admin_id": "admin-123",
                "role": "super_admin",
                "permissions": ["all"],
            }
        )

        result = await admin_auth_service.authenticate_admin(
            username="admin", password="secure_admin_password", mfa_token="123456"
        )

        assert result["valid"] is True
        assert result["role"] == "super_admin"
        assert "all" in result["permissions"]

    @pytest.mark.asyncio
    async def test_admin_login_invalid_credentials(self, admin_auth_service):
        """Test admin login with invalid credentials."""
        admin_auth_service.validate_credentials = AsyncMock(
            return_value={"valid": False, "error": "Invalid credentials"}
        )

        result = await admin_auth_service.authenticate_admin(
            username="admin", password="wrong_password", mfa_token="000000"
        )

        assert result["valid"] is False
        assert "error" in result

    @pytest.mark.asyncio
    async def test_mfa_validation(self, admin_auth_service):
        """Test multi-factor authentication validation."""
        admin_id = "admin-mfa-test"
        secret = admin_auth_service.generate_mfa_secret(admin_id)

        # Generate valid TOTP code
        totp_code = admin_auth_service.generate_totp_code(secret)

        # Validate code
        is_valid = admin_auth_service.validate_mfa_code(admin_id, totp_code)
        assert is_valid is True

        # Invalid code
        is_valid = admin_auth_service.validate_mfa_code(admin_id, "000000")
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_admin_session_management(self, admin_auth_service):
        """Test admin session management."""
        admin_id = "session-test-admin"

        # Create session
        session_token = admin_auth_service.create_admin_session(admin_id)
        assert isinstance(session_token, str)

        # Validate session
        session_data = admin_auth_service.validate_admin_session(session_token)
        assert session_data["admin_id"] == admin_id
        assert session_data["valid"] is True

        # Expire session
        admin_auth_service.expire_admin_session(session_token)

        # Validate expired session
        session_data = admin_auth_service.validate_admin_session(session_token)
        assert session_data["valid"] is False

    def test_admin_permission_hierarchy(self, admin_auth_service):
        """Test admin permission hierarchy."""
        permissions = {
            "super_admin": ["all"],
            "system_admin": ["users", "system", "monitoring"],
            "user_admin": ["users"],
            "read_only_admin": ["view"],
        }

        for role, perms in permissions.items():
            # Check role permissions
            has_permission = admin_auth_service.check_admin_permission(role, perms[0])
            assert has_permission is True

            # Super admin should have access to everything
            if role != "super_admin":
                has_all = admin_auth_service.check_admin_permission(
                    "super_admin", perms[0]
                )
                assert has_all is True


@pytest.mark.integration
@pytest.mark.security
class TestSecurityIntegration:
    """Integration tests for security components."""

    @pytest.fixture
    def security_stack(self, api_key_manager):
        """Create complete security stack."""
        from cartrita.orchestrator.middleware.security import SecurityMiddleware
        from cartrita.orchestrator.services.auth import APIKeyAuthService
        from cartrita.orchestrator.services.jwt_auth import JWTAuthService

        return {
            "jwt": JWTAuthService(),
            "api_key": APIKeyAuthService(api_key_manager),
            "middleware": SecurityMiddleware(),
        }

    @pytest.mark.asyncio
    async def test_end_to_end_authentication_flow(self, security_stack):
        """Test complete authentication flow."""
        # 1. API Key authentication
        api_key = "test-api-key-123"
        security_stack["api_key"].key_manager.validate_key = Mock(
            return_value={"valid": True, "key_id": "test-key"}
        )

        api_validation = security_stack["api_key"].validate_api_key(api_key)
        assert api_validation["valid"] is True

        # 2. JWT token generation
        user_data = {"user_id": "integration-test", "role": "user"}
        jwt_token = security_stack["jwt"].generate_token(user_data)
        assert isinstance(jwt_token, str)

        # 3. JWT token validation
        decoded = security_stack["jwt"].verify_token(jwt_token)
        assert decoded["user_id"] == "integration-test"

        # 4. Security middleware processing
        mock_request = Mock()
        mock_request.headers = {
            "Authorization": f"Bearer {jwt_token}",
            "X-API-Key": api_key,
        }

        security_result = await security_stack["middleware"].process_request(
            mock_request
        )
        assert security_result["authenticated"] is True

    @pytest.mark.asyncio
    async def test_security_under_attack(self, security_stack):
        """Test security stack under simulated attack."""
        # Simulate various attack vectors
        attack_scenarios = [
            {
                "type": "brute_force",
                "requests": [{"api_key": f"fake-key-{i}"} for i in range(100)],
            },
            {
                "type": "sql_injection",
                "requests": [{"input": "'; DROP TABLE users; --"}],
            },
            {"type": "xss", "requests": [{"input": "<script>alert('xss')</script>"}]},
        ]

        for scenario in attack_scenarios:
            attack_type = scenario["type"]
            requests = scenario["requests"]

            blocked_count = 0
            for request in requests:
                if attack_type == "brute_force":
                    result = security_stack["api_key"].validate_api_key(
                        request["api_key"]
                    )
                    if not result.get("valid", False):
                        blocked_count += 1

                elif attack_type in ["sql_injection", "xss"]:
                    sanitized = security_stack["middleware"].sanitize_input(
                        request["input"]
                    )
                    if sanitized != request["input"]:
                        blocked_count += 1

            # Should block majority of attacks
            assert blocked_count > len(requests) * 0.8

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_security_performance_under_load(self, security_stack):
        """Test security performance under load."""
        import asyncio
        import time

        start_time = time.time()

        # Simulate high load
        tasks = []
        for i in range(1000):
            # Mix of valid and invalid requests
            api_key = "valid-key" if i % 2 == 0 else f"invalid-key-{i}"
            task = asyncio.create_task(
                security_stack["api_key"].validate_api_key_async(api_key)
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        processing_time = end_time - start_time

        # Should handle 1000 requests in reasonable time
        assert processing_time < 10  # Under 10 seconds
        assert len(results) == 1000

    @pytest.mark.asyncio
    async def test_compliance_audit_trail(self, security_stack):
        """Test security audit trail compliance."""
        # Enable audit logging
        security_stack["middleware"].enable_audit_logging()

        # Perform various security-relevant actions
        actions = [
            {"type": "login", "user": "test-user", "success": True},
            {"type": "api_access", "key": "test-key", "endpoint": "/agents"},
            {"type": "admin_action", "admin": "admin-user", "action": "user_delete"},
            {"type": "failed_auth", "attempt": "invalid-key", "success": False},
        ]

        for action in actions:
            security_stack["middleware"].log_security_event(action)

        # Retrieve audit logs
        audit_logs = security_stack["middleware"].get_audit_logs()

        assert len(audit_logs) >= len(actions)
        for log_entry in audit_logs:
            assert "timestamp" in log_entry
            assert "event_type" in log_entry
            assert "details" in log_entry


@pytest.mark.performance
class TestSecurityPerformance:
    """Performance tests for security components."""

    @pytest.mark.asyncio
    async def test_jwt_performance(self, jwt_service):
        """Test JWT operations performance."""
        import time

        user_data = {"user_id": "perf-test", "role": "user"}

        # Test token generation performance
        start_time = time.time()
        tokens = []
        for i in range(1000):
            token = jwt_service.generate_token(user_data)
            tokens.append(token)
        generation_time = time.time() - start_time

        # Test token verification performance
        start_time = time.time()
        for token in tokens:
            jwt_service.verify_token(token)
        verification_time = time.time() - start_time

        # Performance assertions
        assert generation_time < 2.0  # 1000 tokens in under 2 seconds
        assert verification_time < 1.0  # 1000 verifications in under 1 second

    @pytest.mark.asyncio
    async def test_password_hashing_performance(self, password_service):
        """Test password hashing performance."""
        import time

        passwords = [f"password_{i}" for i in range(100)]

        # Test hashing performance
        start_time = time.time()
        hashes = []
        for password in passwords:
            hashed = password_service.hash_password(password)
            hashes.append(hashed)
        hashing_time = time.time() - start_time

        # Test verification performance
        start_time = time.time()
        for password, hashed in zip(passwords, hashes):
            password_service.verify_password(password, hashed)
        verification_time = time.time() - start_time

        # Performance assertions (bcrypt is intentionally slow)
        assert hashing_time < 30.0  # 100 hashes in under 30 seconds
        assert verification_time < 30.0  # 100 verifications in under 30 seconds

    def test_input_sanitization_performance(self, security_middleware):
        """Test input sanitization performance."""
        import time

        # Generate large inputs
        inputs = [f"<script>alert('test_{i}')</script>" * 100 for i in range(1000)]

        start_time = time.time()
        for input_text in inputs:
            security_middleware.sanitize_input(input_text)
        sanitization_time = time.time() - start_time

        # Should sanitize 1000 large inputs quickly
        assert sanitization_time < 5.0  # Under 5 seconds
