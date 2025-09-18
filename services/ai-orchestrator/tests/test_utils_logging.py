"""
Tests for utilities modules without LangChain dependencies.
"""

import pytest

from cartrita.orchestrator.utils.logger import get_logger


def test_get_logger():
    """Test get_logger functionality."""
    logger = get_logger("test_component")
    assert logger is not None
    # Test logger has basic methods
    assert hasattr(logger, "info")
    assert hasattr(logger, "error")
    assert hasattr(logger, "debug")
    assert hasattr(logger, "warning")


def test_multiple_loggers():
    """Test creating multiple logger instances."""
    logger1 = get_logger("component1")
    logger2 = get_logger("component2")
    assert logger1 is not None
    assert logger2 is not None
    # Different loggers should have different names or contexts
    # Just verify they're both valid loggers
    assert hasattr(logger1, "info")
    assert hasattr(logger2, "info")


def test_logger_methods():
    """Test that logger has expected methods."""
    logger = get_logger("test_methods")

    # Test basic logging methods exist
    methods = ["debug", "info", "warning", "error", "critical"]
    for method in methods:
        assert hasattr(logger, method)
        assert callable(getattr(logger, method))


def test_logger_usage():
    """Test basic logger usage without errors."""
    logger = get_logger("test_usage")

    # These should not raise errors
    try:
        logger.info("Test info message")
        logger.debug("Test debug message")
        logger.error("Test error message")
        success = True
    except Exception:
        success = False

    assert success


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
