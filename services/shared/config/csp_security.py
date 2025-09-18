"""
Enhanced Content Security Policy Configuration for Cartrita AI OS
Provides comprehensive CSP with nonce-based inline script protection and violation reporting.
"""

import os
import secrets
from typing import Dict, List, Optional
from .environment import load_env_file


class CSPSecurityConfig:
    """
    Enhanced Content Security Policy configuration with nonce-based protection
    and comprehensive violation reporting for XSS prevention.
    """

    def __init__(self):
        # Load environment variables
        load_env_file()

        # CSP violation reporting endpoint
        self.report_uri = os.getenv("CSP_REPORT_URI", "/api/security/csp-violation")

        # Trusted domains from environment
        self.frontend_urls = self._get_frontend_urls()
        self.api_urls = self._get_api_urls()
        self.websocket_urls = self._get_websocket_urls()

        # Nonce generation for inline scripts
        self.current_nonce = self._generate_nonce()

    def _get_frontend_urls(self) -> List[str]:
        """Get allowed frontend URLs from environment."""
        urls = []

        # Primary frontend URL
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3001")
        urls.append(frontend_url)

        # Production frontend URL
        prod_url = os.getenv("PRODUCTION_FRONTEND_URL")
        if prod_url and prod_url != frontend_url:
            urls.append(prod_url)

        # Development URLs
        dev_urls = [
            "http://localhost:3000",
            "http://localhost:3003",  # Turbopack
            "https://localhost:3001",
            "https://localhost:3000",
        ]

        # Only add dev URLs in development
        if os.getenv("NODE_ENV") != "production":
            urls.extend(dev_urls)

        return list(set(urls))

    def _get_api_urls(self) -> List[str]:
        """Get allowed API URLs from environment."""
        urls = []

        # Primary API URL
        api_url = os.getenv("NEXT_PUBLIC_API_URL", "http://localhost:8000")
        urls.append(api_url)

        # Internal API URLs
        internal_apis = [
            "http://localhost:8000",
            "http://localhost:8001",
            "http://localhost:3001",  # API Gateway
        ]
        urls.extend(internal_apis)

        # External APIs
        external_apis = [
            "https://api.openai.com",
            "https://api.deepgram.com",
            "https://fonts.googleapis.com",
            "https://fonts.gstatic.com",
        ]
        urls.extend(external_apis)

        return list(set(urls))

    def _get_websocket_urls(self) -> List[str]:
        """Get allowed WebSocket URLs."""
        urls = []

        # WebSocket URLs from environment
        ws_url = os.getenv("NEXT_PUBLIC_WS_URL", "ws://localhost:3001")
        urls.append(ws_url)

        # Development WebSocket URLs
        if os.getenv("NODE_ENV") != "production":
            dev_ws_urls = [
                "ws://localhost:8000",
                "wss://localhost:8000",
                "ws://localhost:3001",
                "wss://localhost:3001",
                "ws://localhost:3003",
                "wss://localhost:3003",
            ]
            urls.extend(dev_ws_urls)

        return list(set(urls))

    def _generate_nonce(self) -> str:
        """Generate a cryptographically secure nonce for inline scripts."""
        return secrets.token_urlsafe(16)

    def get_nonce(self, regenerate: bool = False) -> str:
        """Get current nonce, optionally regenerating it."""
        if regenerate:
            self.current_nonce = self._generate_nonce()
        return self.current_nonce

    def get_csp_policy(self, environment: str = "production") -> str:
        """
        Generate comprehensive CSP policy based on environment.

        Args:
            environment: Target environment ("production", "development", "testing")

        Returns:
            Complete CSP policy string
        """
        # Base policy for maximum security
        policy_parts = [
            "default-src 'self'",
            self._get_script_src_policy(environment),
            self._get_style_src_policy(),
            self._get_img_src_policy(),
            self._get_connect_src_policy(),
            self._get_font_src_policy(),
            "object-src 'none'",
            "media-src 'self' blob: data:",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-src 'none'",
            "child-src 'none'",
            "worker-src 'self' blob:",
            "manifest-src 'self'",
        ]

        # Add upgrade-insecure-requests in production
        if environment == "production":
            policy_parts.append("upgrade-insecure-requests")

        # Add report-uri if configured
        if self.report_uri:
            policy_parts.append(f"report-uri {self.report_uri}")

        return "; ".join(policy_parts)

    def _get_script_src_policy(self, environment: str) -> str:
        """Get script-src policy with nonce-based inline protection."""
        sources = ["'self'"]

        # Use nonce for inline scripts in production
        if environment == "production":
            sources.append(f"'nonce-{self.current_nonce}'")
        else:
            # Allow unsafe-inline and unsafe-eval only in development
            sources.extend(["'unsafe-inline'", "'unsafe-eval'"])

        # Add trusted frontend domains
        sources.extend(self.frontend_urls)

        return f"script-src {' '.join(sources)}"

    def _get_style_src_policy(self) -> str:
        """Get style-src policy."""
        sources = [
            "'self'",
            "'unsafe-inline'",
        ]  # Inline styles often needed for dynamic UI
        sources.append("https://fonts.googleapis.com")
        sources.extend(self.frontend_urls)
        return f"style-src {' '.join(sources)}"

    def _get_img_src_policy(self) -> str:
        """Get img-src policy."""
        sources = ["'self'", "data:", "blob:", "https:"]
        return f"img-src {' '.join(sources)}"

    def _get_connect_src_policy(self) -> str:
        """Get connect-src policy including WebSocket URLs."""
        sources = ["'self'"]
        sources.extend(self.api_urls)
        sources.extend(self.websocket_urls)
        sources.extend(["wss:", "https:"])  # Allow secure connections
        return f"connect-src {' '.join(sources)}"

    def _get_font_src_policy(self) -> str:
        """Get font-src policy."""
        sources = [
            "'self'",
            "https://fonts.googleapis.com",
            "https://fonts.gstatic.com",
        ]
        return f"font-src {' '.join(sources)}"

    def get_csp_headers(self, environment: str = "production") -> Dict[str, str]:
        """
        Get comprehensive CSP and related security headers.

        Args:
            environment: Target environment

        Returns:
            Dictionary of security headers
        """
        return {
            "Content-Security-Policy": self.get_csp_policy(environment),
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": (
                "camera=(), microphone=(), geolocation=(), "
                "payment=(), usb=(), interest-cohort=(), "
                "accelerometer=(), gyroscope=(), magnetometer=(), "
                "ambient-light-sensor=(), autoplay=(), "
                "encrypted-media=(), fullscreen=(), picture-in-picture=()"
            ),
            "Cross-Origin-Embedder-Policy": "require-corp",
            "Cross-Origin-Opener-Policy": "same-origin",
            "Cross-Origin-Resource-Policy": "same-origin",
        }

    def is_violation_report_valid(self, report_data: Dict) -> bool:
        """
        Validate CSP violation report to prevent abuse.

        Args:
            report_data: CSP violation report payload

        Returns:
            True if report appears valid
        """
        required_fields = ["csp-report"]
        if not all(field in report_data for field in required_fields):
            return False

        csp_report = report_data.get("csp-report", {})
        report_fields = ["document-uri", "violated-directive", "blocked-uri"]

        return all(field in csp_report for field in report_fields)


def create_csp_config() -> CSPSecurityConfig:
    """
    Factory function to create CSP security configuration.

    Returns:
        Configured CSPSecurityConfig instance
    """
    return CSPSecurityConfig()


# Global instance for reuse
csp_config = create_csp_config()
