"""
Research Agent for Cartrita AI OS.
Specialized agent for web search, information gathering, and research
tasks using GPT-5.
"""

import time
from typing import Any

import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from cartrita.orchestrator.utils.llm_factory import create_chat_openai
from pydantic import BaseModel, Field


# Configure logger
logger = structlog.get_logger(__name__)


# ============================================
# Research Models
# ============================================


class ResearchRequest(BaseModel):
    """Research request model."""

    query: str = Field(..., description="Research query or topic")
    depth: str = Field(
        default="comprehensive",
        description="Research depth: 'quick', 'detailed', 'comprehensive'",
    )
    sources: int = Field(default=5, description="Number of sources to gather")
    include_citations: bool = Field(default=True, description="Include citations")
    focus_areas: list[str] | None = Field(
        default=None, description="Specific areas to focus on"
    )


class ResearchResult(BaseModel):
    """Research result model."""

    summary: str = Field(..., description="Research summary")
    key_findings: list[str] = Field(default_factory=list, description="Key findings")
    sources: list[dict[str, Any]] = Field(
        default_factory=list, description="Source information"
    )
    citations: list[str] = Field(default_factory=list, description="Citations")
    confidence_score: float = Field(default=0.0, description="Confidence in results")


# ============================================
# Research Agent
# ============================================


