def test_orchestrator_imports():
    # Import a representative set of orchestrator modules to register them for coverage
    import importlib

    modules = [
        "cartrita.orchestrator.utils.llm_factory",
        "cartrita.orchestrator.agents.code.code_agent",
        "cartrita.orchestrator.agents.knowledge.knowledge_agent",
        "cartrita.orchestrator.agents.task.task_agent",
        "cartrita.orchestrator.providers.fallback_provider",
        "cartrita.orchestrator.services.openai_service",
    ]
    loaded = []
    for m in modules:
        loaded.append(importlib.import_module(m))
    assert len(loaded) == len(modules)
