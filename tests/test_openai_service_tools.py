import pytest
try:
    from cartrita.orchestrator.services.openai_service import OpenAIService
except ModuleNotFoundError:
    # Allow running tests from repo root without installing the package
    import os
    import sys
    _ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    _CANDIDATES = [
        _ROOT,
        os.path.join(_ROOT, "services", "ai-orchestrator"),
        os.path.join(_ROOT, "services", "ai_orchestrator"),
    ]
    for _p in _CANDIDATES:
        if os.path.isdir(_p) and _p not in sys.path:
            sys.path.insert(0, _p)
    from cartrita.orchestrator.services.openai_service import OpenAIService


def test_prepare_tools_schema_web_search():
    svc = OpenAIService()
    tools = svc._prepare_tools(["web_search"])
    assert tools and any(
        (t.get("function") or t).get("name") == "web_search" for t in tools
    )
    # Should have required 'query' parameter
    schema = (tools[0]["function"] if "function" in tools[0] else tools[0]["parameters"])
    assert "query" in schema["parameters"]["properties"]


def test_prepare_tools_schema_file_op():
    svc = OpenAIService()
    tools = svc._prepare_tools(["file_op"])
    assert tools and any(
        (t.get("function") or t).get("name") == "file_op" for t in tools
    )
    schema = (tools[0]["function"] if "function" in tools[0] else tools[0]["parameters"])
    assert "operation" in schema["parameters"]["properties"]
    assert "path" in schema["parameters"]["properties"]
    assert "content" in schema["parameters"]["properties"]
