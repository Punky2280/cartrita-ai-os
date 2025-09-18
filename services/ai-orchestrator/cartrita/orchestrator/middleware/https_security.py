"""
HTTPS Security Middleware for Cartrita AI OS
Implements comprehensive HTTPS enforcement and security headers for FastAPI application.
"""

import os
from typing import Any, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Import enhanced CSP configuration
try:
    from services.shared.config.csp_security import csp_config
except ImportError:
    # Fallback if shared config not available
    csp_config = None


class HTTPSSecurityMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive HTTPS security middleware that enforces secure headers
    and HTTPS redirection for production environments.
    """

    def __init__(self, app: Any, force_https: Optional[bool] = None):
        super().__init__(app)
        # Determine if we should force HTTPS based on environment
        if force_https is None:
            force_https = (
                os.getenv("NODE_ENV") == "production"
                or os.getenv("ENVIRONMENT") == "production"
            )
        self.force_https = force_https

        # Load configuration from .env.production
        self.hsts_max_age = int(os.getenv("HSTS_MAX_AGE", "31536000"))  # 1 year default
        self.hsts_include_subdomains = (
            os.getenv("HSTS_INCLUDE_SUBDOMAINS", "true").lower() == "true"
        )
        self.hsts_preload = os.getenv("HSTS_PRELOAD", "false").lower() == "true"

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and add security headers to response."""

        # Check if we need to redirect to HTTPS
        if self.force_https and request.url.scheme != "https":
            # Only redirect if not in development/testing
            if not self._is_development_request(request):
                https_url = request.url.replace(scheme="https")
                return Response(status_code=301, headers={"Location": str(https_url)})

        # Process request
        response = await call_next(request)

        # Add comprehensive security headers
        self._add_security_headers(response, request)

        return response

    def _is_development_request(self, request: Request) -> bool:
        """Check if request is from development environment."""
        host = request.headers.get("host", "").lower()
        return (
            "localhost" in host
            or "127.0.0.1" in host
            or host.startswith("192.168.")
            or host.startswith("10.")
            or host.startswith("172.")
        )

    def _add_security_headers(self, response: Response, request: Request) -> None:
        """Add comprehensive security headers to response."""
        headers = response.headers

        # HSTS (HTTP Strict Transport Security) - only over HTTPS
        if request.url.scheme == "https" or self.force_https:
            hsts_value = f"max-age={self.hsts_max_age}"
            if self.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            if self.hsts_preload:
                hsts_value += "; preload"
            headers["Strict-Transport-Security"] = hsts_value

        # Content Security Policy - comprehensive policy
        csp_policy = self._get_csp_policy()
        headers["Content-Security-Policy"] = csp_policy

        # Security headers
        headers.update(
            {
                # Prevent MIME type sniffing
                "X-Content-Type-Options": "nosniff",
                # Prevent clickjacking
                "X-Frame-Options": "DENY",
                # XSS protection (legacy but still useful)
                "X-XSS-Protection": "1; mode=block",
                # Referrer policy
                "Referrer-Policy": "strict-origin-when-cross-origin",
                # Feature policy / Permissions policy
                "Permissions-Policy": (
                    "camera=(), microphone=(), geolocation=(), "
                    "payment=(), usb=(), interest-cohort=()"
                ),
                # Cross-Origin policies
                "Cross-Origin-Embedder-Policy": "require-corp",
                "Cross-Origin-Opener-Policy": "same-origin",
                "Cross-Origin-Resource-Policy": "same-origin",
            }
        )

        # Secure cookie settings
        self._update_cookie_security(response)

    def _get_csp_policy(self) -> str:
        """Get Content Security Policy appropriate for our application."""
        # Use enhanced CSP configuration if available
        if csp_config:
            environment = "production" if self.force_https else "development"
            return csp_config.get_csp_policy(environment)

        # Fallback to basic CSP policy
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3001")
        api_url = os.getenv("NEXT_PUBLIC_API_URL", "http://localhost:8000")

        policy_parts = [
            "default-src 'self'",
            f"script-src 'self' {frontend_url}",  # Removed unsafe-inline/unsafe-eval
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "img-src 'self' data: blob: https:",
            f"connect-src 'self' {api_url} {frontend_url} wss: https://fonts.googleapis.com https://fonts.gstatic.com",
            "font-src 'self' https://fonts.googleapis.com https://fonts.gstatic.com",
            "object-src 'none'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]

        # Add upgrade-insecure-requests in production
        if self.force_https:
            policy_parts.append("upgrade-insecure-requests")

        # Add CSP violation reporting
        report_uri = os.getenv("CSP_REPORT_URI", "/api/security/csp-violation")
        policy_parts.append(f"report-uri {report_uri}")

        return "; ".join(policy_parts)

    def _update_cookie_security(self, response: Response) -> None:
        """Update cookie security settings."""
        # Note: FastAPI cookies are handled elsewhere, but we can set defaults
        # This would be applied to any cookies set in the response
        set_cookie_header = response.headers.get("set-cookie")
        if set_cookie_header:
            # Add security flags to cookies
            if "Secure" not in set_cookie_header:
                response.headers["set-cookie"] = f"{set_cookie_header}; Secure"
            if "HttpOnly" not in set_cookie_header:
                response.headers[
                    "set-cookie"
                ] = f"{response.headers['set-cookie']}; HttpOnly"
            if "SameSite" not in set_cookie_header:
                response.headers[
                    "set-cookie"
                ] = f"{response.headers['set-cookie']}; SameSite=Strict"


def create_https_middleware(
    force_https: Optional[bool] = None,
) -> HTTPSSecurityMiddleware:
    """
    Factory function to create HTTPS security middleware with configuration.

    Args:
        force_https: Whether to force HTTPS redirection. If None, determined by environment.

    Returns:
        Configured HTTPSSecurityMiddleware instance
    """
    return HTTPSSecurityMiddleware(None, force_https)
