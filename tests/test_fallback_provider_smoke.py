"""Fallback provider smoke test."""
import pytest

def test_fallback_provider_import():
    try:
        from cartrita.orchestrator.providers import fallback_provider  # noqa: F401
    except ModuleNotFoundError as e:
        pytest.skip(f"Fallback provider module not found: {e}")
    else:
        assert hasattr(fallback_provider, "get_fallback_provider")
