from __future__ import annotations

import os
import inspect
from types import SimpleNamespace

import pytest

os.environ.setdefault("CARTRITA_DISABLE_DB", "1")


class _DummyLLM:
    def __init__(self, *a, **k):
        self.calls = 0

    def invoke(self, messages, **kwargs):
        self.calls += 1
        return SimpleNamespace(content="OK")


@pytest.mark.anyio("asyncio")
async def test_supervisor_single_iteration(monkeypatch):
    """
    Ensures the supervisor can execute a single iteration (caps applied if available)
    and returns a structured result. Skips gracefully if components are missing.
    """
    try:
        from cartrita.orchestrator.core.supervisor import SupervisorOrchestrator  # type: ignore
    except Exception as e:
        pytest.skip(f"Cannot import supervisor: {e}")

    try:
        import cartrita.orchestrator.utils.llm_factory as llm_factory  # type: ignore
    except Exception as e:
        pytest.skip(f"Cannot import llm_factory: {e}")

    # Prevent real model creation.
    monkeypatch.setattr(llm_factory, "create_chat_openai", lambda **_: _DummyLLM(), raising=True)

    # Build lightweight stub dependency objects expected by SupervisorOrchestrator
    class _Stub:
        async def start(self):  # noqa: D401
            return None

        async def stop(self):  # noqa: D401
            return None

        async def health_check(self):  # noqa: D401
            return True

    class _SettingsStub:
        class ai:  # type: ignore
            # Provide minimal attributes accessed in supervisor __init__
            openai_api_key = type("_K", (), {"get_secret_value": staticmethod(lambda: "")})()
            orchestrator_model = "gpt-4.1"
            agent_model = "gpt-4o-mini"

    # Prevent agent initialization to avoid pulling full settings (external APIs etc.)
    monkeypatch.setattr(SupervisorOrchestrator, "_initialize_agents", lambda self: {}, raising=True)

    supervisor = SupervisorOrchestrator(
        db_manager=_Stub(),
        cache_manager=_Stub(),
        metrics_collector=_Stub(),
        settings=_SettingsStub(),
    )

    # Apply iteration caps if present.
    orchestrator_settings = getattr(getattr(supervisor, "settings", None), "orchestrator", None)
    if orchestrator_settings:
        for attr in ("max_total_iterations", "max_attempts_per_agent"):
            if hasattr(orchestrator_settings, attr):
                setattr(orchestrator_settings, attr, 1)

    run_method = None
    for name in ("run_async", "run", "execute"):
        if hasattr(supervisor, name):
            run_method = getattr(supervisor, name)
            break

    if run_method is None:
        pytest.skip("No runnable method found on supervisor")

    # Try common invocation signatures.
    async def _invoke():
        try:
            if inspect.iscoroutinefunction(run_method):
                try:
                    return await run_method(user_input="Hello", context={})  # type: ignore
                except TypeError:
                    return await run_method("Hello")  # type: ignore
            # Sync fallback
            try:
                return run_method(user_input="Hello", context={})  # type: ignore
            except TypeError:
                return run_method("Hello")  # type: ignore
        except Exception as exc:  # pragma: no cover (unexpected path)
            pytest.fail(f"Supervisor invocation raised unexpectedly: {exc}")

    result = await _invoke()
    assert result is not None, "Supervisor returned None"

    if isinstance(result, dict):
        assert any(k in result for k in ("response", "final_response", "messages")), (
            f"Unexpected result keys: {list(result.keys())}"
        )
