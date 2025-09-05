# Cartrita AI OS - Computer Use Agent
# GPT-5 powered computer interaction and automation

"""
Computer Use Agent for Cartrita AI OS.
Specialized agent for computer interactions, screenshots, file operations using GPT-5.
"""

import json
import time
from typing import Any

import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from cartrita.orchestrator.utils.config import settings

# Configure logger
logger = structlog.get_logger(__name__)


# ============================================
# Computer Use Models
# ============================================


class ScreenshotRequest(BaseModel):
    """Screenshot request model."""

    description: str = Field(..., description="What to capture in the screenshot")
    format: str = Field(default="png", description="Image format: 'png', 'jpg', 'webp'")
    quality: int = Field(
        default=90,
        ge=1,
        le=100,
        description="Image quality (for lossy formats)",
    )


class FileOperation(BaseModel):
    """File operation model."""

    operation: str = Field(
        ...,
        description="Operation type: 'read', 'write', 'list', 'delete', 'move'",
    )
    path: str = Field(..., description="File or directory path")
    content: str | None = Field(
        default=None, description="Content for write operations"
    )
    recursive: bool = Field(
        default=False, description="Recursive operation for directories"
    )


class SystemCommand(BaseModel):
    """System command model."""

    command: str = Field(..., description="Command to execute")
    timeout: int = Field(
        default=30, ge=1, le=300, description="Command timeout in seconds"
    )
    working_directory: str | None = Field(default=None, description="Working directory")


class ComputerUseRequest(BaseModel):
    """Computer use request model."""

    task: str = Field(..., description="Computer task description")
    screenshot_needed: bool = Field(
        default=False, description="Whether screenshot is needed"
    )
    file_operations: list[FileOperation] = Field(
        default_factory=list, description="File operations to perform"
    )
    system_commands: list[SystemCommand] = Field(
        default_factory=list, description="System commands to execute"
    )
    safety_mode: bool = Field(default=True, description="Enable safety restrictions")


