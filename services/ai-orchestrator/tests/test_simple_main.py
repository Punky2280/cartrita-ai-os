#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for simple_main.py
Tests simple API key verification and basic FastAPI functionality.

Coverage Target: Basic functions in simple_main.py without complex imports
Dependencies: Standard library + FastAPI (already in use)
"""

import os
import sys
from pathlib import Path

# Add the orchestrator directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio

import pytest


@pytest.fixture(scope="function")
def clean_env():
    """Clean environment fixture to avoid interference between tests."""
    original_env = os.environ.get("CARTRITA_API_KEY")
    yield
    # Restore original environment
    if original_env is not None:
        os.environ["CARTRITA_API_KEY"] = original_env
    elif "CARTRITA_API_KEY" in os.environ:
        del os.environ["CARTRITA_API_KEY"]


class TestSimpleMainBasicFunctions:
    """Test simple functions from simple_main.py that don't require complex imports."""

    def test_simple_main_import(self):
        """Test that simple_main can be imported."""
        try:
            import simple_main

            assert simple_main is not None
        except ImportError as e:
            pytest.fail(f"Failed to import simple_main: {e}")

    @pytest.mark.asyncio
    async def test_verify_api_key_default_development(self, clean_env):
        """Test verify_api_key returns development key when no env var set."""
        # Clear environment variable
        if "CARTRITA_API_KEY" in os.environ:
            del os.environ["CARTRITA_API_KEY"]

        from simple_main import verify_api_key

        # Should return dev key for any invalid input
        result = await verify_api_key("wrong-key")
        assert result == "dev-api-key-2025"

    @pytest.mark.asyncio
    async def test_verify_api_key_with_none(self, clean_env):
        """Test verify_api_key with None input."""
        # Clear environment variable
        if "CARTRITA_API_KEY" in os.environ:
            del os.environ["CARTRITA_API_KEY"]

        from simple_main import verify_api_key

        result = await verify_api_key(None)
        assert result == "dev-api-key-2025"

    @pytest.mark.asyncio
    async def test_verify_api_key_with_env_var_match(self, clean_env):
        """Test verify_api_key when provided key matches environment."""
        # Set environment variable
        test_key = "test-api-key-12345"
        os.environ["CARTRITA_API_KEY"] = test_key

        from simple_main import verify_api_key

        # Should return the provided key when it matches
        result = await verify_api_key(test_key)
        assert result == test_key

    @pytest.mark.asyncio
    async def test_verify_api_key_with_env_var_no_match(self, clean_env):
        """Test verify_api_key when provided key doesn't match environment."""
        # Set environment variable
        os.environ["CARTRITA_API_KEY"] = "correct-key"

        from simple_main import verify_api_key

        # Should return dev key when provided key doesn't match
        result = await verify_api_key("wrong-key")
        assert result == "dev-api-key-2025"

    @pytest.mark.asyncio
    async def test_verify_api_key_default_env_value(self, clean_env):
        """Test verify_api_key uses default when no env var set."""
        # Clear environment variable
        if "CARTRITA_API_KEY" in os.environ:
            del os.environ["CARTRITA_API_KEY"]

        from simple_main import verify_api_key

        # Should work with the default dev key
        result = await verify_api_key("dev-api-key-2025")
        assert result == "dev-api-key-2025"

    def test_simple_main_has_expected_imports(self):
        """Test that simple_main has expected imports and structure."""
        import simple_main

        # Should have the verify_api_key function
        assert hasattr(simple_main, "verify_api_key")
        assert callable(simple_main.verify_api_key)

        # Should have standard imports
        assert hasattr(simple_main, "json")
        assert hasattr(simple_main, "os")
        assert hasattr(simple_main, "time")

    def test_simple_main_has_docstring(self):
        """Test that simple_main module has a docstring."""
        import simple_main

        assert simple_main.__doc__ is not None
        assert isinstance(simple_main.__doc__, str)
        assert len(simple_main.__doc__.strip()) > 0
        assert "FastAPI" in simple_main.__doc__

    @pytest.mark.asyncio
    async def test_verify_api_key_function_signature(self):
        """Test that verify_api_key has correct function signature."""
        import inspect

        from simple_main import verify_api_key

        # Should be an async function
        assert asyncio.iscoroutinefunction(verify_api_key)

        # Check parameter signature
        sig = inspect.signature(verify_api_key)
        assert "api_key" in sig.parameters

        # Should have Optional[str] parameter with default None
        param = sig.parameters["api_key"]
        assert param.default is None

    def test_simple_main_constants_and_structure(self):
        """Test basic module structure and expected constants."""
        import simple_main

        # Should have load_dotenv call (import should work)
        assert hasattr(simple_main, "load_dotenv")

        # Should have FastAPI imports
        assert hasattr(simple_main, "FastAPI")
        assert hasattr(simple_main, "HTTPException")


if __name__ == "__main__":
    # Run tests with coverage
    pytest.main([__file__, "-v", "--tb=short"])
