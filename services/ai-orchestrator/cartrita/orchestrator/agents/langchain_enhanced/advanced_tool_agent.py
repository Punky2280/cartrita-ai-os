"""
Advanced Tool Agent with LangChain
Implements sophisticated tool management and execution patterns
"""

import asyncio
import inspect
from typing import Any, Callable, Dict, List, Optional, Type, Union
from enum import Enum
from datetime import datetime, timedelta

from langchain.tools import BaseTool, StructuredTool, Tool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.schema import AgentAction, AgentFinish
from langchain.callbacks.manager import CallbackManagerForToolRun, AsyncCallbackManagerForToolRun
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from cartrita.orchestrator.utils.llm_factory import create_chat_openai
from langchain.memory import ConversationBufferMemory
from langchain.pydantic_v1 import BaseModel, Field
from langchain.pydantic_v1 import BaseModel as LangChainBaseModel, Field as LangChainField, validator
import json
import time
from functools import wraps


class ToolCategory(str, Enum):
    """Tool categories for organization"""
    COMPUTATION = "computation"
    DATA_ACCESS = "data_access"
    COMMUNICATION = "communication"
    FILE_SYSTEM = "file_system"
    WEB_SEARCH = "web_search"
    CODE_EXECUTION = "code_execution"
    MULTIMEDIA = "multimedia"
    SYSTEM = "system"


class ToolExecutionResult(BaseModel):
    """Result of tool execution"""
    tool_name: str = Field(description="Name of executed tool")
    success: bool = Field(description="Whether execution succeeded")
    result: Any = Field(description="Tool execution result")
    execution_time: float = Field(description="Execution time in seconds")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ToolMetrics(BaseModel):
    """Tool performance metrics"""
    name: str = Field(description="Tool name")
    total_calls: int = Field(default=0, description="Total number of calls")
    success_rate: float = Field(default=1.0, description="Success rate")
    average_execution_time: float = Field(default=0.0, description="Average execution time")
    last_used: Optional[datetime] = Field(default=None, description="Last usage timestamp")
    error_count: int = Field(default=0, description="Total error count")


class AdvancedCartritaTool(BaseTool):
    """Enhanced base tool with advanced features"""

    category: ToolCategory = Field(description="Tool category")
    cost_factor: float = Field(default=1.0, description="Relative cost factor")
    rate_limit: Optional[int] = Field(default=None, description="Calls per minute limit")
    dependencies: List[str] = Field(default_factory=list, description="Required dependencies")
    version: str = Field(default="1.0", description="Tool version")
    author: Optional[str] = Field(default=None, description="Tool author")

    # Runtime metrics
    _metrics = None
    _last_call_time: Optional[float] = Field(default=None, description="Last call timestamp")
    _call_history: List[float] = Field(default_factory=list, description="Recent call timestamps")

    class Config:
        arbitrary_types_allowed = True
        underscore_attrs_are_private = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not hasattr(self, '_metrics'):
            self._metrics = ToolMetrics(name=self.name)
        self._metrics.name = self.name
        self._call_history = []

    def _run(
        self,
        *args,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any
    ) -> str:
        """Enhanced run with metrics and rate limiting"""
        # Check rate limiting
        if not self._check_rate_limit():
            return f"Rate limit exceeded for tool {self.name}. Please wait."

        # Record call start
        start_time = time.time()
        self._last_call_time = start_time
        self._call_history.append(start_time)

        # Keep only recent calls for rate limiting (last hour)
        cutoff_time = start_time - 3600
        self._call_history = [t for t in self._call_history if t > cutoff_time]

        try:
            if run_manager:
                run_manager.on_text(f"Executing {self.name}...\n", color="blue")

            # Execute tool
            result = self._execute(*args, **kwargs)

            # Update metrics
            execution_time = time.time() - start_time
            self._update_metrics(True, execution_time)

            if run_manager:
                run_manager.on_text(f"Completed in {execution_time:.2f}s\n", color="green")

            return str(result)

        except Exception as e:
            execution_time = time.time() - start_time
            self._update_metrics(False, execution_time, str(e))

            if run_manager:
                run_manager.on_text(f"Error: {str(e)}\n", color="red")

            return f"Tool execution failed: {str(e)}"

    async def _arun(
        self,
        *args,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
        **kwargs: Any
    ) -> str:
        """Enhanced async run"""
        if not self._check_rate_limit():
            return f"Rate limit exceeded for tool {self.name}. Please wait."

        start_time = time.time()
        self._last_call_time = start_time
        self._call_history.append(start_time)

        cutoff_time = start_time - 3600
        self._call_history = [t for t in self._call_history if t > cutoff_time]

        try:
            if run_manager:
                await run_manager.on_text(f"Executing {self.name}...\n", color="blue")

            result = await self._aexecute(*args, **kwargs)

            execution_time = time.time() - start_time
            self._update_metrics(True, execution_time)

            if run_manager:
                await run_manager.on_text(f"Completed in {execution_time:.2f}s\n", color="green")

            return str(result)

        except Exception as e:
            execution_time = time.time() - start_time
            self._update_metrics(False, execution_time, str(e))

            if run_manager:
                await run_manager.on_text(f"Error: {str(e)}\n", color="red")

            return f"Tool execution failed: {str(e)}"

    def _execute(self, *args, **kwargs) -> Any:
        """Override in subclasses for sync execution"""
        raise NotImplementedError(f"{self.name} must implement _execute method")

    async def _aexecute(self, *args, **kwargs) -> Any:
        """Override in subclasses for async execution"""
        # Default to sync execution
        return self._execute(*args, **kwargs)

    def _check_rate_limit(self) -> bool:
        """Check if rate limit allows execution"""
        if not self.rate_limit:
            return True

        current_time = time.time()
        recent_calls = [t for t in self._call_history if t > current_time - 60]  # Last minute
        return len(recent_calls) < self.rate_limit

    def _update_metrics(self, success: bool, execution_time: float, error: Optional[str] = None):
        """Update tool metrics"""
        self._metrics.total_calls += 1
        self._metrics.last_used = datetime.now()

        if not success:
            self._metrics.error_count += 1

        # Update success rate
        self._metrics.success_rate = (
            (self._metrics.total_calls - self._metrics.error_count) / self._metrics.total_calls
        )

        # Update average execution time
        total_time = self._metrics.average_execution_time * (self._metrics.total_calls - 1)
        self._metrics.average_execution_time = (total_time + execution_time) / self._metrics.total_calls

    def get_metrics(self) -> ToolMetrics:
        """Get tool performance metrics"""
        return self._metrics.copy()

    def reset_metrics(self):
        """Reset tool metrics"""
        self._metrics = ToolMetrics(name=self.name)
        self._call_history = []


