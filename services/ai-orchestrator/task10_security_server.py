#!/usr/bin/env python3
"""
Task 10: Comprehensive Input Validation and CSRF Protection
Standalone Security Server Implementation

This file implements comprehensive input validation, XSS prevention,
SQL injection detection, command injection prevention, and CSRF protection
as a complete standalone FastAPI server for security testing.
"""

import asyncio
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import time
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union
from urllib.parse import quote, unquote

from pydantic import field_validator

try:
    import uvicorn
    from fastapi import Depends, FastAPI, HTTPException, Request, Response
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
    from pydantic import BaseModel, Field
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Please install: pip install fastapi uvicorn python-dotenv")
    exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Security Constants
CSRF_TOKEN_LENGTH = 32
CSRF_TOKEN_EXPIRY = 3600  # 1 hour
MAX_INPUT_LENGTH = 10000
RATE_LIMIT_WINDOW = 60  # 1 minute
RATE_LIMIT_MAX_REQUESTS = 100


class SecurityLevel(str, Enum):
    """Security validation levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ValidationViolation(BaseModel):
    """Represents a security validation violation"""

    type: str = Field(..., description="Type of violation")
    severity: SecurityLevel = Field(..., description="Severity level")
    message: str = Field(..., description="Human-readable violation message")
    field: Optional[str] = Field(None, description="Field that caused violation")
    pattern: Optional[str] = Field(None, description="Matched security pattern")
    suggested_fix: Optional[str] = Field(None, description="Suggested remediation")


class ValidationResult(BaseModel):
    """Result of security validation"""

    is_valid: bool = Field(..., description="Whether input passed validation")
    violations: List[ValidationViolation] = Field(
        default=[], description="List of violations found"
    )
    sanitized_input: Optional[str] = Field(
        None, description="Sanitized version of input"
    )
    security_score: float = Field(
        default=1.0, description="Security score (0.0-1.0, higher is better)"
    )


class CSRFTokenResponse(BaseModel):
    """CSRF token response"""

    csrf_token: str
    expires_at: datetime
    token_id: str


class SecureMessage(BaseModel):
    """Secure message with validation"""

    message: str = Field(
        ..., max_length=MAX_INPUT_LENGTH, description="Message content"
    )
    csrf_token: Optional[str] = Field(None, description="CSRF protection token")

    @field_validator("message")
    @classmethod
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()


class BasicSecurityValidator:
    """
    Comprehensive security validator for input sanitization and threat detection.
    Implements detection for XSS, SQL injection, command injection, and other security threats.
    """

    def __init__(self):
        # XSS patterns
        self.xss_patterns = [
            re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
            re.compile(r"javascript:", re.IGNORECASE),
            re.compile(r"vbscript:", re.IGNORECASE),
            re.compile(r"onload\s*=", re.IGNORECASE),
            re.compile(r"onclick\s*=", re.IGNORECASE),
            re.compile(r"onerror\s*=", re.IGNORECASE),
            re.compile(r"onmouseover\s*=", re.IGNORECASE),
            re.compile(r"<iframe[^>]*>", re.IGNORECASE),
            re.compile(r"<object[^>]*>", re.IGNORECASE),
            re.compile(r"<embed[^>]*>", re.IGNORECASE),
            re.compile(r"<link[^>]*>", re.IGNORECASE),
            re.compile(r"<meta[^>]*http-equiv", re.IGNORECASE),
            re.compile(r"expression\s*\(", re.IGNORECASE),
            re.compile(r"url\s*\(", re.IGNORECASE),
            re.compile(r"@import", re.IGNORECASE),
            re.compile(r"<svg[^>]*onload", re.IGNORECASE),
        ]

        # SQL injection patterns
        self.sql_patterns = [
            re.compile(r"union\s+select", re.IGNORECASE),
            re.compile(r"select\s+.*\s+from", re.IGNORECASE),
            re.compile(r"insert\s+into", re.IGNORECASE),
            re.compile(r"delete\s+from", re.IGNORECASE),
            re.compile(r"update\s+.*\s+set", re.IGNORECASE),
            re.compile(r"drop\s+table", re.IGNORECASE),
            re.compile(r"truncate\s+table", re.IGNORECASE),
            re.compile(r"alter\s+table", re.IGNORECASE),
            re.compile(r"create\s+table", re.IGNORECASE),
            re.compile(r"--\s", re.IGNORECASE),
            re.compile(r"/\*.*\*/", re.IGNORECASE | re.DOTALL),
            re.compile(
                r";\s*(select|insert|update|delete|drop|create|alter)", re.IGNORECASE
            ),
            re.compile(r"'\s*or\s*'1'\s*=\s*'1", re.IGNORECASE),
            re.compile(r'"\s*or\s*"1"\s*=\s*"1', re.IGNORECASE),
            re.compile(r"'\s*or\s*1\s*=\s*1", re.IGNORECASE),
            re.compile(r"exec\s*\(", re.IGNORECASE),
            re.compile(r"sp_executesql", re.IGNORECASE),
        ]

        # Command injection patterns
        self.command_patterns = [
            re.compile(r";\s*(rm|del|format|fdisk)", re.IGNORECASE),
            re.compile(r"`[^`]*`", re.IGNORECASE),
            re.compile(r"\$\([^)]*\)", re.IGNORECASE),
            re.compile(r"&&\s*(rm|del|cat|type)", re.IGNORECASE),
            re.compile(r"\|\s*(nc|netcat|telnet)", re.IGNORECASE),
            re.compile(r">\s*/dev/", re.IGNORECASE),
            re.compile(r"<\s*/etc/", re.IGNORECASE),
            re.compile(r"curl\s+", re.IGNORECASE),
            re.compile(r"wget\s+", re.IGNORECASE),
            re.compile(r"eval\s*\(", re.IGNORECASE),
            re.compile(r"system\s*\(", re.IGNORECASE),
            re.compile(r"exec\s*\(", re.IGNORECASE),
            re.compile(r"shell_exec\s*\(", re.IGNORECASE),
            re.compile(r"passthru\s*\(", re.IGNORECASE),
        ]

        # Directory traversal patterns
        self.path_traversal_patterns = [
            re.compile(r"\.\./", re.IGNORECASE),
            re.compile(r"\.\.\\", re.IGNORECASE),
            re.compile(r"%2e%2e%2f", re.IGNORECASE),
            re.compile(r"%2e%2e%5c", re.IGNORECASE),
            re.compile(r"..%252f", re.IGNORECASE),
            re.compile(r"..%255c", re.IGNORECASE),
        ]

    def detect_xss(self, input_str: str) -> List[ValidationViolation]:
        """Detect XSS attempts in input"""
        violations = []
        for pattern in self.xss_patterns:
            matches = pattern.finditer(input_str)
            for match in matches:
                violations.append(
                    ValidationViolation(
                        type="xss",
                        severity=SecurityLevel.HIGH,
                        message=f"Potential XSS detected: {match.group()[:100]}",
                        pattern=pattern.pattern,
                        suggested_fix="Remove or encode HTML/JavaScript content",
                    )
                )
        return violations

    def detect_sql_injection(self, input_str: str) -> List[ValidationViolation]:
        """Detect SQL injection attempts in input"""
        violations = []
        for pattern in self.sql_patterns:
            matches = pattern.finditer(input_str)
            for match in matches:
                violations.append(
                    ValidationViolation(
                        type="sql_injection",
                        severity=SecurityLevel.CRITICAL,
                        message=f"Potential SQL injection detected: {match.group()[:100]}",
                        pattern=pattern.pattern,
                        suggested_fix="Use parameterized queries and input sanitization",
                    )
                )
        return violations

    def detect_command_injection(self, input_str: str) -> List[ValidationViolation]:
        """Detect command injection attempts in input"""
        violations = []
        for pattern in self.command_patterns:
            matches = pattern.finditer(input_str)
            for match in matches:
                violations.append(
                    ValidationViolation(
                        type="command_injection",
                        severity=SecurityLevel.CRITICAL,
                        message=f"Potential command injection detected: {match.group()[:100]}",
                        pattern=pattern.pattern,
                        suggested_fix="Validate and sanitize all user input",
                    )
                )
        return violations

    def detect_path_traversal(self, input_str: str) -> List[ValidationViolation]:
        """Detect path traversal attempts in input"""
        violations = []
        for pattern in self.path_traversal_patterns:
            matches = pattern.finditer(input_str)
            for match in matches:
                violations.append(
                    ValidationViolation(
                        type="path_traversal",
                        severity=SecurityLevel.HIGH,
                        message=f"Potential path traversal detected: {match.group()[:100]}",
                        pattern=pattern.pattern,
                        suggested_fix="Validate file paths and use absolute paths",
                    )
                )
        return violations

    def sanitize_html(self, input_str: str) -> str:
        """Basic HTML sanitization"""
        # Remove script tags
        input_str = re.sub(
            r"<script[^>]*>.*?</script>", "", input_str, flags=re.IGNORECASE | re.DOTALL
        )

        # Remove event handlers
        input_str = re.sub(
            r'on\w+\s*=\s*["\'][^"\']*["\']', "", input_str, flags=re.IGNORECASE
        )

        # Remove javascript: and vbscript: URIs
        input_str = re.sub(
            r'(javascript|vbscript):[^"\'>\s]*', "", input_str, flags=re.IGNORECASE
        )

        # Remove potentially dangerous tags
        dangerous_tags = ["iframe", "object", "embed", "link", "meta"]
        for tag in dangerous_tags:
            input_str = re.sub(f"<{tag}[^>]*>", "", input_str, flags=re.IGNORECASE)
            input_str = re.sub(f"</{tag}>", "", input_str, flags=re.IGNORECASE)

        return input_str

    def calculate_security_score(self, violations: List[ValidationViolation]) -> float:
        """Calculate security score based on violations"""
        if not violations:
            return 1.0

        severity_weights = {
            SecurityLevel.LOW: 0.1,
            SecurityLevel.MEDIUM: 0.3,
            SecurityLevel.HIGH: 0.6,
            SecurityLevel.CRITICAL: 1.0,
        }

        total_weight = sum(severity_weights[v.severity] for v in violations)
        # Score decreases with more severe violations
        score = max(0.0, 1.0 - (total_weight / len(violations)))
        return round(score, 3)

    def validate_input(
        self, input_str: str, field_name: str = None
    ) -> ValidationResult:
        """Comprehensive input validation"""
        if not isinstance(input_str, str):
            return ValidationResult(
                is_valid=False,
                violations=[
                    ValidationViolation(
                        type="type_error",
                        severity=SecurityLevel.HIGH,
                        message="Input must be a string",
                        field=field_name,
                    )
                ],
            )

        # Check length
        if len(input_str) > MAX_INPUT_LENGTH:
            return ValidationResult(
                is_valid=False,
                violations=[
                    ValidationViolation(
                        type="length_error",
                        severity=SecurityLevel.MEDIUM,
                        message=f"Input exceeds maximum length of {MAX_INPUT_LENGTH}",
                        field=field_name,
                    )
                ],
            )

        # Collect all violations
        violations = []
        violations.extend(self.detect_xss(input_str))
        violations.extend(self.detect_sql_injection(input_str))
        violations.extend(self.detect_command_injection(input_str))
        violations.extend(self.detect_path_traversal(input_str))

        # Sanitize input
        sanitized = self.sanitize_html(input_str)

        # Calculate security score
        security_score = self.calculate_security_score(violations)

        # Determine if input is valid (no critical or high severity violations)
        critical_violations = [
            v
            for v in violations
            if v.severity in [SecurityLevel.CRITICAL, SecurityLevel.HIGH]
        ]
        is_valid = len(critical_violations) == 0

        return ValidationResult(
            is_valid=is_valid,
            violations=violations,
            sanitized_input=sanitized,
            security_score=security_score,
        )


class CSRFManager:
    """CSRF token management"""

    def __init__(self):
        self.tokens: Dict[str, Dict[str, Any]] = {}
        self.secret_key = secrets.token_urlsafe(32)

    def generate_token(self, user_id: str = None) -> CSRFTokenResponse:
        """Generate a new CSRF token"""
        token_id = str(uuid.uuid4())
        token = secrets.token_urlsafe(CSRF_TOKEN_LENGTH)
        expires_at = datetime.now() + timedelta(seconds=CSRF_TOKEN_EXPIRY)

        # Create HMAC signature
        message = f"{token_id}:{token}:{expires_at.isoformat()}"
        if user_id:
            message += f":{user_id}"

        signature = hmac.new(
            self.secret_key.encode(), message.encode(), hashlib.sha256
        ).hexdigest()

        self.tokens[token_id] = {
            "token": token,
            "signature": signature,
            "expires_at": expires_at,
            "user_id": user_id,
            "created_at": datetime.now(),
            "used": False,
        }

        # Clean up expired tokens
        self._cleanup_expired_tokens()

        return CSRFTokenResponse(
            csrf_token=f"{token_id}:{token}:{signature}",
            expires_at=expires_at,
            token_id=token_id,
        )

    def validate_token(self, token_string: str, user_id: str = None) -> bool:
        """Validate a CSRF token"""
        try:
            parts = token_string.split(":")
            if len(parts) != 3:
                return False

            token_id, token, provided_signature = parts

            if token_id not in self.tokens:
                return False

            token_data = self.tokens[token_id]

            # Check if already used (one-time use)
            if token_data["used"]:
                return False

            # Check expiration
            if datetime.now() > token_data["expires_at"]:
                del self.tokens[token_id]
                return False

            # Verify token matches
            if token != token_data["token"]:
                return False

            # Verify signature
            message = f"{token_id}:{token}:{token_data['expires_at'].isoformat()}"
            if user_id:
                message += f":{user_id}"

            expected_signature = hmac.new(
                self.secret_key.encode(), message.encode(), hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(provided_signature, expected_signature):
                return False

            # Mark as used
            token_data["used"] = True

            return True

        except Exception as e:
            logger.error(f"CSRF token validation error: {e}")
            return False

    def _cleanup_expired_tokens(self):
        """Remove expired tokens"""
        now = datetime.now()
        expired_tokens = [
            token_id
            for token_id, data in self.tokens.items()
            if now > data["expires_at"]
        ]
        for token_id in expired_tokens:
            del self.tokens[token_id]


# Global instances
security_validator = BasicSecurityValidator()
csrf_manager = CSRFManager()
security_bearer = HTTPBearer(auto_error=False)

# Rate limiting storage
rate_limit_storage: Dict[str, List[float]] = {}


def get_client_ip(request: Request) -> str:
    """Extract client IP address"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_rate_limit(client_ip: str) -> bool:
    """Check if client is within rate limits"""
    now = time.time()

    # Clean old requests
    if client_ip in rate_limit_storage:
        rate_limit_storage[client_ip] = [
            timestamp
            for timestamp in rate_limit_storage[client_ip]
            if now - timestamp < RATE_LIMIT_WINDOW
        ]
    else:
        rate_limit_storage[client_ip] = []

    # Check limit
    if len(rate_limit_storage[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
        return False

    # Record request
    rate_limit_storage[client_ip].append(now)
    return True


async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware"""
    client_ip = get_client_ip(request)

    if not check_rate_limit(client_ip):
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": f"Too many requests from {client_ip}",
                "retry_after": RATE_LIMIT_WINDOW,
            },
        )

    response = await call_next(request)
    return response


# Initialize FastAPI app
app = FastAPI(
    title="Task 10: Security Validation Server",
    description="Comprehensive input validation, XSS prevention, and CSRF protection",
    version="1.0.0",
)

# Add CORS middleware with security headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers[
        "Strict-Transport-Security"
    ] = "max-age=31536000; includeSubDomains"
    response.headers[
        "Content-Security-Policy"
    ] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    return response


@app.middleware("http")
async def rate_limiting_middleware(request: Request, call_next):
    """Apply rate limiting"""
    return await rate_limit_middleware(request, call_next)


# Routes


@app.get("/")
async def root():
    """Root endpoint with security information"""
    return {
        "message": "Task 10: Comprehensive Security Validation Server",
        "version": "1.0.0",
        "features": [
            "XSS Prevention",
            "SQL Injection Detection",
            "Command Injection Prevention",
            "CSRF Protection",
            "Input Validation",
            "Rate Limiting",
            "Security Headers",
        ],
        "endpoints": [
            "/api/security/validate",
            "/api/security/csrf-token",
            "/api/security/secure-message",
            "/api/security/health",
        ],
    }


@app.get("/api/security/csrf-token")
async def get_csrf_token(request: Request):
    """Generate a new CSRF token"""
    client_ip = get_client_ip(request)
    token_response = csrf_manager.generate_token(user_id=client_ip)

    logger.info(f"Generated CSRF token for {client_ip}: {token_response.token_id}")

    return {
        "csrf_token": token_response.csrf_token,
        "expires_at": token_response.expires_at.isoformat(),
        "token_id": token_response.token_id,
        "message": "CSRF token generated successfully",
    }


@app.post("/api/security/validate")
async def validate_input(request: Request):
    """Validate input for security threats"""
    try:
        body = await request.json()
        input_text = body.get("input", "")
        field_name = body.get("field", "input")

        if not input_text:
            raise HTTPException(status_code=400, detail="Input text is required")

        # Perform validation
        result = security_validator.validate_input(input_text, field_name)

        # Log validation results
        client_ip = get_client_ip(request)
        logger.info(
            f"Validation request from {client_ip}: valid={result.is_valid}, score={result.security_score}, violations={len(result.violations)}"
        )

        return {
            "validation_result": result.dict(),
            "timestamp": datetime.now().isoformat(),
            "client_ip": client_ip,
        }

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error during validation"
        )


@app.post("/api/security/secure-message")
async def send_secure_message(request: Request):
    """Send a message with CSRF protection and validation"""
    try:
        body = await request.json()
        message_text = body.get("message", "")
        csrf_token = body.get("csrf_token", "")

        if not message_text:
            raise HTTPException(status_code=400, detail="Message is required")

        if not csrf_token:
            raise HTTPException(status_code=400, detail="CSRF token is required")

        # Validate CSRF token
        client_ip = get_client_ip(request)
        if not csrf_manager.validate_token(csrf_token, user_id=client_ip):
            raise HTTPException(status_code=403, detail="Invalid or expired CSRF token")

        # Validate message content
        result = security_validator.validate_input(message_text, "message")

        if not result.is_valid:
            critical_violations = [
                v
                for v in result.violations
                if v.severity in [SecurityLevel.CRITICAL, SecurityLevel.HIGH]
            ]
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Message failed security validation",
                    "violations": [v.dict() for v in critical_violations],
                    "security_score": result.security_score,
                    "message": "Please modify your message to remove security threats",
                },
            )

        # Log successful message
        logger.info(
            f"Secure message from {client_ip}: length={len(message_text)}, score={result.security_score}"
        )

        return {
            "success": True,
            "message": "Message processed successfully",
            "security_score": result.security_score,
            "sanitized_message": result.sanitized_input,
            "timestamp": datetime.now().isoformat(),
            "violations_found": len(result.violations),
            "client_ip": client_ip,
        }

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Secure message error: {e}")
        raise HTTPException(
            status_code=500, detail="Internal server error processing message"
        )


@app.get("/api/security/health")
async def security_health():
    """Security system health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "security_features": {
            "input_validation": True,
            "xss_protection": True,
            "sql_injection_detection": True,
            "command_injection_prevention": True,
            "csrf_protection": True,
            "rate_limiting": True,
            "security_headers": True,
        },
        "active_csrf_tokens": len(csrf_manager.tokens),
        "rate_limit_clients": len(rate_limit_storage),
        "version": "1.0.0",
    }


# Error handlers


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler with security logging"""
    client_ip = get_client_ip(request)
    logger.warning(f"HTTP {exc.status_code} from {client_ip}: {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat(),
            "request_id": str(uuid.uuid4()),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler with security logging"""
    client_ip = get_client_ip(request)
    logger.error(f"Unhandled error from {client_ip}: {str(exc)}")

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "timestamp": datetime.now().isoformat(),
            "request_id": str(uuid.uuid4()),
        },
    )


if __name__ == "__main__":
    print("Starting Task 10: Comprehensive Security Validation Server")
    print(
        "Features: XSS Prevention, SQL Injection Detection, CSRF Protection, Rate Limiting"
    )
    print("Server will be available at: http://127.0.0.1:8000")
    print("API Documentation: http://127.0.0.1:8000/docs")

    uvicorn.run(
        "task10_security_server:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info",
    )
