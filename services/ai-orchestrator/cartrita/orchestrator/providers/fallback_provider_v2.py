"""
Lightweight production fallback provider (v2).

This module adapts the existing v1 provider to the simplified async API
expected by the orchestrator and agents:

- Prefer get_fallback_provider() from this module
- provider.generate_response(message, conversation_id, context) -> str
- provider.get_capabilities_info() -> dict

The adapter ensures compatibility without duplicating logic.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

# Reuse the mature v1 provider implementation
from .fallback_provider import (  # type: ignore
    FallbackProvider as V1FallbackProvider,
    get_fallback_provider as get_v1_fallback_provider,
)


logger = logging.getLogger(__name__)


class FallbackProviderV2:
    """Async adapter over the v1 fallback provider, returning plain strings."""

    def __init__(self, v1_provider: V1FallbackProvider) -> None:
        self._v1 = v1_provider

    async def generate_response(
        self,
        message: str,
        conversation_id: Optional[str] = None,  # kept for API compatibility
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate a response as a plain string.

        Parameters:
        - message: user input
        - conversation_id: optional identifier (not used by v1 but accepted)
        - context: optional metadata forwarded to v1
        """
        try:
            # v1 returns a dict with {"response": str, "metadata": {...}}
            result = await self._v1.generate_response(user_input=message, context=context or {})
            if isinstance(result, dict):
                response = result.get("response")
                if isinstance(response, str) and response:
                    return response
                # Fall back to a stringified representation if structure differs
                return str(result)
            # In case v1 ever returns a raw string
            if isinstance(result, str):
                return result
            return "I'm here to help. Could you rephrase your request?"
        except Exception as e:  # pragma: no cover - defensive guard
            logger.error("FallbackProviderV2 error", extra={"error": str(e)})
            return "I'm operating in a limited mode right now but can still help. What would you like to do?"

    def get_capabilities_info(self) -> Dict[str, Any]:
        if hasattr(self._v1, "get_capabilities_info"):
            return self._v1.get_capabilities_info()
        return {"rule_based_available": True}


_fallback_provider_v2: Optional[FallbackProviderV2] = None


def get_fallback_provider() -> FallbackProviderV2:
    """Return a singleton instance of the v2 fallback provider adapter."""
    global _fallback_provider_v2
    if _fallback_provider_v2 is None:
        _fallback_provider_v2 = FallbackProviderV2(get_v1_fallback_provider())
    return _fallback_provider_v2

