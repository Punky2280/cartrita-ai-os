"""
Base Agent Template following LangChain patterns
Provides standard interface for all Cartrita agents
"""

from typing import Any, Dict, List, Optional, Tuple, Union
from abc import ABC, abstractmethod

from langchain_core.callbacks import CallbackManagerForChainRun, AsyncCallbackManagerForChainRun
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.tools import BaseTool
from langchain.memory import ConversationBufferMemory
from pydantic import Field

class CartritaBaseAgent(ABC):
    """Base class for all Cartrita agents following LangChain patterns"""

    name: str = Field(..., description="Agent name")
    description: str = Field(..., description="Agent description")
    tools: List[BaseTool] = Field(default_factory=list, description="Available tools")
    memory: Optional[ConversationBufferMemory] = Field(default=None, description="Conversation memory")
    max_iterations: int = Field(default=10, description="Maximum iterations")
    verbose: bool = Field(default=False, description="Verbose output")

    class Config:
        arbitrary_types_allowed = True

    @property
    def input_keys(self) -> List[str]:
        """Input keys for the agent"""
        return ["input"]

    @property
    def return_values(self) -> List[str]:
        """Return values from the agent"""
        return ["output"]

    def plan(
        self,
        intermediate_steps: List[Tuple[AgentAction, str]],
        callbacks: Optional[CallbackManagerForChainRun] = None,
        **kwargs: Any
    ) -> Union[AgentAction, AgentFinish]:
        """
        Plan the next action based on intermediate steps

        Args:
            intermediate_steps: Previous actions and observations
            callbacks: Callback manager
            **kwargs: Additional arguments

        Returns:
            Next action or final answer
        """
        # Get current input
        input_text = kwargs.get("input", "")

        # Check if we should finish
        if self._should_finish(intermediate_steps):
            return self._create_finish(intermediate_steps, input_text)

        # Plan next action
        action = self._plan_next_action(intermediate_steps, input_text, callbacks)
        return action

    async def aplan(
        self,
        intermediate_steps: List[Tuple[AgentAction, str]],
        callbacks: Optional[AsyncCallbackManagerForChainRun] = None,
        **kwargs: Any
    ) -> Union[AgentAction, AgentFinish]:
        """
        Async version of plan

        Args:
            intermediate_steps: Previous actions and observations
            callbacks: Async callback manager
            **kwargs: Additional arguments

        Returns:
            Next action or final answer
        """
        input_text = kwargs.get("input", "")

        if self._should_finish(intermediate_steps):
            return self._create_finish(intermediate_steps, input_text)

        action = await self._aplan_next_action(intermediate_steps, input_text, callbacks)
        return action

    @abstractmethod
    def _plan_next_action(
        self,
        intermediate_steps: List[Tuple[AgentAction, str]],
        input_text: str,
        callbacks: Optional[CallbackManagerForChainRun] = None
    ) -> AgentAction:
        """Plan the next action - must be implemented by subclasses"""
        pass

    @abstractmethod
    async def _aplan_next_action(
        self,
        intermediate_steps: List[Tuple[AgentAction, str]],
        input_text: str,
        callbacks: Optional[AsyncCallbackManagerForChainRun] = None
    ) -> AgentAction:
        """Async plan next action - must be implemented by subclasses"""
        pass

    def _should_finish(self, intermediate_steps: List[Tuple[AgentAction, str]]) -> bool:
        """Check if agent should finish"""
        # Check max iterations
        if len(intermediate_steps) >= self.max_iterations:
            return True

        # Check for completion signals in observations
        if intermediate_steps:
            last_observation = intermediate_steps[-1][1]
            if "final answer:" in last_observation.lower():
                return True

        return False

    def _create_finish(
        self,
        intermediate_steps: List[Tuple[AgentAction, str]],
        input_text: str
    ) -> AgentFinish:
        """Create final answer"""
        if intermediate_steps:
            # Get last observation as final answer
            final_answer = intermediate_steps[-1][1]
        else:
            final_answer = f"No answer found for: {input_text}"

        return AgentFinish(
            return_values={"output": final_answer},
            log=f"Agent {self.name} finished"
        )

    def get_tools(self) -> List[BaseTool]:
        """Get available tools"""
        return self.tools

    def add_tool(self, tool: BaseTool) -> None:
        """Add a tool to the agent"""
        self.tools.append(tool)

    def remove_tool(self, tool_name: str) -> None:
        """Remove a tool by name"""
        self.tools = [t for t in self.tools if t.name != tool_name]

    def save_memory(self) -> Dict:
        """Save conversation memory"""
        if self.memory:
            return self.memory.save_context({}, {})
        return {}

    def load_memory(self, memory_dict: Dict) -> None:
        """Load conversation memory"""
        if self.memory and memory_dict:
            self.memory.load_memory_variables(memory_dict)

    def clear_memory(self) -> None:
        """Clear conversation memory"""
        if self.memory:
            self.memory.clear()

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "CartritaBaseAgent":
        """Create agent from configuration"""
        return cls(**config)

    def to_config(self) -> Dict[str, Any]:
        """Export agent configuration"""
        return {
            "name": self.name,
            "description": self.description,
            "max_iterations": self.max_iterations,
            "verbose": self.verbose
        }
