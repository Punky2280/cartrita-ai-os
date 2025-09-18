"""
Simple coverage test for config module without LangChain dependencies.
"""

import pytest

from cartrita.orchestrator.utils.config import Settings, get_settings


def test_config_loading():
    """Test basic config loading."""
    settings = get_settings()
    assert isinstance(settings, Settings)
    assert settings.app_name == "Cartrita AI OS"


def test_database_settings():
    """Test database configuration."""
    settings = get_settings()
    db_config = settings.database
    assert db_config.host == "localhost"
    assert db_config.port == 5432
    assert db_config.pool_size >= 1


def test_security_settings():
    """Test security configuration."""
    settings = get_settings()
    security_config = settings.security
    assert security_config.secret_key is not None
    assert security_config.jwt_algorithm in ["HS256", "RS256"]


def test_ai_settings():
    """Test AI configuration."""
    settings = get_settings()
    ai_config = settings.ai
    assert hasattr(ai_config, "openai_api_key")
    assert ai_config.orchestrator_model is not None


def test_monitoring_settings():
    """Test monitoring configuration."""
    settings = get_settings()
    monitoring_config = settings.monitoring
    assert monitoring_config.otel_service_name == "cartrita-ai-orchestrator"
    assert monitoring_config.log_level in ["DEBUG", "INFO", "WARNING", "ERROR"]


def test_settings_fields():
    """Test settings fields."""
    settings = get_settings()
    assert settings.app_name == "Cartrita AI OS"
    assert settings.environment in ["development", "production", "testing"]
    assert settings.host is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
