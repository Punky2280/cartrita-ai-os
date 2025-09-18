"""
Enhanced Input Validation and Sanitization Service

Provides comprehensive input validation, sanitization, and CSRF protection
for all user inputs across the Cartrita AI OS platform.

Security Features:
- Comprehensive input sanitization and XSS prevention
- CSRF token validation and protection
- File upload validation and content scanning
- Rate limiting integration
- Audit logging for validation failures
- Multi-layer validation with Pydantic and custom validators
"""

import re
import html
import uuid
import hashlib
import secrets
import logging
from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from enum import Enum
from pydantic import field_validator

try:
    from pydantic import BaseModel, Field, ValidationError

    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

    # Define basic fallback classes
    class BaseModel:
        pass

    class Field:
        pass

    class ValidationError(Exception):
        pass

    def validator(field_name: str, pre: bool = False):
        def decorator(func):
            return func

        return decorator


try:
    from fastapi import HTTPException, Request

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

    # Define basic fallback classes
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str):
            self.status_code = status_code
            self.detail = detail

    class Request:
        pass


try:
    import bleach

    BLEACH_AVAILABLE = True
except ImportError:
    BLEACH_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """Validation failure severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CSRFTokenData(BaseModel):
    """CSRF token validation data."""

    token: str = Field(..., min_length=32, max_length=128)
    timestamp: datetime = Field(default_factory=datetime.now)
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None

    @field_validator("token")
    @classmethod
    def validate_token_format(cls, v):
        """Ensure CSRF token is alphanumeric."""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Invalid CSRF token format")
        return v


class ValidationFailure(BaseModel):
    """Validation failure audit record."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.now)
    severity: ValidationSeverity
    field_name: str
    original_value: str
    sanitized_value: Optional[str] = None
    violation_type: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None


class InputSanitizerConfig:
    """Configuration for input sanitization."""

    # HTML tags allowed in rich text inputs
    ALLOWED_HTML_TAGS = [
        "p",
        "br",
        "strong",
        "em",
        "u",
        "ol",
        "ul",
        "li",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "blockquote",
    ]

    # HTML attributes allowed for specific tags
    ALLOWED_ATTRIBUTES = {
        "*": ["class", "id"],
        "a": ["href", "title"],
        "img": ["src", "alt", "width", "height"],
    }

    # File extensions allowed for uploads
    ALLOWED_FILE_EXTENSIONS = {
        "image": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"],
        "document": [".pdf", ".doc", ".docx", ".txt", ".md"],
        "audio": [".mp3", ".wav", ".ogg", ".m4a"],
        "video": [".mp4", ".webm", ".avi", ".mov"],
    }

    # Maximum file sizes by type (bytes)
    MAX_FILE_SIZES = {
        "image": 10 * 1024 * 1024,  # 10MB
        "document": 50 * 1024 * 1024,  # 50MB
        "audio": 100 * 1024 * 1024,  # 100MB
        "video": 500 * 1024 * 1024,  # 500MB
    }

    # Dangerous file patterns
    DANGEROUS_FILE_PATTERNS = [
        r"\.exe$",
        r"\.bat$",
        r"\.cmd$",
        r"\.com$",
        r"\.scr$",
        r"\.pif$",
        r"\.vbs$",
        r"\.js$",
        r"\.jar$",
        r"\.sh$",
        r"\.php$",
        r"\.asp$",
        r"\.jsp$",
    ]

    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"union\s+select",
        r"drop\s+table",
        r"delete\s+from",
        r"insert\s+into",
        r"update\s+set",
        r"alter\s+table",
        r"exec\s*\(",
        r"xp_cmdshell",
        r"sp_executesql",
    ]

    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>",
        r"javascript:",
        r"vbscript:",
        r"onload\s*=",
        r"onerror\s*=",
        r"onclick\s*=",
        r"onmouseover\s*=",
        r"onfocus\s*=",
        r"data:text/html",
    ]

    # Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$]",
        r"\.\./\.\./",
        r"rm\s+-rf",
        r"cat\s+/etc/",
        r"nc\s+-l",
        r"wget\s+http",
        r"curl\s+http",
    ]


