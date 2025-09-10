# Cartrita AI OS - Main FastAPI Application
# GPT-4.1 Orchestrator with Hierarchical Multi-Agent System

"""
Main FastAPI application for Cartrita AI OS.
Implements GPT-4.1 orchestrator with hierarchical multi-agent architecture.
"""

import asyncio
import json
import os
import structlog
import time
import uvicorn
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional
from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
# Load environment variables from .env file
from dotenv import load_dotenv

# Import core components
from cartrita.orchestrator.core.supervisor import SupervisorOrchestrator

# Load environment variables from current directory or /app/.env (for Docker)
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
if not os.path.exists(env_path):
    env_path = '/app/.env'
load_dotenv(env_path)

try:
    # Import core services with fallbacks
    from cartrita.orchestrator.core.database import (  # type: ignore
        DatabaseManager,
    )
except ImportError:
    DatabaseManager = None

try:
    from cartrita.orchestrator.core.cache import CacheManager  # type: ignore
except ImportError:
    CacheManager = None

try:
    from cartrita.orchestrator.core.metrics import (  # type: ignore
        MetricsCollector,
    )
except ImportError:
    MetricsCollector = None

try:
    from cartrita.orchestrator.providers.fallback_provider import (  # type: ignore
        get_fallback_provider,
        generate_fallback_response,
    )
    FALLBACK_PROVIDER_AVAILABLE = True
except ImportError:
    get_fallback_provider = None
    generate_fallback_response = None
    FALLBACK_PROVIDER_AVAILABLE = False
    structlog.get_logger(__name__).warning("Fallback provider not available - install transformers and langchain for enhanced fallback capabilities")

# Import agents with fallbacks
try:
    from cartrita.orchestrator.agents.research_agent import (  # type: ignore
        ResearchAgent,
    )
except ImportError:
    ResearchAgent = None

try:
    from cartrita.orchestrator.agents.code_agent import (  # type: ignore
        CodeAgent,
    )
except ImportError:
    CodeAgent = None

try:
    from cartrita.orchestrator.agents.computer_use_agent import (  # type: ignore
        ComputerUseAgent,
    )
except ImportError:
    ComputerUseAgent = None

try:
    from cartrita.orchestrator.agents.knowledge_agent import (  # type: ignore
        KnowledgeAgent,
    )
except ImportError:
    KnowledgeAgent = None

try:
    from cartrita.orchestrator.agents.task_agent import (  # type: ignore
        TaskAgent,
    )
except ImportError:
    TaskAgent = None

# Import models with fallbacks
try:
    from cartrita.orchestrator.models.schemas import (  # type: ignore
        AgentStatusResponse,
        ChatRequest,
        ChatResponse,
        HealthResponse,
        Message,
        MessageRole,
    )
except ImportError:
    # Provide minimal fallbacks to avoid type annotation errors and keep endpoints functional
    from enum import Enum

    class MessageRole(str, Enum):
        USER = "user"
        ASSISTANT = "assistant"
        SYSTEM = "system"

    class Message(BaseModel):
        role: MessageRole
        content: str

    class ChatRequest(BaseModel):
        message: str
        context: Optional[Dict[str, Any]] = None
        agent_override: Optional[str] = None
        stream: bool = False

    class ChatResponse(BaseModel):
        # Fields used across endpoints; additional fields allowed via optionals
        response: str
        conversation_id: str
        agent_used: Optional[str] = None
        agent_type: Optional[str] = None
        timestamp: Optional[int] = None
        messages: Optional[List[Message]] = None
        context: Optional[Dict[str, Any]] = None
        task_result: Optional[Any] = None
        metadata: Optional[Dict[str, Any]] = None
        processing_time: Optional[float] = None
        token_usage: Optional[Dict[str, Any]] = None

    class AgentStatusResponse(BaseModel):
        # Keep flexible to match supervisor payloads
        # Add fields as needed by your implementation
        pass

    class HealthResponse(BaseModel):
        status: str
        version: str
        services: Dict[str, str]
        timestamp: float


