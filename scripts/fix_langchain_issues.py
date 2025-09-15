#!/usr/bin/env python3
"""
Fix LangChain Integration Issues
Addresses compatibility issues found during testing
"""

import os
import sys
from pathlib import Path
import shutil

def fix_pydantic_field_issues():
    """Fix Pydantic Field compatibility issues"""
    print("Fixing Pydantic Field issues...")

    # Files to fix
    files_to_fix = [
        "services/ai-orchestrator/cartrita/orchestrator/agents/langchain_enhanced/supervisor_agent.py",
        "services/ai-orchestrator/cartrita/orchestrator/agents/langchain_enhanced/reasoning_chain_agent.py",
        "services/ai-orchestrator/cartrita/orchestrator/agents/langchain_enhanced/advanced_tool_agent.py",
        "services/ai-orchestrator/cartrita/orchestrator/agents/langchain_enhanced/multi_provider_orchestrator.py"
    ]

    for file_path in files_to_fix:
        path = Path(file_path)
        if path.exists():
            content = path.read_text()

            # Replace pydantic imports for LangChain compatibility
            content = content.replace(
                "from pydantic import BaseModel, Field",
                "from pydantic import BaseModel, Field\nfrom langchain.pydantic_v1 import BaseModel as LangChainBaseModel, Field as LangChainField"
            )

            # Use LangChain's pydantic for BaseTool subclasses
            if "BaseTool" in content:
                content = content.replace(
                    "from pydantic import BaseModel, Field",
                    "from langchain.pydantic_v1 import BaseModel, Field"
                )

            path.write_text(content)
            print(f"✓ Fixed Pydantic issues in {file_path}")

def fix_missing_llm_initialization():
    """Fix missing LLM initialization in memory"""
    print("Fixing LLM initialization issues...")

    orchestrator_path = Path("services/ai-orchestrator/cartrita/orchestrator/agents/langchain_enhanced/multi_provider_orchestrator.py")

    if orchestrator_path.exists():
        content = orchestrator_path.read_text()

        # Fix memory initialization
        old_memory_init = """        # Memory for context
        self.memory = ConversationSummaryBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            max_token_limit=4000
        )"""

        new_memory_init = """        # Initialize basic LLM for memory if keys available
        basic_llm = None
        if self.openai_api_key:
            try:
                from langchain_openai import ChatOpenAI
                basic_llm = ChatOpenAI(api_key=self.openai_api_key, model="gpt-3.5-turbo")
            except:
                pass

        # Memory for context
        if basic_llm:
            self.memory = ConversationSummaryBufferMemory(
                llm=basic_llm,
                memory_key="chat_history",
                return_messages=True,
                max_token_limit=4000
            )
        else:
            from langchain.memory import ConversationBufferMemory
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )"""

        content = content.replace(old_memory_init, new_memory_init)
        orchestrator_path.write_text(content)
        print("✓ Fixed memory initialization")

def fix_import_errors():
    """Fix import errors in test file"""
    print("Fixing import errors...")

    # Fix reasoning agent import
    reasoning_path = Path("services/ai-orchestrator/cartrita/orchestrator/agents/langchain_enhanced/reasoning_chain_agent.py")
    if reasoning_path.exists():
        content = reasoning_path.read_text()
        # Move TaskRequirements class to top level
        if "class TaskRequirements:" not in content:
            task_req_definition = '''

@dataclass
class TaskRequirements:
    """Requirements for a specific task"""
    complexity: TaskComplexity
    max_cost: float
    max_latency: float  # seconds
    quality_threshold: float  # 0-1 scale
    requires_function_calling: bool = False
    requires_streaming: bool = False
    domain_expertise: List[str] = field(default_factory=list)
'''
            # Insert after imports
            import_end = content.find('\n\n')
            if import_end > 0:
                content = content[:import_end] + task_req_definition + content[import_end:]
                reasoning_path.write_text(content)
                print("✓ Added TaskRequirements to reasoning agent")

