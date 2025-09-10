# Cartrita AI OS - Tavily Service
# Tavily integration for web search and research

"""
Tavily service for Cartrita AI OS.
Handles web search, content extraction, and research capabilities.
"""

from typing import Any, Dict, List, Optional

import structlog
from tavily import TavilyClient

from cartrita.orchestrator.utils.config import settings

logger = structlog.get_logger(__name__)


class TavilyService:
    """Tavily service for web search and research."""

    def __init__(self):
        """Initialize Tavily service."""
        self.api_key = settings.ai.tavily_api_key.get_secret_value()
        self.client = TavilyClient(api_key=self.api_key)
        self.max_results = 10
        self.include_images = False
        self.include_answer = True
        self.include_raw_content = False

        logger.info("Tavily service initialized")

    async def search(
        self,
        query: str,
        search_depth: str = "advanced",
        include_answer: Optional[bool] = None,
        include_images: Optional[bool] = None,
        max_results: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform web search using Tavily.

        Args:
            query: Search query
            search_depth: Search depth ("basic" or "advanced")
            include_answer: Whether to include AI-generated answer
            include_images: Whether to include images
            max_results: Maximum number of results
            **kwargs: Additional search parameters

        Returns:
            Search results
        """
        try:
            # Prepare search parameters
            search_params = {
                "query": query,
                "search_depth": search_depth,
                "include_answer": include_answer if include_answer is not None else self.include_answer,
                "include_images": include_images if include_images is not None else self.include_images,
                "max_results": max_results or self.max_results,
                **kwargs
            }

            logger.info("Performing web search", query=query, search_depth=search_depth)

            # Execute search
            response = self.client.search(**search_params)

            # Process results
            results = {
                "query": query,
                "answer": response.get("answer", ""),
                "results": [],
                "images": response.get("images", []),
                "query_time": response.get("response_time", 0)
            }

            # Process individual results
            for result in response.get("results", []):
                processed_result = {
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", ""),
                    "score": result.get("score", 0),
                    "published_date": result.get("published_date"),
                    "author": result.get("author"),
                    "source": self._extract_domain(result.get("url", ""))
                }
                results["results"].append(processed_result)

            logger.info(
                "Search completed",
                query=query,
                results_count=len(results["results"]),
                has_answer=bool(results["answer"])
            )

            return results

        except Exception as e:
            logger.error("Web search failed", query=query, error=str(e))
            return {
                "query": query,
                "error": str(e),
                "results": [],
                "answer": ""
            }

    async def extract_content(
        self,
        urls: List[str],
        include_images: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract content from specific URLs.

        Args:
            urls: List of URLs to extract content from
            include_images: Whether to include images

        Returns:
            Extracted content for each URL
        """
        try:
            logger.info("Extracting content from URLs", url_count=len(urls))

            results = []
            for url in urls:
                try:
                    response = self.client.extract(
                        url=url,
                        include_images=include_images if include_images is not None else self.include_images
                    )

                    extracted = {
                        "url": url,
                        "content": response.get("content", ""),
                        "images": response.get("images", []),
                        "title": response.get("title", ""),
                        "author": response.get("author"),
                        "published_date": response.get("published_date"),
                        "domain": self._extract_domain(url),
                        "success": True
                    }

                    results.append(extracted)

                except Exception as e:
                    logger.warning("Failed to extract content from URL", url=url, error=str(e))
                    results.append({
                        "url": url,
                        "error": str(e),
                        "success": False
                    })

            logger.info("Content extraction completed", success_count=sum(1 for r in results if r.get("success")))
            return results

        except Exception as e:
            logger.error("Content extraction failed", error=str(e))
            return [{"error": str(e), "success": False}]

    async def search_and_extract(
        self,
        query: str,
        max_results: int = 5,
        extract_content: bool = True
    ) -> Dict[str, Any]:
        """
        Search and optionally extract content from top results.

        Args:
            query: Search query
            max_results: Maximum number of results to process
            extract_content: Whether to extract full content

        Returns:
            Combined search and extraction results
        """
        try:
            # First perform search
            search_results = await self.search(query, max_results=max_results)

            if not extract_content or not search_results.get("results"):
                return search_results

            # Extract content from top results
            urls = [result["url"] for result in search_results["results"][:max_results]]
            extracted_content = await self.extract_content(urls)

            # Combine results
            combined_results = []
            for i, result in enumerate(search_results["results"][:max_results]):
                combined = {
                    **result,
                    "extracted_content": extracted_content[i].get("content", "") if i < len(extracted_content) else "",
                    "extraction_success": extracted_content[i].get("success", False) if i < len(extracted_content) else False
                }
                combined_results.append(combined)

            search_results["results"] = combined_results

            logger.info(
                "Search and extract completed",
                query=query,
                results_count=len(combined_results),
                extraction_success_count=sum(1 for r in combined_results if r.get("extraction_success"))
            )

            return search_results

        except Exception as e:
            logger.error("Search and extract failed", query=query, error=str(e))
            return {
                "query": query,
                "error": str(e),
                "results": []
            }

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except Exception:
            return ""

    async def get_search_suggestions(self, query: str) -> List[str]:
        """
        Get search suggestions based on query.

        Args:
            query: Partial search query

        Returns:
            List of suggested search queries
        """
        try:
            # This would use Tavily's suggestion API if available
            # For now, return basic suggestions
            suggestions = [
                f"{query} tutorial",
                f"{query} documentation",
                f"{query} examples",
                f"{query} best practices",
                f"{query} vs alternatives"
            ]

            return suggestions

        except Exception as e:
            logger.error("Failed to get search suggestions", query=query, error=str(e))
            return []

    async def health_check(self) -> Dict[str, Any]:
        """Check Tavily service health."""
        try:
            # Test API connectivity with a simple search
            response = self.client.search(query="test", max_results=1)
            return {
                "status": "healthy",
                "response_time": response.get("response_time", 0),
                "results_available": len(response.get("results", [])) > 0
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
