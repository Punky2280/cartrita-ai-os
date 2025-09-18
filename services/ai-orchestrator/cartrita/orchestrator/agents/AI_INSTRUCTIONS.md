# AI Instructions: Agent Development

## Agent Architecture

**Location:** `services/ai-orchestrator/cartrita/orchestrator/agents/`

**Directory Structure:**
```
agents/
├── langchain_templates/
│   └── base_agent_langchain.py  # Base class - EXTEND THIS
├── research/                     # Research agents
├── code/                        # Code generation agents
├── computer_use/                # System automation agents
├── knowledge/                   # RAG and knowledge agents
├── task/                       # Planning and decomposition agents
└── {your_domain}/              # New agent domain
```

## Creating New Agents

**Step 1: Create Agent Directory**
```bash
# Create new agent domain
mkdir cartrita/orchestrator/agents/your_domain
touch cartrita/orchestrator/agents/your_domain/__init__.py
```

**Step 2: Implement Agent Class**
```python
# cartrita/orchestrator/agents/your_domain/agent.py
from cartrita.orchestrator.agents.langchain_templates.base_agent_langchain import CartritaBaseAgent
from cartrita.orchestrator.providers.fallback_provider import get_fallback_provider
import structlog

logger = structlog.get_logger(__name__)

class YourDomainAgent(CartritaBaseAgent):
    """Your agent description - be specific about capabilities"""

    def __init__(self, api_key_manager):
        super().__init__(
            name="your_domain",
            description="Specific description of what this agent does"
        )
        self.api_key_manager = api_key_manager
        self.fallback_provider = get_fallback_provider()

    async def execute(self, messages: list, context: dict, metadata: dict):
        """
        CRITICAL: Do not change this method signature

        Args:
            messages: List of conversation messages
            context: Agent context and configuration
            metadata: Request metadata

        Returns:
            dict: {"response": str, "metadata": dict}
        """
        try:
            logger.info("Agent execution started",
                       agent=self.name,
                       message_count=len(messages))

            # Your agent logic here
            response = await self._process_request(messages, context)

            logger.info("Agent execution completed",
                       agent=self.name,
                       status="success")

            return {
                "response": response,
                "metadata": {**metadata, "agent": self.name, "status": "success"}
            }

        except Exception as e:
            logger.error("Agent execution failed",
                        agent=self.name,
                        error=str(e))

            # Use fallback provider
            fallback_response = await self._handle_fallback(messages, context)

            return {
                "response": fallback_response,
                "metadata": {**metadata, "agent": self.name, "status": "fallback", "error": str(e)}
            }

    async def _process_request(self, messages: list, context: dict) -> str:
        """Main processing logic"""
        # Use fallback provider for LLM calls
        response = await self.fallback_provider.chat_completion(
            messages=messages,
            max_completion_tokens=2000,  # Use max_completion_tokens, not max_tokens
            temperature=0.7
        )
        return response

    async def _handle_fallback(self, messages: list, context: dict) -> str:
        """Fallback response when primary execution fails"""
        return f"I apologize, but I encountered an error processing your request as a {self.name} agent."
```

**Step 3: Register Agent**
```python
# cartrita/orchestrator/agents/your_domain/__init__.py
from .agent import YourDomainAgent

__all__ = ["YourDomainAgent"]
```

## Agent Integration Patterns

**Tool Integration:**
```python
from langchain_core.tools import BaseTool
from typing import Type, List

class YourDomainAgent(CartritaBaseAgent):
    @property
    def available_tools(self) -> List[Type[BaseTool]]:
        """Return tools available to this agent"""
        return [
            YourCustomTool,
            AnotherTool,
        ]

    async def execute_with_tools(self, messages: list, context: dict):
        """Execute with tool integration"""
        tools = [tool() for tool in self.available_tools]

        # Tool execution logic
        response = await self.fallback_provider.chat_completion_with_tools(
            messages=messages,
            tools=tools,
            max_completion_tokens=2000
        )

        return response
```

**Memory Integration:**
```python
from langchain.memory import ConversationBufferMemory

class YourDomainAgent(CartritaBaseAgent):
    def __init__(self, api_key_manager):
        super().__init__(name="your_domain", description="Agent with memory")
        self.api_key_manager = api_key_manager
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

    async def execute(self, messages: list, context: dict, metadata: dict):
        # Load conversation history
        history = self.memory.chat_memory.messages

        # Combine with new messages
        full_context = history + messages

        # Process request
        response = await self._process_request(full_context, context)

        # Save to memory
        self.memory.save_context(
            {"input": messages[-1]["content"]},
            {"output": response}
        )

        return {"response": response, "metadata": metadata}
```

