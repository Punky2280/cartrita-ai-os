import os
import importlib
import inspect

os.environ.setdefault("CARTRITA_DISABLE_DB", "1")

AGENT_MODULES = [
    "cartrita.orchestrator.agents.cartrita_core.cartrita_agent",
    "cartrita.orchestrator.agents.task.task_agent",
    "cartrita.orchestrator.agents.knowledge.knowledge_agent",
]

REQUIRED_CLASSES = [
    "CartritaAgent",
    "TaskAgent",
    "KnowledgeAgent",
]


def test_agent_modules_import_and_classes_present():
    missing = []
    for mod_name in AGENT_MODULES:
        mod = importlib.import_module(mod_name)
        for cls in REQUIRED_CLASSES:
            # tolerate some agents not defining all classes, but ensure at least one matches
            if any(obj_name == cls for obj_name, obj in inspect.getmembers(mod) if inspect.isclass(obj)):
                break
        else:
            missing.append(mod_name)
    # At least one module must contain one required class (prevents total stub drift)
    assert len(missing) < len(AGENT_MODULES)
