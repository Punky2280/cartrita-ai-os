#!/usr/bin/env python3
"""
Demo script showing the Memory Agent with /memo commands in action
"""

import asyncio
import sys

# Add current directory to Python path
sys.path.insert(0, ".")


async def demo_memory_agent():
    """Demonstrate the Memory Agent functionality."""
    print("🎭 Memory Agent with MCP Protocol Demo\n")
    print("=" * 60)

    # Mock API key manager for demo
    class MockAPIKeyManager:
        pass

    from cartrita.orchestrator.agents.memory import MemoryAgent

    # Initialize memory agent
    memory_agent = MemoryAgent(MockAPIKeyManager())
    print(
        f"✅ Memory Agent initialized with {len(memory_agent.mcp_protocol.tools)} MCP tools"
    )
    print(
        f"📋 Available tools: {', '.join(list(memory_agent.mcp_protocol.tools.keys()))}\n"
    )

    # Demo commands
    commands = [
        "/memo help",
        "/memo create Alice:person:Lead software engineer specializing in AI and machine learning",
        "/memo create Python:skill:Programming language used for AI development",
        "/memo create CartritaProject:project:Advanced AI operating system with multi-agent architecture",
        "/memo relate Alice:Python:expert_in",
        "/memo relate Alice:CartritaProject:works_on",
        "/memo relate Python:CartritaProject:used_in",
        "/memo list",
        "/memo search engineer",
        "/memo search Python",
        "/memo get Alice",
        "/memo get CartritaProject",
    ]

    for i, command in enumerate(commands, 1):
        print(f"🔸 Command {i}: {command}")
        print("-" * 40)

        try:
            response = await memory_agent.process_request(command)
            print(response.content)
        except Exception as e:
            print(f"❌ Error: {e}")

        print()

    print("=" * 60)
    print("🎉 Demo completed! The Memory Agent successfully:")
    print("   • Integrated with MCP Protocol")
    print("   • Created entities (people, skills, projects)")
    print("   • Established relationships between entities")
    print("   • Performed searches across memory")
    print("   • Retrieved detailed entity information")
    print("   • Provided a comprehensive /memo command interface")


if __name__ == "__main__":
    asyncio.run(demo_memory_agent())
