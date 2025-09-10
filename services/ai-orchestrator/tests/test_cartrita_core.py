# Cartrita AI OS - Cartrita Core Tests
# Comprehensive tests for the complete orchestration system

"""
Tests for Cartrita Core Agent system including:
- API Key Manager functionality
- MCP Protocol integration
- Cartrita Agent personality and delegation
- Complete orchestration workflow
"""

import time
from unittest.mock import patch

import pytest

# Import Cartrita components
from cartrita.orchestrator.agents.cartrita_core.api_key_manager import (
    APIKeyInfo,
    APIKeyManager,
    PermissionLevel,
    ToolPermission,
)
from cartrita.orchestrator.agents.cartrita_core.cartrita_agent import CartritaCoreAgent
from cartrita.orchestrator.agents.cartrita_core.mcp_protocol import (
    CartritaMCPProtocol,
    MCPMessage,
    MCPMessageType,
    MCPTool,
)
from cartrita.orchestrator.agents.cartrita_core.orchestrator import CartritaOrchestrator


class TestAPIKeyManager:
    """Test suite for API Key Manager."""

    @pytest.fixture
    def api_key_manager(self):
        """Create API Key Manager instance for testing."""
        return APIKeyManager()

    @pytest.fixture
    def sample_tool_permission(self):
        """Create sample tool permission."""
        return ToolPermission(
            tool_name="test_tool",
            required_keys=["openai"],
            permission_level=PermissionLevel.READ,
            rate_limit=10,
        )

    def test_initialization(self, api_key_manager):
        """Test API Key Manager initialization."""
        if api_key_manager is None:
            raise AssertionError("API Key Manager should not be None")
        if api_key_manager.vault is None:
            raise AssertionError("Vault should not be None")
        if len(api_key_manager.tool_permissions) == 0:
            raise AssertionError("Tool permissions should not be empty")
        if "web_search" not in api_key_manager.tool_permissions:
            raise AssertionError("web_search should be in tool permissions")

    def test_key_storage_and_retrieval(self, api_key_manager):
        """Test storing and retrieving API keys."""
        # Create test key info
        key_info = APIKeyInfo(
            key_id="test_key",
            service="test_service",
            permissions=[PermissionLevel.READ],
            allowed_agents={"test_agent"},
        )

        # Store key
        success = api_key_manager.vault.store_key(
            "test_key", "secret-api-key", key_info
        )
        if not success:
            raise AssertionError("Key storage should succeed")

        # Retrieve key
        retrieved_key = api_key_manager.vault.retrieve_key("test_key", "test_agent")
        if retrieved_key != "secret-api-key":
            raise AssertionError("Retrieved key should match stored key")

        # Test unauthorized access
        unauthorized_key = api_key_manager.vault.retrieve_key(
            "test_key", "unauthorized_agent"
        )
        if unauthorized_key is not None:
            raise AssertionError("Unauthorized access should return None")

    @pytest.mark.asyncio
    async def test_tool_registration(self, api_key_manager, sample_tool_permission):
        """Test tool registration."""
        result = await api_key_manager.register_tool(sample_tool_permission)
        if result is not True:
            raise AssertionError("Tool registration should succeed")
        if "test_tool" not in api_key_manager.tool_permissions:
            raise AssertionError("test_tool should be in tool permissions")

    @pytest.mark.asyncio
    async def test_key_access_request(self, api_key_manager, sample_tool_permission):
        """Test API key access request workflow."""
        # Register tool
        await api_key_manager.register_tool(sample_tool_permission)

        # Add a test key
        key_info = APIKeyInfo(
            key_id="openai_test",
            service="openai",
            permissions=[PermissionLevel.READ, PermissionLevel.EXECUTE],
            allowed_agents={"test_agent"},
        )
        api_key_manager.vault.store_key("openai_test", "test-openai-key", key_info)

        # Request access
        access_info = await api_key_manager.request_key_access(
            "test_agent", "test_tool"
        )

        # Verify access granted
        if access_info is None:
            raise AssertionError("Access info should not be None")
        if access_info["tool_name"] != "test_tool":
            raise AssertionError("Tool name should match requested tool")
        if "openai" not in access_info["keys"]:
            raise AssertionError("OpenAI should be in access keys")
        if access_info["keys"]["openai"]["key"] != "test-openai-key":
            raise AssertionError("OpenAI key should match expected value")

    @pytest.mark.asyncio
    async def test_key_return(self, api_key_manager):
        """Test key return functionality."""
        result = await api_key_manager.return_key_access(
            "test_agent", "test_checkout_id"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_agent_permissions(self, api_key_manager):
        """Test getting agent permissions."""
        permissions = await api_key_manager.get_agent_permissions("test_agent")

        assert permissions["agent_id"] == "test_agent"
        if permissions["agent_id"] != "test_agent":
            raise AssertionError("Agent ID should match")
        if "available_tools" not in permissions:
            raise AssertionError("Available tools should be in permissions")
        if "active_checkouts" not in permissions:
            raise AssertionError("Active checkouts should be in permissions")
        if "rate_limits" not in permissions:
            raise AssertionError("Rate limits should be in permissions")

    @pytest.mark.asyncio
    async def test_health_check(self, api_key_manager):
        """Test API Key Manager health check."""
        health = await api_key_manager.health_check()

        assert health["status"] == "healthy"
        if health["status"] != "healthy":
            raise AssertionError("Health status should be healthy")
        if "total_keys" not in health:
            raise AssertionError("Total keys should be in health check")
        if "registered_tools" not in health:
            raise AssertionError("Registered tools should be in health check")
        if "vault_operational" not in health:
            raise AssertionError("Vault operational status should be in health check")
        if health["vault_operational"] is not True:
            raise AssertionError("Vault should be operational")


class TestMCPProtocol:
    """Test suite for MCP Protocol."""

    @pytest.fixture
    def api_key_manager(self):
        """Create API Key Manager for MCP testing."""
        return APIKeyManager()

    @pytest.fixture
    def mcp_protocol(self, api_key_manager):
        """Create MCP Protocol instance."""
        return CartritaMCPProtocol(api_key_manager)

    @pytest.fixture
    def sample_mcp_tool(self):
        """Create sample MCP tool."""
        return MCPTool(
            name="test_mcp_tool",
            description="Test tool for MCP protocol",
            input_schema={
                "type": "object",
                "properties": {"input": {"type": "string"}},
                "required": ["input"],
            },
            hierarchy_level=2,
            safety_level=1,
        )

    def test_initialization(self, mcp_protocol):
        """Test MCP Protocol initialization."""
        assert mcp_protocol is not None
        assert mcp_protocol.protocol_version == "2025.01"
        assert len(mcp_protocol.tools) > 0
        assert "web_search" in mcp_protocol.tools

    def test_tool_registration(self, mcp_protocol, sample_mcp_tool):
        """Test tool registration in MCP."""
        result = mcp_protocol.register_tool(sample_mcp_tool)
        assert result is True
        assert "test_mcp_tool" in mcp_protocol.tools

    @pytest.mark.asyncio
    async def test_list_tools_message(self, mcp_protocol):
        """Test MCP list tools message handling."""
        message = MCPMessage(
            method="tools/list", params={"max_hierarchy": 3, "include_schema": True}
        )

        response = await mcp_protocol.handle_message(message)

        assert response.type == MCPMessageType.RESPONSE
        assert "tools" in response.result
        assert len(response.result["tools"]) > 0

    @pytest.mark.asyncio
    async def test_capabilities_message(self, mcp_protocol):
        """Test MCP capabilities message handling."""
        message = MCPMessage(method="capabilities")

        response = await mcp_protocol.handle_message(message)

        assert response.type == MCPMessageType.RESPONSE
        assert response.result["protocol_version"] == "2025.01"
        assert "capabilities" in response.result
        assert response.result["api_key_management"] is True

    @pytest.mark.asyncio
    async def test_tool_execution_message(self, mcp_protocol):
        """Test MCP tool execution message handling."""
        message = MCPMessage(
            method="tools/call",
            params={
                "name": "web_search",
                "arguments": {"query": "test query"},
                "agent_id": "test_agent",
            },
        )

        response = await mcp_protocol.handle_message(message)

        assert response.type == MCPMessageType.RESPONSE
        assert "execution_id" in response.result
        assert response.result["tool_name"] == "web_search"

    @pytest.mark.asyncio
    async def test_unknown_method_error(self, mcp_protocol):
        """Test error handling for unknown methods."""
        message = MCPMessage(method="unknown/method")

        response = await mcp_protocol.handle_message(message)

        assert response.type == MCPMessageType.ERROR
        assert response.error["code"] == "METHOD_NOT_FOUND"

    def test_hierarchy_report(self, mcp_protocol):
        """Test tool hierarchy reporting."""
        report = mcp_protocol.get_tool_hierarchy_report()

        assert "total_tools" in report
        assert "hierarchy_distribution" in report
        assert "api_dependencies" in report
        assert report["protocol_version"] == "2025.01"


class TestCartritaAgent:
    """Test suite for Cartrita Core Agent."""

    @pytest.fixture
    def api_key_manager(self):
        """Create API Key Manager for agent testing."""
        return APIKeyManager()

    @pytest.fixture
    def cartrita_agent(self, api_key_manager):
        """Create Cartrita Agent instance."""
        with patch(
            "cartrita.orchestrator.agents.cartrita_core.cartrita_agent.ChatOpenAI"
        ):
            return CartritaCoreAgent(api_key_manager)

    def test_initialization(self, cartrita_agent):
        """Test Cartrita Agent initialization."""
        assert cartrita_agent is not None
        assert cartrita_agent.agent_id == "cartrita_core"
        assert len(cartrita_agent.available_agents) > 0
        assert cartrita_agent.personality_traits["origin"] == "Hialeah, Florida"

    def test_personality_traits(self, cartrita_agent):
        """Test Cartrita's personality configuration."""
        traits = cartrita_agent.personality_traits

        assert traits["cultural_background"] == "Caribbean-Cuban heritage"
        assert traits["personality"]["sassy"] is True
        assert traits["personality"]["direct"] is True
        assert traits["personality"]["professional"] is True
        assert "Calle Ocho festivals" in traits["cultural_references"]
        assert "Family first" in traits["values"]

    def test_system_prompt_contains_cultural_elements(self, cartrita_agent):
        """Test that system prompt includes cultural elements."""
        prompt = cartrita_agent.system_prompt

        assert "Hialeah" in prompt
        assert "Caribbean" in prompt
        assert "Miami" in prompt
        assert "cafecito" in prompt
        assert "abuela" in prompt
        assert "Spanglish" in prompt

    @pytest.mark.asyncio
    async def test_agent_delegation_logic(self, cartrita_agent):
        """Test agent delegation decision making."""
        # Test research task delegation
        result = await cartrita_agent._delegate_task(
            "Find information about AI trends", "research", ["web_search"]
        )
        assert "research specialist" in result

    @pytest.mark.asyncio
    async def test_get_status(self, cartrita_agent):
        """Test getting Cartrita's status."""
        status = await cartrita_agent.get_status()

        assert status["agent_id"] == "cartrita_core"
        assert status["name"] == "Cartrita"
        assert status["type"] == "orchestrator"
        assert status["personality"] == "Sassy Hialeah Miami Queen"
        assert status["location"] == "Hialeah, Florida"
        assert "Task delegation" in status["capabilities"]

    def test_personality_touch_addition(self, cartrita_agent):
        """Test personality enhancement of responses."""
        test_response = "This is a test response."
        enhanced = cartrita_agent._add_personality_touch(test_response)

        # Should be either enhanced with personality or unchanged
        assert len(enhanced) >= len(test_response)


class TestCartritaOrchestrator:
    """Test suite for complete Cartrita Orchestrator."""

    @pytest.fixture
    def orchestrator(self):
        """Create Cartrita Orchestrator instance."""
        with patch(
            "cartrita.orchestrator.agents.cartrita_core.cartrita_agent.ChatOpenAI"
        ):
            return CartritaOrchestrator()

    def test_initialization(self, orchestrator):
        """Test orchestrator initialization."""
        assert orchestrator is not None
        assert orchestrator.orchestrator_id == "cartrita_main_orchestrator"
        assert orchestrator.api_key_manager is not None
        assert orchestrator.mcp_protocol is not None
        assert orchestrator.cartrita_agent is not None

    @pytest.mark.asyncio
    async def test_startup_and_shutdown(self, orchestrator):
        """Test orchestrator startup and shutdown."""
        # Mock the startup checks
        with patch.object(orchestrator, "_perform_startup_checks", return_value=None):
            await orchestrator.start()
            assert orchestrator.is_running is True

            await orchestrator.stop()
            assert orchestrator.is_running is False

    @pytest.mark.asyncio
    async def test_health_check(self, orchestrator):
        """Test orchestrator health check."""
        with (
            patch.object(orchestrator, "is_running", True),
            patch.object(
                orchestrator.api_key_manager,
                "health_check",
                return_value={"status": "healthy"},
            ),
            patch.object(
                orchestrator.mcp_protocol,
                "_handle_tool_status",
                return_value={"active": 0},
            ),
            patch.object(
                orchestrator.cartrita_agent,
                "get_status",
                return_value={"status": "active"},
            ),
        ):

            health = await orchestrator.health_check()
            assert health is True

    @pytest.mark.asyncio
    async def test_get_agent_statuses(self, orchestrator):
        """Test getting all agent statuses."""
        with (
            patch.object(
                orchestrator.cartrita_agent,
                "get_status",
                return_value={
                    "status": "active",
                    "available_agents": ["research", "code"],
                },
            ),
            patch.object(
                orchestrator.api_key_manager,
                "health_check",
                return_value={"status": "healthy"},
            ),
            patch.object(
                orchestrator.mcp_protocol,
                "_handle_capabilities",
                return_value={"protocol_version": "2025.01"},
            ),
        ):

            statuses = await orchestrator.get_agent_statuses()

            assert "cartrita_core" in statuses
            assert "api_key_manager" in statuses
            assert "mcp_protocol" in statuses
            assert statuses["cartrita_core"]["status"] == "active"

    @pytest.mark.asyncio
    async def test_mcp_tool_execution(self, orchestrator):
        """Test MCP tool execution through orchestrator."""
        mock_response = MCPMessage(
            type=MCPMessageType.RESPONSE,
            result={"execution_id": "test_123", "status": "completed"},
        )

        with patch.object(
            orchestrator.mcp_protocol, "handle_message", return_value=mock_response
        ):
            result = await orchestrator.execute_mcp_tool(
                "test_tool", {"param": "value"}, "test_agent"
            )

            assert result["execution_id"] == "test_123"
            assert result["status"] == "completed"

    def test_system_stats(self, orchestrator):
        """Test system statistics generation."""
        stats = orchestrator.get_system_stats()

        assert stats["orchestrator_id"] == "cartrita_main_orchestrator"
        assert "uptime_seconds" in stats
        assert "total_requests" in stats
        assert "error_count" in stats
        assert "components" in stats
        assert "api_key_manager" in stats["components"]
        assert "mcp_protocol" in stats["components"]
        assert "cartrita_agent" in stats["components"]


class TestIntegrationWorkflows:
    """Integration tests for complete workflows."""

    @pytest.fixture
    def full_system(self):
        """Create complete system for integration testing."""
        with patch(
            "cartrita.orchestrator.agents.cartrita_core.cartrita_agent.ChatOpenAI"
        ):
            return CartritaOrchestrator()

    @pytest.mark.asyncio
    async def test_complete_chat_workflow(self, full_system):
        """Test complete chat processing workflow."""
        # Mock the agent processing
        mock_response = {
            "response": "¡Dale! I'll help you with that research task.",
            "agent_type": "cartrita_core",
            "processing_time": 1.5,
            "metadata": {"personality_active": True},
        }

        with patch.object(
            full_system.cartrita_agent, "process_request", return_value=mock_response
        ):
            result = await full_system.process_chat_request(
                message="Help me research AI trends",
                context={"conversation_id": "test_123"},
                stream=False,
            )

            assert "¡Dale!" in result["response"]
            assert result["agent_type"] == "cartrita_core"
            assert "request_id" in result["metadata"]
            assert result["metadata"]["personality_active"] is True

    @pytest.mark.asyncio
    async def test_tool_access_workflow(self, full_system):
        """Test complete tool access workflow."""
        # Setup test tool permission
        tool_permission = ToolPermission(
            tool_name="integration_test_tool",
            required_keys=["openai"],
            permission_level=PermissionLevel.READ,
        )

        await full_system.api_key_manager.register_tool(tool_permission)

        # Add test API key
        key_info = APIKeyInfo(
            key_id="openai_integration",
            service="openai",
            permissions=[PermissionLevel.READ],
            allowed_agents={"test_agent"},
        )
        full_system.api_key_manager.vault.store_key(
            "openai_integration", "test-integration-key", key_info
        )

        # Test the workflow
        async with full_system.request_context("test_agent", ["integration_test_tool"]):
            # Context manager should handle key access automatically
            access_info = await full_system.api_key_manager.request_key_access(
                "test_agent", "integration_test_tool"
            )
            assert access_info is not None
            assert "openai" in access_info["keys"]

    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, full_system):
        """Test error handling throughout the system."""
        # Test chat processing with error
        with patch.object(
            full_system.cartrita_agent,
            "process_request",
            side_effect=Exception("Test error"),
        ):
            result = await full_system.process_chat_request(
                message="This will cause an error"
            )

            assert "error" in result
            assert (
                "Ay, mi amor" in result["response"]
            )  # Cartrita's personality in error
            assert result["metadata"]["error_handled"] is True


@pytest.mark.asyncio
async def test_performance_benchmarks():
    """Performance benchmarks for the system."""
    with patch("cartrita.orchestrator.agents.cartrita_core.cartrita_agent.ChatOpenAI"):
        orchestrator = CartritaOrchestrator()

        # Benchmark initialization time
        start_time = time.time()
        await orchestrator.start()
        init_time = time.time() - start_time

        assert init_time < 5.0  # Should initialize in under 5 seconds

        # Benchmark key access time
        start_time = time.time()
        access_info = await orchestrator.api_key_manager.request_key_access(
            "benchmark_agent", "web_search"
        )
        access_time = time.time() - start_time

        assert access_time < 0.1  # Should grant access in under 100ms

        await orchestrator.stop()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
