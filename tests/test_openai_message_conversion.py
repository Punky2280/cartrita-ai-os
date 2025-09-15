import pytest

from cartrita.orchestrator.models.schemas import Message, MessageRole
from cartrita.orchestrator.services.openai_service import OpenAIService


def test_convert_messages_maps_tool_call_id_to_tool_role():
    svc = OpenAIService()
    msg = Message(
        role=MessageRole.ASSISTANT,
        content="",
        metadata={"tool_call_id": "tc_123"},
    )

    out = svc._convert_messages([msg])
    assert len(out) == 1
    assert out[0]["role"] == "tool"
    assert out[0]["tool_call_id"] == "tc_123"


def test_convert_messages_tool_result_content_sets_tool_role():
    svc = OpenAIService()
    msg = Message(
        role=MessageRole.ASSISTANT,
        content={"type": "tool_result", "result": {"ok": True}},
    )

    out = svc._convert_messages([msg])
    assert len(out) == 1
    assert out[0]["role"] == "tool"
    assert out[0]["content"]["type"] == "tool_result"
