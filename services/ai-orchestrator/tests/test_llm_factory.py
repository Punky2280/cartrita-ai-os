from cartrita.orchestrator.utils.llm_factory import create_chat_openai

# We avoid importing real network; we only introspect constructed object.


def test_create_chat_openai_maps_max_completion_tokens(monkeypatch):
    captured_kwargs = {}

    def fake_init(self, **kwargs):  # type: ignore
        captured_kwargs.update(kwargs)

    # Patch ChatOpenAI __init__
    from langchain_openai import ChatOpenAI

    monkeypatch.setattr(ChatOpenAI, "__init__", fake_init, raising=True)

    test_api_key = "sk-test"  # Mock API key for testing only
    create_chat_openai(
        model="gpt-test",
        max_completion_tokens=1234,
        temperature=0.55,
        openai_api_key=test_api_key,
    )
    # Object constructed; attributes may not exist; focus on kwargs capture.
    assert "max_tokens" in captured_kwargs, captured_kwargs
    assert "max_completion_tokens" not in captured_kwargs, captured_kwargs
    assert captured_kwargs["max_tokens"] == 1234
    assert captured_kwargs["temperature"] == 0.55
    assert captured_kwargs["model"] == "gpt-test"
    assert captured_kwargs["openai_api_key"] == test_api_key


def test_create_chat_openai_default_max_tokens(monkeypatch):
    captured_kwargs = {}

    def fake_init(self, **kwargs):  # type: ignore
        captured_kwargs.update(kwargs)

    from langchain_openai import ChatOpenAI

    monkeypatch.setattr(ChatOpenAI, "__init__", fake_init, raising=True)

    test_api_key_2 = "sk-test-2"  # Mock API key for testing only
    create_chat_openai(
        model="gpt-test-2", temperature=0.1, openai_api_key=test_api_key_2
    )
    assert captured_kwargs["max_tokens"] == 4096  # default path
    assert "max_completion_tokens" not in captured_kwargs
