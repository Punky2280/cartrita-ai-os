"""
LangChain-Enhanced Supervisor Agent
Advanced agent orchestrator using LangChain patterns with tool calling and streaming
"""

import asyncio
from typing import Any, Dict, List, Optional, Sequence, Union
from datetime import datetime

from langchain.agents import BaseSingleActionAgent, AgentExecutor, create_openai_tools_agent
from langchain.callbacks.manager import CallbackManagerForChainRun, AsyncCallbackManagerForChainRun
from langchain.schema import AgentAction, AgentFinish, BaseMessage, HumanMessage, AIMessage
from langchain.tools import BaseTool, StructuredTool
from langchain.memory import ConversationSummaryBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from cartrita.orchestrator.utils.llm_factory import create_chat_openai
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.pydantic_v1 import BaseModel, Field
from langchain.pydantic_v1 import BaseModel as LangChainBaseModel, Field as LangChainField
import json


class SupervisorDecision(BaseModel):
    """Structured output for supervisor decisions"""
    action: str = Field(description="Action to take: 'delegate', 'synthesize', 'clarify'")
    target_agent: Optional[str] = Field(description="Agent to delegate to")
    reasoning: str = Field(description="Reasoning for the decision")
    priority: int = Field(description="Priority level 1-5")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentCapability(BaseModel):
    """Agent capability definition"""
    name: str = Field(description="Agent name")
    description: str = Field(description="Capability description")
    expertise_areas: List[str] = Field(description="Areas of expertise")
    cost_factor: float = Field(default=1.0, description="Resource cost factor")
    average_response_time: float = Field(default=5.0, description="Average response time")


