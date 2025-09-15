#!/usr/bin/env python3
"""
LangChain Agent Refactoring Script
Refactors existing agents to follow LangChain patterns and best practices
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class AgentRefactorer:
    def __init__(self):
        self.agents_dir = Path("services/ai-orchestrator/cartrita/orchestrator/agents")
        self.backup_dir = Path("services/ai-orchestrator/cartrita/orchestrator/agents_backup")
        self.templates_created = []

    def create_backup(self):
        """Create backup of existing agents"""
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        shutil.copytree(self.agents_dir, self.backup_dir)
        print(f"Backup created at {self.backup_dir}")

    def create_base_agent_template(self) -> str:
        """Create LangChain-compatible base agent template"""
        template = '''"""
Base Agent Template following LangChain patterns
Provides standard interface for all Cartrita agents
"""

from typing import Any, Dict, List, Optional, Sequence, Tuple, Union
from abc import ABC, abstractmethod
import asyncio
from datetime import datetime

from langchain.agents import BaseSingleActionAgent
from langchain.callbacks.manager import CallbackManagerForChainRun, AsyncCallbackManagerForChainRun
from langchain.schema import (
    AgentAction,
    AgentFinish,
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage
)
from langchain.tools import BaseTool
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field

class CartritaBaseAgent(BaseSingleActionAgent, ABC):
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
'''
        return template

    def create_tool_template(self) -> str:
        """Create LangChain tool template"""
        template = '''"""
LangChain Tool Template for Cartrita
Standard tool implementation following LangChain patterns
"""

from typing import Any, Optional, Type
from langchain.tools import BaseTool
from langchain.callbacks.manager import CallbackManagerForToolRun, AsyncCallbackManagerForToolRun
from pydantic import BaseModel, Field

class CartritaToolInput(BaseModel):
    """Input schema for Cartrita tools"""
    query: str = Field(..., description="Input query or command")
    parameters: Optional[Dict[str, Any]] = Field(default=None, description="Additional parameters")

class CartritaBaseTool(BaseTool):
    """Base tool class for Cartrita following LangChain patterns"""

    name: str = "cartrita_tool"
    description: str = "Base Cartrita tool"
    args_schema: Type[BaseModel] = CartritaToolInput
    return_direct: bool = False

    def _run(
        self,
        query: str,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any
    ) -> str:
        """
        Execute the tool synchronously

        Args:
            query: Input query
            run_manager: Callback manager
            **kwargs: Additional arguments

        Returns:
            Tool output as string
        """
        try:
            # Log tool execution
            if run_manager:
                run_manager.on_text(f"Executing {self.name} with query: {query}\\n")

            # Execute tool logic
            result = self._execute(query, **kwargs)

            # Log result
            if run_manager:
                run_manager.on_text(f"Result: {result}\\n")

            return result

        except Exception as e:
            error_msg = f"Error in {self.name}: {str(e)}"
            if run_manager:
                run_manager.on_text(f"Error: {error_msg}\\n", color="red")
            return error_msg

    async def _arun(
        self,
        query: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
        **kwargs: Any
    ) -> str:
        """
        Execute the tool asynchronously

        Args:
            query: Input query
            run_manager: Async callback manager
            **kwargs: Additional arguments

        Returns:
            Tool output as string
        """
        try:
            if run_manager:
                await run_manager.on_text(f"Executing {self.name} with query: {query}\\n")

            result = await self._aexecute(query, **kwargs)

            if run_manager:
                await run_manager.on_text(f"Result: {result}\\n")

            return result

        except Exception as e:
            error_msg = f"Error in {self.name}: {str(e)}"
            if run_manager:
                await run_manager.on_text(f"Error: {error_msg}\\n", color="red")
            return error_msg

    def _execute(self, query: str, **kwargs: Any) -> str:
        """Execute tool logic - override in subclasses"""
        raise NotImplementedError(f"{self.name} must implement _execute method")

    async def _aexecute(self, query: str, **kwargs: Any) -> str:
        """Async execute tool logic - override in subclasses"""
        # Default to sync execution
        return self._execute(query, **kwargs)

    @classmethod
    def from_function(
        cls,
        func: Callable,
        name: str,
        description: str,
        args_schema: Optional[Type[BaseModel]] = None,
        return_direct: bool = False
    ) -> "CartritaBaseTool":
        """Create tool from a function"""
        class FunctionTool(cls):
            def _execute(self, query: str, **kwargs: Any) -> str:
                return str(func(query, **kwargs))

        return FunctionTool(
            name=name,
            description=description,
            args_schema=args_schema or CartritaToolInput,
            return_direct=return_direct
        )
'''
        return template

    def create_chain_template(self) -> str:
        """Create LangChain chain template"""
        template = '''"""
