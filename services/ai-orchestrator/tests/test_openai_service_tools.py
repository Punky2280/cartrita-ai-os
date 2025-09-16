import asyncio
from typing import Any, AsyncGenerator, Dict, List
from unittest.mock import patch

import pytest

from cartrita.orchestrator.models.schemas import ChatRequest, Message, MessageContent, MessageRole
from cartrita.orchestrator.services.openai_service import OpenAIService


@pytest.fixture
def service() -> OpenAIService:
    # Avoid real network calls
    with patch("cartrita.orchestrator.services.openai_service.AsyncOpenAI"):
        return OpenAIService()


def _assert_tool_def(tool: Dict[str, Any], expected_name: str) -> None:
    # Both LC convert_to_openai_tool and our fallback produce {"type":"function","function":{...}}
    assert isinstance(tool, dict)
    assert tool.get("type") == "function"
    fn = tool.get("function")
    assert isinstance(fn, dict)
    assert fn.get("name") == expected_name
    assert "parameters" in fn and isinstance(fn["parameters"], dict)


@pytest.mark.parametrize(
    "tool_names",
    [
        ["web_search"],
        ["file_op"],
        ["tavily_search"],
        ["web_search", "file_op", "tavily_search"],
    ],
)
def test_prepare_tools_shapes(service: OpenAIService, tool_names: List[str]) -> None:
    tools = service._prepare_tools(tool_names)
    assert len(tools) == len(tool_names)
    for name, tool in zip(tool_names, tools):
        _assert_tool_def(tool, name)


def test_convert_messages_preserves_tool_role_and_id(service: OpenAIService) -> None:
    # Message with explicit tool_call_id in metadata
    msg_with_id = Message(
        role=MessageRole.ASSISTANT,
        content="result payload",
        metadata={"tool_call_id": "abc123", "other": 1},
    )

    # Message whose content includes a tool_result structure
    msg_with_content = Message(
        role=MessageRole.ASSISTANT,
        content=[MessageContent(type="tool_result", text="done", data={})],
    )

    converted = service._convert_messages([msg_with_id, msg_with_content])
    assert converted[0]["role"] == "tool"
    assert converted[0]["tool_call_id"] == "abc123"

    assert converted[1]["role"] == "tool"
    # Content is normalized; ensure structure preserved
    assert isinstance(converted[1]["content"], list)
    assert converted[1]["content"][0]["type"] == "tool_result"


def test_convert_messages_handles_list_content_tool_result(service: OpenAIService) -> None:
    content: List[MessageContent] = [
        MessageContent(type="text", text="irrelevant preface"),
        MessageContent(type="tool_result", text="computed", data={"value": 7}),
        MessageContent(type="text", text="postface"),
    ]
    msg = Message(
        role=MessageRole.ASSISTANT,
        content=content,
        metadata={"tool_call_id": "tc_list_1"},
    )

    converted = service._convert_messages([msg])
    assert converted[0]["role"] == "tool"
    assert converted[0]["tool_call_id"] == "tc_list_1"
    assert isinstance(converted[0]["content"], list)
    types = [part.get("type") for part in converted[0]["content"]]
    assert "tool_result" in types


@pytest.mark.asyncio
async def test_process_chat_request_collects_tool_calls(service: OpenAIService) -> None:
    # Stub chat_completion to yield a tool_call, some content, then done
    async def fake_chat_completion(**_kwargs) -> AsyncGenerator[Dict[str, Any], None]:
        yield {
            "type": "tool_call",
            "tool_call": {
                "id": "tc_1",
                "function": {"name": "web_search", "arguments": "{\"query\":\"x\"}"},
            },
        }
        yield {"type": "content", "content": "Processing..."}
        yield {"type": "done", "finish_reason": "stop"}

    with patch.object(service, "chat_completion", side_effect=fake_chat_completion):
        req = ChatRequest(message="hello", conversation_id=None, tools=["web_search"], stream=True)
        resp = await service.process_chat_request(req)

    # Response should include content and a tool message capturing the call metadata
    assert resp.response.startswith("Processing") or resp.response == ""
    assert resp.messages is not None
    tool_msgs = [m for m in resp.messages if m.role == MessageRole.TOOL]
    assert tool_msgs, "Expected at least one tool message"
    # Verify metadata preservation
    meta = tool_msgs[0].metadata or {}
    assert meta.get("tool_call_id") == "tc_1"
    assert meta.get("tool_name") == "web_search"
