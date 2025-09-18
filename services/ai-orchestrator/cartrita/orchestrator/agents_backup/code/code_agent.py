# Cartrita AI OS - Code Agent
# GPT-5 powered code generation and analysis

"""
Code Agent for Cartrita AI OS.
Specialized agent for code generation, debugging, optimization, and technical tasks using GPT-5.
"""

import json
import time
from typing import Any

import structlog

# Optional: Add try-except for import robustness (not required to fix the error)
try:
    from langchain_core.messages import HumanMessage, SystemMessage
except ImportError as e:
    # Defer logging until logger is configured below
    _import_error = e  # store for later
    HumanMessage = None  # type: ignore
    SystemMessage = None  # type: ignore
from pydantic import BaseModel, Field

from cartrita.orchestrator.utils.llm_factory import create_chat_openai

# Configure logger
logger = structlog.get_logger(__name__)

# Log deferred import error if present
_tmp_err = globals().get("_import_error")
if _tmp_err is not None:
    logger.error("Failed to import langchain_core.messages", error=str(_tmp_err))
    _import_error = None


# ============================================
# Code Models
# ============================================


class CodeRequest(BaseModel):
    """Code request model."""

    task: str = Field(..., description="Coding task description")
    language: str = Field(default="python", description="Programming language")
    framework: str | None = Field(default=None, description="Framework or library")
    complexity: str = Field(
        default="intermediate",
        description="Code complexity: 'simple', 'intermediate', 'advanced'",
    )
    include_tests: bool = Field(default=True, description="Include unit tests")
    include_docs: bool = Field(default=True, description="Include documentation")
    existing_code: str | None = Field(
        default=None, description="Existing code to work with"
    )


class CodeAnalysis(BaseModel):
    """Code analysis result."""

    language: str = Field(..., description="Detected programming language")
    complexity: str = Field(..., description="Code complexity assessment")
    quality_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Code quality score"
    )
    issues: list[dict[str, Any]] = Field(
        default_factory=list, description="Identified issues"
    )
    suggestions: list[str] = Field(
        default_factory=list, description="Improvement suggestions"
    )
    security_concerns: list[str] = Field(
        default_factory=list, description="Security concerns"
    )


class CodeGeneration(BaseModel):
    """Code generation result."""

    code: str = Field(..., description="Generated code")
    explanation: str = Field(..., description="Code explanation")
    tests: str | None = Field(default=None, description="Generated tests")
    documentation: str | None = Field(
        default=None, description="Generated documentation"
    )
    dependencies: list[str] = Field(
        default_factory=list, description="Required dependencies"
    )
    usage_examples: list[str] = Field(
        default_factory=list, description="Usage examples"
    )


class CodeReview(BaseModel):
    """Code review result."""

    overall_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Overall code quality score"
    )
    strengths: list[str] = Field(default_factory=list, description="Code strengths")
    issues: list[dict[str, Any]] = Field(
        default_factory=list, description="Identified issues"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Improvement recommendations"
    )
    security_review: dict[str, Any] = Field(
        default_factory=dict, description="Security assessment"
    )


# ============================================
# Code Agent
# ============================================