# Concrete tool implementations
class MathCalculatorTool(AdvancedCartritaTool):
    """Advanced mathematical calculator tool"""

    name: str = "math_calculator"
    description: str = "Perform mathematical calculations and evaluations"
    category: ToolCategory = ToolCategory.COMPUTATION
    cost_factor: float = 0.1

    def _execute(self, expression: str) -> str:
        """Execute mathematical expression safely"""
        import ast
        import operator
        import math

        # Safe operators
        operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.BitXor: operator.xor,
            ast.USub: operator.neg,
        }

        # Safe functions
        functions = {
            'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
            'sqrt': math.sqrt, 'log': math.log, 'exp': math.exp,
            'abs': abs, 'round': round, 'min': min, 'max': max,
            'pi': math.pi, 'e': math.e
        }

        def eval_expr(expr):
            return eval_(ast.parse(expression, mode='eval').body)

        def eval_(node):
            if isinstance(node, ast.Num):
                return node.n
            elif isinstance(node, ast.BinOp):
                return operators[type(node.op)](eval_(node.left), eval_(node.right))
            elif isinstance(node, ast.UnaryOp):
                return operators[type(node.op)](eval_(node.operand))
            elif isinstance(node, ast.Name):
                return functions.get(node.id, 0)
            elif isinstance(node, ast.Call):
                func_name = node.func.id
                if func_name in functions:
                    args = [eval_(arg) for arg in node.args]
                    return functions[func_name](*args)
            else:
                raise TypeError(f"Unsupported operation: {node}")

        try:
            result = eval_expr(expression)
            return f"Result: {result}"
        except Exception as e:
            raise ValueError(f"Invalid mathematical expression: {e}")


class FileSystemTool(AdvancedCartritaTool):
    """Safe file system operations tool"""

    name: str = "file_system"
    description: str = "Perform safe file system operations"
    category: ToolCategory = ToolCategory.FILE_SYSTEM
    cost_factor: float = 0.2
    rate_limit: int = 30  # 30 operations per minute

    def _execute(self, operation: str, path: str, content: Optional[str] = None) -> str:
        """Execute file system operation"""
        import os
        import tempfile
        from pathlib import Path

        # Security: Only allow operations in temp directory or user-specified safe paths
        safe_base = Path(tempfile.gettempdir()) / "cartrita_workspace"
        safe_base.mkdir(exist_ok=True)

        target_path = safe_base / Path(path).name  # Only filename, not full path

        if operation == "read":
            if target_path.exists():
                return target_path.read_text()
            else:
                return f"File {target_path} does not exist"

        elif operation == "write":
            if content is not None:
                target_path.write_text(content)
                return f"Successfully wrote to {target_path}"
            else:
                return "Content is required for write operation"

        elif operation == "list":
            if target_path.is_dir():
                files = [f.name for f in target_path.iterdir()]
                return f"Contents: {', '.join(files)}"
            else:
                return f"{target_path} is not a directory"

        elif operation == "delete":
            if target_path.exists():
                if target_path.is_file():
                    target_path.unlink()
                    return f"Deleted file {target_path}"
                else:
                    return "Cannot delete directories for safety"
            else:
                return f"File {target_path} does not exist"

        else:
            return f"Unsupported operation: {operation}"


