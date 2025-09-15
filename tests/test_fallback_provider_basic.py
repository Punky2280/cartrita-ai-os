import importlib
import inspect


def test_get_fallback_provider_singleton_and_capabilities():
    provider_mod = importlib.import_module("cartrita.orchestrator.providers.fallback_provider")

    # Reset global for isolation
    if getattr(provider_mod, '_fallback_provider', None) is not None:
        provider_mod._fallback_provider = None  # type: ignore

    first = provider_mod.get_fallback_provider()
    second = provider_mod.get_fallback_provider()
    assert first is second, "Expected singleton fallback provider instance"

    # Basic sanity of capabilities dict
    caps = first.get_capabilities_info()
    required_keys = {
        'openai_available', 'huggingface_available', 'rule_based_available',
        'emergency_template_available', 'transformers_installed', 'langchain_installed'
    }
    assert required_keys.issubset(caps.keys())

    # Ensure generate_fallback_response convenience function exists and awaits provider
    assert hasattr(provider_mod, 'generate_fallback_response')
    sig = inspect.signature(provider_mod.generate_fallback_response)
    assert 'user_input' in sig.parameters
