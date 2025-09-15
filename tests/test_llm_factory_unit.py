import importlib

llm_factory_mod = importlib.import_module("cartrita.orchestrator.utils.llm_factory")
create_chat_openai = llm_factory_mod.create_chat_openai


def test_llm_factory_basic_model_alias_normalization(monkeypatch):
    calls = {}

    class DummyModel:
        def __init__(self, **inner):
            calls.update(inner)

        async def ainvoke(self, *a, **k):  # pragma: no cover
            return None

    monkeypatch.setattr(llm_factory_mod, 'ChatOpenAI', DummyModel)

    inst = create_chat_openai(model="gpt-4o", temperature=0.2, max_completion_tokens=123, timeout=15)

    assert calls.get('model') == "gpt-4o"
    assert calls.get('temperature') == 0.2
    # Factory must translate max_completion_tokens -> max_tokens
    assert 'max_tokens' in calls and calls['max_tokens'] == 123
    assert 'max_completion_tokens' not in calls
    assert calls.get('timeout') == 15
    assert inst is not None


def test_llm_factory_defaults(monkeypatch):
    calls = {}

    class DummyModel:
        def __init__(self, **inner):
            calls.update(inner)

    monkeypatch.setattr(llm_factory_mod, 'ChatOpenAI', DummyModel)

    inst = create_chat_openai(model="gpt-4.1")
    assert calls.get('model') == "gpt-4.1"
    # No temperature passed, so it should not appear
    assert 'temperature' not in calls
    # Default token limit applied
    assert calls.get('max_tokens') == 4096
    # Timeout not supplied, ensure absence
    assert 'timeout' not in calls
    assert inst is not None


def test_llm_factory_penalties_and_presence(monkeypatch):
    captured = {}

    class DummyModel:
        def __init__(self, **inner):
            captured.update(inner)

    monkeypatch.setattr(llm_factory_mod, 'ChatOpenAI', DummyModel)
    inst = create_chat_openai(
        model="gpt-4.1-mini",
        frequency_penalty=0.5,
        presence_penalty=0.25,
        top_p=0.9,
    )
    assert inst is not None
    assert captured.get('frequency_penalty') == 0.5
    assert captured.get('presence_penalty') == 0.25
    assert captured.get('top_p') == 0.9


def test_llm_factory_custom_extra_kwargs(monkeypatch):
    captured = {}

    class DummyModel:
        def __init__(self, **inner):
            captured.update(inner)

    monkeypatch.setattr(llm_factory_mod, 'ChatOpenAI', DummyModel)
    inst = create_chat_openai(model="gpt-custom", experimental_flag=True, retry_policy={"retries": 2})
    assert inst is not None
    assert captured.get('experimental_flag') is True
    assert captured.get('retry_policy') == {"retries": 2}
