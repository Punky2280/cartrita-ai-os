# Cartrita AI OS - MCP Protocol Integration
# Model Context Protocol with LangSmith-style tool hierarchy

"""
MCP (Model Context Protocol) Integration for Cartrita AI OS.
Implements LangSmith-inspired tool hierarchy with secure API key management.
"""

import asyncio
import os
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import structlog
from langsmith import Client as LangSmithClient
from pydantic import BaseModel, Field

from cartrita.orchestrator.agents.cartrita_core.api_key_manager import APIKeyManager

logger = structlog.get_logger(__name__)


class MCPMessageType(str, Enum):
    """MCP message types."""

    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    ERROR = "error"


class MCPCapability(str, Enum):
    """MCP protocol capabilities."""

    TOOLS = "tools"
    PROMPTS = "prompts"
    RESOURCES = "resources"
    SAMPLING = "sampling"


class ToolExecutionStatus(str, Enum):
    """Tool execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class MCPMessage:
    """MCP protocol message structure."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: MCPMessageType = MCPMessageType.REQUEST
    method: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class ToolExecution:
    """Tool execution tracking."""

    execution_id: str
    tool_name: str
    agent_id: str
    parameters: Dict[str, Any]
    status: ToolExecutionStatus
    start_time: float
    end_time: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    api_keys_used: List[str] = field(default_factory=list)


class MCPTool(BaseModel):
    """MCP tool definition with hierarchy support."""

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    input_schema: Dict[str, Any] = Field(..., description="JSON schema for input")
    output_schema: Dict[str, Any] = Field(
        default_factory=dict, description="JSON schema for output"
    )
    hierarchy_level: int = Field(
        default=1, description="Tool hierarchy level (1=basic, 5=expert)"
    )
    required_capabilities: List[str] = Field(
        default_factory=list, description="Required capabilities"
    )
    api_dependencies: List[str] = Field(
        default_factory=list, description="Required API keys"
    )
    safety_level: int = Field(
        default=1, description="Safety level (1=safe, 5=dangerous)"
    )
    execution_timeout: int = Field(
        default=60, description="Execution timeout in seconds"
    )


