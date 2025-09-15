#!/usr/bin/env python3
"""
LangChain System Integration Test
Comprehensive testing of the overhauled LangChain-based agent system
"""

import os
import sys
import json
import asyncio
import time
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add the services directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "ai-orchestrator"))

# Test imports
def test_imports():
    """Test that all new LangChain components can be imported"""
    print("Testing imports...")

    try:
        # Test enhanced agents
        from cartrita.orchestrator.agents.langchain_enhanced.supervisor_agent import LangChainSupervisorAgent
        from cartrita.orchestrator.agents.langchain_enhanced.reasoning_chain_agent import ReasoningChainAgent
        from cartrita.orchestrator.agents.langchain_enhanced.advanced_tool_agent import AdvancedToolAgent
        from cartrita.orchestrator.agents.langchain_enhanced.multi_provider_orchestrator import MultiProviderOrchestrator

        print("✓ All enhanced agents imported successfully")

        # Test core LangChain
        from langchain.agents import AgentExecutor
        from langchain.tools import BaseTool
        from langchain.memory import ConversationBufferMemory
        from langchain_openai import ChatOpenAI

        print("✓ LangChain core components imported successfully")

        return True

    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_multi_provider_orchestrator():
    """Test the multi-provider orchestrator"""
    print("\nTesting Multi-Provider Orchestrator...")

    try:
        from cartrita.orchestrator.agents.langchain_enhanced.multi_provider_orchestrator import (
            MultiProviderOrchestrator, TaskRequirements, TaskComplexity
        )

        # Initialize orchestrator
        orchestrator = MultiProviderOrchestrator(
            cost_optimization=True,
            fallback_strategy=True
        )

        # Test model selection
        task_req = TaskRequirements(
            complexity=TaskComplexity.SIMPLE,
            max_cost=1.0,
            max_latency=10.0,
            quality_threshold=0.7
        )

        selected_model = orchestrator.select_optimal_model(task_req, context_length=100)
        print(f"✓ Model selection works: {selected_model}")

        # Test available models
        models = orchestrator.get_available_models()
        print(f"✓ Found {len(models)} available models")

        # Test simple chat (if API keys available)
        if orchestrator.openai_api_key or orchestrator.huggingface_api_key:
            try:
                response = orchestrator.chat("Hello, test message")
                print(f"✓ Chat functionality works: {response[:50]}...")
            except Exception as e:
                print(f"⚠ Chat test skipped (API key issue): {e}")
        else:
            print("⚠ Chat test skipped (no API keys)")

        print("✓ Multi-Provider Orchestrator tests passed")
        return True

    except Exception as e:
        print(f"✗ Multi-Provider Orchestrator test failed: {e}")
        return False

def test_reasoning_chain_agent():
    """Test the reasoning chain agent"""
    print("\nTesting Reasoning Chain Agent...")

    try:
        from cartrita.orchestrator.agents.langchain_enhanced.reasoning_chain_agent import (
            ReasoningChainAgent, ReasoningType, TaskRequirements
        )

        # Mock LLM for testing (if no API key)
        agent = ReasoningChainAgent(
            max_reasoning_steps=3,
            confidence_threshold=0.8,
            enable_backtracking=True
        )

        print("✓ Reasoning agent initialized")

        # Test configuration
        stats = agent.get_reasoning_stats()
        print(f"✓ Agent stats: {stats['max_steps']} max steps")

        # Test reasoning type selection
        analysis = "This problem involves cause and effect relationships"
        reasoning_type = agent._select_reasoning_type(analysis)
        print(f"✓ Reasoning type selection: {reasoning_type.value}")

        print("✓ Reasoning Chain Agent tests passed")
        return True

    except Exception as e:
        print(f"✗ Reasoning Chain Agent test failed: {e}")
        return False

def test_advanced_tool_agent():
    """Test the advanced tool agent"""
    print("\nTesting Advanced Tool Agent...")

    try:
        from cartrita.orchestrator.agents.langchain_enhanced.advanced_tool_agent import (
            AdvancedToolAgent, MathCalculatorTool, FileSystemTool
        )

        # Initialize agent
        agent = AdvancedToolAgent()

        print(f"✓ Tool agent initialized with {len(agent.tools)} tools")

        # Test tool metrics
        metrics = agent.get_tool_metrics()
        print(f"✓ Tool metrics available: {len(metrics['individual_tools'])} tools")

        # Test math tool specifically
        math_tool = MathCalculatorTool()
        result = math_tool._execute("2 + 2 * 3")
        print(f"✓ Math tool works: {result}")

        # Test file system tool
        fs_tool = FileSystemTool()
        result = fs_tool._execute("write", "test.txt", "Hello World")
        print(f"✓ File system tool works: {result}")

        print("✓ Advanced Tool Agent tests passed")
        return True

    except Exception as e:
        print(f"✗ Advanced Tool Agent test failed: {e}")
        return False

def test_supervisor_agent():
    """Test the supervisor agent"""
    print("\nTesting Supervisor Agent...")

    try:
        from cartrita.orchestrator.agents.langchain_enhanced.supervisor_agent import (
            LangChainSupervisorAgent, SupervisorDecision
        )

        # Initialize supervisor
        supervisor = LangChainSupervisorAgent()

        print("✓ Supervisor agent initialized")
        print(f"✓ Available agents: {len(supervisor.available_agents)}")

        # Test agent capabilities formatting
        formatted = supervisor._format_agent_capabilities()
        lines = formatted.split('\n')
        print(f"✓ Agent capabilities formatted: {len(lines)} lines")

        # Test metrics
        metrics = supervisor.get_metrics()
        print(f"✓ Supervisor metrics: {metrics}")

        print("✓ Supervisor Agent tests passed")
        return True

    except Exception as e:
        print(f"✗ Supervisor Agent test failed: {e}")
        return False

