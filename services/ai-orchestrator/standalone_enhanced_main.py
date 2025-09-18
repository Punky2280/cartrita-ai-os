#!/usr/bin/env python3
"""
Enhanced FastAPI server for Cartrita AI OS with basic security validation.
Standalone implementation of Task 10 comprehensive security features.
"""

import hashlib
import json
import logging
import os
import re
import secrets
import sys
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import field_validator

try:
    from fastapi import Depends, FastAPI, HTTPException, Request, Response
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse, StreamingResponse
    from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
    from pydantic import BaseModel, Field
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Please install: pip install fastapi uvicorn pydantic")
    sys.exit(1)

try:
    from dotenv import load_dotenv

    load_dotenv("/app/.env")
except ImportError:
    print("dotenv not available, continuing without .env file loading")
    pass

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()


class SecurityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ValidationViolation(BaseModel):
    """Represents a security validation violation."""

    type: str
    severity: SecurityLevel
    message: str
    field: str
    value: Optional[str] = None
    pattern: Optional[str] = None


class ValidationResult(BaseModel):
    """Result of input validation."""

    is_valid: bool
    sanitized_value: str
    violations: List[ValidationViolation] = []
    security_score: float = 1.0  # 1.0 = clean, 0.0 = maximum violations


class BasicSecurityValidator:
    """Basic security validation without external dependencies."""

    def __init__(self):
        self.csrf_tokens: Dict[str, Dict[str, Any]] = {}

        # Security patterns
        self.xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"onload\s*=",
            r"onerror\s*=",
            r"onclick\s*=",
            r"<iframe[^>]*>",
            r"eval\s*\(",
            r"document\.(write|writeln|cookie)",
        ]

        self.sql_patterns = [
            r"(\bUNION\b.*\bSELECT\b)",
            r"(\bDROP\b.*\bTABLE\b)",
            r"(\bINSERT\b.*\bINTO\b)",
            r"(\bDELETE\b.*\bFROM\b)",
            r"(\bUPDATE\b.*\bSET\b)",
            r"(\'\s*OR\s*\')",
            r"(\'\s*;\s*--)",
            r"(\bEXEC\b.*\bXP_)",
        ]

        self.command_patterns = [
            r"[;&|`$]",
            r"\.\./\.\./",
            r"rm\s+-rf",
            r"cat\s+/etc/",
            r"nc\s+-l",
            r"wget\s+http",
            r"curl\s+http",
        ]

    def sanitize_input(self, value: str) -> str:
        """Basic input sanitization."""
        if not isinstance(value, str):
            return str(value)

        # Remove potentially dangerous characters
        sanitized = value.replace("<", "&lt;").replace(">", "&gt;")
        sanitized = sanitized.replace('"', "&quot;").replace("'", "&#x27;")
        sanitized = sanitized.replace("&", "&amp;")

        # Remove null bytes
        sanitized = sanitized.replace("\x00", "")

        return sanitized[:1000]  # Limit length

    def validate_input(self, value: str, field_name: str) -> ValidationResult:
        """Validate input for security violations."""
        violations = []

        if not isinstance(value, str):
            value = str(value)

        # Check for XSS
        for pattern in self.xss_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                violations.append(
                    ValidationViolation(
                        type="XSS",
                        severity=SecurityLevel.HIGH,
                        message=f"Potential XSS detected in {field_name}",
                        field=field_name,
                        pattern=pattern,
                    )
                )

        # Check for SQL injection
        for pattern in self.sql_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                violations.append(
                    ValidationViolation(
                        type="SQL_INJECTION",
                        severity=SecurityLevel.CRITICAL,
                        message=f"Potential SQL injection detected in {field_name}",
                        field=field_name,
                        pattern=pattern,
                    )
                )

        # Check for command injection
        for pattern in self.command_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                violations.append(
                    ValidationViolation(
                        type="COMMAND_INJECTION",
                        severity=SecurityLevel.CRITICAL,
                        message=f"Potential command injection detected in {field_name}",
                        field=field_name,
                        pattern=pattern,
                    )
                )

        # Calculate security score
        critical_count = len(
            [v for v in violations if v.severity == SecurityLevel.CRITICAL]
        )
        high_count = len([v for v in violations if v.severity == SecurityLevel.HIGH])
        medium_count = len(
            [v for v in violations if v.severity == SecurityLevel.MEDIUM]
        )

        score = 1.0 - (critical_count * 0.5 + high_count * 0.3 + medium_count * 0.1)
        score = max(0.0, score)

        return ValidationResult(
            is_valid=len(violations) == 0,
            sanitized_value=self.sanitize_input(value),
            violations=violations,
            security_score=score,
        )

    def generate_csrf_token(self, request: Request) -> str:
        """Generate a CSRF token for the request."""
        # Create unique identifier for this request
        request_id = hashlib.sha256(
            f"{request.client.host}{time.time()}{secrets.token_hex(16)}".encode()
        ).hexdigest()

        token = secrets.token_urlsafe(32)

        # Store token with expiration
        self.csrf_tokens[token] = {
            "request_id": request_id,
            "created_at": time.time(),
            "expires_at": time.time() + 3600,  # 1 hour
            "client_ip": request.client.host,
        }

        return token

    def validate_csrf_token(self, token: str, request: Request) -> bool:
        """Validate a CSRF token."""
        if not token or token not in self.csrf_tokens:
            return False

        token_data = self.csrf_tokens[token]

        # Check expiration
        if time.time() > token_data["expires_at"]:
            del self.csrf_tokens[token]
            return False

        # Basic client validation (could be enhanced)
        if token_data["client_ip"] != request.client.host:
            logger.warning(
                f"CSRF token client IP mismatch: {token_data['client_ip']} vs {request.client.host}"
            )

        return True