# Voice Chat Request Model
class VoiceChatRequest(BaseModel):
    """Request model for voice conversations."""
    conversationId: str = Field(..., description="Unique conversation identifier")
    transcribedText: str = Field(..., description="Text transcribed from user's speech")
    conversationHistory: Optional[List[Dict[str, Any]]] = Field(
        None, description="Previous conversation messages for context"
    )
    voiceMode: bool = Field(True, description="Whether this is a voice conversation")


# ============================================
# Lifespan Management
# ============================================

# Import services with fallbacks
try:
    from cartrita.orchestrator.services.auth import (  # type: ignore
        verify_api_key,
    )
except ImportError:
    # Fallback auth function
    async def verify_api_key(api_key: Optional[str] = None) -> str:
        """Fallback API key verification."""
        if not api_key:
            expected_key = os.getenv("CARTRITA_API_KEY", "dev-api-key-2025")
            if api_key != expected_key:
                raise HTTPException(status_code=403, detail="Invalid API key")
        return api_key or "dev-api-key-2025"

try:
    from cartrita.orchestrator.utils.config import Settings  # type: ignore
except ImportError:
    Settings = None
try:
    from cartrita.orchestrator.utils.logger import (  # type: ignore
        setup_logging,
    )
except ImportError:
    setup_logging = None

# Configure structured logging
setup_logging()
logger = structlog.get_logger(__name__)

# Global instances
supervisor = None
db_manager = None
cache_manager = None
metrics_collector = None

# Specialized agents
research_agent = None
code_agent = None
computer_use_agent = None
knowledge_agent = None
task_agent = None

# ============================================
# Lifespan Management
# ============================================


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan manager with proper resource cleanup."""
    global supervisor, db_manager, cache_manager, metrics_collector
    global research_agent, code_agent, computer_use_agent
    global knowledge_agent, task_agent

    logger.info("🚀 Starting Cartrita AI Orchestrator...")

    try:
        # Initialize core components
        settings = Settings()

        # Initialize database
        db_manager = DatabaseManager(settings)
        await db_manager.connect()

        # Initialize cache
        cache_manager = CacheManager(settings.redis.url)
        await cache_manager.connect()

        # Initialize metrics collector
        from cartrita.orchestrator.core.metrics import MetricsCollector, MetricsConfig
        metrics_config = MetricsConfig(
            service_name="cartrita-ai-orchestrator",
            enable_prometheus=True,
            enable_tracing=True,
            enable_metrics=True
        )
        metrics_collector = MetricsCollector(metrics_config)
        await metrics_collector.initialize()

        # Initialize specialized agents
        # research_agent = ResearchAgent()
        # await research_agent.start()

        # code_agent = CodeAgent()
        # await code_agent.start()

        # computer_use_agent = ComputerUseAgent()
        # await computer_use_agent.start()

        # knowledge_agent = KnowledgeAgent()
        # await knowledge_agent.start()

        # task_agent = TaskAgent()
        # await task_agent.start()

        # Initialize GPT-4.1 Supervisor Orchestrator
        supervisor = SupervisorOrchestrator(
            db_manager=db_manager,
            cache_manager=cache_manager,
            metrics_collector=metrics_collector,
            settings=settings,
        )

        # Start background tasks
        await supervisor.start()

        logger.info("✅ Cartrita AI Orchestrator started successfully")

        yield

    except Exception as e:
        logger.error("❌ Failed to start Cartrita AI Orchestrator", error=str(e))
        raise

    finally:
        logger.info("🛑 Shutting down Cartrita AI Orchestrator...")

        # Graceful shutdown
        if supervisor:
            await supervisor.stop()

        # Stop specialized agents
        agents_to_stop = [
            research_agent,
            code_agent,
            computer_use_agent,
            knowledge_agent,
            task_agent,
        ]

        for agent in agents_to_stop:
            if agent:
                try:
                    await agent.stop()
                except Exception as exc:
                    logger.error(
                        f"Error stopping agent {agent.__class__.__name__}",
                        error=str(exc),
                    )

        if db_manager:
            await db_manager.disconnect()

        if cache_manager:
            await cache_manager.disconnect()

        if metrics_collector:
            await metrics_collector.shutdown()

        logger.info("✅ Cartrita AI Orchestrator shutdown complete")


# ============================================
# FastAPI Application
# ============================================

app = FastAPI(
    title="Cartrita AI OS - Orchestrator",
    description="Hierarchical Multi-Agent AI OS with GPT-4.1 Orchestration",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ============================================
# Middleware Configuration
# ============================================

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3003",  # For Turbopack dev server
        "https://cartrita-ai-os.com"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Trusted host middleware
# Trusted host middleware - restrict to known hosts (configurable)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "localhost",
        "127.0.0.1",
        "cartrita-ai-os.com",
        "*.cartrita-ai-os.com",
    ],
)


# ============================================
# Metrics Middleware
# ============================================

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Middleware to automatically record metrics for all HTTP requests."""
    start_time = time.time()

    try:
        response = await call_next(request)

        # Record successful request metrics
        if metrics_collector and metrics_collector.is_healthy():
            duration = time.time() - start_time
            await metrics_collector.record_request(
                method=request.method,
                endpoint=str(request.url.path),
                status=response.status_code,
                duration=duration
            )

        return response

    except Exception as e:
        # Record error metrics
        if metrics_collector and metrics_collector.is_healthy():
            duration = time.time() - start_time
            status_code = getattr(e, 'status_code', 500)
            await metrics_collector.record_request(
                method=request.method,
                endpoint=str(request.url.path),
                status=status_code,
                duration=duration
            )
            await metrics_collector.record_error(
                error_type=type(e).__name__.lower(),
                endpoint=str(request.url.path)
            )

        raise