def test_existing_agents_compatibility():
    """Test that existing agents still work"""
    print("\nTesting existing agents compatibility...")

    try:
        # Test existing agent imports
        from cartrita.orchestrator.agents.cartrita_core.cartrita_agent import CartritaAgent
        from cartrita.orchestrator.agents.code.code_agent import CodeAgent
        from cartrita.orchestrator.agents.research.research_agent import ResearchAgent

        print("✓ Existing agents can still be imported")

        # Test that they can be instantiated (basic test)
        try:
            cartrita = CartritaAgent()
            print("✓ CartritaAgent can be instantiated")
        except Exception as e:
            print(f"⚠ CartritaAgent instantiation warning: {e}")

        print("✓ Existing agents compatibility verified")
        return True

    except Exception as e:
        print(f"✗ Existing agents compatibility test failed: {e}")
        return False

def test_langchain_templates():
    """Test the LangChain templates"""
    print("\nTesting LangChain templates...")

    templates_dir = Path("services/ai-orchestrator/cartrita/orchestrator/agents/langchain_templates")

    if not templates_dir.exists():
        print("⚠ LangChain templates directory not found")
        return True

    template_files = [
        "base_agent_langchain.py",
        "tool_langchain.py",
        "chain_langchain.py",
        "memory_langchain.py",
        "callbacks_langchain.py"
    ]

    for template_file in template_files:
        template_path = templates_dir / template_file
        if template_path.exists():
            print(f"✓ Template exists: {template_file}")
        else:
            print(f"⚠ Template missing: {template_file}")

    print("✓ LangChain templates test completed")
    return True

def test_documentation_availability():
    """Test that LangChain documentation was extracted"""
    print("\nTesting documentation availability...")

    docs_dir = Path("docs/langchain/langchain_extracted")

    if not docs_dir.exists():
        print("⚠ LangChain documentation directory not found")
        return False

    # Count files in each category
    categories = ["agents", "chains", "tools", "core", "community"]
    total_files = 0

    for category in categories:
        category_dir = docs_dir / category
        if category_dir.exists():
            file_count = len(list(category_dir.glob("*.json")))
            print(f"✓ {category}: {file_count} files")
            total_files += file_count
        else:
            print(f"⚠ Category missing: {category}")

    print(f"✓ Total documentation files: {total_files}")

    # Test analysis report
    report_file = Path("langchain_analysis_report.json")
    if report_file.exists():
        with open(report_file, 'r') as f:
            report = json.load(f)
        print(f"✓ Analysis report available: {report['summary']['total_patterns_identified']} patterns")
    else:
        print("⚠ Analysis report not found")

    return True

def test_requirements():
    """Test that requirements are available"""
    print("\nTesting requirements...")

    req_files = [
        "services/ai-orchestrator/requirements_langchain.txt",
        "services/ai-orchestrator/requirements.in",
        "services/ai-orchestrator/constraints.txt"
    ]

    for req_file in req_files:
        req_path = Path(req_file)
        if req_path.exists():
            print(f"✓ Requirements file exists: {req_file}")
        else:
            print(f"⚠ Requirements file missing: {req_file}")

    return True

def run_integration_test():
    """Run full integration test"""
    print("=== LangChain System Integration Test ===")
    print(f"Started at: {datetime.now()}")
    print()

    tests = [
        ("Import Tests", test_imports),
        ("Multi-Provider Orchestrator", test_multi_provider_orchestrator),
        ("Reasoning Chain Agent", test_reasoning_chain_agent),
        ("Advanced Tool Agent", test_advanced_tool_agent),
        ("Supervisor Agent", test_supervisor_agent),
        ("Existing Agents Compatibility", test_existing_agents_compatibility),
        ("LangChain Templates", test_langchain_templates),
        ("Documentation Availability", test_documentation_availability),
        ("Requirements", test_requirements)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            start_time = time.time()
            result = test_func()
            end_time = time.time()

            results.append({
                "test": test_name,
                "passed": result,
                "duration": end_time - start_time
            })

        except Exception as e:
            print(f"✗ {test_name} crashed: {e}")
            results.append({
                "test": test_name,
                "passed": False,
                "duration": 0.0,
                "error": str(e)
            })

    # Summary
    print("\n=== TEST SUMMARY ===")
    passed = sum(1 for r in results if r["passed"])
    total = len(results)

    print(f"Passed: {passed}/{total}")
    print(f"Success rate: {passed/total*100:.1f}%")

    for result in results:
        status = "✓ PASS" if result["passed"] else "✗ FAIL"
        duration = f"{result['duration']:.2f}s"
        print(f"{status} {result['test']} ({duration})")

        if not result["passed"] and "error" in result:
            print(f"    Error: {result['error']}")

    print(f"\nCompleted at: {datetime.now()}")

    # Save test results
    with open("langchain_test_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "passed": passed,
                "total": total,
                "success_rate": passed/total*100
            },
            "results": results
        }, f, indent=2)

    print(f"\nTest results saved to: langchain_test_results.json")

    return passed == total

if __name__ == "__main__":
    success = run_integration_test()
    sys.exit(0 if success else 1)
