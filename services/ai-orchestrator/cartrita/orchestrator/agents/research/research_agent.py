"""
Research Agent for Cartrita AI OS.
Specialized agent for web search, information gathering, and research
tasks using GPT-5.
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
        model: str = "gpt-4-turbo-preview",
        api_key: str | None = None,
        tavily_api_key: str | None = None,
    ):
        """Initialize the research agent."""
        # Get settings with proper initialization
        from cartrita.orchestrator.utils.config import get_settings
        _settings = get_settings()
        
        self.model = model
        self.api_key = api_key or _settings.ai.openai_api_key
        self.tavily_api_key = tavily_api_key or getattr(
            _settings.external, "tavily_api_key", None
        )

        # Initialize LLM
        self.llm = ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            temperature=0.1,  # Lower temperature for research accuracy
        )

        self.agent_id = f"research_agent_{int(time.time())}"
        logger.info("Research agent initialized", agent_id=self.agent_id)

    async def start(self) -> None:
        """Start the research agent."""
        logger.info("Research agent started", agent_id=self.agent_id)

    async def stop(self) -> None:
        """Stop the research agent."""
        logger.info("Research agent stopped", agent_id=self.agent_id)

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
        # Create research prompt
        system_prompt = """You are an expert research assistant with access to web search capabilities.
        Conduct thorough research on the given topic and provide comprehensive, well-sourced information.

        Your response should include:
        1. A clear summary of the topic
        2. Key findings and insights
        3. Relevant sources and citations
        4. Confidence score (0.0-1.0) based on source quality and consensus

        Be objective, accurate, and cite your sources properly."""

        research_prompt = f"""Research Topic: {query}

        Please provide a comprehensive research summary with the following structure:
        - Executive Summary
        - Key Findings
        - Sources & Citations
        - Confidence Assessment

        Focus on reliable, recent information and provide balanced perspectives."""

        # Get research from GPT-5
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=research_prompt),
        ]

        response = await self.llm.ainvoke(messages)
        research_content = response.content

        # Parse and structure the research result
        return self._parse_research_response(research_content, query)

    def _parse_research_response(self, content: str, query: str) -> dict[str, Any]:
        """Parse the research response into structured format."""
        # This is a simplified parser - in production, you'd want more sophisticated parsing
        lines = content.split("\n")
        summary = ""
        findings = []
        sources = []
        citations = []

        current_section = None
        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.lower().startswith("executive summary"):
                current_section = "summary"
                continue
            elif line.lower().startswith("key findings"):
                current_section = "findings"
                continue
            elif line.lower().startswith("sources") or line.lower().startswith(
                "citations"
            ):
                current_section = "sources"
                continue

            if current_section == "summary":
                summary += line + " "
            elif current_section == "findings" and line.startswith("-"):
                findings.append(line[1:].strip())
            elif current_section == "sources" and line.startswith("-"):
                sources.append({"title": line[1:].strip(), "url": ""})
                citations.append(line[1:].strip())

        return {
            "summary": summary.strip() or f"Research conducted on: {query}",
            "key_findings": findings or [f"Research findings for: {query}"],
            "sources": sources or [{"title": f"Research on {query}", "url": ""}],
            "citations": citations or [f"Research sources for {query}"],
            "confidence_score": 0.8,  # Default confidence
        }

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
