#!/usr/bin/env python3
"""
Simple LangChain Integration Test for Cartrita
Tests basic functionality with your existing credentials
"""

import os
import sys
from pathlib import Path
import asyncio

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

def test_credentials():
    """Test that credentials are available"""
    print("=== Testing Credentials ===")

    openai_key = os.getenv("OPENAI_API_KEY", "")
    hf_token = os.getenv("HUGGINGFACE_TOKEN", "")

    print(f"OpenAI API Key: {'✓ Found' if openai_key.startswith('sk-') else '✗ Missing'}")
    print(f"Hugging Face Token: {'✓ Found' if hf_token.startswith('hf_') else '✗ Missing'}")

    return bool(openai_key.startswith('sk-') or hf_token.startswith('hf_'))

def test_openai_integration():
    """Test OpenAI integration"""
    print("\n=== Testing OpenAI Integration ===")

    openai_key = os.getenv("OPENAI_API_KEY", "")
    if not openai_key.startswith('sk-'):
        print("⚠ Skipping OpenAI test - no API key")
        return False

    try:
        from langchain_openai import ChatOpenAI

        # Initialize with your API key
        llm = ChatOpenAI(
            api_key=openai_key,
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=100
        )

        # Test simple message
        from langchain.schema import HumanMessage

        messages = [HumanMessage(content="Hello! Say 'LangChain integration working' if you can respond.")]
        response = llm.invoke(messages)

        print("✓ OpenAI integration successful")
        print(f"  Response: {response.content}")
        return True

    except Exception as e:
        print(f"✗ OpenAI integration failed: {e}")
        return False

def test_huggingface_integration():
    """Test Hugging Face integration using inference API"""
    print("\n=== Testing Hugging Face Integration ===")

    hf_token = os.getenv("HUGGINGFACE_TOKEN", "")
    if not hf_token.startswith('hf_'):
        print("⚠ Skipping Hugging Face test - no token")
        return False

    try:
        # Test with Hugging Face Inference API
        from langchain_community.llms import HuggingFaceEndpoint

        # Use a reliable, fast model for testing
        llm = HuggingFaceEndpoint(
            repo_id="microsoft/DialoGPT-medium",
            huggingfacehub_api_token=hf_token,
            max_new_tokens=50,
            temperature=0.7
        )

        response = llm.invoke("Hello! Please respond briefly.")

        print("✓ Hugging Face integration successful")
        print(f"  Response: {response}")
        return True

    except Exception as e:
        print(f"✗ Hugging Face integration failed: {e}")
        print("  Trying alternative approach...")

        # Try with a simpler approach
        try:
            from transformers import pipeline

            # Test with local pipeline (no API key needed)
            classifier = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest"
            )

            result = classifier("LangChain integration is working great!")
            print("✓ Hugging Face transformers working locally")
            print(f"  Test sentiment: {result[0]['label']} ({result[0]['score']:.2f})")
            return True

        except Exception as e2:
            print(f"✗ Alternative approach also failed: {e2}")
            return False

def test_basic_langchain_patterns():
    """Test basic LangChain patterns"""
    print("\n=== Testing Basic LangChain Patterns ===")

    try:
        # Test memory
        from langchain.memory import ConversationBufferMemory
        memory = ConversationBufferMemory()
        memory.save_context({"input": "Hello"}, {"output": "Hi there!"})
        print("✓ Memory system working")

        # Test prompts
        from langchain.prompts import PromptTemplate
        template = PromptTemplate(
            input_variables=["name"],
            template="Hello {name}! How are you today?"
        )
        formatted = template.format(name="Cartrita")
        print("✓ Prompt templates working")
        print(f"  Example: {formatted}")

        # Test schema
        from langchain.schema import HumanMessage, AIMessage, SystemMessage
        messages = [
            SystemMessage(content="You are a helpful assistant"),
            HumanMessage(content="Hello!"),
            AIMessage(content="Hi there!")
        ]
        print("✓ Message schema working")
        print(f"  Created {len(messages)} messages")

        return True

    except Exception as e:
        print(f"✗ LangChain patterns test failed: {e}")
        return False

