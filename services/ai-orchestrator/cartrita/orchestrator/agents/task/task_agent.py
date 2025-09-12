# Cartrita AI OS - Task Agent
# GPT-5 powered task planning and project management

"""
Task Agent for Cartrita AI OS.
Specialized agent for task planning, project management, and workflow orchestration using GPT-5.
"""

import time
from typing import Any

import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


# Configure logger
logger = structlog.get_logger(__name__)


# ============================================
# Task Models
# ============================================


class Task(BaseModel):
    """Task model."""

    id: str = Field(..., description="Task ID")
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Task description")
    priority: str = Field(default="medium", description="Task priority")
    status: str = Field(default="pending", description="Task status")
    assignee: str | None = Field(default=None, description="Task assignee")
    dependencies: list[str] = Field(
        default_factory=list, description="Task dependencies"
    )
    estimated_hours: float | None = Field(default=None, description="Estimated hours")
    actual_hours: float | None = Field(default=None, description="Actual hours")
    due_date: str | None = Field(default=None, description="Due date")
    tags: list[str] = Field(default_factory=list, description="Task tags")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Task metadata")


class Project(BaseModel):
    """Project model."""

    id: str = Field(..., description="Project ID")
    name: str = Field(..., description="Project name")
    description: str = Field(..., description="Project description")
    status: str = Field(default="active", description="Project status")
    tasks: list[Task] = Field(default_factory=list, description="Project tasks")
    start_date: str | None = Field(default=None, description="Start date")
    end_date: str | None = Field(default=None, description="End date")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Project metadata"
    )


class TaskPlan(BaseModel):
    """Task planning model."""

    tasks: list[Task] = Field(default_factory=list, description="Planned tasks")
    dependencies: list[dict[str, str]] = Field(
        default_factory=list, description="Task dependencies"
    )
    timeline: dict[str, Any] = Field(
        default_factory=dict, description="Project timeline"
    )
    risks: list[str] = Field(default_factory=list, description="Project risks")
    recommendations: list[str] = Field(
        default_factory=list, description="Planning recommendations"
    )


class TaskResponse(BaseModel):
    """Task response model."""

    plan: TaskPlan = Field(..., description="Task plan")
    summary: str = Field(..., description="Plan summary")
    confidence_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Confidence in plan"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Response metadata"
    )


# ============================================
# Task Agent
# ============================================