# ============================================
# Request/Response Models
# ============================================


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    details: dict[str, Any] | None = Field(None, description="Additional error details")


# ============================================
# Exception Handlers
# ============================================


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured logging."""
    logger.warning(
        "HTTP exception occurred",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
        method=request.method,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            code=f"HTTP_{exc.status_code}",
            details={"path": request.url.path, "method": request.method},
        ).dict(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with error tracking."""
    logger.error(
        "Unhandled exception occurred",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        method=request.method,
        exc_info=True,
    )

    # Report to error tracking service
    if metrics_collector:
        await metrics_collector.record_error(exc, request)

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            code="INTERNAL_ERROR",
            details={"type": type(exc).__name__},
        ).dict(),
    )


# ============================================
# Root Endpoint
# ============================================


@app.get("/")
async def root():
    """Root endpoint providing API information and available endpoints."""
    return {
        "message": "Welcome to Cartrita AI OS - Hierarchical Multi-Agent System",
        "version": "2.0.0",
        "status": "operational",
        "streaming": {
            "primary_transport": "SSE (Server-Sent Events)",
            "fallback_transport": "WebSocket",
            "sse_events": [
                "token", "function_call", "tool_result", "metrics",
                "done", "agent_task_started", "agent_task_progress",
                "agent_task_output", "agent_task_complete", "orchestration_decision",
                "chain_reconfigured", "safety_flag", "evaluation_metric",
                "audio_interim", "audio_final", "file.attach.progress",
                "computer_use.execute.progress"
            ]
        },
        "endpoints": {
            "health": "/health",
            "metrics": "/metrics",
            "chat": "/api/chat",
            "chat_stream": "/api/chat/stream",
            "voice_chat": "/api/chat/voice",
            "voice_chat_stream": "/api/chat/voice/stream",
            "agents": "/api/agents",
            "websocket": "/ws/chat",
            "docs": "/docs",
            "admin": {
                "reload_agents": "/api/admin/reload-agents",
                "stats": "/api/admin/stats"
            }
        },
        "frontend": "http://localhost:3001 (or 3003 with Turbopack)",
        "documentation": "Available at /docs"
    }