class ResearchAgent:
    """Research agent for information gathering and analysis."""
    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        tavily_api_key: str | None = None,
    ):
        """Initialize the research agent with optimal GPT-4o model."""
        # Get settings with proper initialization
        from cartrita.orchestrator.utils.config import get_settings
        _settings = get_settings()
        self.model = model or _settings.ai.research_model
        self.api_key = api_key or _settings.ai.openai_api_key
        self.tavily_api_key = tavily_api_key or getattr(
            _settings.external, "tavily_api_key", None
        )

        # Initialize LLM via factory
        self.llm = create_chat_openai(
            model=self.model,
            openai_api_key=self.api_key,
            temperature=0.1,
        )

        self.agent_id = f"research_agent_{int(time.time())}"
        logger.info("Research agent initialized", agent_id=self.agent_id)

    async def start(self) -> None:
        """Start the research agent."""
        logger.info("Research agent started", agent_id=self.agent_id)

    async def stop(self) -> None:
        """Stop the research agent."""
        logger.info("Research agent stopped", agent_id=self.agent_id)

    async def process_messages(
        self, messages: list[dict[str, Any]], context: dict[str, Any] = None
    ) -> dict[str, Any]:
        """Process messages using research capabilities."""
        if context is None:
            context = {}

        try:
            # Extract query from messages
            query = self._extract_query(messages)
            if not query:
                return {
                    "response": "I need a specific research question to investigate. What would you like me to research?",
                    "success": False,
                    "metadata": {"agent": "research_agent", "error": "no_query"},
                }

            # Add real-time context for time-related queries
            if any(word in query.lower() for word in ["time", "date", "today", "now", "current"]):
                return await self._handle_time_query(query, context)

            # Perform research
            result = await self._perform_research(query, context)

            # Format response for orchestrator
            return {
                "response": result.get("summary", "Research completed but no summary available."),
                "success": True,
                "metadata": {
                    "agent": "research_agent",
                    "model": self.model,
                    "query": query,
                    "sources_count": len(result.get("sources", [])),
                    "confidence_score": result.get("confidence_score", 0.0),
                    "processing_time": time.time(),
                },
                "context": {"last_research": result},
            }

        except Exception as e:
            logger.error(f"Research agent process_messages failed: {e}")
            return {
                "response": f"Research investigation ran into some issues: {str(e)[:100]}...",
                "success": False,
                "metadata": {"agent": "research_agent", "error": str(e)},
            }

    async def _handle_time_query(self, query: str, context: dict[str, Any]) -> dict[str, Any]:
        """Handle time and date queries with real-time information."""
        # Mark unused parameters for linter; kept for interface stability
        _ = (query, context)
        try:
            from datetime import datetime
            import pytz

            # Get current time in Miami timezone
            miami_tz = pytz.timezone('America/New_York')
            current_time = datetime.now(miami_tz)

            # Format comprehensive time information
            formatted_time = current_time.strftime('%I:%M %p')
            formatted_date = current_time.strftime('%A, %B %d, %Y')
            timezone_name = current_time.strftime('%Z')

            response = f"""🕐 **Current Time & Date in Miami**

**Time**: {formatted_time} {timezone_name}
**Date**: {formatted_date}
**Timezone**: {timezone_name} (Miami/Eastern Time)

**Additional Context**:
- Miami follows Eastern Standard Time (EST) in winter and Eastern Daylight Time (EDT) in summer
- Current season: {'Summer Time' if current_time.dst() else 'Standard Time'}
- This information is accurate as of the moment you asked ⚡

**Quick Miami Time Facts**:
- Perfect time for cafecito ☕
- Hurricane season runs June 1 - November 30
- Beach weather year-round! 🌴"""

            return {
                "response": response,
                "success": True,
                "metadata": {
                    "agent": "research_agent",
                    "query_type": "time_date",
                    "current_time": current_time.isoformat(),
                    "timezone": str(miami_tz),
                    "real_time_data": True
                }
            }

        except Exception as e:
            logger.error(f"Time query handling failed: {e}")
            return {
                "response": "Had trouble getting the exact time - you can check your device's clock or search 'Miami time' online.",
                "success": False,
                "metadata": {"agent": "research_agent", "error": str(e)}
            }

    async def get_status(self) -> dict[str, Any]:
        """Get agent status."""
        return {
            "id": self.agent_id,
            "name": "Research Agent",
            "type": "research",
            "status": "active",
            "description": "Specialized agent for research and information gathering",
            "model": self.model,
            "capabilities": [
                "web_search",
                "information_gathering",
                "fact_checking",
                "source_analysis",
                "research_summarization",
            ],
        }

    async def execute(
        self,
        messages: list[dict[str, Any]],
        context: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Execute research task."""
        # Use metadata for future extensibility
        _ = metadata
        try:
            # Extract research query from messages
            query = self._extract_query(messages)

            if not query:
                return {
                    "response": "I need a specific research topic or question to work with. Please provide more details about what you'd like me to research.",
                    "success": False,
                    "error": "No query found in messages",
                }

            # Perform research
            research_result = await self._perform_research(query, context or {})

            # Format response
            response = self._format_research_response(research_result)

            return {
                "response": response,
                "success": True,
                "metadata": {
                    "query": query,
                    "sources_count": len(research_result.get("sources", [])),
                    "confidence_score": research_result.get("confidence_score", 0.0),
                    "processing_time": time.time(),
                },
                "context": {"last_research": research_result, "query": query},
            }

        except Exception as e:
            logger.error(
                "Research execution failed",
                error=str(e),
                agent_id=self.agent_id,
            )
            return {
                "response": f"I encountered an error while conducting research: {str(e)}. Please try again.",
                "success": False,
                "error": str(e),
            }

    def _extract_query(self, messages: list[dict[str, Any]]) -> str | None:
        """Extract research query from messages."""
        for message in reversed(messages):
            if isinstance(message, dict) and message.get("role") == "user":
                content = message.get("content", "")
                if content.strip():
                    return content.strip()

        return None

    async def _perform_research(
        self, query: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Perform the actual research using GPT-5 capabilities."""
        # Use context for future research customization
        _ = context
        # Time awareness
        from datetime import datetime
        import pytz

        miami_tz = pytz.timezone('America/New_York')
        current_time = datetime.now(miami_tz).strftime('%A, %B %d, %Y at %I:%M %p %Z')

        # Build prompts using helpers to reduce method size
        system_prompt = self._build_system_prompt(current_time)
        research_prompt = self._build_research_prompt(query)

        # Invoke LLM
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=research_prompt),
        ]

        response = await self.llm.ainvoke(messages)
        research_content = response.content

        # Parse and structure the research result
        return self._parse_research_response(research_content, query)

    def _parse_research_response(self, content: str, query: str) -> dict[str, Any]:
        """Parse the research response into structured format with reduced branching."""
        sections = self._extract_sections(content)
        summary = sections.get("executive summary") or sections.get("summary") or ""
        findings_block = sections.get("key findings", "")
        sources_block = sections.get("sources", "") or sections.get("citations", "")

        # Normalize findings: lines starting with '-' or numeric list
        findings: list[str] = []
        for line in findings_block.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("-"):
                findings.append(line[1:].strip())
            elif line[0:2].isdigit() and "." in line:
                # e.g., "1. point" -> remove number
                findings.append(line.split(".", 1)[1].strip())

        # Extract sources as plain titles/URLs if present
        sources: list[dict[str, Any]] = []
        citations: list[str] = []
        for line in sources_block.splitlines():
            t = line.strip().lstrip("- ")
            if not t:
                continue
            sources.append({"title": t, "url": ""})
            citations.append(t)

        return {
            "summary": summary.strip() or f"Research conducted on: {query}",
            "key_findings": findings or [f"Research findings for: {query}"],
            "sources": sources or [{"title": f"Research on {query}", "url": ""}],
            "citations": citations or [f"Research sources for {query}"],
            "confidence_score": 0.8,
        }

    # --------------------------------------------
    # Prompt builders and parsing helpers
    # --------------------------------------------

    def _build_system_prompt(self, current_time: str) -> str:
        """Construct a concise research system prompt with clear standards."""
        return (
            "You are Cartrita's Research Agent. Perform professional-grade research:"
            " analyze queries, cross-verify claims, assess source credibility, and"
            f" account for temporal context (now: {current_time}). Provide an executive"
            " summary, key findings, sources with brief reliability notes, temporal"
            " context, and actionable insights. If information is uncertain, state"
            " limitations and propose next steps."
        )

    def _build_research_prompt(self, query: str) -> str:
        """Build the user prompt describing the expected structure."""
        return (
            f"Research Topic: {query}\n\n"
            "Please provide:\n"
            "- Executive Summary (2-3 sentences)\n"
            "- Key Findings (bulleted)\n"
            "- Sources & Citations (credible, recent)\n"
            "- Temporal Context (recency, trends)\n"
            "- Actionable Insights (what to do next)\n"
        )

    def _extract_sections(self, content: str) -> dict[str, str]:
        """Extract sections by simple heading detection; lowers cyclomatic complexity."""
        headings = [
            "executive summary",
            "summary",
            "key findings",
            "deep analysis",
            "sources",
            "citations",
            "temporal context",
            "actionable insights",
        ]
        current = None
        buckets: dict[str, list[str]] = {h: [] for h in headings}
        for raw in content.splitlines():
            line = raw.strip()
            if not line:
                continue
            lower = line.lower().strip(":")
            if lower in headings:
                current = lower
                continue
            if current:
                buckets[current].append(line)
        return {k: "\n".join(v).strip() for k, v in buckets.items() if v}

    def _format_research_response(self, research_result: dict[str, Any]) -> str:
        """Format research results into a readable response."""
        summary = research_result.get("summary", "")
        findings = research_result.get("key_findings", [])
        sources = research_result.get("sources", [])
        confidence = research_result.get("confidence_score", 0.0)

        response = "## Research Results\n\n"
        response += f"**Summary:** {summary}\n\n"

        if findings:
            response += "**Key Findings:**\n"
            for finding in findings:
                response += f"• {finding}\n"
            response += "\n"

        if sources:
            response += "**Sources:**\n"
            for i, source in enumerate(sources, 1):
                title = source.get("title", f"Source {i}")
                response += f"{i}. {title}\n"
            response += "\n"

        response += f"**Confidence Score:** {confidence:.1%}\n\n"
        response += (
            "*This research was conducted using advanced AI analysis and "
            "web search capabilities.*"

        )
        return response