class CodeAgent:
    """
    Code Agent using GPT-5 for code generation, analysis, and optimization.

    Capabilities:
    - Code generation in multiple languages
    - Code analysis and quality assessment
    - Debugging and error resolution
    - Code optimization and refactoring
    - Test generation
    - Documentation generation
    - Security analysis
    """

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
    ):
        # Get settings with proper initialization
        from cartrita.orchestrator.utils.config import get_settings

        _settings = get_settings()

        self.model = model or _settings.ai.code_model
        self.api_key = api_key or _settings.ai.openai_api_key.get_secret_value()

        # Initialize GPT-5 code model via factory (normalizes token params)
        self.code_llm = create_chat_openai(
            model=self.model,
            temperature=0.2,
            max_completion_tokens=8192,
            openai_api_key=self.api_key,
        )

        # Supported languages and frameworks
        self.supported_languages = [
            "python",
            "javascript",
            "typescript",
            "java",
            "c++",
            "c#",
            "go",
            "rust",
            "php",
            "ruby",
            "swift",
            "kotlin",
            "scala",
        ]

        self.supported_frameworks = {
            "python": [
                "fastapi",
                "django",
                "flask",
                "pydantic",
                "numpy",
                "pandas",
            ],
            "javascript": ["react", "vue", "angular", "node", "express"],
            "typescript": ["react", "vue", "angular", "node", "nest"],
        }

        # Runtime state
        self.is_running = False

        logger.info("Code Agent initialized with GPT-5", model=self.model)

    async def start(self) -> None:
        """Start the code agent."""
        self.is_running = True
        logger.info("Code Agent started")

    async def stop(self) -> None:
        """Stop the code agent."""
        self.is_running = False
        logger.info("Code Agent stopped")

    async def health_check(self) -> bool:
        """Perform health check."""
        return self.is_running

    async def get_status(self) -> dict[str, Any]:
        """Get agent status."""
        return {
            "id": "code_agent",
            "name": "Code Agent",
            "type": "code",
            "status": "active" if self.is_running else "inactive",
            "model": self.model,
            "supported_languages": self.supported_languages,
            "description": "GPT-5 powered code generation and analysis agent",
        }

    # ============================================
    # Core Code Methods
    # ============================================

    async def execute(
        self,
        messages: list[dict[str, Any]],
        context: dict[str, Any],
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute code-related task.

        Args:
            messages: Conversation messages
            context: Execution context
            metadata: Additional metadata

        Returns:
            Code execution results
        """
        start_time = time.time()

        try:
            # Extract code task from messages
            code_task = self._extract_code_task(messages)

            # Determine task type
            task_type = self._determine_task_type(code_task, context)

            # Execute appropriate task
            if task_type == "generate":
                result = await self._generate_code(code_task, context)
            elif task_type == "analyze":
                result = await self._analyze_code(code_task, context)
            elif task_type == "debug":
                result = await self._debug_code(code_task, context)
            elif task_type == "optimize":
                result = await self._optimize_code(code_task, context)
            elif task_type == "review":
                result = await self._review_code(code_task, context)
            else:
                result = await self._generate_code(
                    code_task, context
                )  # Default to generation

            # Format response
            response = {
                "response": result.get("response", ""),
                "code_data": result,
                "execution_time": time.time() - start_time,
                "metadata": {
                    "agent": "code_agent",
                    "model": self.model,
                    "task_type": task_type,
                    "language": context.get("language", "python"),
                    **metadata,
                },
            }

            logger.info(
                "Code task completed",
                task_type=task_type,
                language=context.get("language", "python"),
                execution_time=time.time() - start_time,
            )

            return response

        except Exception as e:
            logger.error(
                "Code execution failed",
                error=str(e),
                task=code_task[:100] if "code_task" in locals() else "unknown",
            )
            return {
                "response": f"I apologize, but I encountered an error while processing the code task: {str(e)}",
                "error": str(e),
                "execution_time": time.time() - start_time,
                "metadata": {
                    "agent": "code_agent",
                    "status": "error",
                    **metadata,
                },
            }

    async def _generate_code(
        self, task: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate code using GPT-5."""
        language = context.get("language", "python")
        framework = context.get("framework")
        complexity = context.get("complexity", "intermediate")
        include_tests = context.get("include_tests", True)
        include_docs = context.get("include_docs", True)
        existing_code = context.get("existing_code")

        # Create code generation prompt
        prompt_parts = [
            f"Generate {complexity} level {language} code for the following task:",
            f"Task: {task}",
            f"Language: {language}",
        ]

        if framework:
            prompt_parts.append(f"Framework: {framework}")

        if existing_code:
            prompt_parts.append(f"Existing code to work with:\n{existing_code}")

        if include_tests:
            prompt_parts.append("Include comprehensive unit tests")

        if include_docs:
            prompt_parts.append("Include detailed documentation and docstrings")

        prompt_parts.extend(
            [
                "",
                "Provide the response in the following JSON format:",
                "{",
                '  "code": "the generated code",',
                '  "explanation": "detailed explanation of the code",',
                '  "tests": "unit tests if requested",',
                '  "documentation": "documentation if requested",',
                '  "dependencies": ["list", "of", "dependencies"],',
                '  "usage_examples": ["example1", "example2"]',
                "}",
            ]
        )

        generation_prompt = "\n".join(prompt_parts)

        try:
            messages = [
                SystemMessage(
                    content=f"You are an expert {language} developer using GPT-5. Generate high-quality, well-documented code that follows best practices."
                ),
                HumanMessage(content=generation_prompt),
            ]

            response = await self.code_llm.ainvoke(messages)
            code_text = response.content.strip()

            # Parse JSON response
            code_result = json.loads(code_text)
            result = CodeGeneration(**code_result)

            logger.info(
                "Code generation completed",
                language=language,
                lines=len(result.code.split("\n")),
            )
            return result.dict()

        except Exception as e:
            logger.error("Code generation failed", error=str(e), language=language)
            return {
                "code": f"# Error generating code: {str(e)}",
                "explanation": f"Code generation failed: {str(e)}",
                "tests": None,
                "documentation": None,
                "dependencies": [],
                "usage_examples": [],
            }

    async def _analyze_code(self, code: str, context: dict[str, Any]) -> dict[str, Any]:
        """Analyze code using GPT-5."""
        language = self._detect_language(code)

        analysis_prompt = f"""Analyze the following {language} code for quality, complexity, and potential issues:

Code to analyze:
``` {language}
{code}
```

Provide a comprehensive analysis including:
1. Programming language detection
2. Complexity assessment
3. Code quality score (0.0-1.0)
4. Identified issues with severity levels
5. Improvement suggestions
6. Security concerns

Format your response as JSON:
{{
    "language": "detected_language",
    "complexity": "simple/intermediate/advanced",
    "quality_score": 0.85,
    "issues": [
        {{"type": "issue_type", "severity": "low/medium/high", "description": "description", "line": 10}}
    ],
    "suggestions": ["suggestion1", "suggestion2"],
    "security_concerns": ["concern1", "concern2"]
}}"""

        try:
            messages = [
                SystemMessage(
                    content="You are an expert code analyst using GPT-5. Provide thorough, actionable code analysis."
                ),
                HumanMessage(content=analysis_prompt),
            ]

            response = await self.code_llm.ainvoke(messages)
            analysis_text = response.content.strip()

            # Parse JSON response
            analysis_result = json.loads(analysis_text)
            result = CodeAnalysis(**analysis_result)

            logger.info(
                "Code analysis completed",
                language=language,
                quality_score=result.quality_score,
            )
            return result.dict()

        except Exception as e:
            logger.error("Code analysis failed", error=str(e))
            return {
                "language": language,
                "complexity": "unknown",
                "quality_score": 0.0,
                "issues": [
                    {
                        "type": "error",
                        "severity": "high",
                        "description": f"Analysis failed: {str(e)}",
                    }
                ],
                "suggestions": [],
                "security_concerns": [],
            }

    async def _debug_code(
        self, code_with_error: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Debug code using GPT-5."""
        error_message = context.get("error_message", "")
        language = self._detect_language(code_with_error)

        debug_prompt = f"""Debug the following {language} code that has an error:

Code with error:
``` {language}
{code_with_error}
```

Error message:
{error_message}

Please:
1. Identify the root cause of the error
2. Provide the corrected code
3. Explain what was wrong and how to fix it
4. Suggest preventive measures

Format your response as JSON:
{{
    "root_cause": "description of the problem",
    "corrected_code": "the fixed code",
    "explanation": "detailed explanation of the fix",
    "preventive_measures": ["measure1", "measure2"]
}}"""

        try:
            messages = [
                SystemMessage(
                    content="You are an expert debugger using GPT-5. Provide clear, actionable debugging solutions."
                ),
                HumanMessage(content=debug_prompt),
            ]

            response = await self.code_llm.ainvoke(messages)
            debug_text = response.content.strip()

            # Parse JSON response
            debug_result = json.loads(debug_text)

            logger.info("Code debugging completed", language=language)
            return debug_result

        except Exception as e:
            logger.error("Code debugging failed", error=str(e))
            return {
                "root_cause": f"Debugging failed: {str(e)}",
                "corrected_code": code_with_error,
                "explanation": "Unable to debug the code automatically",
                "preventive_measures": [
                    "Add proper error handling",
                    "Use logging for debugging",
                ],
            }

    async def _optimize_code(
        self, code: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Optimize code using GPT-5."""
        language = self._detect_language(code)
        optimization_focus = context.get(
            "focus", "performance"
        )  # performance, memory, readability

        optimize_prompt = f"""Optimize the following {language} code focusing on {optimization_focus}:

Original code:
``` {language}
{code}
```

Please:
1. Analyze the current implementation
2. Identify optimization opportunities
3. Provide the optimized code
4. Explain the optimizations made
5. Note any trade-offs

Format your response as JSON:
{{
    "analysis": "analysis of current implementation",
    "optimizations": ["optimization1", "optimization2"],
    "optimized_code": "the optimized code",
    "explanation": "detailed explanation of changes",
    "trade_offs": ["trade_off1", "trade_off2"]
}}"""

        try:
            messages = [
                SystemMessage(
                    content=f"You are an expert code optimizer using GPT-5, specializing in {optimization_focus} optimization."
                ),
                HumanMessage(content=optimize_prompt),
            ]

            response = await self.code_llm.ainvoke(messages)
            optimize_text = response.content.strip()

            # Parse JSON response
            optimize_result = json.loads(optimize_text)

            logger.info(
                "Code optimization completed",
                language=language,
                focus=optimization_focus,
            )
            return optimize_result

        except Exception as e:
            logger.error("Code optimization failed", error=str(e))
            return {
                "analysis": f"Optimization analysis failed: {str(e)}",
                "optimizations": [],
                "optimized_code": code,
                "explanation": "Unable to optimize the code automatically",
                "trade_offs": [],
            }

    async def _review_code(self, code: str, context: dict[str, Any]) -> dict[str, Any]:
        """Review code using GPT-5."""
        language = self._detect_language(code)

        review_prompt = f"""Perform a comprehensive code review of the following {language} code:

Code to review:
``` {language}
{code}
```

Provide a detailed code review covering:
1. Overall quality score (0.0-1.0)
2. Code strengths
3. Identified issues with severity and location
4. Specific improvement recommendations
5. Security assessment

Format your response as JSON:
{{
    "overall_score": 0.85,
    "strengths": ["strength1", "strength2"],
    "issues": [
        {{"severity": "medium", "type": "bug", "description": "description", "line": 15, "suggestion": "fix"}}
    ],
    "recommendations": ["rec1", "rec2"],
    "security_review": {{
        "vulnerabilities": ["vuln1"],
        "recommendations": ["sec_rec1"],
        "overall_risk": "low/medium/high"
    }}
}}"""

        try:
            messages = [
                SystemMessage(
                    content="You are an expert code reviewer using GPT-5. Provide thorough, constructive code reviews."
                ),
                HumanMessage(content=review_prompt),
            ]

            response = await self.code_llm.ainvoke(messages)
            review_text = response.content.strip()

            # Parse JSON response
            review_result = json.loads(review_text)
            result = CodeReview(**review_result)

            logger.info(
                "Code review completed",
                language=language,
                score=result.overall_score,
            )
            return result.dict()

        except Exception as e:
            logger.error("Code review failed", error=str(e))
            return {
                "overall_score": 0.0,
                "strengths": [],
                "issues": [
                    {
                        "severity": "high",
                        "type": "error",
                        "description": f"Review failed: {str(e)}",
                    }
                ],
                "recommendations": [],
                "security_review": {
                    "vulnerabilities": [],
                    "recommendations": [],
                    "overall_risk": "unknown",
                },
            }

    # ============================================
    # Utility Methods
    # ============================================

    def _extract_code_task(self, messages: list[dict[str, Any]]) -> str:
        """Extract code task from conversation messages."""
        for message in reversed(messages):
            if isinstance(message, dict) and message.get("role") == "user":
                content = message.get("content", "")
                if content:
                    return content

        return "General coding task"

    def _determine_task_type(self, task: str, context: dict[str, Any]) -> str:
        """Determine the type of code task."""
        task_lower = task.lower()

        # Check for explicit task types in context
        if context.get("task_type"):
            return context["task_type"]

        # Analyze task description
        if any(
            keyword in task_lower
            for keyword in ["generate", "create", "write", "build"]
        ):
            return "generate"
        elif any(
            keyword in task_lower
            for keyword in ["analyze", "review", "assess", "evaluate"]
        ):
            return "analyze"
        elif any(
            keyword in task_lower for keyword in ["debug", "fix", "error", "problem"]
        ):
            return "debug"
        elif any(
            keyword in task_lower
            for keyword in ["optimize", "improve", "performance", "speed"]
        ):
            return "optimize"
        elif any(
            keyword in task_lower for keyword in ["review", "feedback", "comments"]
        ):
            return "review"
        else:
            return "generate"  # Default to generation

    def _detect_language(self, code: str) -> str:
        """Detect programming language from code."""
        # Simple language detection based on keywords and syntax

        if "def " in code and "import " in code:
            return "python"
        elif "function" in code and (
            "var " in code or "const " in code or "let " in code
        ):
            return "javascript"
        elif "public class" in code and "void main" in code:
            return "java"
        elif "#include" in code and "int main" in code:
            return "c++"
        elif "fn " in code and "let " in code:
            return "rust"
        elif "func " in code and "package main" in code:
            return "go"
        else:
            return "unknown"

    async def reload_configuration(self) -> None:
        """Reload agent configuration."""
        # Reload settings if needed
        logger.info("Code Agent configuration reloaded")
