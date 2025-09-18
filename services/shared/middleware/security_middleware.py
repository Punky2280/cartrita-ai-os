"""
Enhanced Security Middleware for FastAPI

Comprehensive security middleware providing CSRF protection, input validation,
rate limiting, and security headers for all API endpoints.
"""

import time
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta

try:
    from fastapi import FastAPI, Request, Response, HTTPException, Depends
    from fastapi.responses import JSONResponse
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request as StarletteRequest
    from starlette.responses import Response as StarletteResponse

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

    # Define basic fallback classes
    class BaseHTTPMiddleware:
        def __init__(self, app):
            self.app = app

    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str):
            self.status_code = status_code
            self.detail = detail

    class JSONResponse:
        def __init__(self, content: Dict[str, Any], status_code: int = 200):
            self.content = content
            self.status_code = status_code


# Import validation services
try:
    from ..validation.enhanced_input_validator import InputValidator, CSRFTokenManager

    VALIDATOR_AVAILABLE = True
except ImportError:
    VALIDATOR_AVAILABLE = False

# Configure logging
logger = logging.getLogger(__name__)

import json
import logging
from typing import Any, Dict, Optional, Callable
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.security import HTTPBearer
from starlette.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

# Import our enhanced validation services
try:
    from ..validation.enhanced_input_validator import (
        input_validator,
        ValidationSeverity,
    )
except ImportError:
    # Fallback for development
    input_validator = None

    class ValidationSeverity:
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
        CRITICAL = "critical"


logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware for FastAPI."""

    def __init__(self, app: FastAPI, csrf_required_paths: Optional[list] = None):
        super().__init__(app)
        self.csrf_required_paths = csrf_required_paths or [
            "/api/chat",
            "/api/admin",
            "/api/upload",
            "/api/config",
            "/api/user",
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through security checks."""

        # 1. Basic security headers
        response = await self._add_security_headers(request, call_next)

        return response

    async def _add_security_headers(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Add comprehensive security headers."""

        # Process request
        response = await call_next(request)

        # Add security headers
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin",
        }

        for header, value in security_headers.items():
            response.headers[header] = value

        # Add CSP header
        csp = self._generate_csp_header()
        response.headers["Content-Security-Policy"] = csp

        return response

    def _generate_csp_header(self) -> str:
        """Generate Content Security Policy header."""
        frontend_url = "http://localhost:3001"  # From env in production
        api_url = "http://localhost:8000"  # From env in production

        policies = [
            "default-src 'self'",
            f"script-src 'self' {frontend_url}",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "img-src 'self' data: blob: https:",
            f"connect-src 'self' {api_url} {frontend_url} ws: wss:",
            "font-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com",
            "object-src 'none'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "report-uri /api/security/csp-violation",
        ]

        return "; ".join(policies)


async def validate_csrf_token(request: Request) -> bool:
    """FastAPI dependency for CSRF token validation."""
    if not input_validator:
        logger.warning("Input validator not available - CSRF validation skipped")
        return True

    # Check if CSRF validation is required for this path
    path = request.url.path
    csrf_required = any(
        path.startswith(required_path)
        for required_path in [
            "/api/chat",
            "/api/admin",
            "/api/upload",
            "/api/config",
            "/api/user",
        ]
    )

    if not csrf_required:
        return True

    # Get CSRF token from header or body
    csrf_token = request.headers.get("X-CSRF-Token")

    if not csrf_token and request.method == "POST":
        # Try to get token from request body
        try:
            if hasattr(request, "_json"):
                body_data = request._json
            else:
                body = await request.body()
                body_data = json.loads(body) if body else {}

            csrf_token = body_data.get("csrf_token")
        except (json.JSONDecodeError, AttributeError):
            pass

    if not csrf_token:
        raise HTTPException(
            status_code=403, detail="CSRF token required for this endpoint"
        )

    # Validate token
    if not input_validator.validate_csrf_token(csrf_token, request):
        raise HTTPException(status_code=403, detail="Invalid or expired CSRF token")

    return True


async def validate_request_input(request: Request) -> Dict[str, Any]:
    """FastAPI dependency for comprehensive input validation."""
    if not input_validator:
        logger.warning("Input validator not available - input validation skipped")
        return {}

    try:
        # Get request body
        body = await request.body()
        if not body:
            return {}

        # Parse JSON data
        data = json.loads(body)

        # Validate and sanitize input
        sanitized_data = input_validator.validate_api_request(
            data=data, endpoint=request.url.path, request=request
        )

        return sanitized_data

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in request body")
    except Exception as e:
        logger.error(f"Input validation error: {str(e)}")
        raise HTTPException(status_code=400, detail="Request validation failed")


def setup_enhanced_security(app: FastAPI) -> None:
    """Configure comprehensive security for FastAPI application."""

    # Add security middleware
    app.add_middleware(SecurityMiddleware)

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:3003",  # Turbopack dev server
            "https://cartrita.ai",
            "https://cartrita-ai-os.com",
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-CSRF-Token"],
    )

    # Add CSRF token endpoint
    @app.get("/api/security/csrf-token")
    async def get_csrf_token(request: Request):
        """Generate and return a CSRF token."""
        if not input_validator:
            raise HTTPException(
                status_code=500, detail="Validation service not available"
            )

        token = input_validator.generate_csrf_token(request)
        return {"csrf_token": token}

    # Add CSP violation reporting endpoint
    @app.post("/api/security/csp-violation")
    async def csp_violation_report(request: Request):
        """Handle CSP violation reports."""
        try:
            report = await request.json()
            logger.warning(
                f"CSP Violation: {report.get('blocked-uri', 'unknown')} "
                f"from {request.client.host if request.client else 'unknown'}"
            )
            return {"status": "reported"}
        except Exception as e:
            logger.error(f"Error processing CSP violation report: {str(e)}")
            return {"status": "error"}

    # Add validation summary endpoint for monitoring
    @app.get("/api/security/validation-summary")
    async def validation_summary():
        """Get validation failure summary for monitoring."""
        if not input_validator:
            return {"error": "Validation service not available"}

        summary = input_validator.get_validation_summary(hours=24)
        return summary


# Dependency functions for use with FastAPI endpoints
def require_csrf_token():
    """Dependency that requires CSRF token validation."""
    return Depends(validate_csrf_token)


def validate_input():
    """Dependency that validates and sanitizes input."""
    return Depends(validate_request_input)


def require_security_validation():
    """Combined dependency for full security validation."""

    async def _validate(
        csrf_valid: bool = Depends(validate_csrf_token),
        sanitized_input: Dict[str, Any] = Depends(validate_request_input),
    ) -> Dict[str, Any]:
        return sanitized_input

    return Depends(_validate)


# Rate limiting dependency
class RateLimitDependency:
    """Rate limiting dependency for FastAPI endpoints."""

    def __init__(self, max_requests: int = 100, window_minutes: int = 1):
        self.max_requests = max_requests
        self.window_minutes = window_minutes
        self.request_counts = {}

    async def __call__(self, request: Request) -> bool:
        """Check rate limit for request."""
        # Get client IP
        client_ip = (
            request.headers.get("x-forwarded-for", "").split(",")[0].strip()
            or request.headers.get("x-real-ip", "")
            or request.client.host
            if request.client
            else "unknown"
        )

        # Simple in-memory rate limiting (use Redis in production)
        import time

        current_time = int(time.time() / 60)  # Current minute
        key = f"{client_ip}:{current_time}"

        # Clean old entries
        old_keys = [
            k
            for k in self.request_counts.keys()
            if int(k.split(":")[1]) < current_time - self.window_minutes
        ]
        for old_key in old_keys:
            del self.request_counts[old_key]

        # Check current count
        current_count = self.request_counts.get(key, 0)
        if current_count >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded",
                headers={"Retry-After": "60"},
            )

        # Increment count
        self.request_counts[key] = current_count + 1
        return True


# Create rate limit dependencies
standard_rate_limit = RateLimitDependency(max_requests=100, window_minutes=1)
strict_rate_limit = RateLimitDependency(max_requests=10, window_minutes=1)
auth_rate_limit = RateLimitDependency(max_requests=5, window_minutes=1)
