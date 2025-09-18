# AI Instructions: Backend Development

## Agent System Architecture

**All agents MUST extend the base class:**
```python
from cartrita.orchestrator.agents.langchain_templates.base_agent_langchain import CartritaBaseAgent

class YourAgent(CartritaBaseAgent):
    def __init__(self, api_key_manager):
        super().__init__(name="your_agent", description="Your agent description")
        self.api_key_manager = api_key_manager

    async def execute(self, messages, context, metadata):
        """Standard execution interface - DO NOT CHANGE SIGNATURE"""
        # Implementation here
        return {"response": response_text, "metadata": updated_metadata}
```

**Agent Directory Structure:**
- Place new agents in: `cartrita/orchestrator/agents/{domain}/`
- Follow existing patterns in `research/`, `code/`, `computer_use/`, `knowledge/`, `task/`

## Fallback Provider System

**4-Level Fallback Chain - CRITICAL:**
1. OpenAI API (Primary)
2. HuggingFace Local
3. Rule-based FSM
4. Emergency Templates

**Access pattern:**
```python
from cartrita.orchestrator.providers.fallback_provider import get_fallback_provider

# ALWAYS use max_completion_tokens (NOT max_tokens)
provider = get_fallback_provider()
response = await provider.chat_completion(
    messages=messages,
    max_completion_tokens=1000,  # Correct parameter
    temperature=0.7
)
```

## Structured Logging - MANDATORY

```python
import structlog

logger = structlog.get_logger(__name__)

# Good - structured with context
logger.info("Agent execution complete",
           agent_name=self.name,
           user_id=user_id,
           status="success",
           duration_ms=duration)

# Bad - unstructured
print("Agent done")  # Never use print()
logger.info(f"Agent {self.name} done")  # No f-strings in logs
```

## State Management - CRITICAL CONSTRAINTS

**NEVER mutate LangGraph state directly:**
```python
# Correct - use safe helpers
from cartrita.orchestrator.core.state_helpers import (
    _safe_get_messages,
    _safe_append_message,
    _safe_set_messages
)

messages = _safe_get_messages(state)
_safe_append_message(state, new_message)

# WRONG - direct mutation
state["messages"].append(message)  # Will break the system
```

## Streaming Responses

**FastAPI SSE Pattern:**
```python
from fastapi.responses import StreamingResponse

async def stream_agent_response(request: ChatRequest):
    async def generate():
        # Stream agent responses
        async for chunk in agent.stream_execute(messages):
            yield f"data: {json.dumps(chunk)}\n\n"

        # CRITICAL: Always terminate properly
        yield "data: {'type': 'done'}\n\n"

    return StreamingResponse(generate(), media_type="text/plain")
```

## Testing Patterns

**Use fixtures from conftest.py - NEVER hardcode API keys:**
```python
# tests/test_your_agent.py
import pytest

def test_agent_execution(mock_api_key_manager, sample_messages):
    agent = YourAgent(mock_api_key_manager)
    result = await agent.execute(sample_messages, {}, {})

    assert result["response"]
    assert "metadata" in result

def test_agent_fallback(mock_failed_openai, mock_api_key_manager):
    # Test fallback behavior when OpenAI fails
    agent = YourAgent(mock_api_key_manager)
    # Test implementation
```

**Quick test command after changes:**
```bash
pytest -m "not slow" -q
```

## Dependencies

**ONLY edit requirements.in - NEVER edit constraints.txt directly:**
```bash
# Add new dependency
echo "new-package==1.0.0" >> requirements.in

# Regenerate constraints with hashes
pip-compile --generate-hashes --output-file constraints.txt requirements.in

# Always maintain hash-locked dependencies
```

## Database Operations

**Use DatabaseManager - NEVER write raw SQL:**
```python
from cartrita.orchestrator.core.database import DatabaseManager

async def store_conversation(conversation_data):
    async with DatabaseManager() as db:
        await db.store_conversation(conversation_data)
        # DatabaseManager handles transactions, connections, security
```

## Security Checks - MANDATORY

**Before ANY commit:**
```bash
# Check for exposed API keys
grep -r "sk-" . --exclude-dir=node_modules --exclude-dir=.git

# Should return no results
```

**Import Path Structure:**
```python
# Correct
from cartrita.orchestrator.core.module import Class
from cartrita.orchestrator.agents.research.agent import ResearchAgent
from cartrita.orchestrator.providers.openai_provider import OpenAIProvider

# Wrong
from services.ai_orchestrator.cartrita import something  # Avoid absolute paths
```

## Quality Checks

**Before committing:**
```bash
# Fix linting issues
ruff check . --fix

# Type checking
mypy .

# Run tests
pytest -q
```

## Performance Guidelines

- **Avoid redundant LLM calls** - cache responses when possible
- **Batch database operations** - don't make individual DB calls in loops
- **Use async/await properly** - don't block the event loop
- **Respect iteration limits** - check `max_total_iterations`, `max_attempts_per_agent`

## Error Handling

```python
async def execute(self, messages, context, metadata):
    try:
        # Primary execution path
        return await self._execute_with_openai(messages)
    except OpenAIError:
        logger.warning("OpenAI failed, using fallback", agent=self.name)
        return await self._execute_with_fallback(messages)
    except Exception as e:
        logger.error("Agent execution failed", agent=self.name, error=str(e))
        return {"response": "Error occurred", "metadata": {"error": True}}
```
