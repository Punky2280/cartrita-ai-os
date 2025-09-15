import os
import pytest
import importlib

os.environ.setdefault("CARTRITA_DISABLE_DB", "1")


@pytest.mark.anyio("asyncio")
async def test_fallback_provider_rule_based_path(monkeypatch):
    mod = importlib.import_module("cartrita.orchestrator.providers.fallback_provider")

    # Force openai client absence & transformers absence
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setattr(mod, "LANGCHAIN_AVAILABLE", False, raising=False)
    monkeypatch.setattr(mod, "TRANSFORMERS_AVAILABLE", False, raising=False)

    provider_cls = getattr(mod, "FallbackProvider")
    provider = provider_cls()

    # Sanity: ensure openai & hf disabled
    assert provider.openai_client is None
    assert provider.hf_provider is None

    result = await provider.generate_response("Hello there")
    assert result["metadata"]["provider_used"] in {"rule_based_fsm", "emergency_template"}
    assert result["metadata"]["fallback_level"] >= 3
    assert isinstance(result["response"], str) and len(result["response"]) > 0
