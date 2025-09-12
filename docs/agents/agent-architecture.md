# Cartrita AI OS Agent Architecture

## Overview

The Cartrita AI OS implements a sophisticated multi-agent architecture based on hierarchical orchestration patterns. The system uses a supervisor-agent model where a central GPT-4.1-powered supervisor coordinates specialized agents for different tasks.

## Architecture Components

### 1. Supervisor Orchestrator (`supervisor.py`)

The supervisor serves as the central coordinator and uses GPT-4.1 to:

- **Agent Selection**: Intelligently routes user requests to appropriate specialized agents
- **Task Coordination**: Manages complex multi-step tasks across different agents  
- **Response Synthesis**: Combines responses from multiple agents when needed
- **Fallback Handling**: Provides direct responses when no specialized agent is suitable

**Key Features:**

- Hierarchical task delegation based on LangGraph supervisor patterns
- Multi-agent conversation management
- Dynamic agent selection using LLM reasoning
- Comprehensive error handling and fallback mechanisms

### 2. Specialized Agents

#### Research Agent (`research/research_agent.py`)

- **Purpose**: Web search, information gathering, and research tasks
- **Model**: GPT-5 with Tavily search integration
- **Capabilities:**
  - Academic research and fact-checking
  - Market analysis and trend research
  - Technical documentation research
  - Real-time information gathering

#### Code Agent (`code/code_agent.py`)

- **Purpose**: Code generation, analysis, and programming tasks
- **Model**: GPT-5 optimized for coding
- **Capabilities**:
  - Multi-language code generation
  - Code review and optimization
  - Bug fixing and debugging
  - Architecture design and documentation

#### Computer Use Agent (`computer_use/computer_use_agent.py`)

- **Purpose**: System automation and computer interaction
- **Model**: GPT-5 with safety constraints
- **Capabilities**:
  - File system operations
  - Application automation
  - System monitoring and diagnostics
  - Secure command execution

#### Knowledge Agent (`knowledge/knowledge_agent.py`)

- **Purpose**: Information retrieval from knowledge bases
- **Model**: GPT-5 with vector database integration
- **Capabilities**:
  - RAG-based document search
  - Knowledge base query optimization
  - Context-aware information retrieval
  - Document similarity analysis

#### Task Agent (`task/task_agent.py`)

- **Purpose**: Task planning and project management
- **Model**: GPT-5 for structured planning
- **Capabilities**:
  - Project breakdown and planning
  - Dependency analysis and timeline creation
  - Risk assessment and mitigation
  - Resource allocation and optimization

## Implementation Details

### Agent Initialization

All agents are dynamically initialized by the supervisor with proper error handling:

```python
def _initialize_agents(self) -> dict[AgentType, Any]:
    """Initialize all specialized agents."""
    try:
        from cartrita.orchestrator.agents import (
            ResearchAgent, CodeAgent, ComputerUseAgent, 
            KnowledgeAgent, TaskAgent
        )
        logger.info("Successfully imported all agents")
    except ImportError as e:
        logger.error(f"Failed to import agents: {str(e)}")
        # Graceful degradation...
```

### Agent Selection Logic

The supervisor uses GPT-4.1 to intelligently route requests:

```python
async def _select_appropriate_agent(
    self, messages: list[dict[str, Any]]
) -> AgentType | None:
    """Use GPT-4.1 to select the most appropriate agent."""
    # Analyzes user request and selects optimal agent
    # Falls back to direct response if no agent matches
```

### Configuration Management

Each agent is configured with appropriate models and API keys:

```python
agent_configs = {
    AgentType.RESEARCH: {
        "class": ResearchAgent,
        "model": self.settings.ai.agent_model,
        "tavily_api_key": self.settings.external.tavily_api_key,
    },
    # ... other agents
}
```

## Multi-Agent Workflow

### 1. Request Processing

1. User submits request via chat interface
2. Supervisor receives and analyzes request
3. GPT-4.1 determines optimal agent selection
4. Request is routed to appropriate specialized agent

### 2. Agent Execution  

1. Specialized agent processes request using domain-specific logic
2. Agent leverages appropriate tools and APIs
3. Response is generated with metadata and confidence scores
4. Results are returned to supervisor

### 3. Response Coordination

1. Supervisor receives agent response
2. Additional processing or agent coordination if needed
3. Final response is formatted and returned to user
4. Conversation state is updated

## Error Handling & Resilience

### Graceful Degradation

- Import failures don't crash the system
- Missing agents trigger fallback responses
- Configuration errors are logged and handled

### Retry Logic

- Failed agent calls are retried with exponential backoff
- Alternative agents can be selected for similar tasks
- Supervisor provides direct responses when agents fail

### Monitoring & Observability

- Comprehensive structured logging with correlation IDs
- Agent performance metrics and execution times
- Error tracking and debugging information

## Benefits of This Architecture

### 1. Scalability

- New agents can be added without modifying existing code
- Horizontal scaling through multiple supervisor instances
- Independent agent deployment and versioning

### 2. Maintainability

- Clear separation of concerns between agents
- Modular design enables independent development
- Standardized agent interface and lifecycle management

### 3. Flexibility

- Dynamic agent selection based on request analysis
- Multi-agent coordination for complex tasks
- Easy configuration and feature toggling

### 4. Reliability

- Robust error handling and fallback mechanisms
- Health monitoring and automatic recovery
- Graceful degradation under failure conditions

## Configuration

Agents are configured through environment variables and settings:

```python
# AI Model Configuration
AGENT_MODEL=gpt-5
OPENAI_API_KEY=<api_key>

# External Service Keys
TAVILY_API_KEY=<tavily_key>

# Safety Settings
COMPUTER_USE_SAFETY_MODE=strict
```

## Monitoring & Debugging

The system provides comprehensive logging and monitoring:

- **Structured Logging**: All agent activities logged with structured data
- **Execution Metrics**: Performance tracking for agent selection and execution
- **Error Tracking**: Detailed error information for debugging
- **Health Checks**: Agent availability and status monitoring

## Future Enhancements

- **Agent Learning**: Implement feedback loops for improving agent selection
- **Dynamic Scaling**: Auto-scaling based on load and performance
- **Advanced Coordination**: Multi-agent collaboration patterns
- **Custom Agents**: Plugin system for user-defined agents
- **Performance Optimization**: Caching and parallel execution

This architecture provides a robust foundation for building sophisticated AI applications with specialized capabilities while maintaining system reliability and user experience.
