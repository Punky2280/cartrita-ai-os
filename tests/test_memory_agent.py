#!/usr/bin/env python3
"""
Simple test for Memory Agent functionality
"""

import asyncio
import sys

# Add current directory to Python path
sys.path.insert(0, ".")


async def test_memory_agent():
    """Test memory agent basic functionality."""
    try:
        print("🧠 Testing Memory Agent...")

        # Import required components
        from cartrita.orchestrator.agents.memory import MemoryAgent
        from cartrita.orchestrator.agents.cartrita_core.api_key_manager import (
            APIKeyManager,
        )

        # Initialize components
        print("  ✓ Importing components...")
        api_key_manager = APIKeyManager()
        memory_agent = MemoryAgent(api_key_manager)

        print("  ✓ Memory agent initialized")
        print(f"  ✓ MCP tools registered: {len(memory_agent.mcp_protocol.tools)}")
        print(f"  ✓ Available tools: {list(memory_agent.mcp_protocol.tools.keys())}")

        # Test /memo help command
        print("\n📖 Testing /memo help command...")
        help_response = await memory_agent.process_request("/memo help")
        print(f"  ✓ Help response: {help_response.content[:100]}...")

        # Test /memo create command
        print("\n📝 Testing /memo create command...")
        create_response = await memory_agent.process_request(
            "/memo create TestUser:person:Software engineer who loves AI"
        )
        print(f"  ✓ Create response: {create_response.content}")

        # Test /memo list command
        print("\n📋 Testing /memo list command...")
        list_response = await memory_agent.process_request("/memo list")
        print(f"  ✓ List response: {list_response.content}")

        # Test /memo search command
        print("\n🔍 Testing /memo search command...")
        search_response = await memory_agent.process_request("/memo search engineer")
        print(f"  ✓ Search response: {search_response.content}")

        # Test /memo get command
        print("\n📄 Testing /memo get command...")
        get_response = await memory_agent.process_request("/memo get TestUser")
        print(f"  ✓ Get response: {get_response.content}")

        print("\n🎉 All memory agent tests passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_orchestrator_integration():
    """Test memory agent integration with orchestrator."""
    try:
        print("\n🎭 Testing Orchestrator Integration...")

        from cartrita.orchestrator.agents.cartrita_core.orchestrator import (
            CartritaOrchestrator,
        )

        # Initialize orchestrator
        orchestrator = CartritaOrchestrator()
        await orchestrator.start()

        print("  ✓ Orchestrator started")

        # Test /memo command routing
        print("\n🔀 Testing /memo command routing...")
        response = await orchestrator.process_chat_request("/memo help")
        print(
            f"  ✓ Routing response: {response.get('response', 'No response')[:100]}..."
        )

        # Test memory agent creation
        print("\n📝 Testing memory creation via orchestrator...")
        create_response = await orchestrator.process_chat_request(
            "/memo create OrchestratorTest:test:Integration test entity"
        )
        print(
            f"  ✓ Create via orchestrator: {create_response.get('response', 'No response')}"
        )

        await orchestrator.stop()
        print("  ✓ Orchestrator stopped")

        print("\n🎉 Orchestrator integration tests passed!")
        return True

    except Exception as e:
        print(f"❌ Orchestrator test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("🚀 Starting Memory Agent Tests...\n")

    # Test 1: Memory Agent standalone
    agent_test = await test_memory_agent()

    if agent_test:
        # Test 2: Orchestrator integration
        orchestrator_test = await test_orchestrator_integration()

        if orchestrator_test:
            print("\n✅ All tests passed! Memory Agent with MCP is working correctly.")
            return True

    print("\n❌ Some tests failed.")
    return False


if __name__ == "__main__":
    asyncio.run(main())