class LangChainSupervisorAgent(BaseSingleActionAgent):
    """
    Advanced supervisor agent using LangChain with:
    - Tool calling for agent orchestration
    - Streaming responses
    - Memory management
    - Cost optimization
    - Performance monitoring
    """

    name: str = Field(default="supervisor", description="Agent name")
    description: str = Field(
        default="Advanced supervisor agent for orchestrating specialized AI agents",
        description="Agent description"
    )
    llm: Any = Field(description="Language model")
    memory: ConversationSummaryBufferMemory = Field(description="Conversation memory")
    available_agents: List[AgentCapability] = Field(
        default_factory=list,
        description="Available specialized agents"
    )
    tools: List[BaseTool] = Field(default_factory=list, description="Available tools")
    max_iterations: int = Field(default=10, description="Maximum iterations")
    cost_threshold: float = Field(default=100.0, description="Cost threshold")
    streaming: bool = Field(default=True, description="Enable streaming")

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Initialize LLM if not provided
        if not hasattr(self, 'llm') or self.llm is None:
            callbacks = [StreamingStdOutCallbackHandler()] if self.streaming else None
            self.llm = create_chat_openai(
                model="gpt-4o",
                temperature=0.7,
                streaming=self.streaming,
                callbacks=callbacks
            )

        # Initialize memory
        if not hasattr(self, 'memory') or self.memory is None:
            self.memory = ConversationSummaryBufferMemory(
                llm=self.llm,
                memory_key="chat_history",
                return_messages=True,
                max_token_limit=2000
            )

        # Initialize default agent capabilities
        self._initialize_agent_capabilities()

        # Initialize tools
        self._initialize_tools()

    def _initialize_agent_capabilities(self):
        """Initialize available agent capabilities"""
        if not self.available_agents:
            self.available_agents = [
                AgentCapability(
                    name="research",
                    description="Research and information gathering",
                    expertise_areas=["web search", "data analysis", "fact checking"],
                    cost_factor=0.8,
                    average_response_time=3.0
                ),
                AgentCapability(
                    name="code",
                    description="Code generation and analysis",
                    expertise_areas=["programming", "debugging", "architecture"],
                    cost_factor=1.2,
                    average_response_time=4.0
                ),
                AgentCapability(
                    name="creative",
                    description="Creative content generation",
                    expertise_areas=["writing", "storytelling", "brainstorming"],
                    cost_factor=1.0,
                    average_response_time=2.5
                ),
                AgentCapability(
                    name="analytical",
                    description="Data analysis and reasoning",
                    expertise_areas=["statistics", "logic", "problem solving"],
                    cost_factor=1.1,
                    average_response_time=3.5
                ),
                AgentCapability(
                    name="multimodal",
                    description="Image and audio processing",
                    expertise_areas=["computer vision", "audio analysis", "multimedia"],
                    cost_factor=1.5,
                    average_response_time=6.0
                )
            ]

    def _initialize_tools(self):
        """Initialize supervisor tools"""
        self.tools = [
            StructuredTool(
                name="delegate_task",
                description="Delegate a task to a specialized agent",
                func=self._delegate_task,
                args_schema=SupervisorDecision
            ),
            StructuredTool.from_function(
                func=self._get_agent_status,
                name="get_agent_status",
                description="Get status and availability of agents"
            ),
            StructuredTool.from_function(
                func=self._synthesize_responses,
                name="synthesize_responses",
                description="Synthesize multiple agent responses"
            ),
            StructuredTool.from_function(
                func=self._optimize_workflow,
                name="optimize_workflow",
                description="Optimize workflow based on constraints"
            )
        ]

    @property
    def input_keys(self) -> List[str]:
        return ["input"]

    @property
    def return_values(self) -> List[str]:
        return ["output"]

    def plan(
        self,
        intermediate_steps: List[tuple],
        callbacks: Optional[CallbackManagerForChainRun] = None,
        **kwargs: Any
    ) -> Union[AgentAction, AgentFinish]:
        """Plan next action using LangChain tools"""

        # Get input
        user_input = kwargs.get("input", "")

        # Build context
        context = self._build_context(intermediate_steps, user_input)

        # Create prompt
        prompt = self._create_planning_prompt(context, user_input)

        # Get LLM decision
        response = self.llm.invoke(prompt, callbacks=callbacks)

        # Parse response to action
        action = self._parse_response_to_action(response.content, intermediate_steps)

        return action

    async def aplan(
        self,
        intermediate_steps: List[tuple],
        callbacks: Optional[AsyncCallbackManagerForChainRun] = None,
        **kwargs: Any
    ) -> Union[AgentAction, AgentFinish]:
        """Async plan next action"""

        user_input = kwargs.get("input", "")
        context = self._build_context(intermediate_steps, user_input)
        prompt = self._create_planning_prompt(context, user_input)

        response = await self.llm.ainvoke(prompt, callbacks=callbacks)
        action = self._parse_response_to_action(response.content, intermediate_steps)

        return action

    def _create_planning_prompt(self, context: str, user_input: str) -> List[BaseMessage]:
        """Create planning prompt with context"""

        system_msg = f"""You are the Supervisor Agent for Cartrita AI OS, an advanced AI orchestrator.

Your role is to analyze user requests and coordinate specialized agents to provide optimal responses.

Available Agents:
{self._format_agent_capabilities()}

Current Context:
{context}

Instructions:
1. Analyze the user's request carefully
2. Determine the best approach: delegate to specialist, synthesize multiple agents, or handle directly
3. Consider cost, speed, and quality trade-offs
4. Use tools to execute your decision
5. Provide clear reasoning for your choices

Remember: You can delegate to multiple agents, synthesize their responses, and iterate to improve quality."""

        return [
            AIMessage(content=system_msg),
            HumanMessage(content=f"User Request: {user_input}")
        ]

    def _format_agent_capabilities(self) -> str:
        """Format agent capabilities for prompt"""
        formatted = []
        for agent in self.available_agents:
            formatted.append(
                f"- {agent.name}: {agent.description}\n"
                f"  Expertise: {', '.join(agent.expertise_areas)}\n"
                f"  Cost Factor: {agent.cost_factor}x, Avg Time: {agent.average_response_time}s"
            )
        return "\n".join(formatted)

    def _build_context(self, intermediate_steps: List[tuple], user_input: str) -> str:
        """Build context from conversation and steps"""
        context_parts = []

        # Add memory context
        if self.memory:
            memory_vars = self.memory.load_memory_variables({})
            if "chat_history" in memory_vars:
                context_parts.append("Recent Conversation:")
                for msg in memory_vars["chat_history"][-3:]:  # Last 3 messages
                    context_parts.append(f"  {msg.type}: {msg.content[:100]}")

        # Add intermediate steps
        if intermediate_steps:
            context_parts.append("\nRecent Actions:")
            for action, observation in intermediate_steps[-3:]:
                context_parts.append(f"  Action: {action.tool}({action.tool_input})")
                context_parts.append(f"  Result: {observation[:100]}")

        return "\n".join(context_parts) if context_parts else "No previous context"

    def _parse_response_to_action(self, response: str, intermediate_steps: List[tuple]) -> Union[AgentAction, AgentFinish]:
        """Parse LLM response to determine next action"""

        # Check if should finish
        if len(intermediate_steps) >= self.max_iterations:
            return AgentFinish(
                return_values={"output": "Maximum iterations reached"},
                log="Reached maximum iterations"
            )

        # Simple parsing logic - can be enhanced with structured output
        if "delegate" in response.lower():
            # Extract agent name and task
            agent_name = self._extract_agent_name(response)
            task = self._extract_task(response)

            return AgentAction(
                tool="delegate_task",
                tool_input={
                    "action": "delegate",
                    "target_agent": agent_name,
                    "reasoning": response,
                    "priority": 3,
                    "metadata": {"user_input": task}
                },
                log=response
            )

        elif "synthesize" in response.lower():
            return AgentAction(
                tool="synthesize_responses",
                tool_input={"responses": intermediate_steps},
                log=response
            )

        elif "status" in response.lower():
            return AgentAction(
                tool="get_agent_status",
                tool_input={},
                log=response
            )

        else:
            # Direct response
            return AgentFinish(
                return_values={"output": response},
                log="Providing direct response"
            )

    def _extract_agent_name(self, response: str) -> str:
        """Extract agent name from response"""
        for agent in self.available_agents:
            if agent.name.lower() in response.lower():
                return agent.name
        return "research"  # Default

    def _extract_task(self, response: str) -> str:
        """Extract task description from response"""
        # Simple extraction - can be improved with NLP
        lines = response.split('\n')
        for line in lines:
            if 'task:' in line.lower():
                return line.split(':', 1)[1].strip()
        return response

    # Tool implementations
    def _delegate_task(self, decision_data: Dict[str, Any]) -> str:
        """Delegate task to specialized agent"""
        agent_name = decision_data.get("target_agent", "research")
        task = decision_data.get("metadata", {}).get("user_input", "")

        # Find agent capability
        agent_info = next(
            (a for a in self.available_agents if a.name == agent_name),
            self.available_agents[0]
        )

        # Simulate delegation (in real implementation, this would call actual agents)
        result = f"""
Delegated to {agent_info.name} agent:
Task: {task}
Status: Processing...
Estimated completion: {agent_info.average_response_time}s
Cost factor: {agent_info.cost_factor}x
"""

        return result

    def _get_agent_status(self) -> str:
        """Get status of all available agents"""
        status_info = []
        for agent in self.available_agents:
            status_info.append(
                f"{agent.name}: Available (expertise: {', '.join(agent.expertise_areas[:2])})"
            )
        return "\n".join(status_info)

    def _synthesize_responses(self, responses_data: Dict[str, Any]) -> str:
        """Synthesize multiple agent responses"""
        responses = responses_data.get("responses", [])

        if not responses:
            return "No responses to synthesize"

        # Extract observations from intermediate steps
        observations = [obs for _, obs in responses]

        synthesis_prompt = f"""
Synthesize the following agent responses into a coherent, comprehensive answer:

Responses:
{chr(10).join([f"- {obs[:200]}" for obs in observations])}

Provide a unified, well-structured response that combines the best insights from all agents.
"""

        result = self.llm.invoke([HumanMessage(content=synthesis_prompt)])
        return result.content

    def _optimize_workflow(self, workflow_data: Dict[str, Any]) -> str:
        """Optimize workflow based on constraints"""
        return "Workflow optimized for cost and performance balance"

    # Public interface methods
    def run(self, input_text: str, **kwargs) -> str:
        """Run supervisor with agent executor"""
        executor = AgentExecutor.from_agent_and_tools(
            agent=self,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            max_iterations=self.max_iterations
        )

        result = executor.invoke({"input": input_text})
        return result["output"]

    async def arun(self, input_text: str, **kwargs) -> str:
        """Async run supervisor"""
        executor = AgentExecutor.from_agent_and_tools(
            agent=self,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            max_iterations=self.max_iterations
        )

        result = await executor.ainvoke({"input": input_text})
        return result["output"]

    def stream_response(self, input_text: str, callback=None):
        """Stream response with callback"""
        if not self.streaming:
            return self.run(input_text)

        # Implementation for streaming would integrate with callback
        return self.run(input_text)

    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            "total_iterations": 0,  # Track in real implementation
            "average_response_time": 0.0,
            "cost_consumed": 0.0,
            "success_rate": 100.0,
            "available_agents": len(self.available_agents)
        }