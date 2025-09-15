#!/usr/bin/env python3
"""
Configure LangChain Integration with Existing Credentials
Sets up the LangChain agents to work with existing Hugging Face and OpenAI credentials
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import json

def load_environment_variables():
    """Load environment variables from .env file"""
    env_file = Path(".env")
    if env_file.exists():
        load_dotenv(env_file)
        print("✓ Loaded environment variables from .env")
    else:
        print("⚠ No .env file found, using system environment variables")

    return {
        "openai_key": os.getenv("OPENAI_API_KEY", ""),
        "huggingface_token": os.getenv("HUGGINGFACE_TOKEN", "") or os.getenv("HUGGING_FACE_HUB_TOKEN", ""),
        "langchain_api_key": os.getenv("LANGCHAIN_API_KEY", ""),
        "cartrita_secret": os.getenv("CARTRITA_SECRET", "")
    }

def create_langchain_config():
    """Create LangChain configuration file"""
    env_vars = load_environment_variables()

    config = {
        "providers": {
            "openai": {
                "enabled": bool(env_vars["openai_key"] and not env_vars["openai_key"].startswith("sk-proj-your_")),
                "api_key": env_vars["openai_key"] if env_vars["openai_key"] and not env_vars["openai_key"].startswith("sk-proj-your_") else None,
                "models": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]
            },
            "huggingface": {
                "enabled": bool(env_vars["huggingface_token"] and not env_vars["huggingface_token"].startswith("your_")),
                "token": env_vars["huggingface_token"] if env_vars["huggingface_token"] and not env_vars["huggingface_token"].startswith("your_") else None,
                "models": [
                    "meta-llama/Meta-Llama-3.1-70B-Instruct",
                    "meta-llama/Meta-Llama-3.1-8B-Instruct",
                    "mistralai/Mixtral-8x7B-Instruct-v0.1",
                    "codellama/CodeLlama-34b-Instruct-hf"
                ]
            }
        },
        "orchestrator": {
            "cost_optimization": True,
            "fallback_strategy": True,
            "session_cost_limit": 50.0,
            "default_provider": "huggingface" if env_vars["huggingface_token"] else "openai"
        },
        "langchain": {
            "tracing_enabled": bool(env_vars["langchain_api_key"]),
            "api_key": env_vars["langchain_api_key"] if env_vars["langchain_api_key"] and not env_vars["langchain_api_key"].startswith("lsv2_pt_your_") else None,
            "project": "cartrita-v2"
        },
        "security": {
            "secret_key": env_vars["cartrita_secret"]
        }
    }

    # Save configuration
    config_file = Path("services/ai-orchestrator/langchain_config.json")
    config_file.parent.mkdir(parents=True, exist_ok=True)

    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"✓ Created LangChain configuration: {config_file}")
    return config

def create_integration_test():
    """Create integration test specific to your setup"""
    test_content = '''#!/usr/bin/env python3
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
    print("\\n=== Testing Hugging Face Connection ===")

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
    print("\\n=== Testing LangChain Imports ===")

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
    print("\\n=== Testing Multi-Provider Orchestrator ===")

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
    print("\\n=== Testing Simple Chat ===")

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
    print("\\n=== Testing Existing System Integration ===")

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
    print("=== Cartrita LangChain Integration Test ===\\n")

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
    print("\\n=== INTEGRATION TEST SUMMARY ===")
    passed = sum(1 for _, result in results if result)
    total = len(results)

    print(f"Passed: {passed}/{total} ({passed/total*100:.1f}%)")

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} {test_name}")

    if passed == total:
        print("\\n🎉 All tests passed! LangChain integration is ready.")
    elif passed >= total * 0.7:
        print("\\n⚠ Most tests passed. System is partially ready.")
    else:
        print("\\n❌ Multiple test failures. Check configuration and dependencies.")

    return passed == total

if __name__ == "__main__":
    success = asyncio.run(run_comprehensive_test())
    sys.exit(0 if success else 1)
'''

    test_file = Path("scripts/test_cartrita_langchain_integration.py")
    test_file.write_text(test_content)
    print(f"✓ Created integration test: {test_file}")

def create_environment_helper():
    """Create helper script to check and fix environment"""
    helper_content = '''#!/usr/bin/env python3
"""
Environment Helper for LangChain Integration
Helps diagnose and fix environment issues
"""

import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

def check_dependencies():
    """Check if required dependencies are installed"""
    print("=== Checking Dependencies ===")

    required_packages = [
        "langchain",
        "langchain-community",
        "transformers",
        "torch",
        "accelerate",
        "tokenizers"
    ]

    missing = []

    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✓ {package} installed")
        except ImportError:
            print(f"✗ {package} missing")
            missing.append(package)

    if missing:
        print(f"\\nTo install missing packages:")
        print(f"pip install {' '.join(missing)}")
        return False

    return True

def check_huggingface_auth():
    """Check Hugging Face authentication"""
    print("\\n=== Checking Hugging Face Authentication ===")

    token = os.getenv("HUGGINGFACE_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")

    if not token or token.startswith("your_"):
        print("✗ Hugging Face token not configured")
        print("Set HUGGINGFACE_TOKEN in your .env file")
        return False

    try:
        from huggingface_hub import whoami
        user_info = whoami(token)
        print(f"✓ Authenticated as: {user_info['name']}")
        return True
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        return False

def install_dependencies():
    """Install required dependencies"""
    print("\\n=== Installing Dependencies ===")

    packages = [
        "langchain>=0.1.0",
        "langchain-community>=0.0.10",
        "transformers>=4.20.0",
        "torch>=1.12.0",
        "accelerate>=0.20.0",
        "tokenizers>=0.13.0",
        "huggingface_hub>=0.15.0"
    ]

    for package in packages:
        try:
            print(f"Installing {package}...")
            subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], check=True, capture_output=True, text=True)
            print(f"✓ Installed {package}")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install {package}: {e}")

def main():
    """Main helper function"""
    load_dotenv()

    print("=== LangChain Integration Environment Helper ===\\n")

    # Check current status
    deps_ok = check_dependencies()
    auth_ok = check_huggingface_auth()

    if not deps_ok:
        install_deps = input("\\nInstall missing dependencies? (y/N): ")
        if install_deps.lower() == 'y':
            install_dependencies()

    if not auth_ok:
        print("\\nPlease configure your Hugging Face token:")
        print("1. Get token from https://huggingface.co/settings/tokens")
        print("2. Add to .env file: HUGGINGFACE_TOKEN=your_actual_token_here")

    if deps_ok and auth_ok:
        print("\\n🎉 Environment is ready for LangChain integration!")
    else:
        print("\\n⚠ Please fix the issues above before proceeding.")

if __name__ == "__main__":
    main()
'''

    helper_file = Path("scripts/env_helper_langchain.py")
    helper_file.write_text(helper_content)
    print(f"✓ Created environment helper: {helper_file}")

def update_multi_provider_for_huggingface():
    """Update multi-provider orchestrator to use Hugging Face inference API properly"""

    orchestrator_file = Path("services/ai-orchestrator/cartrita/orchestrator/agents/langchain_enhanced/multi_provider_orchestrator.py")

    if orchestrator_file.exists():
        content = orchestrator_file.read_text()

        # Add Hugging Face Inference API configuration
        hf_api_section = '''        # Hugging Face Models (using Inference API)
        if self.huggingface_api_key:
            configs.update({
                "llama-3.1-8b": ModelConfig(
                    name="meta-llama/Meta-Llama-3.1-8B-Instruct",
                    provider=ModelProvider.HUGGINGFACE,
                    cost_per_1k_tokens=0.0001,
                    max_tokens=8192,
                    supports_streaming=True,
                    supports_function_calling=False,
                    expertise_areas=["general", "reasoning", "coding"],
                    quality_score=0.85
                ),
                "mixtral-8x7b": ModelConfig(
                    name="mistralai/Mixtral-8x7B-Instruct-v0.1",
                    provider=ModelProvider.HUGGINGFACE,
                    cost_per_1k_tokens=0.0002,
                    max_tokens=32768,
                    supports_streaming=True,
                    supports_function_calling=False,
                    expertise_areas=["multilingual", "reasoning"],
                    quality_score=0.88
                ),
                "codellama-7b": ModelConfig(
                    name="codellama/CodeLlama-7b-Instruct-hf",
                    provider=ModelProvider.HUGGINGFACE,
                    cost_per_1k_tokens=0.0001,
                    max_tokens=4096,
                    supports_streaming=True,
                    supports_function_calling=False,
                    expertise_areas=["coding", "debugging"],
                    quality_score=0.82
                )
            })'''

        # Replace the heavy models with lighter ones for better performance
        content = content.replace(
            "\"llama-3.1-70b\": ModelConfig(",
            "\"llama-3.1-8b\": ModelConfig("
        )
        content = content.replace(
            "name=\"meta-llama/Meta-Llama-3.1-70B-Instruct\",",
            "name=\"meta-llama/Meta-Llama-3.1-8B-Instruct\","
        )

        # Update Hugging Face initialization to use inference API
        hf_init_section = '''                elif config.provider == ModelProvider.HUGGINGFACE:
                    # Use Hugging Face Inference API
                    from langchain_community.llms import HuggingFaceEndpoint
                    from langchain_community.chat_models import ChatHuggingFace

                    # Create endpoint with your token
                    endpoint = HuggingFaceEndpoint(
                        repo_id=config.name,
                        huggingfacehub_api_token=self.huggingface_api_key,
                        max_new_tokens=1024,
                        temperature=0.7,
                        timeout=60,
                        streaming=config.supports_streaming
                    )

                    # Wrap in chat interface
                    self.model_instances[model_id] = ChatHuggingFace(
                        llm=endpoint,
                        verbose=False
                    )'''

        # Find and replace the Hugging Face initialization section
        start_marker = "elif config.provider == ModelProvider.HUGGINGFACE:"
        end_marker = "print(f\"Initialized model: {model_id}\")"

        start_idx = content.find(start_marker)
        if start_idx != -1:
            end_idx = content.find(end_marker, start_idx)
            if end_idx != -1:
                end_idx = content.find('\n', end_idx) + 1
                content = content[:start_idx] + hf_init_section.strip() + '\n\n                ' + content[end_idx:]

        orchestrator_file.write_text(content)
        print("✓ Updated multi-provider orchestrator for Hugging Face Inference API")

def main():
    """Main configuration function"""
    print("=== Configuring LangChain Integration for Cartrita ===")

    # Load and check environment
    config = create_langchain_config()

    # Create integration test
    create_integration_test()

    # Create environment helper
    create_environment_helper()

    # Update orchestrator for HF inference API
    update_multi_provider_for_huggingface()

    print("\n=== Configuration Summary ===")

    # Check what's configured
    openai_ready = config["providers"]["openai"]["enabled"]
    hf_ready = config["providers"]["huggingface"]["enabled"]

    print(f"OpenAI: {'✓ Ready' if openai_ready else '✗ Not configured'}")
    print(f"Hugging Face: {'✓ Ready' if hf_ready else '✗ Not configured'}")
    print(f"Cost Optimization: {'✓ Enabled' if config['orchestrator']['cost_optimization'] else '✗ Disabled'}")
    print(f"Default Provider: {config['orchestrator']['default_provider']}")

    if hf_ready or openai_ready:
        print("\n🎉 Configuration complete!")
        print("\nNext steps:")
        print("1. Run: python scripts/env_helper_langchain.py")
        print("2. Run: python scripts/test_cartrita_langchain_integration.py")
        print("3. If tests pass, integrate with your main application")
    else:
        print("\n⚠ No AI providers configured!")
        print("Please set up at least one provider:")
        print("- For OpenAI: Set OPENAI_API_KEY in .env")
        print("- For Hugging Face: Set HUGGINGFACE_TOKEN in .env")

if __name__ == "__main__":
    main()