class ComputerUseResponse(BaseModel):
    """Computer use response model."""

    result: str = Field(..., description="Operation result")
    screenshot: str | None = Field(
        default=None, description="Base64 encoded screenshot"
    )
    file_results: list[dict[str, Any]] = Field(
        default_factory=list, description="File operation results"
    )
    command_results: list[dict[str, Any]] = Field(
        default_factory=list, description="Command execution results"
    )
    safety_warnings: list[str] = Field(
        default_factory=list, description="Safety warnings"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


# ============================================
# Computer Use Agent
# ============================================


class ComputerUseAgent:
    """
    Computer Use Agent using GPT-5 for computer interactions and automation.

    Capabilities:
    - Screenshot capture and analysis
    - File system operations
    - System command execution
    - GUI automation planning
    - Safety and security enforcement
    """

    def __init__(
        self,
        model: str = settings.ai.agent_model,
        api_key: str | None = None,
        safety_mode: bool = True,
    ):
        self.model = model
        self.api_key = api_key or settings.ai.openai_api_key.get_secret_value()
        self.safety_mode = safety_mode

        # Initialize GPT-5 computer use model
        self.computer_llm = ChatOpenAI(
            model=self.model,
            temperature=0.1,  # Low temperature for precise computer operations
            max_tokens=4096,
            openai_api_key=self.api_key,
        )

        # Safety restrictions
        self.dangerous_commands = [
            "rm -rf",
            "sudo",
            "su",
            "passwd",
            "chmod 777",
            "dd",
            "mkfs",
            "fdisk",
            "format",
            "del /f /s /q",
        ]

        self.restricted_paths = [
            "/",
            "/etc",
            "/usr",
            "/bin",
            "/sbin",
            "/root",
            "/home",
        ]

        # Runtime state
        self.is_running = False

        logger.info(
            "Computer Use Agent initialized with GPT-5",
            model=self.model,
            safety_mode=safety_mode,
        )

    async def start(self) -> None:
        """Start the computer use agent."""
        self.is_running = True
        logger.info("Computer Use Agent started")

    async def stop(self) -> None:
        """Stop the computer use agent."""
        self.is_running = False
        logger.info("Computer Use Agent stopped")

    async def health_check(self) -> bool:
        """Perform health check."""
        return self.is_running

    async def get_status(self) -> dict[str, Any]:
        """Get agent status."""
        return {
            "id": "computer_use_agent",
            "name": "Computer Use Agent",
            "type": "computer_use",
            "status": "active" if self.is_running else "inactive",
            "model": self.model,
            "safety_mode": self.safety_mode,
            "description": "GPT-5 powered computer interaction and automation agent",
        }

    # ============================================
    # Core Computer Use Methods
    # ============================================

    async def execute(
        self,
        messages: list[dict[str, Any]],
        context: dict[str, Any],
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute computer use task.

        Args:
            messages: Conversation messages
            context: Execution context
            metadata: Additional metadata

        Returns:
            Computer use execution results
        """
        start_time = time.time()

        try:
            # Extract computer task from messages
            computer_task = self._extract_computer_task(messages)

            # Create computer use request
            computer_request = ComputerUseRequest(
                task=computer_task,
                screenshot_needed=context.get("screenshot_needed", False),
                file_operations=context.get("file_operations", []),
                system_commands=context.get("system_commands", []),
                safety_mode=self.safety_mode,
            )

            # Execute computer task
            result = await self._perform_computer_task(computer_request)

            # Format response
            response = {
                "response": result.result,
                "computer_data": result.dict(),
                "execution_time": time.time() - start_time,
                "metadata": {
                    "agent": "computer_use_agent",
                    "model": self.model,
                    "safety_mode": self.safety_mode,
                    "operations_performed": len(result.file_results)
                    + len(result.command_results),
                    **metadata,
                },
            }

            logger.info(
                "Computer task completed",
                operations=len(result.file_results) + len(result.command_results),
                safety_warnings=len(result.safety_warnings),
                execution_time=time.time() - start_time,
            )

            return response

        except Exception as e:
            logger.error(
                "Computer use execution failed",
                error=str(e),
                task=(
                    computer_task[:100] if "computer_task" in locals() else "unknown"
                ),
            )
            return {
                "response": f"I apologize, but I encountered an error while performing the computer task: {str(e)}",
                "error": str(e),
                "execution_time": time.time() - start_time,
                "metadata": {
                    "agent": "computer_use_agent",
                    "status": "error",
                    **metadata,
                },
            }

    async def _perform_computer_task(
        self, request: ComputerUseRequest
    ) -> ComputerUseResponse:
        """Perform computer task with safety checks."""
        safety_warnings = []

        # Safety check
        if request.safety_mode:
            safety_warnings.extend(self._check_safety(request))

        # Take screenshot if requested
        screenshot = None
        if request.screenshot_needed:
            screenshot = await self._take_screenshot()

        # Execute file operations
        file_results = []
        for operation in request.file_operations:
            if request.safety_mode and not self._is_safe_file_operation(operation):
                safety_warnings.append(
                    f"Unsafe file operation blocked: {operation.operation} on {operation.path}"
                )
                continue

            result = await self._execute_file_operation(operation)
            file_results.append(result)

        # Execute system commands
        command_results = []
        for command in request.system_commands:
            if request.safety_mode and not self._is_safe_command(command):
                safety_warnings.append(f"Unsafe command blocked: {command.command}")
                continue

            result = await self._execute_system_command(command)
            command_results.append(result)

        # Generate comprehensive result using GPT-5
        result_summary = await self._generate_task_summary(
            request, file_results, command_results, safety_warnings
        )

        return ComputerUseResponse(
            result=result_summary,
            screenshot=screenshot,
            file_results=file_results,
            command_results=command_results,
            safety_warnings=safety_warnings,
            metadata={
                "task": request.task,
                "safety_mode": request.safety_mode,
                "operations_completed": len(file_results) + len(command_results),
            },
        )

    async def _take_screenshot(self) -> str | None:
        """Take a screenshot and return base64 encoded image."""
        try:
            # This would integrate with actual screenshot functionality
            # For now, return a placeholder
            logger.info("Screenshot requested (placeholder implementation)")
            return None  # Placeholder - would return base64 encoded image
        except Exception as e:
            logger.error("Screenshot failed", error=str(e))
            return None

    async def _execute_file_operation(self, operation: FileOperation) -> dict[str, Any]:
        """Execute file operation."""
        try:
            # This would integrate with actual file system operations
            # For now, return a placeholder result
            logger.info(
                "File operation requested",
                operation=operation.operation,
                path=operation.path,
            )

            return {
                "operation": operation.operation,
                "path": operation.path,
                "success": True,
                "message": f"File operation {operation.operation} completed (placeholder)",
            }
        except Exception as e:
            logger.error(
                "File operation failed",
                operation=operation.operation,
                path=operation.path,
                error=str(e),
            )
            return {
                "operation": operation.operation,
                "path": operation.path,
                "success": False,
                "error": str(e),
            }

    async def _execute_system_command(self, command: SystemCommand) -> dict[str, Any]:
        """Execute system command."""
        try:
            # This would integrate with actual command execution
            # For now, return a placeholder result
            logger.info("System command requested", command=command.command)

            return {
                "command": command.command,
                "success": True,
                "output": f"Command executed: {command.command} (placeholder)",
                "exit_code": 0,
            }
        except Exception as e:
            logger.error("System command failed", command=command.command, error=str(e))
            return {
                "command": command.command,
                "success": False,
                "error": str(e),
                "exit_code": 1,
            }

    async def _generate_task_summary(
        self,
        request: ComputerUseRequest,
        file_results: list[dict[str, Any]],
        command_results: list[dict[str, Any]],
        safety_warnings: list[str],
    ) -> str:
        """Generate task summary using GPT-5."""
        summary_prompt = f"""Summarize the results of the following computer task:

Task: {request.task}

File Operations Performed:
{json.dumps(file_results, indent=2)}

System Commands Executed:
{json.dumps(command_results, indent=2)}

Safety Warnings:
{json.dumps(safety_warnings, indent=2)}

Provide a clear, concise summary of what was accomplished and any important notes."""

        try:
            messages = [
                SystemMessage(
                    content="You are a computer operations specialist using GPT-5. Provide clear summaries of computer tasks and their results."
                ),
                HumanMessage(content=summary_prompt),
            ]

            response = await self.computer_llm.ainvoke(messages)
            return response.content.strip()

        except Exception as e:
            logger.error("Task summary generation failed", error=str(e))
            return f"Task completed with {len(file_results)} file operations and {len(command_results)} commands executed."

    # ============================================
    # Safety Methods
    # ============================================

    def _check_safety(self, request: ComputerUseRequest) -> list[str]:
        """Check safety of the requested operations."""
        warnings = []

        # Check file operations
        for operation in request.file_operations:
            if not self._is_safe_file_operation(operation):
                warnings.append(
                    f"Potentially unsafe file operation: {operation.operation} on {operation.path}"
                )

        # Check system commands
        for command in request.system_commands:
            if not self._is_safe_command(command):
                warnings.append(f"Potentially unsafe command: {command.command}")

        return warnings

    def _is_safe_file_operation(self, operation: FileOperation) -> bool:
        """Check if file operation is safe."""
        # Check for restricted paths
        for restricted_path in self.restricted_paths:
            if (
                operation.path.startswith(restricted_path)
                and operation.path != restricted_path
            ):
                return False

        # Check for dangerous operations
        if operation.operation in ["delete", "move"] and operation.recursive:
            return False

        return True

    def _is_safe_command(self, command: SystemCommand) -> bool:
        """Check if system command is safe."""
        command_str = command.command.lower()

        # Check for dangerous commands
        for dangerous in self.dangerous_commands:
            if dangerous in command_str:
                return False

        return True

    # ============================================
    # Utility Methods
    # ============================================

    def _extract_computer_task(self, messages: list[dict[str, Any]]) -> str:
        """Extract computer task from conversation messages."""
        for message in reversed(messages):
            if isinstance(message, dict) and message.get("role") == "user":
                content = message.get("content", "")
                if content:
                    return content

        return "General computer task"

    async def reload_configuration(self) -> None:
        """Reload agent configuration."""
        # Reload settings if needed
        logger.info("Computer Use Agent configuration reloaded")