class TaskAgent:
    """
    Task Agent using GPT-5 for task planning and project management.

    Capabilities:
    - Task breakdown and planning
    - Project management
    - Dependency analysis
    - Timeline estimation
    - Risk assessment
    - Resource allocation
    """

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        db_manager: Any | None = None,
    ):
        # Get settings with proper initialization
        from cartrita.orchestrator.utils.config import get_settings

        _settings = get_settings()
        self.model = model or _settings.ai.task_model
        self.api_key = api_key or _settings.ai.openai_api_key.get_secret_value()
        self.db_manager = db_manager

        # Initialize GPT-5 task model
        self.task_llm = ChatOpenAI(
            model=self.model,
            temperature=0.2,  # Moderate temperature for creative planning
            max_completion_tokens=4096,
            openai_api_key=self.api_key,
        )

        # Runtime state
        self.is_running = False

        logger.info("Task Agent initialized with GPT-5", model=self.model)

    async def start(self) -> None:
        """Start the task agent."""
        self.is_running = True
        logger.info("Task Agent started")

    async def stop(self) -> None:
        """Stop the task agent."""
        self.is_running = False
        logger.info("Task Agent stopped")

    async def health_check(self) -> bool:
        """Perform health check."""
        return self.is_running

    async def get_status(self) -> dict[str, Any]:
        """Get agent status."""
        return {
            "id": "task_agent",
            "name": "Task Agent",
            "type": "task",
            "status": "active" if self.is_running else "inactive",
            "model": self.model,
            "description": "GPT-5 powered task planning and project management agent",
        }

    # ============================================
    # Core Task Methods
    # ============================================

    async def execute(
        self,
        messages: list[dict[str, Any]],
        context: dict[str, Any],
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute task planning task.

        Args:
            messages: Conversation messages
            context: Execution context
            metadata: Additional metadata

        Returns:
            Task planning results
        """
        start_time = time.time()

        try:
            # Extract task request from messages
            task_request = self._extract_task_request(messages)

            # Create task plan
            plan = await self._create_task_plan(task_request, context)

            # Format response
            response = {
                "response": plan.summary,
                "task_data": plan.dict(),
                "execution_time": time.time() - start_time,
                "metadata": {
                    "agent": "task_agent",
                    "model": self.model,
                    "tasks_planned": len(plan.plan.tasks),
                    "confidence_score": plan.confidence_score,
                    **metadata,
                },
            }

            logger.info(
                "Task planning completed",
                request=task_request,
                tasks=len(plan.plan.tasks),
                confidence=plan.confidence_score,
                execution_time=time.time() - start_time,
            )

            return response

        except Exception as e:
            logger.error(
                "Task execution failed",
                error=str(e),
                request=(
                    task_request[:100] if "task_request" in locals() else "unknown"
                ),
            )
            return {
                "response": f"I apologize, but I encountered an error while planning tasks: {str(e)}",
                "error": str(e),
                "execution_time": time.time() - start_time,
                "metadata": {
                    "agent": "task_agent",
                    "status": "error",
                    **metadata,
                },
            }

    async def _create_task_plan(
        self, request: str, context: dict[str, Any]
    ) -> TaskResponse:
        """Create comprehensive task plan using GPT-5."""
        # Generate task breakdown
        tasks = await self._generate_task_breakdown(request)

        # Analyze dependencies
        dependencies = await self._analyze_dependencies(tasks)

        # Create timeline
        timeline = await self._create_timeline(tasks, dependencies)

        # Assess risks
        risks = await self._assess_risks(tasks, dependencies)

        # Generate recommendations
        recommendations = await self._generate_recommendations(tasks, risks)

        # Calculate confidence
        confidence_score = self._calculate_plan_confidence(tasks, dependencies)

        plan = TaskPlan(
            tasks=tasks,
            dependencies=dependencies,
            timeline=timeline,
            risks=risks,
            recommendations=recommendations,
        )

        # Generate summary
        summary = await self._generate_plan_summary(plan, request)

        return TaskResponse(
            plan=plan,
            summary=summary,
            confidence_score=confidence_score,
            metadata={
                "request": request,
                "planning_method": "gpt5_structured",
                "total_tasks": len(tasks),
            },
        )

    async def _generate_task_breakdown(self, request: str) -> list[Task]:
        """Generate detailed task breakdown using GPT-5."""
        breakdown_prompt = f"""Break down the following request into specific, actionable tasks:

Request: "{request}"

Please provide a detailed task breakdown that includes:
1. Clear, specific task titles
2. Detailed descriptions for each task
3. Priority levels (high, medium, low)
4. Estimated time requirements
5. Any prerequisites or dependencies

Format your response as a JSON array of task objects with the following structure:
[
  {{
    "title": "Task Title",
    "description": "Detailed description",
    "priority": "high|medium|low",
    "estimated_hours": 4.0
  }}
]

Tasks:"""

        try:
            messages = [
                SystemMessage(
                    content="You are a project management expert using GPT-5. Break down complex requests into detailed, actionable tasks with realistic time estimates."
                ),
                HumanMessage(content=breakdown_prompt),
            ]

            response = await self.task_llm.ainvoke(messages)
            tasks_data = self._parse_json_response(response.content)

            # Convert to Task objects
            tasks = []
            for i, task_data in enumerate(tasks_data, start=1):
                task = Task(
                    id=f"task_{i}",
                    title=task_data.get("title", f"Task {i}"),
                    description=task_data.get("description", ""),
                    priority=task_data.get("priority", "medium"),
                    estimated_hours=task_data.get("estimated_hours", 4.0),
                )
                tasks.append(task)

            return tasks

        except Exception as e:
            logger.error("Task breakdown generation failed", error=str(e))
            # Return basic fallback task
            return [
                Task(
                    id="task_1",
                    title="Main Task",
                    description=f"Complete the request: {request}",
                    priority="medium",
                    estimated_hours=8.0,
                )
            ]

    async def _analyze_dependencies(self, tasks: list[Task]) -> list[dict[str, str]]:
        """Analyze task dependencies using GPT-5."""
        if len(tasks) <= 1:
            return []

        dependency_prompt = f"""Analyze the dependencies between these tasks:

Tasks:
{chr(10).join(f"{i}. {task.title}: {task.description}" for i, task in enumerate(tasks, start=1))}

Identify which tasks must be completed before others can begin. Format as JSON array:
[
  {{"from": "task_1", "to": "task_2", "reason": "Task 2 requires Task 1 completion"}}
]

Dependencies:"""

        try:
            messages = [
                SystemMessage(
                    content="You are a dependency analysis expert using GPT-5. Identify logical dependencies between tasks."
                ),
                HumanMessage(content=dependency_prompt),
            ]

            response = await self.task_llm.ainvoke(messages)
            dependencies = self._parse_json_response(response.content)
            return dependencies

        except Exception as e:
            logger.error("Dependency analysis failed", error=str(e))
            return []

    async def _create_timeline(
        self, tasks: list[Task], dependencies: list[dict[str, str]]
    ) -> dict[str, Any]:
        """Create project timeline."""
        total_hours = sum(task.estimated_hours or 4.0 for task in tasks)

        return {
            "total_estimated_hours": total_hours,
            "total_estimated_days": total_hours / 8.0,  # Assuming 8-hour workdays
            "critical_path": self._identify_critical_path(tasks, dependencies),
            "milestones": self._identify_milestones(tasks),
        }

    async def _assess_risks(
        self, tasks: list[Task], dependencies: list[dict[str, str]]
    ) -> list[str]:
        """Assess project risks using GPT-5."""
        risk_prompt = f"""Assess potential risks for this project:

Tasks: {len(tasks)}
Dependencies: {len(dependencies)}
Total estimated hours: {sum(task.estimated_hours or 4.0 for task in tasks)}

Identify key risks that could impact timeline, budget, or quality. Be specific and actionable.

Risks:"""

        try:
            messages = [
                SystemMessage(
                    content="You are a risk assessment expert using GPT-5. Identify potential project risks and mitigation strategies."
                ),
                HumanMessage(content=risk_prompt),
            ]

            response = await self.task_llm.ainvoke(messages)
            risks = response.content.strip().split("\n")
            return [risk.strip("- ").strip() for risk in risks if risk.strip()]

        except Exception as e:
            logger.error("Risk assessment failed", error=str(e))
            return [
                "Technical complexity may cause delays",
                "Resource availability issues",
            ]

    async def _generate_recommendations(
        self, tasks: list[Task], risks: list[str]
    ) -> list[str]:
        """Generate project recommendations."""
        return [
            "Regular progress check-ins every 2-3 days",
            "Document all decisions and changes",
            "Allocate buffer time for unexpected issues",
            "Consider parallel execution where possible",
        ]

    async def _generate_plan_summary(self, plan: TaskPlan, request: str) -> str:
        """Generate comprehensive plan summary."""
        summary = f"""I've created a detailed task plan for: "{request}"

**Plan Overview:**
- Total Tasks: {len(plan.tasks)}
- Estimated Time: {plan.timeline.get('total_estimated_hours', 0):.1f} hours ({plan.timeline.get('total_estimated_days', 0):.1f} days)
- Key Dependencies: {len(plan.dependencies)}

**Risks Identified:**
{chr(10).join(f"• {risk}" for risk in plan.risks[:3])}

**Recommendations:**
{chr(10).join(f"• {rec}" for rec in plan.recommendations[:3])}

The plan includes detailed task breakdowns with priorities, time estimates, and dependency analysis."""

        return summary

    def _calculate_plan_confidence(
        self, tasks: list[Task], dependencies: list[dict[str, str]]
    ) -> float:
        """Calculate confidence score for the plan."""
        if not tasks:
            return 0.0

        # Base confidence on task detail and dependency analysis
        task_detail_score = min(len(tasks) / 10.0, 1.0)  # More tasks = more detailed
        dependency_score = min(
            len(dependencies) / 5.0, 1.0
        )  # More dependencies = better analysis

        return (task_detail_score + dependency_score) / 2.0

    # ============================================
    # Utility Methods
    # ============================================

    def _extract_task_request(self, messages: list[dict[str, Any]]) -> str:
        """Extract task request from conversation messages."""
        for message in reversed(messages):
            if isinstance(message, dict) and message.get("role") == "user":
                content = message.get("content", "")
                if content:
                    return content

        return "General task planning request"

    def _parse_json_response(self, content: str) -> list[dict[str, Any]]:
        """Parse JSON response from GPT-5."""
        try:
            # Extract JSON from response
            import json
            import re

            # Find JSON array in response
            json_match = re.search(r"\[.*\]", content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            return []

    def _identify_critical_path(
        self, tasks: list[Task], dependencies: list[dict[str, str]]
    ) -> list[str]:
        """Identify critical path tasks."""
        # Simple critical path identification
        critical_tasks = []
        for task in tasks:
            if task.priority == "high":
                critical_tasks.append(task.title)
        return critical_tasks[:3]  # Return top 3 critical tasks

    def _identify_milestones(self, tasks: list[Task]) -> list[str]:
        """Identify project milestones."""
        milestones = []
        total_tasks = len(tasks)
        half_tasks = total_tasks // 2

        if total_tasks >= 3:
            first_title = tasks[0].title
            last_title = tasks[-1].title
            milestones.extend(
                [
                    f"Complete first task: {first_title}",
                    f"Complete {half_tasks} tasks",
                    f"Complete final task: {last_title}",
                ]
            )

        return milestones

    async def reload_configuration(self) -> None:
        """Reload agent configuration."""
        # Reload settings if needed
        logger.info("Task Agent configuration reloaded")
