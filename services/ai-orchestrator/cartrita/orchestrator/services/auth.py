# Cartrita AI OS - Authentication Service
# Basic API key authentication for development

"""
Authentication service for Cartrita AI OS.
Provides basic API key validation for development and testing.
"""

import os

from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

# Try to import shared environment configuration
try:
    from services.shared.config.environment import get_api_key as get_env_api_key
except ImportError:
    # Fallback if shared module not available
    def get_env_api_key():
        return (
            os.getenv("DEV_API_KEY")
            or os.getenv("CARTRITA_API_KEY")
            or os.getenv("API_KEY_SECRET")
        )


# API Key security scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: str | None = Depends(api_key_header),
) -> str:
    """
    Verify API key for authentication.

    Args:
        api_key: The API key from the request header

    Returns:
        The validated API key

    Raises:
        HTTPException: If API key is invalid or missing
    """
    # Get expected API key from environment - prioritize production keys
    try:
        expected_key = get_env_api_key()
    except ValueError:
        expected_key = None

    if not expected_key:
        raise HTTPException(
            status_code=500, detail="Server configuration error: No API key configured"
        )

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required",
            headers={"WWW-Authenticate": "APIKey"},
        )

    if api_key != expected_key:
        raise HTTPException(status_code=403, detail="Invalid API key")

    return api_key


def get_api_key() -> str:
    """Get the current API key from environment."""
    try:
        return get_env_api_key()
    except ValueError:
        return "dev-api-key-fallback"
