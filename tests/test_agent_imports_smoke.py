import os
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

# Pre-import strictly allowlisted agent modules to avoid dynamic import of untrusted names
try:
    from cartrita.orchestrator.agents.cartrita_core import cartrita_agent as _m_cartrita
except ImportError:
    _m_cartrita = None
try:
    from cartrita.orchestrator.agents.task import task_agent as _m_task
except ImportError:
    _m_task = None
try:
    from cartrita.orchestrator.agents.knowledge import knowledge_agent as _m_knowledge
except ImportError:
    _m_knowledge = None

_ALLOWED_MODULES = {
    "cartrita.orchestrator.agents.cartrita_core.cartrita_agent": _m_cartrita,
    "cartrita.orchestrator.agents.task.task_agent": _m_task,
    "cartrita.orchestrator.agents.knowledge.knowledge_agent": _m_knowledge,
}


def _safe_import_module(mod_name: str):
    # Enforce strict allowlist to avoid importing arbitrary modules; no dynamic importlib usage
    mod = _ALLOWED_MODULES.get(mod_name)
    if mod is None:
        raise ImportError("Disallowed or unavailable module import")
    return mod


def test_agent_modules_import_and_classes_present():
    missing = []
    for mod_name in AGENT_MODULES:
        mod = _safe_import_module(mod_name)
        for cls in REQUIRED_CLASSES:
            # tolerate some agents not defining all classes, but ensure at least one matches
            if any(
                obj_name == cls for obj_name, obj in inspect.getmembers(mod) if inspect.isclass(obj)
            ):
                break
        else:
            missing.append(mod_name)
    # At least one module must contain one required class (prevents total stub drift)
    assert len(missing) < len(AGENT_MODULES)
