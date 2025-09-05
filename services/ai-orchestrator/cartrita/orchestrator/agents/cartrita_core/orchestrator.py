# Cartrita AI OS - Main Orchestrator
# Integrates all components: Cartrita agent, API key manager, and MCP protocol

"""
Cartrita Main Orchestrator.
Coordinates Cartrita agent, API key management, and MCP protocol for complete system orchestration.
"""

import asyncio
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import structlog
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from cartrita.orchestrator.agents.cartrita_core.api_key_manager import APIKeyManager
from cartrita.orchestrator.agents.cartrita_core.cartrita_agent import CartritaCoreAgent
from cartrita.orchestrator.agents.cartrita_core.mcp_protocol import (
    CartritaMCPProtocol,
    MCPMessage,
)
from cartrita.orchestrator.utils.config import settings

logger = structlog.get_logger(__name__)


class CartritaOrchestrator:
    """
    Main Cartrita Orchestrator.

    Coordinates all system components:
    - Cartrita Core Agent (personality and delegation)
    - API Key Manager (secure key management)
    - MCP Protocol (tool hierarchy and execution)
    """

    def __init__(self):
        """Initialize the complete Cartrita orchestration system."""
        self.orchestrator_id = "cartrita_main_orchestrator"
        self.startup_time = time.time()

        # Initialize components in dependency order
        logger.info("Initializing Cartrita Orchestrator components...")

        # 1. API Key Manager (foundation)
        self.api_key_manager = APIKeyManager()

        # 2. MCP Protocol (tool management)
        self.mcp_protocol = CartritaMCPProtocol(self.api_key_manager)

        # 3. Cartrita Core Agent (main personality and logic)
        self.cartrita_agent = CartritaCoreAgent(self.api_key_manager)

        # System state
        self.is_running = False
        self.processed_requests = 0
        self.error_count = 0

        logger.info(
            "Cartrita Orchestrator initialized successfully",
            orchestrator_id=self.orchestrator_id,
        )

    async def start(self) -> None:
        """Start the orchestrator system."""
        try:
            self.is_running = True

            # Perform system health checks
            await self._perform_startup_checks()

            logger.info(
                "Cartrita Orchestrator started", uptime=time.time() - self.startup_time
            )

        except Exception as e:
            logger.error("Failed to start Cartrita Orchestrator", error=str(e))
            self.is_running = False
            raise

    async def stop(self) -> None:
        """Stop the orchestrator system."""
        try:
            self.is_running = False

            # Cleanup any active operations
            await self._cleanup_operations()

            logger.info(
                "Cartrita Orchestrator stopped",
                total_requests=self.processed_requests,
                uptime=time.time() - self.startup_time,
            )

        except Exception as e:
            logger.error("Error stopping Cartrita Orchestrator", error=str(e))

    async def process_chat_request(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        agent_override: Optional[str] = None,
        stream: bool = False,
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Main chat processing method.
        Routes through Cartrita's personality and intelligence.
        """
        request_start = time.time()
        request_id = f"req_{int(request_start)}_{self.processed_requests}"

        try:
            if not self.is_running:
                raise RuntimeError("Cartrita Orchestrator is not running")

            # Log request
            logger.info(
                "Processing chat request",
                request_id=request_id,
                message_length=len(message),
                has_context=bool(context),
                agent_override=agent_override,
                stream=stream,
            )

            # Prepare context
            if context is None:
                context = {}

            context.update(
                {
                    "request_id": request_id,
                    "timestamp": request_start,
                    "api_key_hash": api_key[:8] + "..." if api_key else None,
                    "orchestrator": self.orchestrator_id,
                }
            )

            # Process through Cartrita's agent
            response = await self.cartrita_agent.process_request(
                user_message=message, chat_history=context.get("chat_history", [])
            )

            # Add orchestrator metadata
            response["metadata"].update(
                {
                    "request_id": request_id,
                    "processing_time": time.time() - request_start,
                    "orchestrator_version": "2.0.0",
                    "mcp_protocol_version": self.mcp_protocol.protocol_version,
                    "api_key_manager_active": True,
                }
            )

            # Update statistics
            self.processed_requests += 1

            logger.info(
                "Chat request completed",
                request_id=request_id,
                processing_time=response["processing_time"],
                success=True,
            )

            return response

        except Exception as e:
            self.error_count += 1
            processing_time = time.time() - request_start

            logger.error(
                "Chat request failed",
                request_id=request_id,
                error=str(e),
                processing_time=processing_time,
            )

            # Return error response with Cartrita's personality
            return {
                "response": f"Ay, mi amor, something went sideways with that request. {str(e)[:100]}... But I'm still here for you!",
                "conversation_id": context.get(
                    "conversation_id", f"error_{request_id}"
                ),
                "agent_type": "cartrita_core",
                "processing_time": processing_time,
                "error": str(e),
                "metadata": {
                    "request_id": request_id,
                    "error_handled": True,
                    "personality_active": True,
                    "orchestrator": self.orchestrator_id,
                },
            }

    async def get_agent_statuses(self) -> Dict[str, Any]:
        """Get status of all agents in the system."""
        try:
            # Get Cartrita's status
            cartrita_status = await self.cartrita_agent.get_status()

            # Get API key manager status
            key_manager_health = await self.api_key_manager.health_check()

            # Get MCP protocol status
            mcp_capabilities = await self.mcp_protocol._handle_capabilities({})

            # Compile agent statuses
            agent_statuses = {
                "cartrita_core": {
                    **cartrita_status,
                    "last_request_time": (
                        time.time() - 60 if self.processed_requests > 0 else None
                    ),
                    "total_requests": self.processed_requests,
                    "error_rate": self.error_count
                    / max(self.processed_requests, 1)
                    * 100,
                    "uptime": time.time() - self.startup_time,
                },
                "api_key_manager": {
                    "agent_id": "api_key_manager",
                    "name": "API Key Manager",
                    "type": "security",
                    "status": (
                        "active"
                        if key_manager_health["status"] == "healthy"
                        else "degraded"
                    ),
                    "description": "Secure API key and tool permission management",
                    **key_manager_health,
                },
                "mcp_protocol": {
                    "agent_id": "mcp_protocol",
                    "name": "MCP Protocol Handler",
                    "type": "protocol",
                    "status": "active",
                    "description": "Model Context Protocol with tool hierarchy",
                    **mcp_capabilities,
                },
            }

            # Add available specialized agents
            for agent_name, agent_info in self.cartrita_agent.available_agents.items():
                agent_statuses[agent_name] = {
                    "agent_id": agent_name,
                    "name": agent_name.replace("_", " ").title(),
                    "type": "specialist",
                    "status": "idle",  # In production, check actual status
                    "capabilities": [cap.value for cap in agent_info["capabilities"]],
                    "available_tools": agent_info["tools"],
                    "max_complexity": agent_info["max_complexity"],
                    "managed_by": "cartrita_core",
                }

            return agent_statuses

        except Exception as e:
            logger.error("Failed to get agent statuses", error=str(e))
            return {
                "error": f"Failed to retrieve agent statuses: {str(e)}",
                "timestamp": time.time(),
            }

    async def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get status of specific agent."""
        try:
            all_statuses = await self.get_agent_statuses()
            return all_statuses.get(agent_id)
        except Exception as e:
            logger.error("Failed to get agent status", agent_id=agent_id, error=str(e))
            return None

    async def health_check(self) -> bool:
        """Comprehensive health check for the orchestrator."""
        try:
            if not self.is_running:
                return False

            # Check API Key Manager
            key_manager_health = await self.api_key_manager.health_check()
            if key_manager_health["status"] != "healthy":
                return False

            # Check MCP Protocol
            mcp_status = await self.mcp_protocol._handle_tool_status({})
            if "error" in mcp_status:
                return False

            # Check Cartrita agent
            cartrita_status = await self.cartrita_agent.get_status()
            if cartrita_status["status"] != "active":
                return False

            return True

        except Exception as e:
            logger.error("Health check failed", error=str(e))
            return False

    async def reload_agents(self) -> bool:
        """Reload agent configurations."""
        try:
            logger.info("Reloading Cartrita Orchestrator agents")

            # Stop current operations
            await self._cleanup_operations()

            # Reinitialize components
            self.api_key_manager = APIKeyManager()
            self.mcp_protocol = CartritaMCPProtocol(self.api_key_manager)
            self.cartrita_agent = CartritaCoreAgent(self.api_key_manager)

            # Restart
            await self.start()

            logger.info("Agents reloaded successfully")
            return True

        except Exception as e:
            logger.error("Failed to reload agents", error=str(e))
            return False

    async def execute_mcp_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        agent_id: str = "cartrita_core",
    ) -> Dict[str, Any]:
        """Execute MCP tool through the protocol."""
        try:
            message = MCPMessage(
                method="tools/call",
                params={
                    "name": tool_name,
                    "arguments": parameters,
                    "agent_id": agent_id,
                },
            )

            response = await self.mcp_protocol.handle_message(message)
            return response.result or {"error": response.error}

        except Exception as e:
            logger.error("MCP tool execution failed", tool_name=tool_name, error=str(e))
            return {"error": str(e)}

    @asynccontextmanager
    async def request_context(self, agent_id: str, tools_needed: List[str]):
        """Context manager for secure tool access."""
        access_tokens = []

        try:
            # Request access to all needed tools
            for tool in tools_needed:
                async with self.api_key_manager.key_access_context(
                    agent_id, tool
                ) as access_info:
                    access_tokens.append(access_info)

            yield {"tools_access": access_tokens}

        finally:
            # Cleanup is handled by the context manager
            pass

    async def _perform_startup_checks(self) -> None:
        """Perform comprehensive startup health checks."""
        logger.info("Performing startup health checks")

        # Check API Key Manager
        key_health = await self.api_key_manager.health_check()
        if key_health["status"] != "healthy":
            raise RuntimeError(f"API Key Manager not healthy: {key_health}")

        # Check MCP Protocol
        mcp_caps = await self.mcp_protocol._handle_capabilities({})
        if not mcp_caps.get("tools_supported", 0) > 0:
            raise RuntimeError("MCP Protocol has no tools registered")

        # Check Cartrita Agent
        cartrita_status = await self.cartrita_agent.get_status()
        if cartrita_status["status"] != "active":
            raise RuntimeError(f"Cartrita Agent not active: {cartrita_status}")

        logger.info(
            "All startup checks passed",
            key_manager_keys=key_health["total_keys"],
            mcp_tools=mcp_caps["tools_supported"],
            cartrita_agents=len(cartrita_status["available_agents"]),
        )

    async def _cleanup_operations(self) -> None:
        """Cleanup active operations during shutdown."""
        try:
            # Cancel any active tool executions
            active_executions = list(self.mcp_protocol.active_executions.keys())
            for execution_id in active_executions:
                execution = self.mcp_protocol.active_executions.get(execution_id)
                if execution:
                    execution.status = "cancelled"
                    execution.end_time = time.time()

            # Return any checked out API keys
            for agent_id, checkouts in self.api_key_manager.active_checkouts.items():
                for checkout_id in checkouts:
                    await self.api_key_manager.return_key_access(
                        agent_id, f"cleanup_{checkout_id}"
                    )

            logger.info(
                "Cleanup completed", executions_cancelled=len(active_executions)
            )

        except Exception as e:
            logger.error("Cleanup failed", error=str(e))

    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""
        uptime = time.time() - self.startup_time

        return {
            "orchestrator_id": self.orchestrator_id,
            "uptime_seconds": uptime,
            "uptime_hours": uptime / 3600,
            "is_running": self.is_running,
            "total_requests": self.processed_requests,
            "error_count": self.error_count,
            "error_rate": self.error_count / max(self.processed_requests, 1) * 100,
            "requests_per_hour": (
                self.processed_requests / (uptime / 3600) if uptime > 0 else 0
            ),
            "components": {
                "api_key_manager": {
                    "total_keys": len(self.api_key_manager.vault.list_keys()),
                    "active_checkouts": sum(
                        len(checkouts)
                        for checkouts in self.api_key_manager.active_checkouts.values()
                    ),
                    "registered_tools": len(self.api_key_manager.tool_permissions),
                },
                "mcp_protocol": {
                    "protocol_version": self.mcp_protocol.protocol_version,
                    "registered_tools": len(self.mcp_protocol.tools),
                    "active_executions": len(self.mcp_protocol.active_executions),
                    "completed_executions": len(self.mcp_protocol.execution_history),
                },
                "cartrita_agent": {
                    "available_agents": len(self.cartrita_agent.available_agents),
                    "personality_active": True,
                    "cultural_context": "hialeah_miami",
                },
            },
            "version": "2.0.0",
            "timestamp": time.time(),
        }