# ============================================
# Health & Monitoring Endpoints
# ============================================


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check endpoint."""
    start_time = time.time()

    if not all([supervisor, db_manager, cache_manager]):
        if metrics_collector:
            duration = time.time() - start_time
            await metrics_collector.record_request("GET", "/health", 503, duration)
            await metrics_collector.record_error("service_not_ready", "/health")
        raise HTTPException(status_code=503, detail="Service not ready")

    try:
        # Check database connectivity
        db_healthy = await db_manager.health_check()

        # Check cache connectivity
        cache_healthy = await cache_manager.health_check()

        # Check supervisor status
        supervisor_healthy = await supervisor.health_check()

        # Check fallback provider status
        fallback_healthy = False
        if FALLBACK_PROVIDER_AVAILABLE and get_fallback_provider:
            try:
                provider = get_fallback_provider()
                capabilities = provider.get_capabilities_info()
                # Consider fallback healthy if at least one provider is available
                fallback_healthy = any([
                    capabilities.get("openai_available", False),
                    capabilities.get("huggingface_available", False),
                    capabilities.get("rule_based_available", False),
                    capabilities.get("emergency_template_available", False)
                ])
            except Exception as e:
                logger.warning(f"Fallback provider health check failed: {e}")
                fallback_healthy = False

        # Core services must be healthy, fallback is supplementary
        core_healthy = all([db_healthy, cache_healthy, supervisor_healthy])
        overall_healthy = core_healthy  # Fallback failure doesn't make service unhealthy
        status_code = 200 if overall_healthy else 503

        response = HealthResponse(
            status="healthy" if overall_healthy else "unhealthy",
            version="2.0.0",
            services={
                "database": "healthy" if db_healthy else "unhealthy",
                "cache": "healthy" if cache_healthy else "unhealthy",
                "supervisor": "healthy" if supervisor_healthy else "unhealthy",
                "fallback_provider": "healthy" if fallback_healthy else "degraded",
            },
            timestamp=asyncio.get_event_loop().time(),
        )

        # Record metrics
        if metrics_collector:
            duration = time.time() - start_time
            await metrics_collector.record_request("GET", "/health", status_code, duration)

        if not overall_healthy:
            raise HTTPException(status_code=503, detail="Service unhealthy")

        return response

    except HTTPException:
        raise
    except Exception as e:
        if metrics_collector:
            duration = time.time() - start_time
            await metrics_collector.record_request("GET", "/health", 500, duration)
            await metrics_collector.record_error("health_check_failed", "/health")
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=500, detail="Health check failed") from e


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint with proper error handling."""
    if not metrics_collector:
        logger.warning("Metrics collector not available")
        return JSONResponse(
            status_code=503,
            content={
                "error": "Metrics not available",
                "message": "Metrics collector is not initialized",
                "status": "service_unavailable"
            }
        )

    try:
        # Check if metrics collector is healthy
        if not metrics_collector.is_healthy():
            logger.warning("Metrics collector is not healthy")
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Metrics collector unhealthy",
                    "status": metrics_collector.get_status(),
                    "message": "Metrics collection is currently unavailable"
                }
            )

        # Get metrics data
        metrics_data = await metrics_collector.get_metrics()

        if metrics_data is None:
            # Return basic health metrics as fallback
            return JSONResponse(
                content={
                    "service": "cartrita-ai-orchestrator",
                    "status": "healthy",
                    "message": "Metrics collection is available but no data collected yet",
                    "collector_status": metrics_collector.get_status()
                }
            )

        # Return Prometheus format metrics
        from fastapi.responses import Response
        return Response(
            content=metrics_data,
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )

    except Exception as e:
        logger.error("Failed to retrieve metrics", error=str(e), exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Metrics retrieval failed",
                "message": str(e),
                "status": "internal_error"
            }
        )


