"""
CORS Security Configuration Helper for Cartrita AI OS.
Provides centralized CORS origin validation with environment-based configuration.
"""

import os
from typing import List, Optional
from .environment import load_env_file


class CORSSecurityConfig:
    """
    Secure CORS configuration helper that validates origins against allowlists.
    Replaces wildcard '*' origins with specific trusted domains.
    """

    def __init__(self):
        # Load environment variables
        load_env_file()

        # Default allowed origins for development
        self.default_origins = [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:3003",  # Turbopack dev server
        ]

        # Get production origins from environment
        allowed_origins_str = os.getenv("ALLOWED_ORIGINS", "")
        production_origins = [
            origin.strip()
            for origin in allowed_origins_str.split(",")
            if origin.strip()
        ]

        # Combine development and production origins
        self.allowed_origins = list(set(self.default_origins + production_origins))

        # Additional specific environment URLs
        frontend_url = os.getenv("FRONTEND_URL")
        if frontend_url and frontend_url not in self.allowed_origins:
            self.allowed_origins.append(frontend_url)

        production_frontend_url = os.getenv("PRODUCTION_FRONTEND_URL")
        if (
            production_frontend_url
            and production_frontend_url not in self.allowed_origins
        ):
            self.allowed_origins.append(production_frontend_url)

    def is_origin_allowed(self, origin: Optional[str]) -> bool:
        """
        Validate if an origin is in the allowlist.

        Args:
            origin: The origin to validate (can be None for same-origin requests)

        Returns:
            True if origin is allowed, False otherwise
        """
        if origin is None:
            # Same-origin requests have no origin header
            return True

        return origin in self.allowed_origins

    def get_allowed_origins(self) -> List[str]:
        """Get the list of allowed origins."""
        return self.allowed_origins.copy()

    def get_cors_headers(self, request_origin: Optional[str] = None) -> dict:
        """
        Generate secure CORS headers based on request origin.

        Args:
            request_origin: The origin from the request

        Returns:
            Dictionary of CORS headers
        """
        headers = {
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-API-Key, X-Request-ID",
            "Access-Control-Max-Age": "86400",  # 24 hours
            "Vary": "Origin",
        }

        if self.is_origin_allowed(request_origin):
            headers["Access-Control-Allow-Origin"] = request_origin or "null"
            headers["Access-Control-Allow-Credentials"] = "true"
        else:
            # Explicitly deny unauthorized origins
            headers["Access-Control-Allow-Origin"] = "null"
            headers["Access-Control-Allow-Credentials"] = "false"

        return headers


# Global instance
cors_config = CORSSecurityConfig()
