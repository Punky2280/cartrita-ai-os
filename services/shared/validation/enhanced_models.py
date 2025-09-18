"""
Enhanced Pydantic Models with Security Validation

Security-focused validation models that provide comprehensive input validation,
sanitization, and CSRF protection for all API endpoints.
"""

from typing import Any, Dict, List, Optional, Union, Tuple
from datetime import datetime
from enum import Enum
from pydantic import field_validator

try:
    from pydantic import BaseModel, Field, ValidationError

    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False

    # Define basic fallback classes
    class BaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

        def dict(self):
            return {k: v for k, v in self.__dict__.items()}

    class Field:
        def __init__(self, *args, **kwargs):
            pass

    def validator(field_name: str, pre: bool = False):
        def decorator(func):
            return func

        return decorator

    class ValidationError(Exception):
        pass


try:
    from fastapi import File, UploadFile

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

    class File:
        pass

    class UploadFile:
        pass


import re
import html
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum

# Import the validation framework from enhanced_input_validator
try:
    from .enhanced_input_validator import InputValidator, CSRFTokenManager

    VALIDATOR_AVAILABLE = True
except ImportError:
    VALIDATOR_AVAILABLE = False


class MessageRole(str, Enum):
    """Enumeration for message roles."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class AgentType(str, Enum):
    """Enumeration for agent types."""

    RESEARCH = "research"
    CODE = "code_agent"
    COMPUTER_USE = "computer_use"
    KNOWLEDGE = "knowledge"
    TASK = "task_agent"
    AUDIO = "audio"
    EVALUATION = "evaluation"
    MEMORY = "memory"
    MODEL_SELECTOR = "modelSelector"
    SAFETY = "safety"


class ValidationLevel(str, Enum):
    """Validation strictness levels."""

    BASIC = "basic"
    STANDARD = "standard"
    STRICT = "strict"


class SecureMessage(BaseModel):
    """Enhanced message model with security validation."""

    role: MessageRole = Field(..., description="Message role")
    content: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="Message content with XSS protection",
    )
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = Field(default=None)

    @field_validator("content")
    @classmethod
    def validate_content_security(cls, v):
        """Validate content for XSS and injection attacks."""
        if not isinstance(v, str):
            raise ValueError("Content must be a string")

        # XSS pattern detection
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"vbscript:",
            r"onload\s*=",
            r"onerror\s*=",
            r"onclick\s*=",
            r"onmouseover\s*=",
            r"data:text/html",
        ]

        for pattern in xss_patterns:
            if re.search(pattern, v, re.IGNORECASE | re.DOTALL):
                raise ValueError("Content contains potentially malicious code")

        # SQL injection pattern detection
        sql_patterns = [
            r"union\s+select",
            r"drop\s+table",
            r"delete\s+from",
            r"insert\s+into",
            r"exec\s*\(",
            r"xp_cmdshell",
        ]

        for pattern in sql_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Content contains SQL injection patterns")

        # HTML escape the content
        return html.escape(v.strip())


class EnhancedChatRequest(BaseModel):
    """Enhanced chat request with comprehensive validation."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="User message with security validation",
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None, description="Optional conversation context"
    )
    agent_override: Optional[AgentType] = Field(
        default=None, description="Optional agent type override"
    )
    stream: bool = Field(default=False, description="Whether to stream the response")
    conversation_id: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Conversation identifier",
    )
    validation_level: ValidationLevel = Field(
        default=ValidationLevel.STANDARD, description="Validation strictness level"
    )
    csrf_token: Optional[str] = Field(
        default=None, min_length=32, max_length=128, description="CSRF protection token"
    )

    @field_validator("message")
    @classmethod
    def validate_message_content(cls, v):
        """Enhanced message content validation."""
        if not isinstance(v, str):
            raise ValueError("Message must be a string")

        v = v.strip()
        if not v:
            raise ValueError("Message cannot be empty")

        # Check for dangerous patterns
        dangerous_patterns = [
            r"<script[^>]*>",
            r"javascript:",
            r"vbscript:",
            r"data:text/html",
            r"union\s+select",
            r"drop\s+table",
            r"rm\s+-rf",
            r"\.\./\.\.",
            r"[;&|`$].*(?:rm|wget|curl|nc)",
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError(f"Message contains potentially dangerous content")

        return html.escape(v)

    @field_validator("conversation_id")
    @classmethod
    def validate_conversation_id(cls, v):
        """Validate conversation ID format."""
        if v is not None:
            # Allow only alphanumeric, hyphens, and underscores
            if not re.match(r"^[a-zA-Z0-9_-]+$", v):
                raise ValueError("Invalid conversation ID format")
        return v

    @field_validator("csrf_token")
    @classmethod
    def validate_csrf_token(cls, v):
        """Validate CSRF token format."""
        if v is not None:
            # Ensure token is alphanumeric with hyphens/underscores
            if not re.match(r"^[a-zA-Z0-9_-]+$", v):
                raise ValueError("Invalid CSRF token format")
        return v

    @field_validator("context")
    @classmethod
    def validate_context(cls, v):
        """Validate context data."""
        if v is not None:
            # Ensure context doesn't contain sensitive data patterns
            context_str = str(v)
            sensitive_patterns = [
                r"password",
                r"secret",
                r"token",
                r"api_key",
                r"private_key",
                r"credit_card",
                r"ssn",
                r"social_security",
            ]

            for pattern in sensitive_patterns:
                if re.search(pattern, context_str, re.IGNORECASE):
                    raise ValueError("Context contains potentially sensitive data")

        return v


class EnhancedFileUploadRequest(BaseModel):
    """Enhanced file upload validation."""

    filename: str = Field(
        ..., min_length=1, max_length=255, description="Original filename"
    )
    content_type: str = Field(..., description="MIME content type")
    file_size: int = Field(
        ..., gt=0, le=500 * 1024 * 1024, description="File size in bytes"  # 500MB max
    )
    file_category: str = Field(
        ..., description="File category (image, document, audio, video)"
    )
    csrf_token: str = Field(
        ..., min_length=32, max_length=128, description="CSRF protection token"
    )

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v):
        """Validate filename for security."""
        if not isinstance(v, str):
            raise ValueError("Filename must be a string")

        # Check for dangerous file extensions
        dangerous_extensions = [
            ".exe",
            ".bat",
            ".cmd",
            ".com",
            ".scr",
            ".pif",
            ".vbs",
            ".js",
            ".jar",
            ".sh",
            ".php",
            ".asp",
            ".jsp",
        ]

        filename_lower = v.lower()
        for ext in dangerous_extensions:
            if filename_lower.endswith(ext):
                raise ValueError(f"File type {ext} is not allowed")

        # Check for directory traversal attempts
        if ".." in v or "/" in v or "\\" in v:
            raise ValueError("Invalid filename: directory traversal detected")

        # Sanitize filename
        sanitized = re.sub(r"[^\w\-_\.]", "_", v)
        return sanitized

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v):
        """Validate MIME content type."""
        allowed_types = [
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
            "application/pdf",
            "text/plain",
            "text/markdown",
            "audio/mpeg",
            "audio/wav",
            "audio/ogg",
            "video/mp4",
            "video/webm",
        ]

        if v not in allowed_types:
            raise ValueError(f"Content type {v} is not allowed")

        return v

    @field_validator("file_category")
    @classmethod
    def validate_file_category(cls, v):
        """Validate file category."""
        allowed_categories = ["image", "document", "audio", "video"]
        if v not in allowed_categories:
            raise ValueError(f"File category must be one of: {allowed_categories}")
        return v