# ============================================
# Core AI Endpoints
# ============================================


@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest, api_key: str = Depends(verify_api_key)
):
    """Main chat endpoint with GPT-4.1 orchestration and intelligent fallback."""
    start_time = time.time()

    # Try primary supervisor first
    if supervisor:
        try:
            # Process through GPT-4.1 supervisor
            response = await supervisor.process_chat_request(
                message=request.message,
                context=request.context,
                agent_override=request.agent_override,
                stream=request.stream,
                api_key=api_key,
            )

            # Record successful request metrics
            if metrics_collector:
                duration = time.time() - start_time
                await metrics_collector.record_request(
                    method="POST",
                    endpoint="/api/chat",
                    status=200,
                    duration=duration
                )

            return response

        except Exception as e:
            logger.warning(f"Supervisor failed, trying fallback provider: {str(e)}")
            # Continue to fallback logic below

    # Fallback: Use fallback provider when supervisor is unavailable or fails
    if FALLBACK_PROVIDER_AVAILABLE and generate_fallback_response:
        try:
            logger.info("Using fallback provider for chat response")

            # Generate fallback response
            fallback_result = await generate_fallback_response(
                user_input=request.message,
                context=request.context or {}
            )

            # Create ChatResponse in the expected format
            response = ChatResponse(
                response=fallback_result["response"],
                conversation_id="fallback-" + str(int(time.time())),
                agent_used="fallback",
                timestamp=int(time.time()),
                metadata={
                    **fallback_result["metadata"],
                    "fallback_used": True,
                    "supervisor_available": supervisor is not None
                }
            )

            # Record fallback usage metrics
            if metrics_collector:
                duration = time.time() - start_time
                await metrics_collector.record_request(
                    method="POST",
                    endpoint="/api/chat",
                    status=200,
                    duration=duration
                )
                await metrics_collector.record_error("fallback_used", "/api/chat")

            logger.info(f"Fallback response generated using {fallback_result['metadata']['provider_used']}")
            return response

        except Exception as fallback_error:
            logger.error(f"Fallback provider failed: {str(fallback_error)}")
            # Continue to final error handling

    # Final fallback: Return error if everything fails
    if metrics_collector:
        await metrics_collector.record_error("all_providers_failed", "/api/chat")

    raise HTTPException(
        status_code=503,
        detail="Chat service temporarily unavailable - all providers failed"
    )


@app.post("/api/chat/voice", response_model=ChatResponse)
async def voice_chat(
    request: VoiceChatRequest, api_key: str = Depends(verify_api_key)
):
    """Voice conversation endpoint with Deepgram ASR + OpenAI GPT-4.1 + Deepgram TTS."""
    try:
        # Get OpenAI service instance
        from cartrita.orchestrator.services.openai_service import OpenAIService
        openai_service = OpenAIService()

        logger.info(
            "Processing voice conversation",
            conversation_id=request.conversationId,
            voice_mode=request.voiceMode,
            api_key=api_key[:8] + "..."
        )

        # Process voice conversation
        response_content = ""
        async for chunk in openai_service.process_voice_conversation(
            conversation_id=request.conversationId,
            transcribed_text=request.transcribedText,
            conversation_history=request.conversationHistory
        ):
            if chunk["type"] == "content":
                response_content += chunk["content"]
            elif chunk["type"] == "error":
                raise HTTPException(status_code=500, detail=chunk["error"])

        # Create response
        return ChatResponse(
            response=response_content,
            conversation_id=request.conversationId,
            agent_type="openai-voice",
            messages=[
                Message(
                    role=MessageRole.ASSISTANT,
                    content=response_content
                )
            ],
            context=request.conversationHistory,
            task_result=None,
            metadata={
                "voice_mode": request.voiceMode,
                "transcription_length": len(request.transcribedText)
            },
            processing_time=0.0,  # TODO: Track actual processing time
            token_usage=None
        )

    except Exception as e:
        logger.error(
            "Voice chat request failed",
            error=str(e),
            conversation_id=request.conversationId,
            api_key=api_key[:8] + "..."
        )
        raise HTTPException(status_code=500, detail="Voice chat processing failed") from e