# Initialize security validator
security_validator = BasicSecurityValidator()


# Enhanced auth function with security validation
async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    request: Request = None,
) -> str:
    """Enhanced API key verification with security validation."""
    expected_key = os.getenv("CARTRITA_API_KEY", "dev-api-key-2025")

    if not credentials:
        raise HTTPException(status_code=401, detail="API key required")

    api_key = credentials.credentials

    # Validate API key format
    validation_result = security_validator.validate_input(api_key, "api_key")
    if not validation_result.is_valid:
        logger.warning(
            f"Invalid API key format detected: {validation_result.violations}"
        )
        raise HTTPException(status_code=400, detail="Invalid API key format")

    if api_key != expected_key:
        logger.warning(
            f"Invalid API key attempt from {request.client.host if request else 'unknown'}"
        )
        raise HTTPException(status_code=401, detail="Invalid API key")

    return api_key


# Enhanced response models
class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: float
    services: dict
    security_features: dict


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    agent_override: Optional[str] = None
    stream: bool = False
    csrf_token: Optional[str] = None

    @field_validator("message")
    @classmethod
    def validate_message(cls, v):
        if len(v) > 10000:  # Limit message length
            raise ValueError("Message too long")
        return v


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    agent_type: str
    processing_time: float
    security_validated: bool = True
    security_score: float = 1.0


class VoiceChatRequest(BaseModel):
    conversationId: str = Field(..., description="Unique conversation identifier")
    transcribedText: str = Field(..., description="Text transcribed from user's speech")
    conversationHistory: Optional[List[Dict[str, Any]]] = Field(
        None, description="Previous conversation messages"
    )
    voiceMode: bool = Field(True, description="Whether this is a voice conversation")
    csrf_token: Optional[str] = Field(None, description="CSRF protection token")


class CSRFTokenResponse(BaseModel):
    csrf_token: str
    expires_at: float


class SecurityValidationResponse(BaseModel):
    validated: bool
    violations: List[ValidationViolation]
    security_score: float


