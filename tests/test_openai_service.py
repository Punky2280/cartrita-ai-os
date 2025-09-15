import importlib.util
import os
import types
import pytest

MODULE_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    "..",
    "services",
    "ai-orchestrator",
    "cartrita",
    "orchestrator",
    "services",
    "openai_service.py",
))

spec = importlib.util.spec_from_file_location("_openai_service_isolated", MODULE_PATH)
openai_service_module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(openai_service_module)  # type: ignore
OpenAIService = openai_service_module.OpenAIService


class DummySecret:
    def __init__(self, value: str = "test-key"):
        self._v = value

    def get_secret_value(self):
        return self._v


class DummyAISettings:
    openai_api_key = DummySecret("sk-test")
    openai_organization = None
    openai_project = None
    orchestrator_model = "dummy-model"
    temperature = 0.1
    max_tokens = 32
    top_p = 1.0
    frequency_penalty = 0.0
    presence_penalty = 0.0


class DummySettings:
    ai = DummyAISettings()


class MockChatCompletions:
    def __init__(self, responses):
        self._responses = responses

    async def create(self, **kwargs):  # non-streaming path returns an object with choices
        return self._responses[0]


class MockStreamingIterator:
    def __init__(self, chunks):
        self._chunks = chunks

    def __aiter__(self):
        async def gen():
            for c in self._chunks:
                yield c
        return gen()


class MockAsyncClient:
    def __init__(self, streaming_chunks=None, non_stream_response=None, raise_error=False):
        self._streaming_chunks = streaming_chunks or []
        self._non_stream_response = non_stream_response
        self._raise_error = raise_error
        self.chat = types.SimpleNamespace(
            completions=types.SimpleNamespace(
                create=self._create
            )
        )

    async def _create(self, **kwargs):
        if self._raise_error:
            raise RuntimeError("boom")
        stream = kwargs.get("stream", False)
        if stream:
            return MockStreamingIterator(self._streaming_chunks)
        return self._non_stream_response


def _build_choice(content=None, tool_calls=None, finish_reason="stop", delta=False):
    # Minimal objects with attributes accessed in code
    if delta:
        msg = types.SimpleNamespace(content=content, tool_calls=tool_calls)
        choice = types.SimpleNamespace(delta=msg, finish_reason=None)
    else:
        msg = types.SimpleNamespace(content=content, tool_calls=tool_calls)
        choice = types.SimpleNamespace(message=msg, finish_reason=finish_reason)
    return choice


@pytest.mark.asyncio
async def test_openai_service_non_streaming_basic(monkeypatch):
    from cartrita.orchestrator.utils import config as config_mod
    monkeypatch.setattr(config_mod, "settings", DummySettings())
    # Also patch module-level imported settings alias
    monkeypatch.setattr(openai_service_module, "global_settings", DummySettings())

    # Mock client returning one choice with content
    response_obj = types.SimpleNamespace(choices=[_build_choice(content="Hello world")])
    mock_client = MockAsyncClient(non_stream_response=response_obj)
    monkeypatch.setattr(openai_service_module, "AsyncOpenAI", lambda **_: mock_client)

    svc = OpenAIService()
    messages = [{"role": "user", "content": "Hi"}]
    chunks = []
    async for chunk in svc.chat_completion(messages, stream=False):
        chunks.append(chunk)

    assert any(c["type"] == "content" and "Hello" in c["content"] for c in chunks)
    assert any(c["type"] == "done" for c in chunks)


@pytest.mark.asyncio
async def test_openai_service_streaming_with_tool_call(monkeypatch):
    from cartrita.orchestrator.utils import config as config_mod
    monkeypatch.setattr(config_mod, "settings", DummySettings())
    monkeypatch.setattr(openai_service_module, "global_settings", DummySettings())

    # Streaming: first a content delta, then a tool call delta with finish
    tool_call = types.SimpleNamespace(
        id="tc1",
        function=types.SimpleNamespace(name="web_search", arguments="{\"query\": \"python\"}")
    )
    chunk1 = types.SimpleNamespace(choices=[_build_choice(content="Partial", delta=True)])
    # Simulate tool delta
    chunk2 = types.SimpleNamespace(choices=[_build_choice(delta=True, tool_calls=[tool_call])])
    # Final chunk with finish_reason
    final_choice = types.SimpleNamespace(delta=types.SimpleNamespace(content=None, tool_calls=None), finish_reason="stop")
    chunk3 = types.SimpleNamespace(choices=[final_choice])

    mock_client = MockAsyncClient(streaming_chunks=[chunk1, chunk2, chunk3])
    monkeypatch.setattr(openai_service_module, "AsyncOpenAI", lambda **_: mock_client)

    svc = OpenAIService()
    messages = [{"role": "user", "content": "Hi"}]
    emitted = []
    async for chunk in svc.chat_completion(messages, stream=True, tools=[{"name": "web_search"}]):
        emitted.append(chunk)

    # Validate content and tool call presence
    assert any(c["type"] == "content" for c in emitted)
    assert any(c["type"] == "tool_call" for c in emitted)
    assert any(c["type"] == "done" for c in emitted)


@pytest.mark.asyncio
async def test_openai_service_error_path(monkeypatch):
    from cartrita.orchestrator.utils import config as config_mod
    monkeypatch.setattr(config_mod, "settings", DummySettings())
    monkeypatch.setattr(openai_service_module, "global_settings", DummySettings())

    mock_client = MockAsyncClient(raise_error=True)
    monkeypatch.setattr(openai_service_module, "AsyncOpenAI", lambda **_: mock_client)

    svc = OpenAIService()
    messages = [{"role": "user", "content": "Hi"}]
    emitted = []
    async for chunk in svc.chat_completion(messages, stream=False):
        emitted.append(chunk)
    assert any(c["type"] == "error" for c in emitted)
