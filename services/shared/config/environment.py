# Environment Configuration Helper for Cartrita AI OS
# Loads production environment variables with proper fallbacks

"""
Environment configuration helper.
Provides centralized access to environment variables with secure fallbacks.
"""

import os
from pathlib import Path
from typing import Optional


def load_env_file(env_file: str = ".env.production") -> dict:
    """
    Load environment variables from file.

    Args:
        env_file: Path to environment file

    Returns:
        Dictionary of loaded environment variables
    """
    env_vars = {}
    # Try multiple possible paths for .env.production
    possible_paths = [
        Path.cwd() / env_file,  # Current working directory
        Path(__file__).parent.parent.parent / env_file,  # Relative to this file
        Path("/home/robbie/cartrita-ai-os") / env_file,  # Absolute project root
    ]

    env_path = None
    for path in possible_paths:
        if path.exists():
            env_path = path
            break

    if env_path:
        # Simple .env file loader (for production use python-dotenv)
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    if not os.getenv(key):
                        os.environ[key] = value
                    env_vars[key] = value
    return env_vars


def get_api_key(key_name: Optional[str] = None) -> str:
    """
    Get API key from environment with secure fallbacks.

    Args:
        key_name: Specific API key name to retrieve

    Returns:
        API key value

    Raises:
        ValueError: If no valid API key is found
    """
    # Load environment if not already loaded
    if not os.getenv("DEV_API_KEY"):
        load_env_file()

    if key_name:
        value = os.getenv(key_name)
        if value:
            return value

    # Try common API key environment variables
    api_keys = ["DEV_API_KEY", "API_KEY_SECRET", "CARTRITA_API_KEY", "BACKEND_API_KEY"]

    for key in api_keys:
        value = os.getenv(key)
        if value:
            return value

    raise ValueError("No valid API key found in environment")


def get_database_url() -> str:
    """Get database URL from environment."""
    if not os.getenv("DATABASE_URL"):
        load_env_file()

    return os.getenv("DATABASE_URL") or "postgresql://localhost:5432/cartrita_db"


def get_redis_url() -> str:
    """Get Redis URL from environment."""
    if not os.getenv("REDIS_URL"):
        load_env_file()

    return os.getenv("REDIS_URL") or "redis://localhost:6379"


def get_jwt_secret() -> str:
    """Get JWT secret from environment."""
    if not os.getenv("JWT_SECRET"):
        load_env_file()

    return (
        os.getenv("JWT_SECRET")
        or os.getenv("JWT_SECRET_KEY")
        or "fallback_jwt_secret_change_in_production"
    )


def get_openai_api_key() -> str:
    """Get OpenAI API key from environment."""
    if not os.getenv("OPENAI_API_KEY"):
        load_env_file()

    return os.getenv("OPENAI_API_KEY") or ""


def get_deepgram_api_key() -> str:
    """Get Deepgram API key from environment."""
    if not os.getenv("DEEPGRAM_API_KEY"):
        load_env_file()

    return os.getenv("DEEPGRAM_API_KEY") or ""


# Load environment variables when module is imported
load_env_file()
