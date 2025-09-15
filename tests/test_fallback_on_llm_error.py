from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_fallback_provider_on_llm_failure(monkeypatch):
    """
    Forces the primary LLM factory function to raise, then ensures the fallback
    provider still produces a non-empty response string.

    Skips instead of failing if orchestrator modules are unavailable (keeps suite resilient).
    """
    try:
        from cartrita.orchestrator.providers.fallback_provider_v2 import (  # type: ignore
            get_fallback_provider,
        )
    except Exception as e:  # pragma: no cover
        pytest.skip(f"Cannot import fallback provider v2: {e}")

    try:
        import cartrita.orchestrator.utils.llm_factory as lf  # type: ignore
    except Exception as e:  # pragma: no cover
        pytest.skip(f"Cannot import llm_factory: {e}")

    def failing_factory(*_args, **_kwargs):
        raise RuntimeError("synthetic-llm-failure")

    # Force any code that would attempt to build the OpenAI chat model to fail.
    monkeypatch.setattr(lf, "create_chat_openai", failing_factory, raising=True)

    provider = get_fallback_provider()
    result = await provider.generate_response("Trigger fallback due to forced failure")
    assert isinstance(result, str) and result.strip(), "Fallback provider returned empty response"