class EnhancedInputValidator:
    """Enhanced input validation and sanitization service."""

    def __init__(self):
        self.config = InputSanitizerConfig()
        self.csrf_tokens: Dict[str, CSRFTokenData] = {}
        self.validation_failures: List[ValidationFailure] = []

    def generate_csrf_token(self, request: Request) -> str:
        """Generate a secure CSRF token for the user session."""
        token = secrets.token_urlsafe(32)

        csrf_data = CSRFTokenData(
            token=token,
            user_agent=request.headers.get("user-agent"),
            ip_address=self._get_client_ip(request),
        )

        self.csrf_tokens[token] = csrf_data

        # Clean up expired tokens (older than 1 hour)
        self._cleanup_expired_csrf_tokens()

        logger.info(f"Generated CSRF token for IP: {csrf_data.ip_address}")
        return token

    def validate_csrf_token(self, token: str, request: Request) -> bool:
        """Validate CSRF token against stored tokens."""
        if not token or token not in self.csrf_tokens:
            self._log_validation_failure(
                field_name="csrf_token",
                original_value=token or "missing",
                violation_type="invalid_csrf_token",
                severity=ValidationSeverity.HIGH,
                request=request,
            )
            return False

        csrf_data = self.csrf_tokens[token]

        # Check token age (1 hour expiry)
        if datetime.now() - csrf_data.timestamp > timedelta(hours=1):
            del self.csrf_tokens[token]
            self._log_validation_failure(
                field_name="csrf_token",
                original_value=token,
                violation_type="expired_csrf_token",
                severity=ValidationSeverity.MEDIUM,
                request=request,
            )
            return False

        # Validate IP address consistency (optional - can be disabled)
        current_ip = self._get_client_ip(request)
        if csrf_data.ip_address and current_ip != csrf_data.ip_address:
            logger.warning(
                f"CSRF token IP mismatch: {csrf_data.ip_address} vs {current_ip}"
            )

        return True

    def sanitize_text_input(
        self, text: str, field_name: str, request: Request = None
    ) -> str:
        """Comprehensive text input sanitization."""
        if not text or not isinstance(text, str):
            return ""

        original_text = text
        violations = []

        # 1. SQL Injection Detection
        for pattern in self.config.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                violations.append("sql_injection")
                text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        # 2. XSS Prevention
        for pattern in self.config.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                violations.append("xss_attempt")
                text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        # 3. Command Injection Prevention
        for pattern in self.config.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                violations.append("command_injection")
                text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        # 4. HTML Sanitization (using bleach)
        text = bleach.clean(
            text,
            tags=self.config.ALLOWED_HTML_TAGS,
            attributes=self.config.ALLOWED_ATTRIBUTES,
            strip=True,
        )

        # 5. HTML Entity Encoding for remaining content
        text = html.escape(text)

        # 6. Length validation and truncation
        max_length = 10000  # Configurable per field
        if len(text) > max_length:
            violations.append("length_exceeded")
            text = text[:max_length] + "..."

        # Log violations if any were detected
        if violations and request:
            for violation in violations:
                self._log_validation_failure(
                    field_name=field_name,
                    original_value=original_text[:100],  # Truncate for logging
                    sanitized_value=text[:100],
                    violation_type=violation,
                    severity=ValidationSeverity.HIGH
                    if violation
                    in ["sql_injection", "xss_attempt", "command_injection"]
                    else ValidationSeverity.MEDIUM,
                    request=request,
                )

        return text

    def validate_file_upload(
        self, filename: str, content: bytes, file_type: str, request: Request = None
    ) -> Tuple[bool, str]:
        """Comprehensive file upload validation."""
        violations = []

        # 1. File extension validation
        file_ext = filename.lower().split(".")[-1] if "." in filename else ""
        allowed_extensions = self.config.ALLOWED_FILE_EXTENSIONS.get(file_type, [])

        if f".{file_ext}" not in allowed_extensions:
            violations.append("invalid_file_extension")

        # 2. Dangerous file pattern check
        for pattern in self.config.DANGEROUS_FILE_PATTERNS:
            if re.search(pattern, filename, re.IGNORECASE):
                violations.append("dangerous_file_pattern")
                break

        # 3. File size validation
        max_size = self.config.MAX_FILE_SIZES.get(file_type, 1024 * 1024)  # 1MB default
        if len(content) > max_size:
            violations.append("file_size_exceeded")

        # 4. Content-type validation (basic magic number check)
        if not self._validate_file_content(content, file_type):
            violations.append("content_type_mismatch")

        # 5. Filename sanitization
        safe_filename = re.sub(r"[^\w\-_\.]", "_", filename)
        if safe_filename != filename:
            violations.append("filename_sanitized")

        # Log violations
        if violations and request:
            for violation in violations:
                self._log_validation_failure(
                    field_name="file_upload",
                    original_value=filename,
                    sanitized_value=safe_filename,
                    violation_type=violation,
                    severity=ValidationSeverity.HIGH
                    if violation in ["dangerous_file_pattern", "content_type_mismatch"]
                    else ValidationSeverity.MEDIUM,
                    request=request,
                )

        # Return validation result
        is_valid = (
            len(
                [
                    v
                    for v in violations
                    if v in ["dangerous_file_pattern", "content_type_mismatch"]
                ]
            )
            == 0
        )
        violation_summary = ", ".join(violations) if violations else "valid"

        return is_valid, violation_summary

    def validate_api_request(
        self, data: Dict[str, Any], endpoint: str, request: Request
    ) -> Dict[str, Any]:
        """Comprehensive API request validation."""
        sanitized_data = {}

        for field_name, value in data.items():
            if isinstance(value, str):
                sanitized_data[field_name] = self.sanitize_text_input(
                    value, field_name, request
                )
            elif isinstance(value, (list, tuple)):
                sanitized_data[field_name] = [
                    self.sanitize_text_input(str(item), f"{field_name}[{i}]", request)
                    if isinstance(item, str)
                    else item
                    for i, item in enumerate(value)
                ]
            elif isinstance(value, dict):
                sanitized_data[field_name] = self.validate_api_request(
                    value, f"{endpoint}.{field_name}", request
                )
            else:
                sanitized_data[field_name] = value

        return sanitized_data

    def get_validation_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get validation failure summary for monitoring."""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_failures = [f for f in self.validation_failures if f.timestamp >= cutoff]

        # Group by violation type
        violations_by_type = {}
        violations_by_severity = {}

        for failure in recent_failures:
            violations_by_type[failure.violation_type] = (
                violations_by_type.get(failure.violation_type, 0) + 1
            )
            violations_by_severity[failure.severity] = (
                violations_by_severity.get(failure.severity, 0) + 1
            )

        return {
            "total_failures": len(recent_failures),
            "violations_by_type": violations_by_type,
            "violations_by_severity": violations_by_severity,
            "period_hours": hours,
            "csrf_tokens_active": len(self.csrf_tokens),
        }

    def _validate_file_content(self, content: bytes, file_type: str) -> bool:
        """Basic file content validation using magic numbers."""
        if not content:
            return False

        # Magic number signatures
        signatures = {
            "image": [
                b"\xFF\xD8\xFF",  # JPEG
                b"\x89PNG\r\n\x1A\n",  # PNG
                b"GIF87a",
                b"GIF89a",  # GIF
                b"RIFF",  # WebP (partial)
            ],
            "pdf": [b"%PDF-"],
            "audio": [b"ID3", b"RIFF", b"OggS"],  # MP3  # WAV  # OGG
        }

        file_signatures = signatures.get(file_type, [])
        return any(content.startswith(sig) for sig in file_signatures)

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request headers."""
        return (
            request.headers.get("x-forwarded-for", "").split(",")[0].strip()
            or request.headers.get("x-real-ip", "")
            or request.client.host
            if request.client
            else "unknown"
        )

    def _log_validation_failure(
        self,
        field_name: str,
        original_value: str,
        violation_type: str,
        severity: ValidationSeverity,
        request: Request = None,
        sanitized_value: str = None,
    ):
        """Log validation failure for audit purposes."""
        failure = ValidationFailure(
            field_name=field_name,
            original_value=original_value,
            sanitized_value=sanitized_value,
            violation_type=violation_type,
            severity=severity,
            ip_address=self._get_client_ip(request) if request else None,
            user_agent=request.headers.get("user-agent") if request else None,
            endpoint=str(request.url) if request else None,
        )

        self.validation_failures.append(failure)

        # Keep only last 1000 failures to prevent memory issues
        if len(self.validation_failures) > 1000:
            self.validation_failures = self.validation_failures[-1000:]

        # Log based on severity
        log_message = f"Validation failure: {violation_type} in {field_name} from {failure.ip_address}"

        if severity == ValidationSeverity.CRITICAL:
            logger.critical(log_message, extra={"validation_failure": failure.dict()})
        elif severity == ValidationSeverity.HIGH:
            logger.error(log_message, extra={"validation_failure": failure.dict()})
        elif severity == ValidationSeverity.MEDIUM:
            logger.warning(log_message, extra={"validation_failure": failure.dict()})
        else:
            logger.info(log_message, extra={"validation_failure": failure.dict()})

    def _cleanup_expired_csrf_tokens(self):
        """Clean up expired CSRF tokens."""
        cutoff = datetime.now() - timedelta(hours=1)
        expired_tokens = [
            token for token, data in self.csrf_tokens.items() if data.timestamp < cutoff
        ]

        for token in expired_tokens:
            del self.csrf_tokens[token]

        if expired_tokens:
            logger.info(f"Cleaned up {len(expired_tokens)} expired CSRF tokens")


# Global validator instance
input_validator = EnhancedInputValidator()
