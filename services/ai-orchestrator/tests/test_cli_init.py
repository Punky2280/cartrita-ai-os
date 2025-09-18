"""
Tests for CLI package initialization and constants.
Simple module testing CLI package metadata without external dependencies.
"""

from cartrita.cli import main


class TestCLIInit:
    """Test CLI package initialization."""

    def test_main_function_exists(self):
        """Test that main function is properly exported."""
        assert main is not None
        assert callable(main)

    def test_main_function_callable(self):
        """Test that main function is callable."""
        assert hasattr(main, "__call__")

    def test_main_function_has_name(self):
        """Test that main function has proper name."""
        assert hasattr(main, "__name__")
        assert main.__name__ == "main"

    def test_all_export(self):
        """Test __all__ export contains main."""
        from cartrita.cli import __all__

        assert isinstance(__all__, list)
        assert "main" in __all__
        assert len(__all__) == 1