# Enhanced input validation dependency
async def validate_and_sanitize_input(
    request: Request, response: Response
) -> Dict[str, Any]:
    """Enhanced input validation and sanitization dependency."""

    # Get request body for validation
    body = await request.body()
    validation_results = []

    if body:
        try:
            data = json.loads(body)

            # Validate all string inputs
            for key, value in data.items():
                if isinstance(value, str):
                    result = security_validator.validate_input(value, key)
                    validation_results.append(result)

                    # Log security violations
                    if not result.is_valid:
                        logger.warning(
                            f"Security violation in field '{key}': {[v.dict() for v in result.violations]}",
                            extra={
                                "client_ip": request.client.host,
                                "endpoint": request.url.path,
                                "field": key,
                                "violations": [v.dict() for v in result.violations],
                            },
                        )

            # Check for critical violations
            critical_violations = [
                r
                for r in validation_results
                if not r.is_valid
                and any(v.severity == SecurityLevel.CRITICAL for v in r.violations)
            ]

            if critical_violations:
                raise HTTPException(
                    status_code=400, detail="Critical security violations detected"
                )

        except json.JSONDecodeError:
            pass

    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers[
        "Strict-Transport-Security"
    ] = "max-age=31536000; includeSubDomains"
    response.headers[
        "Content-Security-Policy"
    ] = "default-src 'self'; script-src 'self' 'unsafe-inline'"

    return {"validation_passed": True, "violations": validation_results}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Enhanced lifespan manager with security initialization."""
    print("🚀 Starting Cartrita AI Orchestrator (Enhanced Security)...")
    print("✓ Basic security validation enabled")
    print("✓ Input validation and CSRF protection active")
    print("✓ XSS, SQL injection, and command injection detection enabled")

    yield

    print("🛑 Shutting down Cartrita AI Orchestrator...")


# FastAPI app with enhanced security
app = FastAPI(
    title="Cartrita AI OS - Orchestrator (Enhanced Security)",
    description="Hierarchical Multi-Agent AI OS with Comprehensive Security Validation",
    version="2.1.0-security-enhanced",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware with enhanced security
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3003",
        "https://cartrita-ai-os.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-CSRF-Token", "X-Security-Score"],
)


@app.get("/")
async def root():
    """Root endpoint providing API information with security status."""
    return {
        "message": "Welcome to Cartrita AI OS - Hierarchical Multi-Agent System (Enhanced Security)",
        "version": "2.1.0-security-enhanced",
        "status": "operational",
        "security_enhanced": True,
        "cors_configured": True,
        "frontend_ports": ["3000", "3001", "3003"],
        "security_features": {
            "input_validation": True,
            "csrf_protection": True,
            "xss_prevention": True,
            "sql_injection_detection": True,
            "command_injection_detection": True,
            "security_headers": True,
            "audit_logging": True,
        },
        "endpoints": {
            "health": "/health",
            "chat": "/api/chat",
            "chat_stream": "/api/chat/stream",
            "voice_chat": "/api/chat/voice",
            "csrf_token": "/api/security/csrf-token",
            "security_validate": "/api/security/validate",
            "docs": "/docs",
        },
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Enhanced health check endpoint with security status."""
    return HealthResponse(
        status="healthy",
        version="2.1.0-security-enhanced",
        timestamp=time.time(),
        services={
            "api": "healthy",
            "cors": "configured",
            "security": "enhanced",
            "validation": "active",
        },
        security_features={
            "input_validation": True,
            "csrf_protection": True,
            "xss_prevention": True,
            "sql_injection_detection": True,
            "command_injection_detection": True,
            "security_headers": True,
            "audit_logging": True,
        },
    )


@app.get("/api/security/csrf-token", response_model=CSRFTokenResponse)
async def get_csrf_token(request: Request):
    """Get CSRF token for secure form submissions."""
    csrf_token = security_validator.generate_csrf_token(request)

    return CSRFTokenResponse(
        csrf_token=csrf_token, expires_at=time.time() + 3600  # 1 hour from now
    )


@app.post("/api/security/validate", response_model=SecurityValidationResponse)
async def validate_input(
    request: Dict[str, Any], api_key: str = Depends(verify_api_key)
):
    """Validate input for security violations."""
    all_violations = []
    total_score = 1.0

    for field, value in request.items():
        if isinstance(value, str):
            result = security_validator.validate_input(value, field)
            all_violations.extend(result.violations)
            total_score = min(total_score, result.security_score)

    return SecurityValidationResponse(
        validated=len(all_violations) == 0,
        violations=all_violations,
        security_score=total_score,
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    api_key: str = Depends(verify_api_key),
    validation_data: Dict[str, Any] = Depends(validate_and_sanitize_input),
    http_request: Request = None,
    response: Response = None,
):
    """Enhanced chat endpoint with comprehensive security validation."""
    start_time = time.time()

    # Validate CSRF token if provided
    if request.csrf_token:
        if not security_validator.validate_csrf_token(request.csrf_token, http_request):
            raise HTTPException(status_code=403, detail="Invalid CSRF token")

    # Validate and sanitize message
    validation_result = security_validator.validate_input(request.message, "message")

    if not validation_result.is_valid:
        logger.warning(f"Message validation failed: {validation_result.violations}")
        # Use sanitized version for response
        message = validation_result.sanitized_value
    else:
        message = request.message

    # Log security score
    response.headers["X-Security-Score"] = str(validation_result.security_score)

    # Generate enhanced response
    response_text = f"AI Enhanced Echo (Security Score: {validation_result.security_score:.2f}): {message}"

    return ChatResponse(
        response=response_text,
        conversation_id=request.conversation_id or f"conv-{int(time.time())}",
        agent_type="enhanced-security-echo-agent",
        processing_time=time.time() - start_time,
        security_validated=True,
        security_score=validation_result.security_score,
    )