## Agent Testing

**Step 4: Create Tests**
```python
# tests/agents/test_your_domain_agent.py
import pytest
from cartrita.orchestrator.agents.your_domain.agent import YourDomainAgent

class TestYourDomainAgent:

    @pytest.fixture
    def agent(self, mock_api_key_manager):
        return YourDomainAgent(mock_api_key_manager)

    @pytest.mark.asyncio
    async def test_execute_success(self, agent, sample_messages):
        result = await agent.execute(sample_messages, {}, {})

        assert "response" in result
        assert "metadata" in result
        assert result["metadata"]["status"] == "success"

    @pytest.mark.asyncio
    async def test_execute_fallback(self, agent, mock_failed_openai):
        with mock_failed_openai:
            result = await agent.execute([{"role": "user", "content": "test"}], {}, {})

        assert result["metadata"]["status"] == "fallback"
        assert "error" in result["metadata"]

    @pytest.mark.asyncio
    async def test_agent_specialization(self, agent):
        """Test agent-specific functionality"""
        # Test your agent's specialized behavior
        domain_specific_message = [{"role": "user", "content": "domain-specific request"}]
        result = await agent.execute(domain_specific_message, {}, {})

        # Assert domain-specific behavior
        assert "domain-specific response pattern" in result["response"]
```

## Common Agent Patterns

**Research Agent Pattern:**
```python
class ResearchAgent(CartritaBaseAgent):
    async def execute(self, messages: list, context: dict, metadata: dict):
        # 1. Extract search queries from messages
        # 2. Perform web searches
        # 3. Synthesize information
        # 4. Return structured research
        pass
```

**Code Agent Pattern:**
```python
class CodeAgent(CartritaBaseAgent):
    async def execute(self, messages: list, context: dict, metadata: dict):
        # 1. Analyze code requirements
        # 2. Generate code with fallback provider
        # 3. Validate syntax
        # 4. Return code with explanations
        pass
```

**Task Agent Pattern:**
```python
class TaskAgent(CartritaBaseAgent):
    async def execute(self, messages: list, context: dict, metadata: dict):
        # 1. Parse complex requests
        # 2. Break into subtasks
        # 3. Plan execution order
        # 4. Return structured task plan
        pass
```

## Agent Registration

**Step 5: Register in Orchestrator**
```python
# cartrita/orchestrator/core/agent_registry.py
from cartrita.orchestrator.agents.your_domain import YourDomainAgent

AGENT_REGISTRY = {
    "research": ResearchAgent,
    "code": CodeAgent,
    "computer_use": ComputerUseAgent,
    "knowledge": KnowledgeAgent,
    "task": TaskAgent,
    "your_domain": YourDomainAgent,  # Add your agent
}
```

## Performance Guidelines

- **Keep agent execution under 30 seconds** for user-facing requests
- **Implement streaming for long-running operations**
- **Cache expensive computations** when possible
- **Use appropriate max_completion_tokens** limits
- **Log performance metrics** for monitoring

## Security Constraints

- **Never log user input** that might contain secrets
- **Validate all inputs** before processing
- **Use environment variables** for API keys
- **Implement rate limiting** for external API calls
- **Sanitize outputs** before returning to users

## Error Handling Best Practices

```python
async def execute(self, messages: list, context: dict, metadata: dict):
    try:
        # Primary execution path
        return await self._execute_primary(messages, context, metadata)
    except OpenAIError as e:
        logger.warning("OpenAI error, using fallback", agent=self.name, error=str(e))
        return await self._execute_fallback(messages, context, metadata)
    except ExternalAPIError as e:
        logger.error("External API error", agent=self.name, error=str(e))
        return self._create_error_response("External service unavailable", metadata)
    except Exception as e:
        logger.error("Unexpected error", agent=self.name, error=str(e), exc_info=True)
        return self._create_error_response("Internal error occurred", metadata)

def _create_error_response(self, message: str, metadata: dict) -> dict:
    return {
        "response": f"I apologize, but {message}. Please try again.",
        "metadata": {**metadata, "status": "error", "agent": self.name}
    }
```
