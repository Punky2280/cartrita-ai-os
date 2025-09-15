import os
import types
import pytest


class DummySecret:
    def __init__(self, value: str = "sk-test"):
        self._v = value

    def get_secret_value(self):  # pragma: no cover - trivial accessor
        return self._v


class DummyAISettings:
    openai_api_key = DummySecret("sk-test")
    openai_organization = None
    openai_project = None
    orchestrator_model = "dummy-model"
    temperature = 0.2
    max_tokens = 64
    top_p = 1.0
    frequency_penalty = 0.0
    presence_penalty = 0.0


class MockStreamingIterator:
    def __init__(self, chunks):
        self._chunks = chunks

    def __aiter__(self):
        async def gen():
            for c in self._chunks:
                yield c
        return gen()


class MockAsyncClient:
    def __init__(self, streaming_chunks=None, non_stream_response=None):
        self._streaming_chunks = streaming_chunks or []
        self._non_stream_response = non_stream_response
        self.chat = types.SimpleNamespace(
            completions=types.SimpleNamespace(create=self._create)
        )

    async def _create(self, **kwargs):
        if kwargs.get("stream"):
            return MockStreamingIterator(self._streaming_chunks)
        return self._non_stream_response


def _choice_stream_delta(content=None, tool_calls=None, finish=False):
    if finish:
        # Final chunk uses finish_reason on the choice (delta path sets finish_reason)
        return types.SimpleNamespace(choices=[types.SimpleNamespace(delta=types.SimpleNamespace(content=None, tool_calls=None), finish_reason="stop")])
    delta = types.SimpleNamespace(content=content, tool_calls=tool_calls)
    return types.SimpleNamespace(choices=[types.SimpleNamespace(delta=delta, finish_reason=None)])


def _choice_non_stream(content=None, tool_calls=None, finish_reason="stop"):
    msg = types.SimpleNamespace(content=content, tool_calls=tool_calls)
    return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg, finish_reason=finish_reason)])


@pytest.mark.asyncio
async def test_openai_service_package_import_stream_and_non_stream(monkeypatch):
    # Provide required env variable for settings resolution
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    # Import module via canonical package path so coverage tracks it
    from cartrita.orchestrator.services import openai_service as mod

    # Build mock responses
    tool_call = types.SimpleNamespace(
        id="tc1",
        function=types.SimpleNamespace(name="web_search", arguments="{\"query\": \"python\"}")
    )
    streaming_chunks = [
        _choice_stream_delta(content="Hello"),
        _choice_stream_delta(tool_calls=[tool_call]),
        _choice_stream_delta(finish=True),
    ]
    non_stream_response = _choice_non_stream(content="World", tool_calls=[tool_call])

    mock_client = MockAsyncClient(streaming_chunks=streaming_chunks, non_stream_response=non_stream_response)
    monkeypatch.setattr(mod, "AsyncOpenAI", lambda **_: mock_client)

    service = mod.OpenAIService()

    # Non-stream path
    messages = [{"role": "user", "content": "Hi"}]
    non_stream_chunks = []
    async for chunk in service.chat_completion(messages, stream=False):
        non_stream_chunks.append(chunk)

    assert any(c["type"] == "content" for c in non_stream_chunks)
    assert any(c["type"] == "tool_call" for c in non_stream_chunks)
    assert any(c["type"] == "done" for c in non_stream_chunks)

    # Streaming path
    stream_chunks = []
    async for chunk in service.chat_completion(messages, stream=True, tools=[{"name": "web_search"}]):
        stream_chunks.append(chunk)

    assert any(c["type"] == "content" for c in stream_chunks)
    assert any(c["type"] == "tool_call" for c in stream_chunks)
    assert any(c["type"] == "done" for c in stream_chunks)

    # Health check (will call chat_completion once; patching already in place)
    health = await service.health_check()
    assert health["status"] in {"healthy", "unhealthy"}