@app.get("/api/agents", response_model=dict)
async def list_agents(
    _api_key: str = Depends(verify_api_key),
):
    """List all available agents and their status."""
    if not supervisor:
        raise HTTPException(status_code=503, detail="Supervisor not available")

    try:
        agents = await supervisor.get_agent_statuses()
        return agents

    except Exception as e:
        logger.error("Failed to list agents", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve agents") from e


@app.get("/api/agents/{agent_id}", response_model=AgentStatusResponse)
async def get_agent_status(
    agent_id: str, _api_key: str = Depends(verify_api_key)
):
    """Get detailed status of a specific agent."""
    if not supervisor:
        raise HTTPException(status_code=503, detail="Supervisor not available")

    try:
        agent_status = await supervisor.get_agent_status(agent_id)
        if not agent_status:
            raise HTTPException(status_code=404, detail="Agent not found")

        return agent_status

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get agent status", error=str(e), agent_id=agent_id)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve agent status"
        ) from e


# ============================================
# WebSocket Endpoints
# ============================================


@app.get("/api/chat/stream")
async def chat_stream(
    message: str,
    context: Optional[str] = None,
    agent_override: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """SSE endpoint for streaming chat responses with intelligent fallback."""

    async def generate():
        try:
            # Parse context if provided
            context_dict = {}
            if context:
                try:
                    context_dict = json.loads(context)
                except json.JSONDecodeError:
                    context_dict = {"raw_context": context}

            response = None

            # Try primary supervisor first
            if supervisor:
                try:
                    response = await supervisor.process_chat_request(
                        message=message,
                        context=context_dict,
                        agent_override=agent_override,
                        stream=False,  # Supervisor doesn't support streaming yet
                        api_key=api_key,
                    )
                except Exception as e:
                    logger.warning(f"Supervisor failed in streaming, trying fallback: {str(e)}")
                    response = None

            # Fallback: Use fallback provider if supervisor fails or unavailable
            if not response and FALLBACK_PROVIDER_AVAILABLE and generate_fallback_response:
                try:
                    logger.info("Using fallback provider for streaming response")

                    fallback_result = await generate_fallback_response(
                        user_input=message,
                        context=context_dict
                    )

                    # Create ChatResponse format for streaming
                    response = ChatResponse(
                        response=fallback_result["response"],
                        conversation_id="fallback-stream-" + str(int(time.time())),
                        agent_used="fallback",
                        timestamp=int(time.time()),
                        metadata={
                            **fallback_result["metadata"],
                            "fallback_used": True,
                            "supervisor_available": supervisor is not None,
                            "streaming": True
                        }
                    )

                except Exception as fallback_error:
                    logger.error(f"Fallback provider failed in streaming: {str(fallback_error)}")
                    yield f"data: {json.dumps({'error': 'All providers failed', 'details': 'Both supervisor and fallback provider are unavailable'})}\n\n"
                    return

            if response:
                # Send response as SSE event (convert Pydantic model to JSON)
                if hasattr(response, 'model_dump_json'):
                    response_json = response.model_dump_json()
                elif hasattr(response, 'json'):
                    response_json = response.json()
                else:
                    response_json = json.dumps(response, default=str)
                yield f"data: {response_json}\n\n"
                yield "data: [DONE]\n\n"
            else:
                yield f"data: {json.dumps({'error': 'No providers available', 'details': 'All chat providers are currently unavailable'})}\n\n"

        except Exception as e:
            logger.error("Streaming chat failed", error=str(e))
            yield f"data: {json.dumps({'error': 'Streaming failed', 'details': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )


@app.get("/api/chat/voice/stream")
async def voice_chat_stream(
    conversationId: str,
    transcribedText: str,
    conversationHistory: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """SSE endpoint for streaming voice conversations."""
    if not supervisor:
        raise HTTPException(status_code=503, detail="Supervisor not available")

    # Parse conversation history if provided
    history = []
    if conversationHistory:
        try:
            history = json.loads(conversationHistory)
        except json.JSONDecodeError:
            history = []

    async def generate():
        try:
            # For now, use regular chat processing (voice processing not fully implemented)
            # TODO: Implement proper voice processing pipeline
            response = await supervisor.process_chat_request(
                message=transcribedText,
                context={
                    "conversation_id": conversationId,
                    "conversation_history": history,
                    "voice_mode": True
                },
                stream=False,
                api_key=api_key,
            )

            # Send response as SSE event with voice-specific metadata
            if hasattr(response, 'model_dump'):
                response_dict = response.model_dump()
            elif hasattr(response, 'dict'):
                response_dict = response.dict()
            else:
                response_dict = response

            event_data = {
                **response_dict,
                "conversationId": conversationId,
                "timestamp": asyncio.get_event_loop().time(),
                "voiceMode": True
            }
            yield f"data: {json.dumps(event_data, default=str)}\n\n"
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error("Streaming voice chat failed", error=str(e))
            yield f"data: {json.dumps({'error': 'Voice streaming failed', 'conversationId': conversationId})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )


# ============================================
# WebSocket Endpoints
# ============================================


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time chat with streaming."""
    await websocket.accept()

    try:
        # Authenticate WebSocket connection
        auth_message = await websocket.receive_json()
        api_key = auth_message.get("api_key")

        if not api_key or not await verify_api_key(api_key):
            await websocket.send_json({"error": "Invalid API key"})
            await websocket.close()
            return

        while True:
            # Receive chat message
            data = await websocket.receive_json()
            message = data.get("message", "")
            context = data.get("context", {})

            if not message:
                continue

            # Process through supervisor (streaming not yet implemented,
            # send as single response)
            response = await supervisor.process_chat_request(
                message=message, context=context, stream=False, api_key=api_key
            )

            # Send response as WebSocket message
            await websocket.send_json(
                {
                    "response": response.response,
                    "conversation_id": response.conversation_id,
                    "agent_type": response.agent_type,
                    "processing_time": response.processing_time,
                    "done": True,
                }
            )

    except Exception as e:
        logger.error("WebSocket error", error=str(e))
        try:
            await websocket.send_json({"error": "Internal server error"})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


# ============================================
# Administrative Endpoints
# ============================================


@app.post("/api/admin/reload-agents")
async def reload_agents(
    _api_key: str = Depends(verify_api_key),
) -> dict[str, str]:
    """Reload all agents (admin only)."""
    # TODO: Implement admin authentication
    if not supervisor:
        raise HTTPException(status_code=503, detail="Supervisor not available")

    try:
        await supervisor.reload_agents()
        return {"message": "Agents reloaded successfully"}

    except Exception as e:
        logger.error("Failed to reload agents", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to reload agents") from e


@app.get("/api/admin/stats")
async def get_system_stats(
    _api_key: str = Depends(verify_api_key),
) -> dict[str, Any]:
    """Get system statistics (admin only)."""
    # TODO: Implement admin authentication
    if not metrics_collector:
        raise HTTPException(status_code=503, detail="Metrics not available")

    try:
        stats = metrics_collector.get_metrics_summary()
        return stats

    except Exception as e:
        logger.error("Failed to get system stats", error=str(e))
        raise HTTPException(
            status_code=500, detail="Failed to retrieve system stats"
        ) from e


# ============================================
# Startup Configuration
# ============================================

if __name__ == "__main__":
    # Development server configuration
    uvicorn.run(
        "cartrita.orchestrator.main:app",
        host="127.0.0.1",  # Bind to localhost for security
        port=int(os.getenv("AI_ORCHESTRATOR_PORT", "8000")),
        reload=True,
        log_level="info",
        access_log=True,
    )