class WebSearchTool(AdvancedCartritaTool):
    """Web search tool with caching"""

    name: str = "web_search"
    description: str = "Search the web for information"
    category: ToolCategory = ToolCategory.WEB_SEARCH
    cost_factor: float = 2.0
    rate_limit: int = 10  # 10 searches per minute

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not hasattr(self, '_metrics'):
            self._metrics = ToolMetrics(name=self.name)
        self._search_cache: Dict[str, Any] = {}
        self._cache_expiry: Dict[str, datetime] = {}

    def _execute(self, query: str, num_results: int = 5) -> str:
        """Execute web search with caching"""
        # Check cache first
        cache_key = f"{query}:{num_results}"
        if (cache_key in self._search_cache and
            cache_key in self._cache_expiry and
            self._cache_expiry[cache_key] > datetime.now()):
            return self._search_cache[cache_key]

        # Simulate web search (in real implementation, use actual search API)
        results = [
            {
                "title": f"Search result {i+1} for '{query}'",
                "url": f"https://example.com/result-{i+1}",
                "snippet": f"This is a relevant snippet about {query} from result {i+1}"
            }
            for i in range(min(num_results, 5))
        ]

        formatted_results = []
        for i, result in enumerate(results, 1):
            formatted_results.append(
                f"{i}. {result['title']}\n   {result['snippet']}\n   URL: {result['url']}"
            )

        result_text = "\n\n".join(formatted_results)

        # Cache result for 1 hour
        self._search_cache[cache_key] = result_text
        self._cache_expiry[cache_key] = datetime.now() + timedelta(hours=1)

        return result_text


class CodeExecutorTool(AdvancedCartritaTool):
    """Safe code execution tool"""

    name: str = "code_executor"
    description: str = "Execute code safely in sandboxed environment"
    category: ToolCategory = ToolCategory.CODE_EXECUTION
    cost_factor: float = 3.0
    rate_limit: int = 5  # 5 executions per minute

    def _execute(self, code: str, language: str = "python") -> str:
        """Execute code safely"""
        if language.lower() != "python":
            return f"Language {language} not supported. Only Python is available."

        # Security restrictions
        restricted_imports = ['os', 'sys', 'subprocess', 'importlib', '__import__']
        for restricted in restricted_imports:
            if restricted in code:
                return f"Restricted module '{restricted}' not allowed"

        try:
            # Create restricted environment
            safe_globals = {
                '__builtins__': {
                    'print': print, 'len': len, 'str': str, 'int': int, 'float': float,
                    'list': list, 'dict': dict, 'tuple': tuple, 'set': set,
                    'range': range, 'enumerate': enumerate, 'zip': zip,
                    'sum': sum, 'min': min, 'max': max, 'abs': abs, 'round': round
                }
            }

            # Capture output
            from io import StringIO
            import contextlib

            output_buffer = StringIO()
            with contextlib.redirect_stdout(output_buffer):
                exec(code, safe_globals)

            output = output_buffer.getvalue()
            return output if output else "Code executed successfully (no output)"

        except Exception as e:
            return f"Execution error: {str(e)}"


