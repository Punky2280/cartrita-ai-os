import importlib


def test_get_settings_singleton_and_defaults():
    config_mod = importlib.import_module("cartrita.orchestrator.utils.config")

    # Ensure global is cleared for test isolation if previously set
    if getattr(config_mod, 'settings', None) is not None:
        # Reset to force fresh load
        config_mod.settings = None  # type: ignore

    first = config_mod.get_settings()
    second = config_mod.get_settings()

    assert first is second, "get_settings() must return singleton instance"

    # Spot check representative default values from nested settings
    ai = first.ai
    assert ai.orchestrator_model == "gpt-4.1-mini"
    assert ai.embedding_model == "text-embedding-3-small"
    assert ai.max_tokens == 4096
    assert ai.temperature == 0.7

    # Security defaults
    sec = first.security
    assert sec.jwt_algorithm == "HS256"
    assert 300 <= sec.jwt_expiration <= 86400

    # Monitoring defaults
    mon = first.monitoring
    assert mon.prometheus_enabled is True
    assert mon.prometheus_port == 8001

    # Feature flags
    assert first.computer_use_enabled is True
    assert first.computer_use_safety_mode == "strict"

    # Ensure directories exist (created by validator)
    assert first.logs_dir.exists()
    assert first.uploads_dir.exists()
    assert first.temp_dir.exists()