class AdminActionRequest(BaseModel):
    """Enhanced admin action request validation."""

    action: str = Field(
        ..., min_length=1, max_length=50, description="Admin action to perform"
    )
    target: Optional[str] = Field(
        default=None, max_length=200, description="Action target (user, resource, etc.)"
    )
    parameters: Optional[Dict[str, Any]] = Field(
        default=None, description="Action parameters"
    )
    csrf_token: str = Field(
        ..., min_length=32, max_length=128, description="CSRF protection token"
    )
    justification: Optional[str] = Field(
        default=None, max_length=500, description="Justification for admin action"
    )

    @field_validator("action")
    @classmethod
    def validate_action(cls, v):
        """Validate admin action."""
        allowed_actions = [
            "create_user",
            "delete_user",
            "update_user",
            "reset_password",
            "suspend_user",
            "activate_user",
            "view_logs",
            "export_data",
            "system_config",
        ]

        if v not in allowed_actions:
            raise ValueError(f"Admin action must be one of: {allowed_actions}")

        return v

    @field_validator("target")
    @classmethod
    def validate_target(cls, v):
        """Validate action target."""
        if v is not None:
            # Ensure target doesn't contain injection patterns
            if re.search(r"[;&|`$<>]", v):
                raise ValueError("Invalid characters in target")

            # HTML escape
            v = html.escape(v.strip())

        return v

    @field_validator("justification")
    @classmethod
    def validate_justification(cls, v):
        """Validate justification text."""
        if v is not None:
            v = v.strip()
            # Basic XSS prevention
            v = html.escape(v)

        return v