class AdvancedToolAgent:
    """
    Advanced tool management agent with LangChain integration
    Features:
    - Dynamic tool loading and unloading
    - Tool performance monitoring
    - Rate limiting and cost management
    - Tool recommendation system
    - Automatic tool selection
    """

    def __init__(
        self,
        llm: Optional[Any] = None,
        max_cost_per_session: float = 100.0,
        enable_tool_recommendation: bool = True,
        **kwargs
    ):
        # Initialize LLM
        self.llm = llm or create_chat_openai(
            model="gpt-4o",
            temperature=0.3
        )

        # Configuration
        self.max_cost_per_session = max_cost_per_session
        self.current_session_cost = 0.0
        self.enable_tool_recommendation = enable_tool_recommendation

        # Tool management
        self.tools: Dict[str, AdvancedCartritaTool] = {}
        self.tool_categories: Dict[ToolCategory, List[str]] = {}
        self.tool_usage_history: List[Dict[str, Any]] = []

        # Memory for tool usage patterns
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

        # Initialize default tools
        self._initialize_default_tools()

        # Create agent
        self._create_agent()

    def _initialize_default_tools(self):
        """Initialize default tool set"""
        default_tools = [
            MathCalculatorTool(),
            FileSystemTool(),
            WebSearchTool(),
            CodeExecutorTool()
        ]

        for tool in default_tools:
            self.add_tool(tool)

    def _create_agent(self):
        """Create LangChain agent with tools"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an advanced tool management agent. You have access to various tools
            to help users accomplish tasks. Always:
            1. Choose the most appropriate tool for each task
            2. Consider cost and performance implications
            3. Provide clear explanations of tool choices
            4. Monitor tool performance and suggest alternatives if needed

            Available tools: {tool_names}
            Session cost limit: ${max_cost}
            Current session cost: ${current_cost}"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])

        tool_list = list(self.tools.values())
        self.agent = create_openai_tools_agent(self.llm, tool_list, prompt)
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=tool_list,
            memory=self.memory,
            verbose=True,
            max_iterations=10
        )

    def add_tool(self, tool: AdvancedCartritaTool):
        """Add a tool to the agent"""
        self.tools[tool.name] = tool

        # Update category mapping
        if tool.category not in self.tool_categories:
            self.tool_categories[tool.category] = []
        self.tool_categories[tool.category].append(tool.name)

        # Recreate agent with updated tools
        self._create_agent()

    def remove_tool(self, tool_name: str) -> bool:
        """Remove a tool from the agent"""
        if tool_name not in self.tools:
            return False

        tool = self.tools[tool_name]
        del self.tools[tool_name]

        # Update category mapping
        if tool.category in self.tool_categories:
            self.tool_categories[tool.category] = [
                name for name in self.tool_categories[tool.category]
                if name != tool_name
            ]

        # Recreate agent
        self._create_agent()
        return True

    def get_tool_recommendations(self, query: str) -> List[str]:
        """Get recommended tools for a query"""
        if not self.enable_tool_recommendation:
            return list(self.tools.keys())

        query_lower = query.lower()
        recommendations = []

        # Simple keyword-based recommendation (can be enhanced with ML)
        keyword_mapping = {
            ToolCategory.COMPUTATION: ["calculate", "math", "compute", "formula"],
            ToolCategory.FILE_SYSTEM: ["file", "read", "write", "save", "load"],
            ToolCategory.WEB_SEARCH: ["search", "find", "lookup", "web", "internet"],
            ToolCategory.CODE_EXECUTION: ["code", "script", "execute", "run", "program"]
        }

        for category, keywords in keyword_mapping.items():
            if any(keyword in query_lower for keyword in keywords):
                if category in self.tool_categories:
                    recommendations.extend(self.tool_categories[category])

        return recommendations if recommendations else list(self.tools.keys())

    def execute_with_tools(self, query: str) -> str:
        """Execute query using available tools"""
        try:
            # Get tool recommendations
            recommended_tools = self.get_tool_recommendations(query)

            # Check cost constraints
            if self.current_session_cost >= self.max_cost_per_session:
                return "Session cost limit reached. Please start a new session."

            # Execute with agent
            result = self.agent_executor.invoke({
                "input": query,
                "tool_names": ", ".join(self.tools.keys()),
                "max_cost": self.max_cost_per_session,
                "current_cost": self.current_session_cost
            })

            # Update session cost (simplified calculation)
            self.current_session_cost += 1.0  # Base cost per execution

            # Record usage
            self.tool_usage_history.append({
                "timestamp": datetime.now(),
                "query": query,
                "result": result["output"],
                "cost": 1.0
            })

            return result["output"]

        except Exception as e:
            return f"Tool execution failed: {str(e)}"

    def get_tool_metrics(self) -> Dict[str, Any]:
        """Get comprehensive tool metrics"""
        metrics = {}
        for tool_name, tool in self.tools.items():
            metrics[tool_name] = tool.get_metrics().dict()

        return {
            "individual_tools": metrics,
            "session_cost": self.current_session_cost,
            "total_tools": len(self.tools),
            "tool_categories": {
                category.value: len(tools)
                for category, tools in self.tool_categories.items()
            },
            "usage_history_count": len(self.tool_usage_history)
        }

    def reset_session(self):
        """Reset session metrics and history"""
        self.current_session_cost = 0.0
        self.tool_usage_history = []
        self.memory.clear()

        # Reset tool metrics
        for tool in self.tools.values():
            tool.reset_metrics()

    def export_tool_configuration(self) -> Dict[str, Any]:
        """Export current tool configuration"""
        return {
            "tools": {
                name: {
                    "name": tool.name,
                    "description": tool.description,
                    "category": tool.category.value,
                    "cost_factor": tool.cost_factor,
                    "rate_limit": tool.rate_limit,
                    "version": tool.version
                }
                for name, tool in self.tools.items()
            },
            "configuration": {
                "max_cost_per_session": self.max_cost_per_session,
                "enable_tool_recommendation": self.enable_tool_recommendation
            },
            "metrics": self.get_tool_metrics()
        }