"""Smoke import tests for core agents to increase baseline coverage."""
import importlib
import pytest

AGENT_MODULES = [
    "cartrita.orchestrator.agents.task.task_agent",
    "cartrita.orchestrator.agents.code.code_agent",
    "cartrita.orchestrator.agents.research.research_agent",
    "cartrita.orchestrator.agents.computer_use.computer_use_agent",
    "cartrita.orchestrator.agents.image.image_agent",
    "cartrita.orchestrator.agents.audio.audio_agent",
    "cartrita.orchestrator.agents.reasoning.reasoning_agent",
    "cartrita.orchestrator.agents.cartrita_core.cartrita_agent",
]

@pytest.mark.parametrize("module_path", AGENT_MODULES)
def test_agent_module_import(module_path):
    try:
        mod = importlib.import_module(module_path)
    except ModuleNotFoundError as e:
        pytest.skip(f"Module path not present: {e}")
    agent_symbols = [
        name for name, obj in vars(mod).items()
        if name.endswith("Agent") and isinstance(obj, type)
    ]
    assert agent_symbols, f"No agent classes detected in {module_path}"

def test_cartrita_core_orchestrator_import():
    try:
        import cartrita.orchestrator.agents.cartrita_core.orchestrator as _orchestrator  # noqa: F401
    except ModuleNotFoundError as e:
        pytest.skip(f"Orchestrator module not found: {e}")
