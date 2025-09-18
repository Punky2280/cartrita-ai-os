"""
Tests for models without LangChain dependencies.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from cartrita.orchestrator.models.schemas import (
    AgentCapabilities,
    AgentStatus,
    AgentType,
    ChatRequest,
    ChatResponse,
    ConversationCreate,
    ConversationResponse,
    Message,
    MessageContent,
    MessageRole,
    UserCreate,
    UserResponse,
)


def test_message_role_enum():
    """Test MessageRole enum values."""
    assert MessageRole.USER == "user"
    assert MessageRole.ASSISTANT == "assistant"
    assert MessageRole.SYSTEM == "system"


def test_message_content_creation():
    """Test MessageContent model creation."""
    content = MessageContent(
        type="text", text="Hello world", data={"additional": "info"}
    )
    assert content.type == "text"
    assert content.text == "Hello world"
    assert content.data["additional"] == "info"


def test_message_validation():
    """Test Message model validation."""
    # Valid text message
    message = Message(role=MessageRole.USER, content="Hello world")
    assert message.role == MessageRole.USER
    assert message.content == "Hello world"


def test_user_create():
    """Test UserCreate model validation."""
    user = UserCreate(
        username="testuser", email="test@example.com", full_name="Test User"
    )
    assert user.username == "testuser"
    assert user.email == "test@example.com"


def test_conversation_create():
    """Test ConversationCreate model."""
    conversation = ConversationCreate(
        title="Test Conversation",
        agent_override=AgentType.RESEARCH,
        context={"key": "value"},
    )
    assert conversation.title == "Test Conversation"
    assert conversation.agent_override == AgentType.RESEARCH


def test_chat_request():
    """Test ChatRequest model validation."""
    request = ChatRequest(
        message="Test message", stream=True, temperature=0.7, max_tokens=1000
    )
    assert request.message == "Test message"
    assert request.stream is True
    assert request.temperature == 0.7


def test_agent_capabilities():
    """Test AgentCapabilities model."""
    capabilities = AgentCapabilities(
        tools=["web_search", "code_execution"], max_context_length=16384
    )
    assert "web_search" in capabilities.tools
    assert capabilities.max_context_length == 16384


def test_agent_types():
    """Test AgentType enum values."""
    assert AgentType.SUPERVISOR == "supervisor"
    assert AgentType.RESEARCH == "research"
    assert AgentType.CODE == "code"


def test_agent_status():
    """Test AgentStatus enum values."""
    assert AgentStatus.IDLE == "idle"
    assert AgentStatus.BUSY == "busy"
    assert AgentStatus.OFFLINE == "offline"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
