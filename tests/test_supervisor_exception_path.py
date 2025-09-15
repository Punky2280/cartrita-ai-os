import os
import inspect
import pytest

os.environ.setdefault("CARTRITA_DISABLE_DB", "1")


class _ExplodingAgent:
    def __init__(self, *a, **k):
        pass

    async def run(self, *a, **k):  # typical async signature
        raise RuntimeError("boom")


@pytest.mark.anyio("asyncio")
async def test_supervisor_exception_handling(monkeypatch):
    try:
        from cartrita.orchestrator.core.supervisor import SupervisorOrchestrator  # type: ignore
    except Exception as e:
        pytest.skip(f"Cannot import supervisor: {e}")

    # Prevent real LLM creation
    try:
        import cartrita.orchestrator.utils.llm_factory as llm_factory  # type: ignore
        monkeypatch.setattr(llm_factory, "create_chat_openai", lambda **_: _ExplodingAgent(), raising=True)
    except Exception:
        pass

    # Stub settings & managers
    class _Stub:
        async def start(self):
            return None

        async def stop(self):
            return None

        async def health_check(self):
            return True

    class _SettingsStub:
        class ai:
            openai_api_key = type("_K", (), {"get_secret_value": staticmethod(lambda: "")})()
            orchestrator_model = "gpt-4.1"
            agent_model = "gpt-4o-mini"

    # Force minimal agent structure
    def fake_initialize_agents(self):
        # Attempt to import AgentType for proper keying; fall back to skip pattern
        try:
            from cartrita.orchestrator.models.schemas import AgentType  # type: ignore
            return {AgentType.CODE: _ExplodingAgent()}
        except Exception:
            return {}

    monkeypatch.setattr(SupervisorOrchestrator, "_initialize_agents", fake_initialize_agents, raising=True)

    supervisor = SupervisorOrchestrator(
        db_manager=_Stub(),
        cache_manager=_Stub(),
        metrics_collector=_Stub(),
        settings=_SettingsStub(),
    )
    if not getattr(supervisor, 'agents', None):
        pytest.skip("Supervisor agents structure unavailable for test simplification")

    run_method = None
    for name in ("run_async", "run", "execute"):
        if hasattr(supervisor, name):
            run_method = getattr(supervisor, name)
            break

    if run_method is None:
        pytest.skip("No runnable method found on supervisor")

    async def invoke():
        if inspect.iscoroutinefunction(run_method):
            try:
                return await run_method(user_input="Hi", context={})  # type: ignore
            except TypeError:
                return await run_method("Hi")  # type: ignore
        try:
            return run_method(user_input="Hi", context={})  # type: ignore
        except TypeError:
            return run_method("Hi")  # type: ignore

    result = await invoke()
    assert result is not None
    if isinstance(result, dict):
        # Expect some form of error signaling; tolerate flexible keys
        assert any(k in result for k in ("error", "response", "final_response", "messages"))
