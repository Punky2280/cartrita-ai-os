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
from cartrita.orchestrator.utils.llm_factory import create_chat_openai
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
            self.knowledge_llm = create_chat_openai(
                model=self.model,
                temperature=1.0,
                max_completion_tokens=4096,
                openai_api_key=self.api_key,
            )
        except Exception as e:
            logger.warning("Failed to initialize OpenAI client, will use fallback", error=str(e))
            self.knowledge_llm = None

        # Import fallback provider
        try:
            from cartrita.orchestrator.providers.fallback_provider import get_fallback_provider
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
            # Prepare and execute search
            query = self._prepare_knowledge_query(messages, context)
            result = await self._perform_knowledge_search(query)

            # Build and return response
            response = self._build_knowledge_success_response(result, start_time, metadata)
            self._log_knowledge_completion(query.query, result, start_time)

            return response

        except Exception as e:
            return self._build_knowledge_error_response(e, start_time, metadata, locals())

    def _prepare_knowledge_query(
        self, messages: list[dict[str, Any]], context: dict[str, Any]
    ) -> KnowledgeQuery:
        """Prepare knowledge query from messages and context."""
        knowledge_query = self._extract_knowledge_query(messages)

        return KnowledgeQuery(
            query=knowledge_query,
            top_k=context.get("top_k", 5),
            include_metadata=context.get("include_metadata", True),
            semantic_search=context.get("semantic_search", True),
            filters=context.get("filters", {}),
        )

    def _build_knowledge_success_response(
        self, result: KnowledgeResponse, start_time: float, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        """Build success response from knowledge search result."""
        execution_time = time.time() - start_time

        return {
            "response": result.answer,
            "knowledge_data": result.dict(),
            "execution_time": execution_time,
            "metadata": {
                "agent": "knowledge_agent",
                "model": self.model,
                "sources_found": len(result.sources),
                "confidence_score": result.confidence_score,
                **metadata,
            },
        }

    def _log_knowledge_completion(
        self, query: str, result: KnowledgeResponse, start_time: float
    ) -> None:
        """Log information about completed knowledge search."""
        execution_time = time.time() - start_time

        logger.info(
            "Knowledge search completed",
            query=query,
            sources=len(result.sources),
            confidence=result.confidence_score,
            execution_time=execution_time,
        )

    def _build_knowledge_error_response(
        self, error: Exception, start_time: float, metadata: dict[str, Any], local_vars: dict[str, Any]
    ) -> dict[str, Any]:
        """Build error response when knowledge execution fails."""
        execution_time = time.time() - start_time
        query_info = self._extract_query_info_for_error(local_vars)

        logger.error(
            "Knowledge execution failed",
            error=str(error),
            query=query_info,
        )

        return {
            "response": f"I apologize, but I encountered an error while searching knowledge: {str(error)}",
            "error": str(error),
            "execution_time": execution_time,
            "metadata": {
                "agent": "knowledge_agent",
                "status": "error",
                **metadata,
            },
        }

    def _extract_query_info_for_error(self, local_vars: dict[str, Any]) -> str:
        """Extract query information for error logging."""
        knowledge_query = local_vars.get("knowledge_query")
        if knowledge_query:
            return knowledge_query[:100]
        return "unknown"

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
                document = self._convert_single_result(item, i)
                if document:
                    sources.append(document)
            except Exception as conv_err:
                logger.warning("Failed to convert search result", error=str(conv_err))
        return sources

    def _convert_single_result(self, item: dict[str, Any], index: int) -> KnowledgeDocument | None:
        """Convert a single raw result item to KnowledgeDocument.

        Args:
            item: Raw result item
            index: Item index for fallback ID

        Returns:
            KnowledgeDocument or None if conversion fails
        """
        if not isinstance(item, dict):
            return None

        metadata = self._extract_metadata(item)
        document_fields = self._extract_document_fields(item, metadata, index)

        return KnowledgeDocument(**document_fields)

    def _extract_metadata(self, item: dict[str, Any]) -> dict[str, Any]:
        """Extract metadata from raw result item.

        Args:
            item: Raw result item

        Returns:
            Extracted metadata dictionary
        """
        metadata = item.get("metadata", {})
        return metadata if isinstance(metadata, dict) else {}

    def _extract_document_fields(self, item: dict[str, Any], metadata: dict[str, Any], index: int) -> dict[str, Any]:
        """Extract and prepare document fields from raw item.

        Args:
            item: Raw result item
            metadata: Extracted metadata
            index: Item index for fallback values

        Returns:
            Dictionary of document fields
        """
        return {
            "id": str(item.get("id", f"doc_{index}")),
            "title": self._extract_title(item, metadata),
            "content": self._extract_content(item),
            "source": self._extract_source(item, metadata),
            "relevance_score": self._extract_relevance_score(item),
            "metadata": metadata,
        }

    def _extract_title(self, item: dict[str, Any], metadata: dict[str, Any]) -> str:
        """Extract title from item or metadata with fallback."""
        return item.get("title") or metadata.get("title") or "Untitled"

    def _extract_content(self, item: dict[str, Any]) -> str:
        """Extract content from item with fallback to text field."""
        return item.get("content") or item.get("text") or ""

    def _extract_source(self, item: dict[str, Any], metadata: dict[str, Any]) -> str:
        """Extract source from item or metadata with fallback."""
        return item.get("source") or metadata.get("source") or "unknown"

    def _extract_relevance_score(self, item: dict[str, Any]) -> float:
        """Extract relevance score from item with fallback."""
        if not isinstance(item, dict):
            return 0.0

        score_value = item.get("score", item.get("relevance", 0.0))
        try:
            return float(score_value)
        except (ValueError, TypeError):
            return 0.0

    async def _generate_answer_with_rag(
        self, query: KnowledgeQuery, sources: list[KnowledgeDocument]
    ) -> str:
        """Generate answer using RAG with GPT-5."""
        # Handle no sources case early
        if not sources:
            return self._create_no_sources_response(query.query)

        # Prepare RAG components
        current_time = self._get_current_time()
        context_data = self._prepare_rag_context(sources, query.query, current_time)

        # Generate answer using available providers
        return await self._generate_rag_answer(context_data, sources)

    def _create_no_sources_response(self, query: str) -> str:
        """Create response when no sources are found."""
        return (
            "I couldn't find sufficiently relevant documents for your query in the connected knowledge base. "
            f"Query: '{query}'. If you'd like, I can expand the search or suggest refined keywords."
        )

    def _get_current_time(self) -> str:
        """Get current time formatted for context."""
        from datetime import datetime
        import pytz

        miami_tz = pytz.timezone('America/New_York')
        return datetime.now(miami_tz).strftime('%A, %B %d, %Y at %I:%M %p %Z')

    def _prepare_rag_context(
        self, sources: list[KnowledgeDocument], query: str, current_time: str
    ) -> dict[str, str]:
        """Prepare all RAG context components."""
        delimited_sources = self._format_sources_block(sources)
        footnotes = self._format_source_footnotes(sources)

        return {
            "system_msg": self._build_system_prompt(),
            "user_msg": self._build_knowledge_prompt(
                query=query,
                current_time=current_time,
                sources_block=delimited_sources,
                footnotes=footnotes,
            ),
        }

    async def _generate_rag_answer(
        self, context_data: dict[str, str], sources: list[KnowledgeDocument]
    ) -> str:
        """Generate RAG answer using available providers."""
        try:
            # Try OpenAI first
            return await self._try_openai_rag(context_data)
        except Exception as e:
            logger.error("RAG answer generation failed", error=str(e))
            # Fall back to alternative methods
            return await self._try_fallback_rag(context_data, sources)

    async def _try_openai_rag(self, context_data: dict[str, str]) -> str:
        """Try generating RAG answer using OpenAI."""
        if not self.knowledge_llm:
            raise Exception("OpenAI client not available")

        messages = [
            SystemMessage(content=context_data["system_msg"]),
            HumanMessage(content=context_data["user_msg"]),
        ]
        response = await self.knowledge_llm.ainvoke(messages)
        return response.content.strip()

    async def _try_fallback_rag(
        self, context_data: dict[str, str], sources: list[KnowledgeDocument]
    ) -> str:
        """Try fallback provider or create summary when primary fails."""
        if self.fallback_provider:
            try:
                fallback_response = await self.fallback_provider.generate_response(
                    user_input=context_data["user_msg"],
                    context={"type": "knowledge_rag", "sources_count": len(sources)}
                )
                logger.info("Used fallback provider for RAG generation")
                return fallback_response
            except Exception as fallback_error:
                logger.error("Fallback provider also failed", error=str(fallback_error))

        # Create basic summary as last resort
        return self._create_fallback_summary(sources, context_data)

    def _create_fallback_summary(
        self, sources: list[KnowledgeDocument], context_data: dict[str, str]
    ) -> str:
        """Create a basic summary when all providers fail."""
        # Extract query from user message context
        query_match = context_data["user_msg"].split("Query: \"")[1].split("\"")[0] if "Query: \"" in context_data["user_msg"] else "unknown query"

        summary_parts = [
            f"Query: {query_match}",
            "Key source excerpts:",
            "\n".join([f"- {s.title}: {s.content[:240]}" for s in sources[:3]]),
        ]

        # Add footnotes if available in context
        if "## Footnotes" in context_data["user_msg"]:
            footnotes_section = context_data["user_msg"].split("## Footnotes\n")[1]
            summary_parts.append(footnotes_section)

        return "\n\n".join(summary_parts)[:1500]

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
