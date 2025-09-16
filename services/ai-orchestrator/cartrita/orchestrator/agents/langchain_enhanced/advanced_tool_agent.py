"""
Advanced Tool Agent with LangChain
Implements sophisticated tool management and execution patterns
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from cartrita.orchestrator.utils.llm_factory import create_chat_openai
from .base_tool import ToolCategory, AdvancedCartritaTool
from .tools_math import MathCalculatorTool
from .tools_filesystem import FileSystemTool
from .tools_websearch import WebSearchTool
from .tools_code import CodeExecutorTool


try:
    from langchain.agents import AgentExecutor, create_openai_tools_agent  # type: ignore
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder  # type: ignore
    from langchain.memory import ConversationBufferMemory  # type: ignore
    LANGCHAIN_AVAILABLE = True
except Exception:  # pragma: no cover - optional dependency path
    LANGCHAIN_AVAILABLE = False

    class ConversationBufferMemory:  # type: ignore
        def __init__(self, memory_key: str = "chat_history", return_messages: bool = True, **kwargs):
            self.memory_key = memory_key
            self.return_messages = return_messages

        def clear(self):
            pass

    class ChatPromptTemplate:  # type: ignore
        @classmethod
        def from_messages(cls, messages):
            return messages

    class MessagesPlaceholder:  # type: ignore
        def __init__(self, variable_name: str):
            self.variable_name = variable_name


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
        default_tools = [MathCalculatorTool(), FileSystemTool(), WebSearchTool(), CodeExecutorTool()]

        for tool in default_tools:
            self.add_tool(tool)

    def _create_agent(self):
        """Create LangChain agent with tools"""
        if not LANGCHAIN_AVAILABLE:
            # Gracefully degrade when LangChain is unavailable
            self.agent = None
            self.agent_executor = None
            return

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
            # Check cost constraints
            if self.current_session_cost >= self.max_cost_per_session:
                return "Session cost limit reached. Please start a new session."

            if self.agent_executor is None:
                return "LangChain is not installed; agent features are unavailable. Please install 'langchain' to enable tool execution."

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
