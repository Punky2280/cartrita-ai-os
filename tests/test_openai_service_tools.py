import pytest
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
