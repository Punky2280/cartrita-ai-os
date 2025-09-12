# Cartrita AI OS - Knowledge Agent
# GPT-5 powered knowledge retrieval and RAG

"""
Knowledge Agent for Cartrita AI OS.
Specialized agent for document search, knowledge retrieval, and RAG using GPT-5.
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
# Knowledge Models
# ============================================


class KnowledgeQuery(BaseModel):
    """Knowledge query model."""

    query: str = Field(..., description="Knowledge search query")
    top_k: int = Field(
        default=5, ge=1, le=20, description="Number of results to return"
    )
    include_metadata: bool = Field(
        default=True, description="Include document metadata"
    )
    semantic_search: bool = Field(default=True, description="Use semantic search")
    filters: dict[str, Any] = Field(default_factory=dict, description="Search filters")


class KnowledgeDocument(BaseModel):
    """Knowledge document model."""

    id: str = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")
    source: str = Field(..., description="Document source")
    relevance_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Relevance score"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Document metadata"
    )


class KnowledgeResponse(BaseModel):
    """Knowledge response model."""

    answer: str = Field(..., description="Generated answer")
    sources: list[KnowledgeDocument] = Field(
        default_factory=list, description="Source documents"
    )
    confidence_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Confidence in answer"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Response metadata"
    )


# ============================================
# Knowledge Agent
# ============================================


class KnowledgeAgent:
    """
    Knowledge Agent using GPT-5 for document search and RAG.

    Capabilities:
    - Semantic document search
    - Knowledge retrieval and synthesis
    - RAG (Retrieval-Augmented Generation)
    - Source credibility assessment
    - Multi-document analysis
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
        
        self.model = model or _settings.ai.knowledge_model
        self.api_key = api_key or _settings.ai.openai_api_key.get_secret_value()
        self.db_manager = db_manager

        # Initialize GPT-5 knowledge model with fallback support
        try:
            self.knowledge_llm = ChatOpenAI(
                model=self.model,
                temperature=1.0,  # Default temperature (some models don't support custom temperature)
                max_completion_tokens=4096,  # Use correct parameter for newer models
                openai_api_key=self.api_key,
            )
        except Exception as e:
            logger.warning("Failed to initialize OpenAI client, will use fallback", error=str(e))
            self.knowledge_llm = None
            
        # Import fallback provider
        try:
            from cartrita.orchestrator.providers.fallback_provider_v2 import get_fallback_provider
            self.fallback_provider = get_fallback_provider()
            logger.info("Fallback provider initialized for knowledge agent")
        except Exception as e:
            logger.error("Failed to initialize fallback provider", error=str(e))
            self.fallback_provider = None

        # Runtime state
        self.is_running = False

        logger.info("Knowledge Agent initialized with GPT-5", model=self.model)

    async def start(self) -> None:
        """Start the knowledge agent."""
        self.is_running = True
        logger.info("Knowledge Agent started")

    async def stop(self) -> None:
        """Stop the knowledge agent."""
        self.is_running = False
        logger.info("Knowledge Agent stopped")

    async def health_check(self) -> bool:
        """Perform health check."""
        return self.is_running

    async def get_status(self) -> dict[str, Any]:
        """Get agent status."""
        return {
            "id": "knowledge_agent",
            "name": "Knowledge Agent",
            "type": "knowledge",
            "status": "active" if self.is_running else "inactive",
            "model": self.model,
            "description": "GPT-5 powered knowledge retrieval and RAG agent",
        }

    # ============================================
    # Core Knowledge Methods
    # ============================================
    async def execute(
        self,
        messages: list[dict[str, Any]],
        context: dict[str, Any],
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Execute knowledge retrieval task.

        Args:
            messages: Conversation messages
            context: Execution context
            metadata: Additional metadata

        Returns:
            Knowledge retrieval results
        """
        start_time = time.time()

        try:
            # Extract knowledge query from messages
            knowledge_query = self._extract_knowledge_query(messages)

            # Create knowledge query
            query = KnowledgeQuery(
                query=knowledge_query,
                top_k=context.get("top_k", 5),
                include_metadata=context.get("include_metadata", True),
                semantic_search=context.get("semantic_search", True),
                filters=context.get("filters", {}),
            )

            # Execute knowledge search
            result = await self._perform_knowledge_search(query)

            # Format response
            response = {
                "response": result.answer,
                "knowledge_data": result.dict(),
                "execution_time": time.time() - start_time,
                "metadata": {
                    "agent": "knowledge_agent",
                    "model": self.model,
                    "sources_found": len(result.sources),
                    "confidence_score": result.confidence_score,
                    **metadata,
                },
            }

            logger.info(
                "Knowledge search completed",
                query=knowledge_query,
                sources=len(result.sources),
                confidence=result.confidence_score,
                execution_time=time.time() - start_time,
            )

            return response

        except Exception as e:
            logger.error(
                "Knowledge execution failed",
                error=str(e),
                query=(
                    knowledge_query[:100]
                    if "knowledge_query" in locals()
                    else "unknown"
                ),
            )
            return {
                "response": f"I apologize, but I encountered an error while searching knowledge: {str(e)}",
                "error": str(e),
                "execution_time": time.time() - start_time,
                "metadata": {
                    "agent": "knowledge_agent",
                    "status": "error",
                    **metadata,
                },
            }

    async def _perform_knowledge_search(
        self, query: KnowledgeQuery
    ) -> KnowledgeResponse:
        """Perform knowledge search and RAG."""
        # Step 1: Search for relevant documents
        sources = await self._search_documents(query)

        # Step 2: Generate answer using GPT-5 with retrieved context
        answer = await self._generate_answer_with_rag(query, sources)

        # Step 3: Calculate confidence score
        confidence_score = self._calculate_confidence_score(sources)

        return KnowledgeResponse(
            answer=answer,
            sources=sources,
            confidence_score=confidence_score,
            metadata={
                "query": query.query,
                "search_method": ("semantic" if query.semantic_search else "keyword"),
                "total_sources": len(sources),
            },
        )

    async def _search_documents(self, query: KnowledgeQuery) -> list[KnowledgeDocument]:
        """Search for relevant documents with low complexity and clear flow."""
        try:
            raw_results: list[dict[str, Any]] = []
            if self.db_manager is not None:
                raw_results = await self._db_manager_search(query)

            if not raw_results:
                logger.info("No search backend or results; returning empty", query=query.query)
                return []

            sources = self._convert_raw_results(raw_results)
            logger.info(
                "Document search completed",
                query=query.query,
                results=len(sources),
                semantic=query.semantic_search,
            )
            return sources
        except Exception as e:
            logger.error("Document search failed", error=str(e), query=query.query)
            return []

    async def _db_manager_search(self, query: KnowledgeQuery) -> list[dict[str, Any]]:
        """Select and execute the appropriate db_manager search method."""
        try:
            semantic_ok = query.semantic_search and hasattr(self.db_manager, "semantic_search")
            method_name = "semantic_search" if semantic_ok else ("search" if hasattr(self.db_manager, "search") else None)
            if not method_name:
                logger.warning("db_manager present but no compatible search method", available=dir(self.db_manager))
                return []

            search_fn = getattr(self.db_manager, method_name)
            results = await search_fn(
                query=query.query,
                top_k=query.top_k,
                filters=query.filters,
                include_metadata=query.include_metadata,
            )
            return results or []
        except Exception as e:
            logger.error("db_manager search failed", error=str(e))
            return []

    def _convert_raw_results(self, raw_results: list[dict[str, Any]]) -> list[KnowledgeDocument]:
        """Convert raw search rows into KnowledgeDocument objects."""
        sources: list[KnowledgeDocument] = []
        for i, item in enumerate(raw_results or []):
            try:
                meta = item.get("metadata", {}) if isinstance(item, dict) else {}
                sources.append(
                    KnowledgeDocument(
                        id=str(item.get("id", f"doc_{i}")),
                        title=item.get("title") or meta.get("title") or "Untitled",
                        content=item.get("content") or item.get("text") or "",
                        source=item.get("source") or meta.get("source") or "unknown",
                        relevance_score=float(item.get("score", item.get("relevance", 0.0))) if isinstance(item, dict) else 0.0,
                        metadata=meta if isinstance(meta, dict) else {},
                    )
                )
            except Exception as conv_err:
                logger.warning("Failed to convert search result", error=str(conv_err))
        return sources

    async def _generate_answer_with_rag(
        self, query: KnowledgeQuery, sources: list[KnowledgeDocument]
    ) -> str:
        """Generate answer using RAG with GPT-5."""
        # Build time-aware strings
        from datetime import datetime
        import pytz

        miami_tz = pytz.timezone('America/New_York')
        current_time = datetime.now(miami_tz).strftime('%A, %B %d, %Y at %I:%M %p %Z')

        # If no sources, avoid hallucinations and ask for permission to broaden search
        if not sources:
            return (
                "I couldn't find sufficiently relevant documents for your query in the connected knowledge base. "
                f"Query: '{query.query}'. If you'd like, I can expand the search or suggest refined keywords."
            )

        # Prepare context and footnotes
        delimited_sources = self._format_sources_block(sources)
        footnotes = self._format_source_footnotes(sources)

        # Compose prompts
        system_msg = self._build_system_prompt()
        user_msg = self._build_knowledge_prompt(
            query=query.query,
            current_time=current_time,
            sources_block=delimited_sources,
            footnotes=footnotes,
        )

        try:
            # First try OpenAI if available
            if self.knowledge_llm:
                messages = [
                    SystemMessage(content=system_msg),
                    HumanMessage(content=user_msg),
                ]
                response = await self.knowledge_llm.ainvoke(messages)
                return response.content.strip()
            else:
                raise Exception("OpenAI client not available")

        except Exception as e:
            logger.error("RAG answer generation failed", error=str(e))

            # Use fallback provider for knowledge generation
            
            if self.fallback_provider:
                try:
                    fallback_response = await self.fallback_provider.generate_response(
                        message=user_msg,
                        conversation_id=f"knowledge-{int(time.time())}",
                        context={"type": "knowledge_rag", "sources_count": len(sources)}
                    )
                    logger.info("Used fallback provider for RAG generation")
                    return fallback_response
                except Exception as fallback_error:
                    logger.error("Fallback provider also failed", error=str(fallback_error))

            # Final fallback - return basic context summary with footnotes
            summary = "\n\n".join([
                f"Query: {query.query}",
                "Key source excerpts:",
                "\n".join([f"- {s.title}: {s.content[:240]}" for s in sources[:3]]),
                footnotes,
            ])
            return summary[:1500]

    def _calculate_confidence_score(self, sources: list[KnowledgeDocument]) -> float:
        """Calculate confidence score based on sources."""
        if not sources:
            return 0.0

        # Simple confidence calculation based on number and relevance of sources
        avg_relevance = sum(source.relevance_score for source in sources) / len(sources)
        source_count_factor = min(
            len(sources) / 5.0, 1.0
        )  # Max confidence at 5+ sources

        return (avg_relevance + source_count_factor) / 2.0

    # ============================================
    # Utility Methods
    # ============================================

    def _build_system_prompt(self) -> str:
        """Construct a concise, explicit system prompt with strong guardrails.

        Aligned with OpenAI prompt engineering guidance: be explicit about role,
        constraints, formatting, and refusal to fabricate.
        """
        return (
            "You are Cartrita's Knowledge Agent. Your job is to synthesize accurate, well-attributed, and"
            " actionable answers strictly from the provided sources. Do not invent facts. If information"
            " is missing or uncertain, say so and propose next steps. Keep explanations clear and concise."
        )

    def _build_knowledge_prompt(self, *, query: str, current_time: str, sources_block: str, footnotes: str) -> str:
        """Build the user prompt with clear delimiters and a strict output structure."""
        return (
            f"# Knowledge Synthesis Request\n"
            f"Time: {current_time}\n"
            f"Query: \"{query}\"\n\n"
            f"## Sources (do not assume anything not contained below)\n"
            f"<<<SOURCES>>>\n{sources_block}\n<<<END_SOURCES>>>\n\n"
            f"## Instructions\n"
            f"- Base the answer only on the sources.\n"
            f"- Identify conflicts and note currency/recency.\n"
            f"- Separate facts from analysis.\n"
            f"- Use the output structure exactly.\n\n"
            f"## Output Structure\n"
            f"### Direct Answer\n"
            f"Provide a 2-3 sentence direct answer.\n\n"
            f"### Details\n"
            f"Synthesize key points from multiple sources, highlighting agreements and disagreements.\n\n"
            f"### Sources\n"
            f"Cite using footnote numbers like [1], [2] that correspond to the list below.\n\n"
            f"### Gaps or Uncertainty\n"
            f"State what is unknown or requires verification; suggest next steps or search refinements.\n\n"
            f"### Related Insights\n"
            f"Offer 1-3 concise related insights.\n\n"
            f"## Footnotes\n{footnotes}\n"
        )

    def _format_sources_block(self, sources: list[KnowledgeDocument]) -> str:
        """Format the retrieved sources into a delimited block with minimal noise."""
        lines: list[str] = []
        for idx, s in enumerate(sources, start=1):
            lines.append(
                "\n".join(
                    [
                        f"[{idx}] Title: {s.title}",
                        f"URL/Source: {s.source}",
                        f"Excerpt: {s.content[:1200]}",
                    ]
                )
            )
        return "\n\n".join(lines)

    def _format_source_footnotes(self, sources: list[KnowledgeDocument]) -> str:
        """Create a compact footnote list mapping [n] to source metadata."""
        rows: list[str] = []
        for idx, s in enumerate(sources, start=1):
            score = f"{s.relevance_score:.2f}" if isinstance(s.relevance_score, float) else ""
            rows.append(f"[{idx}] {s.title} — {s.source} (relevance {score})")
        return "\n".join(rows)

    def _extract_knowledge_query(self, messages: list[dict[str, Any]]) -> str:
        """Extract knowledge query from conversation messages."""
        for message in reversed(messages):
            if isinstance(message, dict) and message.get("role") == "user":
                content = message.get("content", "")
                if content:
                    return content

        return "General knowledge query"

    async def reload_configuration(self) -> None:
        """Reload agent configuration."""
        # Reload settings if needed
        logger.info("Knowledge Agent configuration reloaded")