class CartritaMCPProtocol:
    """
    Cartrita's MCP Protocol Implementation.

    Hierarchical tool management with LangSmith-inspired monitoring and secure API key delegation.
    """

    def __init__(self, api_key_manager: APIKeyManager):
        """Initialize the MCP protocol handler."""
        self.api_key_manager = api_key_manager
        self.protocol_version = "2025.01"
        self.session_id = str(uuid.uuid4())

        # Tool registry with hierarchy
        self.tools: Dict[str, MCPTool] = {}
        self.tool_executors: Dict[str, Callable] = {}

        # Execution tracking
        self.active_executions: Dict[str, ToolExecution] = {}
        self.execution_history: List[ToolExecution] = []

        # LangSmith-style monitoring
        self.langsmith_client = None
        self._setup_langsmith_integration()

        # Protocol capabilities
        self.capabilities = [
            MCPCapability.TOOLS,
            MCPCapability.PROMPTS,
            MCPCapability.RESOURCES,
            MCPCapability.SAMPLING,
        ]

        # Initialize core tools
        self._register_core_tools()

        logger.info(
            "MCP Protocol initialized",
            version=self.protocol_version,
            session_id=self.session_id,
            tools_registered=len(self.tools),
        )

    def _setup_langsmith_integration(self):
        """Setup LangSmith integration for monitoring."""
        try:
            langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
            if langsmith_api_key:
                self.langsmith_client = LangSmithClient(api_key=langsmith_api_key)
                logger.info("LangSmith integration enabled")
        except Exception as e:
            logger.warning("LangSmith integration failed", error=str(e))

    def _register_core_tools(self):
        """Register core MCP tools with hierarchy."""
        core_tools = [
            # Level 1 - Basic tools
            MCPTool(
                name="web_search",
                description="Search the web for information",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "max_results": {"type": "integer", "default": 5},
                    },
                    "required": ["query"],
                },
                hierarchy_level=1,
                api_dependencies=["tavily", "serper"],
                safety_level=1,
            ),
            # Level 2 - Intermediate tools
            MCPTool(
                name="code_execution",
                description="Execute code in a secure environment",
                input_schema={
                    "type": "object",
                    "properties": {
                        "language": {
                            "type": "string",
                            "enum": ["python", "javascript", "bash"],
                        },
                        "code": {"type": "string", "description": "Code to execute"},
                        "timeout": {"type": "integer", "default": 30},
                    },
                    "required": ["language", "code"],
                },
                hierarchy_level=2,
                safety_level=3,
                execution_timeout=120,
            ),
            # Level 3 - Advanced tools
            MCPTool(
                name="ai_completion",
                description="Generate AI completions using various models",
                input_schema={
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string", "description": "Input prompt"},
                        "model": {
                            "type": "string",
                            "enum": ["gpt-4", "claude-3", "gemini-pro"],
                        },
                        "temperature": {"type": "number", "default": 0.7},
                        "max_tokens": {"type": "integer", "default": 1000},
                    },
                    "required": ["prompt", "model"],
                },
                hierarchy_level=3,
                api_dependencies=["openai", "google"],
                safety_level=2,
            ),
            # Level 4 - Expert tools
            MCPTool(
                name="system_interaction",
                description="Interact with computer systems and files",
                input_schema={
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["read_file", "write_file", "run_command"],
                        },
                        "target": {
                            "type": "string",
                            "description": "File path or command",
                        },
                        "content": {
                            "type": "string",
                            "description": "Content for write operations",
                        },
                    },
                    "required": ["action", "target"],
                },
                hierarchy_level=4,
                safety_level=4,
                execution_timeout=300,
            ),
            # Level 5 - Expert tools with high permissions
            MCPTool(
                name="agent_orchestration",
                description="Orchestrate multiple AI agents for complex tasks",
                input_schema={
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "Complex task description",
                        },
                        "agents": {"type": "array", "items": {"type": "string"}},
                        "coordination_strategy": {
                            "type": "string",
                            "enum": ["sequential", "parallel", "hierarchical"],
                        },
                    },
                    "required": ["task", "agents"],
                },
                hierarchy_level=5,
                api_dependencies=["openai"],
                safety_level=3,
                execution_timeout=600,
            ),
        ]

        # Register tools
        for tool in core_tools:
            self.register_tool(tool)

    def register_tool(self, tool: MCPTool, executor: Optional[Callable] = None) -> bool:
        """Register a new tool in the MCP registry."""
        try:
            self.tools[tool.name] = tool

            if executor:
                self.tool_executors[tool.name] = executor
            else:
                # Create default executor
                self.tool_executors[tool.name] = self._create_default_executor(tool)

            logger.info(
                "Tool registered",
                tool_name=tool.name,
                hierarchy_level=tool.hierarchy_level,
                safety_level=tool.safety_level,
            )
            return True

        except Exception as e:
            logger.error("Tool registration failed", tool_name=tool.name, error=str(e))
            return False

    def _create_default_executor(self, tool: MCPTool) -> Callable:
        """Create default executor for tool."""

        async def default_executor(**kwargs) -> Dict[str, Any]:
            """Default tool executor."""
            return {
                "tool": tool.name,
                "status": "executed",
                "result": f"Tool {tool.name} executed with params: {kwargs}",
                "note": "This is a default executor - implement specific logic for production",
            }

        return default_executor

    async def handle_message(self, message: MCPMessage) -> MCPMessage:
        """Handle incoming MCP protocol messages."""
        try:
            response = MCPMessage(id=message.id, type=MCPMessageType.RESPONSE)

            if message.method == "tools/list":
                response.result = await self._handle_list_tools(message.params or {})

            elif message.method == "tools/call":
                response.result = await self._handle_call_tool(message.params or {})

            elif message.method == "tools/status":
                response.result = await self._handle_tool_status(message.params or {})

            elif message.method == "capabilities":
                response.result = await self._handle_capabilities(message.params or {})

            else:
                response.type = MCPMessageType.ERROR
                response.error = {
                    "code": "METHOD_NOT_FOUND",
                    "message": f"Unknown method: {message.method}",
                }

            return response

        except Exception as e:
            logger.error("Message handling failed", error=str(e), method=message.method)
            return MCPMessage(
                id=message.id,
                type=MCPMessageType.ERROR,
                error={"code": "INTERNAL_ERROR", "message": str(e)},
            )

    async def _handle_list_tools(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools listing request."""
        max_hierarchy = params.get("max_hierarchy", 5)
        include_schema = params.get("include_schema", True)

        filtered_tools = []
        for tool in self.tools.values():
            if tool.hierarchy_level <= max_hierarchy:
                tool_info = {
                    "name": tool.name,
                    "description": tool.description,
                    "hierarchy_level": tool.hierarchy_level,
                    "safety_level": tool.safety_level,
                    "required_capabilities": tool.required_capabilities,
                    "api_dependencies": tool.api_dependencies,
                }

                if include_schema:
                    tool_info["input_schema"] = tool.input_schema
                    tool_info["output_schema"] = tool.output_schema

                filtered_tools.append(tool_info)

        return {
            "tools": filtered_tools,
            "total_count": len(filtered_tools),
            "session_id": self.session_id,
        }

    async def _handle_call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool execution request with secure key management."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        agent_id = params.get("agent_id", "unknown")

        if not tool_name or tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")

        tool = self.tools[tool_name]

        # Create execution record
        execution = ToolExecution(
            execution_id=str(uuid.uuid4()),
            tool_name=tool_name,
            agent_id=agent_id,
            parameters=arguments,
            status=ToolExecutionStatus.PENDING,
            start_time=time.time(),
        )

        self.active_executions[execution.execution_id] = execution

        try:
            # Request API keys if needed
            if tool.api_dependencies:
                key_access_results = {}
                for api_service in tool.api_dependencies:
                    access_info = await self.api_key_manager.request_key_access(
                        agent_id=agent_id,
                        tool_name=f"{tool_name}_{api_service}",
                        duration_minutes=tool.execution_timeout // 60 + 10,
                    )
                    if access_info:
                        key_access_results[api_service] = access_info
                        execution.api_keys_used.append(access_info["checkout_id"])

                # Add keys to arguments
                arguments["_api_keys"] = key_access_results

            # Update status
            execution.status = ToolExecutionStatus.RUNNING

            # Execute tool with timeout
            executor = self.tool_executors[tool_name]
            result = await asyncio.wait_for(
                executor(**arguments), timeout=tool.execution_timeout
            )

            # Update execution record
            execution.status = ToolExecutionStatus.COMPLETED
            execution.end_time = time.time()
            execution.result = result

            # Log to LangSmith if available
            if self.langsmith_client:
                await self._log_to_langsmith(execution)

            # Clean up API keys
            for checkout_id in execution.api_keys_used:
                await self.api_key_manager.return_key_access(agent_id, checkout_id)

            return {
                "execution_id": execution.execution_id,
                "tool_name": tool_name,
                "status": "completed",
                "result": result,
                "execution_time": execution.end_time - execution.start_time,
                "api_keys_used": len(execution.api_keys_used),
            }

        except asyncio.TimeoutError:
            execution.status = ToolExecutionStatus.FAILED
            execution.error = "Tool execution timeout"
            execution.end_time = time.time()

            logger.warning(
                "Tool execution timeout",
                tool_name=tool_name,
                timeout=tool.execution_timeout,
            )

            return {
                "execution_id": execution.execution_id,
                "status": "failed",
                "error": "Execution timeout",
                "execution_time": tool.execution_timeout,
            }

        except Exception as e:
            execution.status = ToolExecutionStatus.FAILED
            execution.error = str(e)
            execution.end_time = time.time()

            logger.error("Tool execution failed", tool_name=tool_name, error=str(e))

            return {
                "execution_id": execution.execution_id,
                "status": "failed",
                "error": str(e),
                "execution_time": time.time() - execution.start_time,
            }

        finally:
            # Move to history
            if execution.execution_id in self.active_executions:
                self.execution_history.append(execution)
                del self.active_executions[execution.execution_id]

    async def _handle_tool_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool status request."""
        execution_id = params.get("execution_id")

        if execution_id:
            # Get specific execution status
            if execution_id in self.active_executions:
                execution = self.active_executions[execution_id]
                return {
                    "execution_id": execution_id,
                    "status": execution.status.value,
                    "tool_name": execution.tool_name,
                    "start_time": execution.start_time,
                    "running_time": time.time() - execution.start_time,
                }
            else:
                # Check history
                for execution in self.execution_history:
                    if execution.execution_id == execution_id:
                        return {
                            "execution_id": execution_id,
                            "status": execution.status.value,
                            "tool_name": execution.tool_name,
                            "execution_time": (
                                execution.end_time - execution.start_time
                                if execution.end_time
                                else None
                            ),
                            "result_available": execution.result is not None,
                        }

                return {"error": f"Execution {execution_id} not found"}

        else:
            # Get overall status
            return {
                "active_executions": len(self.active_executions),
                "completed_executions": len(
                    [
                        e
                        for e in self.execution_history
                        if e.status == ToolExecutionStatus.COMPLETED
                    ]
                ),
                "failed_executions": len(
                    [
                        e
                        for e in self.execution_history
                        if e.status == ToolExecutionStatus.FAILED
                    ]
                ),
                "total_tools": len(self.tools),
                "session_uptime": time.time()
                - (
                    self.execution_history[0].start_time
                    if self.execution_history
                    else time.time()
                ),
            }

    async def _handle_capabilities(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle capabilities request."""
        return {
            "protocol_version": self.protocol_version,
            "capabilities": [cap.value for cap in self.capabilities],
            "tools_supported": len(self.tools),
            "max_hierarchy_level": (
                max(tool.hierarchy_level for tool in self.tools.values())
                if self.tools
                else 0
            ),
            "api_key_management": True,
            "langsmith_integration": self.langsmith_client is not None,
            "session_id": self.session_id,
        }

    async def _log_to_langsmith(self, execution: ToolExecution):
        """Log execution to LangSmith for monitoring."""
        try:
            if not self.langsmith_client:
                return

            run_data = {
                "name": f"cartrita_tool_{execution.tool_name}",
                "inputs": execution.parameters,
                "outputs": execution.result,
                "run_type": "tool",
                "start_time": execution.start_time,
                "end_time": execution.end_time,
                "execution_order": 1,
                "extra": {
                    "tool_name": execution.tool_name,
                    "agent_id": execution.agent_id,
                    "hierarchy_level": self.tools[execution.tool_name].hierarchy_level,
                    "api_keys_used": len(execution.api_keys_used),
                    "safety_level": self.tools[execution.tool_name].safety_level,
                },
            }

            # Create run in LangSmith
            await self.langsmith_client.acreate_run(**run_data)

        except Exception as e:
            logger.warning("LangSmith logging failed", error=str(e))

    def get_tool_hierarchy_report(self) -> Dict[str, Any]:
        """Generate tool hierarchy report."""
        hierarchy_stats = {}
        for level in range(1, 6):
            tools_at_level = [
                tool for tool in self.tools.values() if tool.hierarchy_level == level
            ]
            hierarchy_stats[f"level_{level}"] = {
                "count": len(tools_at_level),
                "tools": [tool.name for tool in tools_at_level],
                "avg_safety_level": (
                    sum(tool.safety_level for tool in tools_at_level)
                    / len(tools_at_level)
                    if tools_at_level
                    else 0
                ),
            }

        return {
            "total_tools": len(self.tools),
            "hierarchy_distribution": hierarchy_stats,
            "api_dependencies": list(
                set(
                    dep for tool in self.tools.values() for dep in tool.api_dependencies
                )
            ),
            "session_id": self.session_id,
            "protocol_version": self.protocol_version,
        }