class UserRegistrationRequest(BaseModel):
    """Enhanced user registration validation."""

    username: str = Field(..., min_length=3, max_length=50, description="User username")
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ..., min_length=8, max_length=128, description="User password"
    )
    full_name: Optional[str] = Field(
        default=None, max_length=100, description="User full name"
    )
    csrf_token: str = Field(
        ..., min_length=32, max_length=128, description="CSRF protection token"
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        """Validate username format."""
        if not isinstance(v, str):
            raise ValueError("Username must be a string")

        # Allow only alphanumeric, hyphens, and underscores
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Username can only contain letters, numbers, hyphens, and underscores"
            )

        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        """Validate password strength."""
        if not isinstance(v, str):
            raise ValueError("Password must be a string")

        # Check password complexity
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")

        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")

        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")

        return v

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v):
        """Validate full name."""
        if v is not None:
            v = v.strip()
            # Allow only letters, spaces, hyphens, and apostrophes
            if not re.match(r"^[a-zA-Z\s\-']+$", v):
                raise ValueError(
                    "Full name can only contain letters, spaces, hyphens, and apostrophes"
                )

            # HTML escape
            v = html.escape(v)

        return v


class ConfigUpdateRequest(BaseModel):
    """Enhanced configuration update validation."""

    config_key: str = Field(
        ..., min_length=1, max_length=100, description="Configuration key"
    )
    config_value: Union[str, int, float, bool, Dict[str, Any]] = Field(
        ..., description="Configuration value"
    )
    csrf_token: str = Field(
        ..., min_length=32, max_length=128, description="CSRF protection token"
    )

    @field_validator("config_key")
    @classmethod
    def validate_config_key(cls, v):
        """Validate configuration key."""
        # Allow only alphanumeric, dots, hyphens, and underscores
        if not re.match(r"^[a-zA-Z0-9._-]+$", v):
            raise ValueError("Invalid configuration key format")

        # Prevent access to sensitive config keys
        sensitive_keys = [
            "jwt_secret",
            "api_key",
            "database_password",
            "encryption_key",
            "private_key",
            "secret",
        ]

        for sensitive in sensitive_keys:
            if sensitive in v.lower():
                raise ValueError("Cannot modify sensitive configuration keys")

        return v

    @field_validator("config_value")
    @classmethod
    def validate_config_value(cls, v):
        """Validate configuration value."""
        if isinstance(v, str):
            # XSS prevention for string values
            v = html.escape(v)

            # Check for injection patterns
            if re.search(r"[;&|`$<>]", v):
                raise ValueError("Invalid characters in configuration value")

        return v
