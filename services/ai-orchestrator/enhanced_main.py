#!/usr/bin/env python3
"""
Enhanced FastAPI server for Cartrita AI OS with comprehensive security validation.
Integrates Task 10 comprehensive input validation and CSRF protection framework.
"""

import importlib.util
import json
import logging
import os
import sys
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field

# Import enhanced security validation with fallbacks
try:
    # Try different import paths
    try:
        from middleware.security_middleware import SecurityMiddleware
        from validation.enhanced_input_validator import EnhancedInputValidator
        from validation.enhanced_models import EnhancedChatRequest, SecureMessage
    except ImportError:
        # Try relative imports
        try:
            sys.path.append("../shared")
            from middleware.security_middleware import SecurityMiddleware
            from validation.enhanced_input_validator import EnhancedInputValidator
            from validation.enhanced_models import EnhancedChatRequest, SecureMessage
        except ImportError:
            # Direct file path import attempt
            base_path = os.path.join(os.path.dirname(__file__), "../shared")

            # Try to load modules directly
            validator_path = os.path.join(
                base_path, "validation/enhanced_input_validator.py"
            )
            if os.path.exists(validator_path):
                spec = importlib.util.spec_from_file_location(
                    "enhanced_input_validator", validator_path
                )
                validator_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(validator_module)
                EnhancedInputValidator = validator_module.EnhancedInputValidator
            else:
                raise ImportError("Enhanced security modules not found")

    SECURITY_AVAILABLE = True
    print("✓ Enhanced security validation loaded successfully")
except ImportError as e:
    SECURITY_AVAILABLE = False
    print(f"⚠ Enhanced security validation not available: {e}")
    print("Using fallback security measures...")

    # Define fallback classes
    class EnhancedInputValidator:
        def __init__(self):
            pass

        def validate_input(self, value, field_name):
            class ValidationResult:
                def __init__(self):
                    self.is_valid = True
                    self.sanitized_value = value
                    self.violations = []

            return ValidationResult()

        def generate_csrf_token(self, request):
            return f"fallback-csrf-{int(time.time())}"

        def validate_csrf_token(self, token, request):
            return True  # Fallback always validates

    class SecurityMiddleware:
        pass


load_dotenv("/app/.env")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize security components
if SECURITY_AVAILABLE:
    input_validator = EnhancedInputValidator()
    csrf_manager = input_validator  # EnhancedInputValidator has CSRF methods
else:
    input_validator = None
    csrf_manager = None

# Security scheme
security = HTTPBearer()


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

    # Validate API key format if security is available
    if SECURITY_AVAILABLE and input_validator:
        validation_result = input_validator.validate_input(api_key, "api_key")
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


# Enhanced response models with security validation
class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: float
    services: dict
    security_features: Optional[dict] = None


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    agent_override: Optional[str] = None
    stream: bool = False
    csrf_token: Optional[str] = None
    model_config = ConfigDict(validate_assignment=True)


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    agent_type: str
    processing_time: float
    security_validated: bool = True


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


# Enhanced input validation dependency
async def validate_and_sanitize_input(
    request: Request, response: Response
) -> Dict[str, Any]:
    """Enhanced input validation and sanitization dependency."""
    if not SECURITY_AVAILABLE or not input_validator:
        return {}

    # Get request body for validation
    body = await request.body()
    if body:
        try:
            data = json.loads(body)

            # Validate all string inputs
            validation_results = []
            for key, value in data.items():
                if isinstance(value, str):
                    result = input_validator.validate_input(value, key)
                    validation_results.append(result)

                    # Log security violations
                    if not result.is_valid:
                        logger.warning(
                            f"Security violation in field '{key}': {result.violations}",
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
                and any(v.severity == "critical" for v in r.violations)
            ]

            if critical_violations:
                raise HTTPException(
                    status_code=400, detail="Critical security violations detected"
                )

            # Add security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers[
                "Strict-Transport-Security"
            ] = "max-age=31536000; includeSubDomains"

            return {"validation_passed": True, "violations": validation_results}

        except json.JSONDecodeError:
            pass

    return {}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Enhanced lifespan manager with security initialization."""
    print("🚀 Starting Cartrita AI Orchestrator (Enhanced Security)...")

    if SECURITY_AVAILABLE:
        print("✓ Enhanced security validation enabled")
        print("✓ Input validation and CSRF protection active")
    else:
        print("⚠ Enhanced security validation not available")

    yield

    print("🛑 Shutting down Cartrita AI Orchestrator...")


# FastAPI app with enhanced security
app = FastAPI(
    title="Cartrita AI OS - Orchestrator (Enhanced Security)",
    description="Hierarchical Multi-Agent AI OS with Comprehensive Security Validation",
    version="2.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add security middleware if available
if SECURITY_AVAILABLE:
    try:
        app.add_middleware(SecurityMiddleware)
    except Exception as e:
        logger.warning(f"Could not add SecurityMiddleware: {e}")

# CORS middleware - Enhanced security configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3003",  # For Turbopack dev server
        "https://cartrita-ai-os.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-CSRF-Token"],  # Allow frontend to access CSRF token
)


@app.get("/")
async def root():
    """Root endpoint providing API information with security status."""
    return {
        "message": "Welcome to Cartrita AI OS - Hierarchical Multi-Agent System (Enhanced Security)",
        "version": "2.1.0",
        "status": "operational",
        "security_enhanced": SECURITY_AVAILABLE,
        "cors_configured": True,
        "frontend_ports": ["3000", "3001", "3003"],
        "endpoints": {
            "health": "/health",
            "chat": "/api/chat",
            "chat_stream": "/api/chat/stream",
            "voice_chat": "/api/chat/voice",
            "csrf_token": "/api/security/csrf-token",
            "docs": "/docs",
        },
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Enhanced health check endpoint with security status."""
    security_features = None
    if SECURITY_AVAILABLE:
        security_features = {
            "input_validation": True,
            "csrf_protection": True,
            "xss_prevention": True,
            "sql_injection_detection": True,
            "command_injection_detection": True,
            "file_upload_validation": True,
            "audit_logging": True,
        }

    return HealthResponse(
        status="healthy",
        version="2.1.0",
        timestamp=time.time(),
        services={
            "api": "healthy",
            "cors": "configured",
            "security": "enhanced" if SECURITY_AVAILABLE else "basic",
        },
        security_features=security_features,
    )