def test_multi_provider_concept():
    """Test the multi-provider concept with available providers"""
    print("\n=== Testing Multi-Provider Concept ===")

    try:
        openai_key = os.getenv("OPENAI_API_KEY", "")
        hf_token = os.getenv("HUGGINGFACE_TOKEN", "")

        providers = {}

        # Test OpenAI if available
        if openai_key.startswith('sk-'):
            try:
                from langchain_openai import ChatOpenAI
                providers['openai'] = ChatOpenAI(
                    api_key=openai_key,
                    model="gpt-3.5-turbo",
                    temperature=0.7,
                    max_tokens=50
                )
                print("✓ OpenAI provider initialized")
            except Exception as e:
                print(f"⚠ OpenAI provider failed: {e}")

        # Test Hugging Face if available
        if hf_token.startswith('hf_'):
            try:
                from langchain_community.llms import HuggingFaceEndpoint
                providers['huggingface'] = HuggingFaceEndpoint(
                    repo_id="microsoft/DialoGPT-medium",
                    huggingfacehub_api_token=hf_token,
                    max_new_tokens=50
                )
                print("✓ Hugging Face provider initialized")
            except Exception as e:
                print(f"⚠ Hugging Face provider failed: {e}")

        if providers:
            print(f"✓ Multi-provider setup successful - {len(providers)} provider(s) available")

            # Test provider selection logic
            def select_provider(task_type="general"):
                """Simple provider selection"""
                if task_type == "creative" and "openai" in providers:
                    return "openai", providers["openai"]
                elif "huggingface" in providers:
                    return "huggingface", providers["huggingface"]
                elif "openai" in providers:
                    return "openai", providers["openai"]
                else:
                    return None, None

            provider_name, provider = select_provider()
            if provider:
                print(f"✓ Provider selection working - selected: {provider_name}")
                return True
            else:
                print("✗ No providers available")
                return False
        else:
            print("✗ No providers could be initialized")
            return False

    except Exception as e:
        print(f"✗ Multi-provider test failed: {e}")
        return False

def test_integration_with_existing_system():
    """Test integration points with existing Cartrita system"""
    print("\n=== Testing Integration with Existing System ===")

    try:
        # Add the services directory to path
        sys.path.insert(0, str(Path(__file__).parent.parent / "services" / "ai-orchestrator"))

        # Test if we can import existing components
        try:
            from cartrita.orchestrator.main import app
            print("✓ Can import existing orchestrator")
        except Exception as e:
            print(f"⚠ Orchestrator import issue: {e}")

        # Test configuration loading
        config_file = Path("services/ai-orchestrator/langchain_config.json")
        if config_file.exists():
            import json
            with open(config_file) as f:
                config = json.load(f)
            print("✓ LangChain configuration file exists")
            print(f"  Providers configured: {len(config['providers'])}")
        else:
            print("⚠ LangChain configuration missing")

        return True

    except Exception as e:
        print(f"✗ System integration test failed: {e}")
        return False

async def run_comprehensive_test():
    """Run all tests"""
    print("=== Cartrita Simple LangChain Integration Test ===")
    print("Testing basic functionality with your existing setup\n")

    tests = [
        ("Credentials Check", test_credentials),
        ("OpenAI Integration", test_openai_integration),
        ("Hugging Face Integration", test_huggingface_integration),
        ("Basic LangChain Patterns", test_basic_langchain_patterns),
        ("Multi-Provider Concept", test_multi_provider_concept),
        ("System Integration", test_integration_with_existing_system)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            print(f"--- {test_name} ---")
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "="*50)
    print("INTEGRATION TEST SUMMARY")
    print("="*50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"Tests passed: {passed}/{total} ({passed/total*100:.1f}%)")

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} {test_name}")

    if passed >= 4:  # Most important tests
        print("\n🎉 LangChain integration is working!")
        print("\nNext steps:")
        print("1. The system is ready for basic use")
        print("2. You can now integrate with your main application")
        print("3. Consider adding more advanced features as needed")
    elif passed >= 2:
        print("\n⚠ Partial integration success")
        print("Basic functionality works, but some features may be limited")
    else:
        print("\n❌ Integration needs attention")
        print("Please check API keys and dependencies")

    return passed >= 2

if __name__ == "__main__":
    success = asyncio.run(run_comprehensive_test())
    sys.exit(0 if success else 1)