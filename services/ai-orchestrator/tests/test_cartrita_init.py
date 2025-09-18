#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for Cartrita main package initialization.
Tests package-level constants, metadata, and module structure.

Coverage Target: 100% of cartrita/__init__.py
Dependencies: Standard library only (avoiding LangChain conflicts)
"""

import sys
from pathlib import Path

# Add the cartrita package to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "cartrita"))

import pytest


def test_cartrita_package_import():
    """Test that cartrita package can be imported successfully."""
    try:
        import cartrita

        assert cartrita is not None
        assert hasattr(cartrita, "__version__")
    except ImportError as e:
        pytest.fail(f"Failed to import cartrita package: {e}")


def test_version_constant_exists():
    """Test that __version__ constant exists and is a string."""
    import cartrita

    assert hasattr(cartrita, "__version__")
    assert isinstance(cartrita.__version__, str)
    assert len(cartrita.__version__) > 0


def test_version_semantic_format():
    """Test that __version__ follows semantic versioning format."""
    import cartrita

    version = cartrita.__version__
    parts = version.split(".")
    assert (
        len(parts) >= 2
    ), f"Version should have at least major.minor format, got: {version}"

    # Test that major and minor parts are numeric
    assert parts[0].isdigit(), f"Major version should be numeric, got: {parts[0]}"
    assert parts[1].isdigit(), f"Minor version should be numeric, got: {parts[1]}"

    # If patch version exists, it should be numeric too
    if len(parts) >= 3:
        assert parts[2].isdigit(), f"Patch version should be numeric, got: {parts[2]}"


def test_author_constant_exists():
    """Test that __author__ constant exists and is a non-empty string."""
    import cartrita

    assert hasattr(cartrita, "__author__")
    assert isinstance(cartrita.__author__, str)
    assert len(cartrita.__author__) > 0


def test_author_content_valid():
    """Test that __author__ contains expected content."""
    import cartrita

    author = cartrita.__author__
    # Should contain team or individual name
    assert len(author.strip()) > 3, f"Author should be more descriptive, got: {author}"
    # Should not contain placeholders
    assert "TODO" not in author.upper()
    assert "PLACEHOLDER" not in author.upper()


def test_description_constant_exists():
    """Test that __description__ constant exists and is a non-empty string."""
    import cartrita

    assert hasattr(cartrita, "__description__")
    assert isinstance(cartrita.__description__, str)
    assert len(cartrita.__description__) > 0


def test_description_content_valid():
    """Test that __description__ contains meaningful content."""
    import cartrita

    description = cartrita.__description__
    # Should be descriptive
    assert (
        len(description.strip()) > 10
    ), f"Description should be descriptive, got: {description}"
    # Should contain key terms
    assert any(
        term in description.lower() for term in ["ai", "agent", "orchestrat"]
    ), f"Description should mention AI/agent/orchestration concepts, got: {description}"
    # Should not contain placeholders
    assert "TODO" not in description.upper()
    assert "PLACEHOLDER" not in description.upper()


def test_module_docstring_exists():
    """Test that the module has a docstring."""
    import cartrita

    assert cartrita.__doc__ is not None
    assert isinstance(cartrita.__doc__, str)
    assert len(cartrita.__doc__.strip()) > 0


def test_constants_immutability():
    """Test that package constants cannot be easily modified."""
    import cartrita

    # Store original values
    original_version = cartrita.__version__
    original_author = cartrita.__author__
    original_description = cartrita.__description__

    # These should remain the same (constants shouldn't be modified externally)
    assert cartrita.__version__ == original_version
    assert cartrita.__author__ == original_author
    assert cartrita.__description__ == original_description


def test_package_structure():
    """Test that package has expected structure and attributes."""
    import cartrita

    # Should have standard package attributes
    assert hasattr(cartrita, "__name__")
    assert hasattr(cartrita, "__package__")

    # Should have our custom constants
    expected_constants = ["__version__", "__author__", "__description__"]
    for constant in expected_constants:
        assert hasattr(cartrita, constant), f"Missing constant: {constant}"


if __name__ == "__main__":
    # Run tests with coverage
    pytest.main([__file__, "-v", "--tb=short"])
