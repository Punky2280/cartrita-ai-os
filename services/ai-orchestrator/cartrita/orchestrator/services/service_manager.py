# Cartrita AI OS - Service Manager
# Service initialization and management

"""
Service manager for Cartrita AI OS.
Handles initialization and lifecycle management of all provider services.
"""

from typing import Any, Dict

import structlog

from cartrita.orchestrator.services import (
    DeepgramService,
    GitHubService,
    HuggingFaceService,
    OpenAIService,
    TavilyService,
)
from cartrita.orchestrator.utils.config import settings

logger = structlog.get_logger(__name__)


class ServiceManager:
    """Manager for all provider services."""

    def __init__(self):
        """Initialize service manager."""
        self.services: Dict[str, Any] = {}
        self.initialized = False

        logger.info("Service manager initialized")

    async def initialize_services(self) -> None:
        """Initialize all configured services."""
        if self.initialized:
            logger.warning("Services already initialized")
            return

        try:
            logger.info("Initializing provider services")

            # Initialize OpenAI service
            if settings.ai.openai_api_key.get_secret_value():
                self.services["openai"] = OpenAIService()
                logger.info("OpenAI service initialized")

            # Initialize HuggingFace service
            if settings.ai.huggingface_api_key.get_secret_value():
                self.services["huggingface"] = HuggingFaceService()
                logger.info("HuggingFace service initialized")

            # Initialize Deepgram service
            if settings.ai.deepgram_api_key.get_secret_value():
                self.services["deepgram"] = DeepgramService()
                logger.info("Deepgram service initialized")

            # Initialize Tavily service
            if settings.ai.tavily_api_key.get_secret_value():
                self.services["tavily"] = TavilyService()
                logger.info("Tavily service initialized")

            # Initialize GitHub service
            if settings.ai.github_api_key.get_secret_value():
                self.services["github"] = GitHubService()
                logger.info("GitHub service initialized")

            self.initialized = True
            logger.info("All services initialized", service_count=len(self.services))

        except Exception as e:
            logger.error("Failed to initialize services", error=str(e))
            raise

    async def get_service(self, service_name: str) -> Any:
        """
        Get a service instance by name.

        Args:
            service_name: Name of the service

        Returns:
            Service instance

        Raises:
            ValueError: If service is not found
        """
        if not self.initialized:
            await self.initialize_services()

        if service_name not in self.services:
            available_services = list(self.services.keys())
            raise ValueError(
                f"Service '{service_name}' not found. Available services: {available_services}"
            )

        return self.services[service_name]

    async def health_check_all(self) -> Dict[str, Any]:
        """
        Perform health check on all services.

        Returns:
            Health status for all services
        """
        if not self.initialized:
            await self.initialize_services()

        health_results = {}
        healthy_count = 0

        for service_name, service in self.services.items():
            try:
                if hasattr(service, "health_check"):
                    health_result = await service.health_check()
                    health_results[service_name] = health_result
                    if health_result.get("status") == "healthy":
                        healthy_count += 1
                else:
                    health_results[service_name] = {
                        "status": "unknown",
                        "error": "No health check method",
                    }
            except Exception as e:
                health_results[service_name] = {"status": "error", "error": str(e)}

        return {
            "overall_status": (
                "healthy" if healthy_count == len(self.services) else "degraded"
            ),
            "total_services": len(self.services),
            "healthy_services": healthy_count,
            "service_health": health_results,
        }

    async def shutdown_services(self) -> None:
        """Shutdown all services gracefully."""
        logger.info("Shutting down services")

        for service_name, service in self.services.items():
            try:
                if hasattr(service, "shutdown"):
                    await service.shutdown()
                logger.info("Service shut down", service=service_name)
            except Exception as e:
                logger.error(
                    "Error shutting down service", service=service_name, error=str(e)
                )

        self.services.clear()
        self.initialized = False
        logger.info("All services shut down")

    def list_services(self) -> Dict[str, str]:
        """
        List all available services with their types.

        Returns:
            Dictionary mapping service names to their class names
        """
        return {name: type(service).__name__ for name, service in self.services.items()}


# Global service manager instance
service_manager = ServiceManager()


async def get_service_manager() -> ServiceManager:
    """Get the global service manager instance."""
    if not service_manager.initialized:
        await service_manager.initialize_services()
    return service_manager


async def get_openai_service() -> OpenAIService:
    """Get OpenAI service instance."""
    return await service_manager.get_service("openai")


async def get_huggingface_service() -> HuggingFaceService:
    """Get HuggingFace service instance."""
    return await service_manager.get_service("huggingface")


async def get_deepgram_service() -> DeepgramService:
    """Get Deepgram service instance."""
    return await service_manager.get_service("deepgram")


async def get_tavily_service() -> TavilyService:
    """Get Tavily service instance."""
    return await service_manager.get_service("tavily")


async def get_github_service() -> GitHubService:
    """Get GitHub service instance."""
    return await service_manager.get_service("github")