LangChain Chain Template for Cartrita
Implements chain patterns for composable workflows
"""

from typing import Any, Dict, List, Optional
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.schema import BasePromptTemplate
from langchain.callbacks.manager import CallbackManagerForChainRun, AsyncCallbackManagerForChainRun
from langchain.base_language import BaseLanguageModel
from pydantic import BaseModel, Field

class CartritaChain(LLMChain):
    """Custom chain for Cartrita following LangChain patterns"""

    chain_type: str = Field(default="cartrita", description="Chain type identifier")

    @classmethod
    def from_prompt(
        cls,
        llm: BaseLanguageModel,
        prompt: BasePromptTemplate,
        **kwargs: Any
    ) -> "CartritaChain":
        """Create chain from prompt template"""
        return cls(llm=llm, prompt=prompt, **kwargs)

    def _call(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None
    ) -> Dict[str, Any]:
        """Execute the chain"""
        # Log chain execution
        if run_manager:
            run_manager.on_text(f"Executing {self.chain_type} chain\\n")

        # Prepare inputs
        prompt_value = self.prompt.format_prompt(**inputs)

        # Execute LLM
        if run_manager:
            response = self.llm.generate_prompt(
                [prompt_value],
                callbacks=run_manager.get_child()
            )
        else:
            response = self.llm.generate_prompt([prompt_value])

        # Extract output
        output = self.output_parser.parse(response.generations[0][0].text)

        # Log output
        if run_manager:
            run_manager.on_text(f"Chain output: {output}\\n", color="green")

        return {self.output_key: output}

    async def _acall(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[AsyncCallbackManagerForChainRun] = None
    ) -> Dict[str, Any]:
        """Async execute the chain"""
        if run_manager:
            await run_manager.on_text(f"Executing {self.chain_type} chain\\n")

        prompt_value = self.prompt.format_prompt(**inputs)

        if run_manager:
            response = await self.llm.agenerate_prompt(
                [prompt_value],
                callbacks=run_manager.get_child()
            )
        else:
            response = await self.llm.agenerate_prompt([prompt_value])

        output = self.output_parser.parse(response.generations[0][0].text)

        if run_manager:
            await run_manager.on_text(f"Chain output: {output}\\n", color="green")

        return {self.output_key: output}

    @property
    def _chain_type(self) -> str:
        """Return chain type"""
        return self.chain_type

class CartritaSequentialChain:
    """Sequential chain for multi-step workflows"""

    def __init__(self, chains: List[LLMChain], **kwargs):
        self.chains = chains
        self.return_all = kwargs.get("return_all", False)

    def run(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Run chains sequentially"""
        results = {}
        current_inputs = inputs.copy()

        for i, chain in enumerate(self.chains):
            output = chain.run(current_inputs)

            if self.return_all:
                results[f"step_{i}"] = output

            # Update inputs for next chain
            current_inputs.update(output)

        if self.return_all:
            return results
        return output

    async def arun(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Async run chains sequentially"""
        results = {}
        current_inputs = inputs.copy()

        for i, chain in enumerate(self.chains):
            output = await chain.arun(current_inputs)

            if self.return_all:
                results[f"step_{i}"] = output

            current_inputs.update(output)

        if self.return_all:
            return results
        return output
'''
        return template

    def create_memory_template(self) -> str:
        """Create LangChain memory template"""
        template = '''"""
LangChain Memory Template for Cartrita
Implements memory patterns for conversation management
"""

from typing import Any, Dict, List, Optional
from langchain.memory import ConversationBufferMemory, ConversationSummaryMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from pydantic import BaseModel, Field

class CartritaMemory(ConversationBufferMemory):
    """Custom memory implementation for Cartrita"""

    max_token_limit: int = Field(default=2000, description="Maximum tokens to store")
    summarize_after: int = Field(default=10, description="Summarize after N messages")

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, Any]) -> None:
        """Save conversation context"""
        # Convert to messages
        if "input" in inputs:
            self.chat_memory.add_user_message(inputs["input"])
        if "output" in outputs:
            self.chat_memory.add_ai_message(outputs["output"])

        # Check if summarization needed
        if len(self.chat_memory.messages) > self.summarize_after:
            self._summarize_old_messages()

    def _summarize_old_messages(self) -> None:
        """Summarize old messages to save tokens"""
        # Keep recent messages, summarize old ones
        recent_messages = self.chat_memory.messages[-5:]
        old_messages = self.chat_memory.messages[:-5]

        if old_messages:
            # Create summary (simplified for template)
            summary = f"Previous conversation summary: {len(old_messages)} messages exchanged"

            # Clear and rebuild memory
            self.chat_memory.clear()
            self.chat_memory.add_ai_message(summary)
            for msg in recent_messages:
                self.chat_memory.messages.append(msg)

class CartritaEntityMemory:
    """Entity memory for tracking entities in conversation"""

    def __init__(self):
        self.entities: Dict[str, Dict[str, Any]] = {}

    def add_entity(self, entity_type: str, entity_name: str, attributes: Dict[str, Any]) -> None:
        """Add or update an entity"""
        if entity_type not in self.entities:
            self.entities[entity_type] = {}
        self.entities[entity_type][entity_name] = attributes

    def get_entity(self, entity_type: str, entity_name: str) -> Optional[Dict[str, Any]]:
        """Get entity information"""
        if entity_type in self.entities:
            return self.entities[entity_type].get(entity_name)
        return None

    def get_all_entities(self, entity_type: Optional[str] = None) -> Dict[str, Any]:
        """Get all entities or entities of a specific type"""
        if entity_type:
            return self.entities.get(entity_type, {})
        return self.entities

    def clear_entities(self, entity_type: Optional[str] = None) -> None:
        """Clear entities"""
        if entity_type:
            if entity_type in self.entities:
                del self.entities[entity_type]
        else:
            self.entities.clear()

    def to_context_string(self) -> str:
        """Convert entities to context string for prompts"""
        context_parts = []
        for entity_type, entities in self.entities.items():
            context_parts.append(f"{entity_type}:")
            for name, attrs in entities.items():
                attrs_str = ", ".join(f"{k}={v}" for k, v in attrs.items())
                context_parts.append(f"  - {name}: {attrs_str}")
        return "\\n".join(context_parts)
'''
        return template

    def create_callbacks_template(self) -> str:
        """Create LangChain callbacks template"""
        template = '''"""
LangChain Callbacks Template for Cartrita
Implements callback patterns for monitoring and debugging
"""

from typing import Any, Dict, List, Optional, Union
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import AgentAction, AgentFinish, LLMResult
import logging
from datetime import datetime

class CartritaCallbackHandler(BaseCallbackHandler):
    """Custom callback handler for Cartrita agents"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.start_time = None
        self.metrics = {
            "llm_calls": 0,
            "tool_calls": 0,
            "errors": 0,
            "tokens_used": 0
        }

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        """Called when LLM starts"""
        self.metrics["llm_calls"] += 1
        self.logger.debug(f"LLM started with {len(prompts)} prompts")

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """Called when LLM ends"""
        # Track tokens if available
        if hasattr(response, "llm_output") and response.llm_output:
            if "token_usage" in response.llm_output:
                self.metrics["tokens_used"] += response.llm_output["token_usage"].get("total_tokens", 0)

        self.logger.debug("LLM completed successfully")

    def on_llm_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Called when LLM errors"""
        self.metrics["errors"] += 1
        self.logger.error(f"LLM error: {error}")

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """Called when tool starts"""
        self.metrics["tool_calls"] += 1
        tool_name = serialized.get("name", "unknown")
        self.logger.debug(f"Tool {tool_name} started with input: {input_str[:100]}")

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Called when tool ends"""
        self.logger.debug(f"Tool completed with output: {output[:100]}")

    def on_tool_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Called when tool errors"""
        self.metrics["errors"] += 1
        self.logger.error(f"Tool error: {error}")

    def on_agent_action(self, action: AgentAction, **kwargs: Any) -> None:
        """Called when agent takes an action"""
        self.logger.info(f"Agent action: {action.tool} with input: {action.tool_input}")

    def on_agent_finish(self, finish: AgentFinish, **kwargs: Any) -> None:
        """Called when agent finishes"""
        self.logger.info(f"Agent finished: {finish.return_values}")

    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> None:
        """Called when chain starts"""
        self.start_time = datetime.now()
        self.logger.info(f"Chain started: {serialized.get('name', 'unknown')}")

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Called when chain ends"""
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            self.logger.info(f"Chain completed in {duration:.2f} seconds")
        self.logger.debug(f"Chain outputs: {outputs}")

    def on_chain_error(
        self, error: Union[Exception, KeyboardInterrupt], **kwargs: Any
    ) -> None:
        """Called when chain errors"""
        self.metrics["errors"] += 1
        self.logger.error(f"Chain error: {error}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get collected metrics"""
        return self.metrics.copy()

    def reset_metrics(self) -> None:
        """Reset metrics"""
        self.metrics = {
            "llm_calls": 0,
            "tool_calls": 0,
            "errors": 0,
            "tokens_used": 0
        }

class CartritaStreamingCallbackHandler(BaseCallbackHandler):
    """Callback handler for streaming responses"""

    def __init__(self, stream_handler: Callable[[str], None]):
        self.stream_handler = stream_handler

    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Called when LLM generates a new token"""
        self.stream_handler(token)

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """Stream tool execution start"""
        tool_name = serialized.get("name", "unknown")
        self.stream_handler(f"\\n[Executing {tool_name}...]\\n")

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Stream tool execution end"""
        self.stream_handler(f"\\n[Tool result: {output[:100]}...]\\n")
'''
        return template

    def refactor_agent(self, agent_path: Path) -> bool:
        """Refactor a single agent to follow LangChain patterns"""
        try:
            # Read existing agent
            with open(agent_path, 'r') as f:
                content = f.read()

            # Check if already uses LangChain
            if 'from langchain' in content:
                print(f"Agent {agent_path.name} already uses LangChain")
                return True

            # Create refactored version
            refactored_content = self._generate_refactored_agent(agent_path.stem, content)

            # Save refactored version
            refactored_path = agent_path.parent / f"{agent_path.stem}_langchain.py"
            with open(refactored_path, 'w') as f:
                f.write(refactored_content)

            print(f"Created refactored agent: {refactored_path}")
            return True

        except Exception as e:
            print(f"Error refactoring {agent_path}: {e}")
            return False

    def _generate_refactored_agent(self, agent_name: str, original_content: str) -> str:
        """Generate refactored agent code"""
        # Extract agent class name
        class_name = agent_name.replace('_agent', '').title().replace('_', '') + 'Agent'

        refactored = f'''"""
{class_name} - Refactored with LangChain patterns
Auto-generated from original agent implementation
"""

from typing import Any, Dict, List, Optional, Tuple
from langchain.callbacks.manager import CallbackManagerForChainRun, AsyncCallbackManagerForChainRun
from langchain.schema import AgentAction, AgentFinish
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from pydantic import Field
import os

# Import base agent
from .base_agent_langchain import CartritaBaseAgent

class {class_name}(CartritaBaseAgent):
    """LangChain-compatible {agent_name.replace('_', ' ').title()}"""

    name: str = Field(default="{agent_name}", description="Agent name")
    description: str = Field(
        default="Refactored {agent_name.replace('_', ' ')} using LangChain patterns",
        description="Agent description"
    )
    llm: Optional[ChatOpenAI] = Field(default=None, description="Language model")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Initialize LLM if not provided
        if not self.llm:
            self.llm = ChatOpenAI(
                model="gpt-4",
                temperature=0.7,
                streaming=True
            )

        # Initialize memory if not provided
        if not self.memory:
            self.memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )

        # Initialize tools
        self._initialize_tools()

    def _initialize_tools(self):
        """Initialize agent-specific tools"""
        # Add default tools based on agent type
        pass

    def _plan_next_action(
        self,
        intermediate_steps: List[Tuple[AgentAction, str]],
        input_text: str,
        callbacks: Optional[CallbackManagerForChainRun] = None
    ) -> AgentAction:
        """Plan the next action"""

        # Build context from intermediate steps
        context = self._build_context(intermediate_steps)

        # Create prompt
        prompt = f"""
        You are {self.name}, {self.description}

        Context: {context}
        User Input: {input_text}

        Available tools: {[tool.name for tool in self.tools]}

        What is the next action to take?
        Respond with the tool name and input.
        """

        # Get LLM response
        response = self.llm.predict(prompt, callbacks=callbacks)

        # Parse response to get action
        action = self._parse_action(response)
        return action

    async def _aplan_next_action(
        self,
        intermediate_steps: List[Tuple[AgentAction, str]],
        input_text: str,
        callbacks: Optional[AsyncCallbackManagerForChainRun] = None
    ) -> AgentAction:
        """Async plan the next action"""

        context = self._build_context(intermediate_steps)

        prompt = f"""
        You are {self.name}, {self.description}

        Context: {context}
        User Input: {input_text}

        Available tools: {[tool.name for tool in self.tools]}

        What is the next action to take?
        """

        response = await self.llm.apredict(prompt, callbacks=callbacks)
        action = self._parse_action(response)
        return action

    def _build_context(self, intermediate_steps: List[Tuple[AgentAction, str]]) -> str:
        """Build context from intermediate steps"""
        if not intermediate_steps:
            return "No previous actions"

        context_parts = []
        for action, observation in intermediate_steps:
            context_parts.append(f"Action: {action.tool}({action.tool_input})")
            context_parts.append(f"Observation: {observation}")

        return "\\n".join(context_parts)

    def _parse_action(self, response: str) -> AgentAction:
        """Parse LLM response to extract action"""
        # Simple parsing - can be enhanced
        lines = response.strip().split('\\n')

        # Default action if parsing fails
        tool = self.tools[0].name if self.tools else "default_tool"
        tool_input = response

        # Try to extract tool and input
        for line in lines:
            if 'tool:' in line.lower():
                tool = line.split(':')[1].strip()
            elif 'input:' in line.lower():
                tool_input = line.split(':')[1].strip()

        return AgentAction(
            tool=tool,
            tool_input=tool_input,
            log=response
        )

    def run(self, input_text: str, **kwargs) -> str:
        """Run the agent"""
        from langchain.agents import AgentExecutor

        executor = AgentExecutor.from_agent_and_tools(
            agent=self,
            tools=self.tools,
            memory=self.memory,
            verbose=self.verbose
        )

        result = executor.run(input_text, **kwargs)
        return result

    async def arun(self, input_text: str, **kwargs) -> str:
        """Async run the agent"""
        from langchain.agents import AgentExecutor

        executor = AgentExecutor.from_agent_and_tools(
            agent=self,
            tools=self.tools,
            memory=self.memory,
            verbose=self.verbose
        )

        result = await executor.arun(input_text, **kwargs)
        return result
'''
        return refactored

    def create_langchain_templates(self):
        """Create all LangChain template files"""
        templates_dir = self.agents_dir / "langchain_templates"
        templates_dir.mkdir(exist_ok=True)

        # Create base agent template
        base_agent_path = templates_dir / "base_agent_langchain.py"
        with open(base_agent_path, 'w') as f:
            f.write(self.create_base_agent_template())
        self.templates_created.append(base_agent_path)

        # Create tool template
        tool_path = templates_dir / "tool_langchain.py"
        with open(tool_path, 'w') as f:
            f.write(self.create_tool_template())
        self.templates_created.append(tool_path)

        # Create chain template
        chain_path = templates_dir / "chain_langchain.py"
        with open(chain_path, 'w') as f:
            f.write(self.create_chain_template())
        self.templates_created.append(chain_path)

        # Create memory template
        memory_path = templates_dir / "memory_langchain.py"
        with open(memory_path, 'w') as f:
            f.write(self.create_memory_template())
        self.templates_created.append(memory_path)

        # Create callbacks template
        callbacks_path = templates_dir / "callbacks_langchain.py"
        with open(callbacks_path, 'w') as f:
            f.write(self.create_callbacks_template())
        self.templates_created.append(callbacks_path)

        print(f"Created {len(self.templates_created)} LangChain templates")

    def refactor_all_agents(self):
        """Refactor all existing agents"""
        agent_files = []
        for agent_dir in self.agents_dir.iterdir():
            if agent_dir.is_dir() and agent_dir.name != "langchain_templates":
                for py_file in agent_dir.glob("*_agent.py"):
                    if "_langchain" not in py_file.name:
                        agent_files.append(py_file)

        print(f"Found {len(agent_files)} agents to refactor")

        success_count = 0
        for agent_file in agent_files:
            if self.refactor_agent(agent_file):
                success_count += 1

        print(f"Successfully refactored {success_count}/{len(agent_files)} agents")

    def create_requirements_update(self):
        """Create requirements.txt update for LangChain dependencies"""
        requirements = """# LangChain dependencies
langchain>=0.1.0
langchain-openai>=0.0.5
langchain-community>=0.0.10
langchain-core>=0.1.0
langsmith>=0.0.70
"""

        req_path = Path("services/ai-orchestrator/requirements_langchain.txt")
        with open(req_path, 'w') as f:
            f.write(requirements)

        print(f"Created requirements file: {req_path}")

def main():
    refactorer = AgentRefactorer()

    print("Creating backup of existing agents...")
    refactorer.create_backup()

    print("\\nCreating LangChain templates...")
    refactorer.create_langchain_templates()

    print("\\nRefactoring existing agents...")
    refactorer.refactor_all_agents()

    print("\\nCreating requirements update...")
    refactorer.create_requirements_update()

    print("\\n=== REFACTORING COMPLETE ===")
    print(f"Templates created: {len(refactorer.templates_created)}")
    print("\\nNext steps:")
    print("1. Review refactored agents in agents/*_langchain.py")
    print("2. Test refactored agents")
    print("3. Update imports in main orchestrator")
    print("4. Install LangChain dependencies from requirements_langchain.txt")
    print("5. Gradually migrate from old agents to new LangChain agents")

if __name__ == "__main__":
    main()