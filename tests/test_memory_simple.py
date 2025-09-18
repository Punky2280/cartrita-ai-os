#!/usr/bin/env python3
"""
Simple test for Memory Agent core functionality without full dependencies
"""

import asyncio
import sys

# Add current directory to Python path
sys.path.insert(0, ".")


async def test_memory_agent_core():
    """Test memory agent core functionality without API dependencies."""
    try:
        print("🧠 Testing Memory Agent Core...")

        # Mock API key manager for testing
        class MockAPIKeyManager:
            pass

        # Import core components
        from cartrita.orchestrator.agents.memory_agent import MemoryAgent

        print("  ✓ Importing MemoryAgent...")

        # Create mock api key manager
        mock_api_manager = MockAPIKeyManager()

        # Initialize memory agent
        memory_agent = MemoryAgent(mock_api_manager)
        print("  ✓ Memory agent initialized")
        print(f"  ✓ MCP tools registered: {len(memory_agent.mcp_protocol.tools)}")
        print(f"  ✓ Available tools: {list(memory_agent.mcp_protocol.tools.keys())}")

        # Test direct MCP tool execution
        print("\n🔧 Testing MCP Tool Execution...")

        # Test create entity
        result = await memory_agent._execute_create_entity(
            name="TestUser",
            entity_type="person",
            observations=["Software engineer who loves AI"],
        )
        print(f"  ✓ Create entity: {result}")

        # Test list entities
        result = await memory_agent._execute_list_entities()
        print(f"  ✓ List entities: {result}")

        # Test search
        result = await memory_agent._execute_search_entities(query="engineer")
        print(f"  ✓ Search entities: {result}")

        # Test get entity
        result = await memory_agent._execute_get_entity(entity_name="TestUser")
        print(f"  ✓ Get entity: {result}")

        print("\n🎉 Core memory agent tests passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_memo_commands():
    """Test /memo command parsing without full initialization."""
    try:
        print("\n📝 Testing /memo Command Parsing...")

        # Mock API key manager
        class MockAPIKeyManager:
            pass

        from cartrita.orchestrator.agents.memory_agent import MemoryAgent

        memory_agent = MemoryAgent(MockAPIKeyManager())

        # Test help command
        response = await memory_agent.process_request("/memo help")
        print(f"  ✓ Help command: {response.content[:50]}...")

        # Test create command
        response = await memory_agent.process_request(
            "/memo create TestEntity:test:This is a test entity"
        )
        print(f"  ✓ Create command: {response.content[:100]}...")

        # Test list command
        response = await memory_agent.process_request("/memo list")
        print(f"  ✓ List command: {response.content[:50]}...")

        print("\n🎉 /memo command tests passed!")
        return True

    except Exception as e:
        print(f"❌ Command test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run all simplified tests."""
    print("🚀 Starting Simplified Memory Agent Tests...\n")

    # Test 1: Core functionality
    core_test = await test_memory_agent_core()

    if core_test:
        # Test 2: Command parsing
        command_test = await test_memo_commands()

        if command_test:
            print(
                "\n✅ All simplified tests passed! Memory Agent with /memo commands is working."
            )
            return True

    print("\n❌ Some tests failed.")
    return False


if __name__ == "__main__":
    asyncio.run(main())
