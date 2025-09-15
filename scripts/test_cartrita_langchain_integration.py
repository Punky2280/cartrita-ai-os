#!/usr/bin/env python3
"""
Cartrita-specific LangChain Integration Test
Tests the LangChain integration with your existing system
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "ai-orchestrator"))

def test_environment_setup():
    """Test environment variables are properly configured"""
    print("=== Testing Environment Setup ===")

    required_vars = {
        "HUGGINGFACE_TOKEN": "Hugging Face token for model access",
        "CARTRITA_SECRET": "Cartrita secret key",
    }

    optional_vars = {
        "OPENAI_API_KEY": "OpenAI API key (optional)",
        "LANGCHAIN_API_KEY": "LangChain tracing key (optional)"
    }

    all_good = True

    for var, description in required_vars.items():
        value = os.getenv(var, "")
        if value and not value.startswith(("your_", "sk-proj-your_")):
            print(f"✓ {var}: Configured")
        else:
            print(f"✗ {var}: Missing or placeholder - {description}")
            all_good = False

    for var, description in optional_vars.items():
        value = os.getenv(var, "")
        if value and not value.startswith(("your_", "sk-proj-your_", "lsv2_pt_your_")):
            print(f"✓ {var}: Configured (optional)")
        else:
            print(f"⚠ {var}: Not configured (optional) - {description}")

    return all_good

def test_huggingface_connection():
    """Test Hugging Face connection"""
    print("\n=== Testing Hugging Face Connection ===")

    try:
        from transformers import pipeline

        # Test with a small model first
        classifier = pipeline(
            "text-classification",
            model="cardiffnlp/twitter-roberta-base-sentiment-latest",
            tokenizer="cardiffnlp/twitter-roberta-base-sentiment-latest",
            return_all_scores=True
        )

        result = classifier("Hello, this is a test!")
        print("✓ Hugging Face connection successful")
        print(f"✓ Test classification result: {result[0][0]['label']}")
        return True

    except Exception as e:
        print(f"✗ Hugging Face connection failed: {e}")
        return False

def test_langchain_imports():
    """Test LangChain imports"""
    print("\n=== Testing LangChain Imports ===")

    try:
        # Test core LangChain imports
        from langchain.schema import BaseMessage, HumanMessage, AIMessage
        from langchain.memory import ConversationBufferMemory
        print("✓ LangChain core imports successful")

        # Test community imports for Hugging Face
        from langchain_community.llms import HuggingFaceEndpoint
        from langchain_community.chat_models import ChatHuggingFace
        print("✓ LangChain community imports successful")

        return True

    except Exception as e:
        print(f"✗ LangChain import failed: {e}")
        print("  Try: pip install langchain langchain-community")
        return False

def test_multi_provider_orchestrator():
    """Test the multi-provider orchestrator"""
    print("\n=== Testing Multi-Provider Orchestrator ===")

    try:
        from cartrita.orchestrator.agents.langchain_enhanced.multi_provider_orchestrator import MultiProviderOrchestrator

        # Initialize with your credentials
        orchestrator = MultiProviderOrchestrator(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            huggingface_api_key=os.getenv("HUGGINGFACE_TOKEN"),
            cost_optimization=True
        )

        print("✓ Multi-Provider Orchestrator initialized")

        # Test model availability
        models = orchestrator.get_available_models()
        available_count = sum(1 for model in models.values() if model["available"])
        print(f"✓ Available models: {available_count}/{len(models)}")

        for model_id, info in models.items():
            status = "✓" if info["available"] else "✗"
            print(f"  {status} {model_id} ({info['provider']})")

        return available_count > 0

    except Exception as e:
        print(f"✗ Multi-Provider Orchestrator test failed: {e}")
        return False

async def test_simple_chat():
    """Test simple chat functionality"""
    print("\n=== Testing Simple Chat ===")

    try:
        from cartrita.orchestrator.agents.langchain_enhanced.multi_provider_orchestrator import (
            MultiProviderOrchestrator, TaskRequirements, TaskComplexity
        )

        orchestrator = MultiProviderOrchestrator(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            huggingface_api_key=os.getenv("HUGGINGFACE_TOKEN")
        )

        # Simple task requirements
        task_req = TaskRequirements(
            complexity=TaskComplexity.SIMPLE,
            max_cost=2.0,
            max_latency=30.0,
            quality_threshold=0.7
        )

        print("Sending test query...")
        result = await orchestrator.execute_with_optimal_model(
            "Hello! Can you tell me a fun fact about Python programming?",
            task_requirements=task_req
        )

        if result["success"]:
            print(f"✓ Chat successful!")
            print(f"  Model used: {result['selected_model']}")
            print(f"  Provider: {result['provider']}")
            print(f"  Response time: {result['execution_time']:.2f}s")
            print(f"  Cost: ${result['cost']:.4f}")
            print(f"  Response preview: {result['response'][:100]}...")
            return True
        else:
            print(f"✗ Chat failed: {result.get('error', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"✗ Chat test failed: {e}")
        return False

def test_existing_system_integration():
    """Test integration with existing Cartrita system"""
    print("\n=== Testing Existing System Integration ===")

    try:
        # Test existing agent imports
        sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "ai-orchestrator"))

        # Check if we can import existing agents
        existing_agents = [
            "cartrita.orchestrator.agents.code.code_agent",
            "cartrita.orchestrator.agents.research.research_agent",
            "cartrita.orchestrator.main"
        ]

        imported_count = 0
        for agent_module in existing_agents:
            try:
                __import__(agent_module)
                print(f"✓ Can import {agent_module}")
                imported_count += 1
            except Exception as e:
                print(f"⚠ Cannot import {agent_module}: {e}")

        print(f"✓ Successfully imported {imported_count}/{len(existing_agents)} existing components")
        return imported_count > 0

    except Exception as e:
        print(f"✗ System integration test failed: {e}")
        return False

async def run_comprehensive_test():
    """Run comprehensive integration test"""
    print("=== Cartrita LangChain Integration Test ===\n")

    tests = [
        ("Environment Setup", test_environment_setup, False),
        ("Hugging Face Connection", test_huggingface_connection, False),
        ("LangChain Imports", test_langchain_imports, False),
        ("Multi-Provider Orchestrator", test_multi_provider_orchestrator, False),
        ("Simple Chat", test_simple_chat, True),  # async
        ("Existing System Integration", test_existing_system_integration, False)
    ]

    results = []

    for test_name, test_func, is_async in tests:
        try:
            if is_async:
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n=== INTEGRATION TEST SUMMARY ===")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"Passed: {passed}/{total} ({passed/total*100:.1f}%)")

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} {test_name}")

    if passed == total:
        print("\n🎉 All tests passed! LangChain integration is ready.")
    elif passed >= total * 0.7:
        print("\n⚠ Most tests passed. System is partially ready.")
    else:
        print("\n❌ Multiple test failures. Check configuration and dependencies.")

    return passed == total

if __name__ == "__main__":
    success = asyncio.run(run_comprehensive_test())
    sys.exit(0 if success else 1)
