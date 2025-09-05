# Cartrita AI OS - HuggingFace Service
# HuggingFace integration for research and documentation

"""
HuggingFace service for Cartrita AI OS.
Handles HuggingFace Hub interactions, model management, and documentation search.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional

import structlog
from huggingface_hub import HfApi, HfFolder
from huggingface_hub.utils import HfHubHTTPError

from cartrita.orchestrator.utils.config import settings

logger = structlog.get_logger(__name__)


class HuggingFaceService:
    """HuggingFace service for model and documentation management."""

    def __init__(self):
        """Initialize HuggingFace service."""
        self.api_key = settings.ai.huggingface_api_key.get_secret_value()
        self.api = HfApi(token=self.api_key)
        self.hf_folder = HfFolder()

        # Set token for authentication
        if self.api_key:
            self.hf_folder.save_token(self.api_key)

        logger.info("HuggingFace service initialized")

    async def search_models(
        self,
        query: str,
        task: Optional[str] = None,
        author: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for models on HuggingFace Hub.

        Args:
            query: Search query
            task: Model task filter
            author: Author/organization filter
            limit: Maximum results to return

        Returns:
            List of model information
        """
        try:
            filters = []
            if task:
                filters.append(f"task:{task}")
            if author:
                filters.append(f"author:{author}")

            models = self.api.list_models(
                search=query,
                filter=filters,
                limit=limit,
                sort="downloads",
                direction=-1
            )

            results = []
            for model in models:
                results.append({
                    "id": model.id,
                    "author": model.author,
                    "name": model.modelId.split("/")[-1],
                    "task": getattr(model, "pipeline_tag", None),
                    "downloads": getattr(model, "downloads", 0),
                    "likes": getattr(model, "likes", 0),
                    "tags": getattr(model, "tags", []),
                    "url": f"https://huggingface.co/{model.id}",
                    "last_modified": getattr(model, "lastModified", None)
                })

            logger.info("Model search completed", query=query, results_count=len(results))
            return results

        except Exception as e:
            logger.error("Model search failed", error=str(e))
            raise

    async def search_datasets(
        self,
        query: str,
        author: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for datasets on HuggingFace Hub.

        Args:
            query: Search query
            author: Author/organization filter
            limit: Maximum results to return

        Returns:
            List of dataset information
        """
        try:
            filters = []
            if author:
                filters.append(f"author:{author}")

            datasets = self.api.list_datasets(
                search=query,
                filter=filters,
                limit=limit,
                sort="downloads",
                direction=-1
            )

            results = []
            for dataset in datasets:
                results.append({
                    "id": dataset.id,
                    "author": dataset.author,
                    "name": dataset.id.split("/")[-1],
                    "downloads": getattr(dataset, "downloads", 0),
                    "likes": getattr(dataset, "likes", 0),
                    "tags": getattr(dataset, "tags", []),
                    "url": f"https://huggingface.co/datasets/{dataset.id}",
                    "description": getattr(dataset, "description", "")
                })

            logger.info("Dataset search completed", query=query, results_count=len(results))
            return results

        except Exception as e:
            logger.error("Dataset search failed", error=str(e))
            raise

    async def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific model.

        Args:
            model_id: HuggingFace model ID

        Returns:
            Model information
        """
        try:
            model_info = self.api.model_info(model_id)

            return {
                "id": model_info.id,
                "author": model_info.author,
                "name": model_info.modelId.split("/")[-1],
                "task": getattr(model_info, "pipeline_tag", None),
                "downloads": getattr(model_info, "downloads", 0),
                "likes": getattr(model_info, "likes", 0),
                "tags": getattr(model_info, "tags", []),
                "url": f"https://huggingface.co/{model_info.id}",
                "description": getattr(model_info, "description", ""),
                "card_data": getattr(model_info, "cardData", {}),
                "last_modified": getattr(model_info, "lastModified", None),
                "siblings": [
                    {
                        "filename": sibling.rfilename,
                        "size": getattr(sibling, "size", 0)
                    }
                    for sibling in getattr(model_info, "siblings", [])
                ]
            }

        except Exception as e:
            logger.error("Failed to get model info", model_id=model_id, error=str(e))
            raise

    async def search_papers(
        self,
        query: str,
        limit: int = 12
    ) -> List[Dict[str, Any]]:
        """
        Search for research papers on HuggingFace.

        Args:
            query: Search query
            limit: Maximum results to return

        Returns:
            List of paper information
        """
        try:
            papers = self.api.list_papers(
                query=query,
                limit=limit
            )

            results = []
            for paper in papers:
                results.append({
                    "id": paper.paperId,
                    "title": paper.title,
                    "authors": paper.authors,
                    "abstract": paper.abstract,
                    "url": f"https://huggingface.co/papers/{paper.paperId}",
                    "published": getattr(paper, "publishedAt", None),
                    "likes": getattr(paper, "upvotes", 0)
                })

            logger.info("Paper search completed", query=query, results_count=len(results))
            return results

        except Exception as e:
            logger.error("Paper search failed", error=str(e))
            raise

    async def get_space_info(self, space_id: str) -> Dict[str, Any]:
        """
        Get information about a HuggingFace Space.

        Args:
            space_id: Space ID

        Returns:
            Space information
        """
        try:
            space_info = self.api.space_info(space_id)

            return {
                "id": space_info.id,
                "author": space_info.author,
                "name": space_info.id.split("/")[-1],
                "url": f"https://huggingface.co/spaces/{space_info.id}",
                "description": getattr(space_info, "description", ""),
                "tags": getattr(space_info, "tags", []),
                "likes": getattr(space_info, "likes", 0),
                "last_modified": getattr(space_info, "lastModified", None),
                "private": getattr(space_info, "private", False)
            }

        except Exception as e:
            logger.error("Failed to get space info", space_id=space_id, error=str(e))
            raise

    async def health_check(self) -> Dict[str, Any]:
        """Check HuggingFace service health."""
        try:
            # Test API connectivity
            self.api.whoami()
            return {
                "status": "healthy",
                "api_available": True
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "api_available": False
            }