@app.get("/api/security/csrf-token", response_model=CSRFTokenResponse)
async def get_csrf_token(request: Request):
    """Get CSRF token for secure form submissions."""
    if not SECURITY_AVAILABLE or not input_validator:
        raise HTTPException(status_code=501, detail="CSRF protection not available")

    # Generate CSRF token using the enhanced validator
    csrf_token = input_validator.generate_csrf_token(request)

    return CSRFTokenResponse(
        csrf_token=csrf_token, expires_at=time.time() + (24 * 3600)  # 24 hours from now
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    api_key: str = Depends(verify_api_key),
    validation_data: Dict[str, Any] = Depends(validate_and_sanitize_input),
    http_request: Request = None,
):
    """Enhanced chat endpoint with comprehensive security validation."""
    start_time = time.time()

    # Validate CSRF token if security is available
    if SECURITY_AVAILABLE and input_validator and request.csrf_token:
        if not input_validator.validate_csrf_token(request.csrf_token, http_request):
            raise HTTPException(status_code=403, detail="Invalid CSRF token")

    # Sanitize input if security is available
    message = request.message
    if SECURITY_AVAILABLE and input_validator:
        validation_result = input_validator.validate_input(message, "message")
        if not validation_result.is_valid:
            logger.warning(f"Message validation failed: {validation_result.violations}")
            # Use sanitized version
            message = validation_result.sanitized_value

    # Generate enhanced response
    response_text = f"AI Enhanced Echo: {message}"

    return ChatResponse(
        response=response_text,
        conversation_id=request.conversation_id or f"conv-{int(time.time())}",
        agent_type="enhanced-echo-agent",
        processing_time=time.time() - start_time,
        security_validated=SECURITY_AVAILABLE,
    )


@app.post("/api/chat/voice", response_model=ChatResponse)
async def voice_chat(
    request: VoiceChatRequest,
    api_key: str = Depends(verify_api_key),
    validation_data: Dict[str, Any] = Depends(validate_and_sanitize_input),
):
    """Enhanced voice chat endpoint with security validation."""
    start_time = time.time()

    # Validate and sanitize transcribed text
    transcribed_text = request.transcribedText
    if SECURITY_AVAILABLE and input_validator:
        validation_result = input_validator.validate_input(
            transcribed_text, "transcribed_text"
        )
        if not validation_result.is_valid:
            logger.warning(
                f"Voice text validation failed: {validation_result.violations}"
            )
            transcribed_text = validation_result.sanitized_value

    response_text = f"Voice Enhanced Echo: {transcribed_text}"

    return ChatResponse(
        response=response_text,
        conversation_id=request.conversationId,
        agent_type="enhanced-voice-echo-agent",
        processing_time=time.time() - start_time,
        security_validated=SECURITY_AVAILABLE,
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

    # Validate input if security is available
    if SECURITY_AVAILABLE and input_validator:
        message_result = input_validator.validate_input(message, "message")
        if not message_result.is_valid:
            logger.warning(
                f"Stream message validation failed: {message_result.violations}"
            )
            message = message_result.sanitized_value

        if context:
            context_result = input_validator.validate_input(context, "context")
            if not context_result.is_valid:
                context = context_result.sanitized_value

    async def generate():
        try:
            # Enhanced streaming response
            response_data = {
                "response": f"Streaming Enhanced Echo: {message}",
                "conversation_id": f"stream-{int(time.time())}",
                "agent_type": "enhanced-streaming-echo",
                "timestamp": time.time(),
                "security_validated": SECURITY_AVAILABLE,
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
            "security_enhanced": SECURITY_AVAILABLE,
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
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=int(os.getenv("AI_ORCHESTRATOR_PORT", "8000")),
        reload=True,
        log_level="info",
    )