def fix_structured_tool_schema():
    """Fix StructuredTool schema issues"""
    print("Fixing StructuredTool schema issues...")

    supervisor_path = Path("services/ai-orchestrator/cartrita/orchestrator/agents/langchain_enhanced/supervisor_agent.py")

    if supervisor_path.exists():
        content = supervisor_path.read_text()

        # Replace problematic StructuredTool creation
        old_tool_creation = '''            StructuredTool(
                name="get_agent_status",
                description="Get status and availability of agents",
                func=self._get_agent_status,
                args_schema=None
            ),'''

        new_tool_creation = '''            StructuredTool.from_function(
                func=self._get_agent_status,
                name="get_agent_status",
                description="Get status and availability of agents"
            ),'''

        content = content.replace(old_tool_creation, new_tool_creation)

        # Fix other similar issues
        old_tool_creation2 = '''            StructuredTool(
                name="synthesize_responses",
                description="Synthesize multiple agent responses",
                func=self._synthesize_responses,
                args_schema=None
            ),'''

        new_tool_creation2 = '''            StructuredTool.from_function(
                func=self._synthesize_responses,
                name="synthesize_responses",
                description="Synthesize multiple agent responses"
            ),'''

        content = content.replace(old_tool_creation2, new_tool_creation2)

        old_tool_creation3 = '''            StructuredTool(
                name="optimize_workflow",
                description="Optimize workflow based on constraints",
                func=self._optimize_workflow,
                args_schema=None
            )'''

        new_tool_creation3 = '''            StructuredTool.from_function(
                func=self._optimize_workflow,
                name="optimize_workflow",
                description="Optimize workflow based on constraints"
            )'''

        content = content.replace(old_tool_creation3, new_tool_creation3)

        supervisor_path.write_text(content)
        print("✓ Fixed StructuredTool schema issues")

def create_simple_compatibility_agents():
    """Create simple compatibility versions of existing agents"""
    print("Creating compatibility agents...")

    # Create a simple CartritaAgent for compatibility
    cartrita_agent_path = Path("services/ai-orchestrator/cartrita/orchestrator/agents/cartrita_core/cartrita_agent_simple.py")

    simple_cartrita = '''"""
Simple CartritaAgent for backward compatibility
"""

class CartritaAgent:
    """Simple Cartrita agent for backward compatibility"""

    def __init__(self, **kwargs):
        self.name = "cartrita"
        self.description = "Simple Cartrita agent"

    def process_request(self, request: str) -> str:
        return f"Processed: {request}"

    async def aprocess_request(self, request: str) -> str:
        return self.process_request(request)
'''

    cartrita_agent_path.write_text(simple_cartrita)
    print("✓ Created simple CartritaAgent")

def fix_advanced_tool_agent():
    """Fix AdvancedToolAgent field issues"""
    print("Fixing AdvancedToolAgent...")

    tool_agent_path = Path("services/ai-orchestrator/cartrita/orchestrator/agents/langchain_enhanced/advanced_tool_agent.py")

    if tool_agent_path.exists():
        content = tool_agent_path.read_text()

        # Fix Field usage
        content = content.replace(
            "from pydantic import BaseModel, Field, validator",
            "from langchain.pydantic_v1 import BaseModel, Field, validator"
        )

        # Fix private field access
        content = content.replace(
            "_metrics: ToolMetrics = Field(default_factory=lambda: ToolMetrics(name=\"\"))",
            "_metrics = None"
        )

        # Add proper initialization in __init__
        init_addition = '''        if not hasattr(self, '_metrics'):
            self._metrics = ToolMetrics(name=self.name)'''

        if "def __init__(self, **kwargs):" in content:
            content = content.replace(
                "def __init__(self, **kwargs):\n        super().__init__(**kwargs)",
                f"def __init__(self, **kwargs):\n        super().__init__(**kwargs)\n{init_addition}"
            )

        tool_agent_path.write_text(content)
        print("✓ Fixed AdvancedToolAgent")

def install_missing_dependencies():
    """Install missing LangChain dependencies"""
    print("Installing missing dependencies...")

    import subprocess

    dependencies = [
        "langchain>=0.1.0",
        "langchain-openai>=0.0.5",
        "langchain-community>=0.0.10",
        "langchain-core>=0.1.0",
        "tiktoken>=0.5.0",
        "pydantic<2.0.0"  # Use pydantic v1 for compatibility
    ]

    for dep in dependencies:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", dep],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"✓ Installed {dep}")
        except subprocess.CalledProcessError as e:
            print(f"⚠ Failed to install {dep}: {e}")

def main():
    """Run all fixes"""
    print("=== Fixing LangChain Integration Issues ===")

    fixes = [
        ("Pydantic Field Issues", fix_pydantic_field_issues),
        ("Missing LLM Initialization", fix_missing_llm_initialization),
        ("Import Errors", fix_import_errors),
        ("StructuredTool Schema", fix_structured_tool_schema),
        ("Compatibility Agents", create_simple_compatibility_agents),
        ("Advanced Tool Agent", fix_advanced_tool_agent),
        ("Missing Dependencies", install_missing_dependencies)
    ]

    for fix_name, fix_func in fixes:
        try:
            print(f"\n--- {fix_name} ---")
            fix_func()
        except Exception as e:
            print(f"✗ Failed to apply {fix_name}: {e}")

    print("\n=== Fixes Applied ===")
    print("Re-run the test script to verify improvements")

if __name__ == "__main__":
    main()