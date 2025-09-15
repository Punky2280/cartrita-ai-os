import pytest
import types
from cartrita.orchestrator.services.openai_service import OpenAIService

@pytest.mark.asyncio
async def test_openai_service_streaming_content_and_tool(monkeypatch):
    # Patch config
    from cartrita.orchestrator.utils import config as config_mod
    class DummySecret:
        def get_secret_value(self):
            return "sk-test"
    class DummyAI:
        openai_api_key = DummySecret()
        openai_organization = None
        openai_project = None
        orchestrator_model = "dummy-model"
        temperature = 0.1
        max_tokens = 32
        top_p = 1.0
        frequency_penalty = 0.0
        presence_penalty = 0.0
    class DummySettings:
        ai = DummyAI()
    monkeypatch.setattr(config_mod, "settings", DummySettings())
    import cartrita.orchestrator.services.openai_service as openai_service_module
    monkeypatch.setattr(openai_service_module, "global_settings", DummySettings())

    # Streaming: content, then tool_call, then done
    tool_call = types.SimpleNamespace(
        id="tc1",
        function=types.SimpleNamespace(name="web_search", arguments="{\"query\": \"python\"}")
    )
    chunk1 = types.SimpleNamespace(choices=[types.SimpleNamespace(delta=types.SimpleNamespace(content="Partial", tool_calls=None), finish_reason=None)])
    chunk2 = types.SimpleNamespace(choices=[types.SimpleNamespace(delta=types.SimpleNamespace(content=None, tool_calls=[tool_call]), finish_reason=None)])
    chunk3 = types.SimpleNamespace(choices=[types.SimpleNamespace(delta=types.SimpleNamespace(content=None, tool_calls=None), finish_reason="stop")])
    class MockStreamingIterator:
        def __init__(self, chunks):
            self._chunks = chunks
        def __aiter__(self):
            async def gen():
                for c in self._chunks:
                    yield c
            return gen()
    class MockAsyncClient:
        def __init__(self):
            self.chat = types.SimpleNamespace(
                completions=types.SimpleNamespace(
                    create=self._create
                )
            )

        async def _create(self, **_):
            return MockStreamingIterator([chunk1, chunk2, chunk3])
    monkeypatch.setattr(openai_service_module, "AsyncOpenAI", lambda **_: MockAsyncClient())
    svc = OpenAIService()
    messages = [{"role": "user", "content": "Hi"}]
    emitted = []
    async for chunk in svc.chat_completion(messages, stream=True, tools=[{"name": "web_search"}]):
        emitted.append(chunk)
    assert any(c["type"] == "content" for c in emitted)
    assert any(c["type"] == "tool_call" for c in emitted)
    assert any(c["type"] == "done" for c in emitted)
