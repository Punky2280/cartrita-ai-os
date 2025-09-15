"""Sentry configuration and initialization for Cartrita AI OS."""

import logging
import os
from typing import Dict, Any, Optional

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from pydantic import SecretStr

logger = logging.getLogger(__name__)

def init_sentry(
    dsn: Optional[SecretStr] = None,
    environment: str = "production",
    traces_sample_rate: float = 1.0,
    debug: bool = False
) -> None:
    """Initialize Sentry with comprehensive integrations for AI OS monitoring."""

    if not dsn or not dsn.get_secret_value():
        logger.info("Sentry DSN not provided, skipping Sentry initialization")
        return

    # Configure integrations for comprehensive monitoring
    integrations = [
        FastApiIntegration(auto_enabling_integrations=True),
        SqlalchemyIntegration(),
        LoggingIntegration(
            level=logging.INFO,        # Capture info and above as breadcrumbs
            event_level=logging.ERROR  # Send errors as events
        ),
        AsyncioIntegration(),
    ]

    # Custom tags and context for AI OS
    def before_send(event, hint):
        """Custom event processing for AI OS specific context."""
        # Add AI OS specific tags
        event.setdefault('tags', {}).update({
            'component': 'ai-orchestrator',
            'system': 'cartrita-ai-os',
        })

        # Add user context if available
        if 'user' in event.get('contexts', {}):
            event['user'].setdefault('segment', 'ai-user')

        return event

    try:
        sentry_sdk.init(
            dsn=dsn.get_secret_value(),
            integrations=integrations,
            traces_sample_rate=traces_sample_rate,
            environment=environment,
            debug=debug,
            before_send=before_send,
            # Enable performance monitoring
            profiles_sample_rate=1.0 if environment == "development" else 0.1,
            # Custom release information
            release=os.getenv("CARTRITA_VERSION", "unknown"),
            # Server name for better organization
            server_name=os.getenv("HOSTNAME", "cartrita-ai-os"),
        )

        # Set custom context
        sentry_sdk.set_context("ai_system", {
            "orchestrator_version": "2.0.0",
            "multi_agent": True,
            "voice_enabled": True,
            "neural_architecture": True
        })

        logger.info(f"Sentry initialized successfully for environment: {environment}")

    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
        # Don't raise - we don't want Sentry issues to crash the app


def capture_ai_error(
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    level: str = "error",
    tags: Optional[Dict[str, str]] = None
) -> Optional[str]:
    """Capture AI-specific errors with enhanced context."""

    with sentry_sdk.configure_scope() as scope:
        # Add AI-specific context
        if context:
            scope.set_context("ai_context", context)

        # Add custom tags
        if tags:
            for key, value in tags.items():
                scope.set_tag(key, value)

        # Set appropriate level
        scope.set_level(level)

        # Capture the exception
        return sentry_sdk.capture_exception(error)


def capture_agent_performance(
    agent_type: str,
    operation: str,
    duration_ms: float,
    success: bool = True,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Capture agent performance metrics."""

    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("agent_type", agent_type)
        scope.set_tag("operation", operation)
        scope.set_tag("success", str(success))

        # Create custom transaction for performance monitoring
        with sentry_sdk.start_transaction(
            op="ai.agent.operation",
            name=f"{agent_type}.{operation}"
        ) as transaction:
            transaction.set_data("duration_ms", duration_ms)
            transaction.set_data("agent_metadata", metadata or {})

            # Record custom metric
            sentry_sdk.metrics.incr(
                key="ai.agent.operations",
                value=1,
                tags={
                    "agent_type": agent_type,
                    "operation": operation,
                    "success": str(success)
                }
            )

            sentry_sdk.metrics.timing(
                key="ai.agent.duration",
                value=duration_ms,
                tags={
                    "agent_type": agent_type,
                    "operation": operation
                }
            )


def capture_conversation_metrics(
    conversation_id: str,
    message_count: int,
    tokens_used: int,
    agents_involved: list[str],
    duration_seconds: float
) -> None:
    """Capture conversation-level metrics."""

    with sentry_sdk.configure_scope() as scope:
        scope.set_tag("conversation_id", conversation_id)
        scope.set_context("conversation", {
            "message_count": message_count,
            "tokens_used": tokens_used,
            "agents_involved": agents_involved,
            "duration_seconds": duration_seconds
        })

        # Record metrics
        sentry_sdk.metrics.incr("ai.conversations.completed", 1)
        sentry_sdk.metrics.timing("ai.conversation.duration", duration_seconds * 1000)
        sentry_sdk.metrics.incr("ai.tokens.used", tokens_used)


def add_breadcrumb_ai_event(
    event_type: str,
    message: str,
    category: str = "ai",
    level: str = "info",
    data: Optional[Dict[str, Any]] = None
) -> None:
    """Add AI-specific breadcrumb for debugging."""

    sentry_sdk.add_breadcrumb(
        message=message,
        category=category,
        level=level,
        type=event_type,
        data=data or {}
    )


# Decorator for automatic error tracking
def track_ai_errors(
    component: str,
    operation: str = None
):
    """Decorator to automatically track AI component errors."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                with sentry_sdk.start_transaction(
                    op=f"ai.{component}",
                    name=operation or func.__name__
                ):
                    return func(*args, **kwargs)
            except Exception as e:
                capture_ai_error(
                    error=e,
                    context={
                        "component": component,
                        "operation": operation or func.__name__,
                        "args": str(args)[:500],  # Limit args size
                        "kwargs": str(kwargs)[:500]
                    },
                    tags={
                        "component": component,
                        "function": func.__name__
                    }
                )
                raise
        return wrapper
    return decorator