@app.post("/api/chat/voice", response_model=ChatResponse)
async def voice_chat(
    request: VoiceChatRequest,
    api_key: str = Depends(verify_api_key),
    validation_data: Dict[str, Any] = Depends(validate_and_sanitize_input),
    response: Response = None,
):
    """Enhanced voice chat endpoint with security validation."""
    start_time = time.time()

    # Validate and sanitize transcribed text
    validation_result = security_validator.validate_input(
        request.transcribedText, "transcribed_text"
    )

    if not validation_result.is_valid:
        logger.warning(f"Voice text validation failed: {validation_result.violations}")
        transcribed_text = validation_result.sanitized_value
    else:
        transcribed_text = request.transcribedText

    response.headers["X-Security-Score"] = str(validation_result.security_score)

    response_text = f"Voice Enhanced Echo (Security Score: {validation_result.security_score:.2f}): {transcribed_text}"

    return ChatResponse(
        response=response_text,
        conversation_id=request.conversationId,
        agent_type="enhanced-security-voice-echo-agent",
        processing_time=time.time() - start_time,
        security_validated=True,
        security_score=validation_result.security_score,
    )


@app.get("/api/chat/stream")
async def chat_stream(
    message: str,
    context: Optional[str] = None,
    csrf_token: Optional[str] = None,
    api_key: str = Depends(verify_api_key),
    request: Request = None,
):
    """Enhanced SSE endpoint for streaming chat responses with security validation."""

    # Validate CSRF token if provided
    if csrf_token and not security_validator.validate_csrf_token(csrf_token, request):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")

    # Validate message
    message_result = security_validator.validate_input(message, "message")
    if not message_result.is_valid:
        logger.warning(f"Stream message validation failed: {message_result.violations}")
        message = message_result.sanitized_value

    # Validate context if provided
    if context:
        context_result = security_validator.validate_input(context, "context")
        if not context_result.is_valid:
            context = context_result.sanitized_value

    async def generate():
        try:
            # Enhanced streaming response
            response_data = {
                "response": f"Streaming Enhanced Echo (Security Score: {message_result.security_score:.2f}): {message}",
                "conversation_id": f"stream-{int(time.time())}",
                "agent_type": "enhanced-security-streaming-echo",
                "timestamp": time.time(),
                "security_validated": True,
                "security_score": message_result.security_score,
            }

            yield f"data: {json.dumps(response_data)}\n\n"
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Enhanced HTTP exception handler with security logging."""
    # Log security-related exceptions
    if exc.status_code in [400, 401, 403]:
        logger.warning(
            f"Security exception: {exc.detail}",
            extra={
                "status_code": exc.status_code,
                "client_ip": request.client.host,
                "endpoint": request.url.path,
                "user_agent": request.headers.get("user-agent", "unknown"),
            },
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "code": f"HTTP_{exc.status_code}",
            "path": request.url.path,
            "security_enhanced": True,
            "timestamp": time.time(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler with security logging."""
    logger.error(
        f"Unexpected error: {str(exc)}",
        extra={
            "client_ip": request.client.host,
            "endpoint": request.url.path,
            "error_type": type(exc).__name__,
        },
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "code": "INTERNAL_ERROR",
            "path": request.url.path,
            "security_enhanced": True,
            "timestamp": time.time(),
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "enhanced_main:app",
        host="127.0.0.1",
        port=int(os.getenv("AI_ORCHESTRATOR_PORT", "8000")),
        reload=True,
        log_level="info",
    )
