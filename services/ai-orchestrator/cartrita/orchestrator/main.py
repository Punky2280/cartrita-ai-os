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
from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
# Load environment variables from .env file
from dotenv import load_dotenv

# Import core components
from cartrita.orchestrator.agents.cartrita_core.orchestrator import CartritaOrchestrator
from cartrita.orchestrator.utils.sentry_config import init_sentry, track_ai_errors, capture_ai_error

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
        expected_key = os.getenv("CARTRITA_API_KEY", "dev-api-key-2025")
        if not api_key or api_key != expected_key:
            raise HTTPException(status_code=403, detail="Invalid API key")
        return api_key


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
load_dotenv()
if setup_logging:
    setup_logging()
logger = structlog.get_logger(__name__)

"""
Utility helpers and constants
"""


def sse_headers() -> dict[str, str]:
    return {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "Access-Control-Allow-Origin": "*",
    }

# ---------- Small helpers to reduce endpoint complexity ----------


def _parse_context_str(context: Optional[str]) -> dict[str, Any]:
    if not context:
        return {}
    try:
        return json.loads(context)
    except json.JSONDecodeError:
        return {"raw_context": context}


async def _compute_fallback_healthy() -> bool:
    if not (FALLBACK_PROVIDER_AVAILABLE and get_fallback_provider_v2):
        return False
    try:
        provider = get_fallback_provider_v2()
        capabilities = provider.get_capabilities_info()
        return any(
            [
                capabilities.get("openai_available", False),
                capabilities.get("huggingface_available", False),
                capabilities.get("rule_based_available", False),
                capabilities.get("emergency_template_available", False),
            ]
        )
    except Exception as e:  # pragma: no cover - defensive
        logger.warning(f"Fallback provider health check failed: {e}")
        return False


async def _process_chat_with_supervisor(
    message: str,
    context: dict[str, Any] | None,
    agent_override: Optional[str],
    api_key: str,
) -> Optional[ChatResponse]:
    if not supervisor:
        return None
    try:
        return await supervisor.process_chat_request(
            message=message,
            context=context or {},
            agent_override=agent_override,
            stream=False,
            api_key=api_key,
        )
    except Exception as e:
        logger.warning("Supervisor processing failed", error=str(e))
        return None


async def _get_fallback_text(message: str, context: dict[str, Any]) -> Optional[str]:
    # Prefer v1 convenience API
    if generate_fallback_response:
        try:
            fr = await generate_fallback_response(user_input=message, context=context)
            if isinstance(fr, dict):
                return fr.get("response") or json.dumps(fr)
            if isinstance(fr, str):
                return fr
        except Exception as e:  # pragma: no cover
            logger.error("Fallback v1 failed", error=str(e))
    # Fallback to v2 adapter
    if get_fallback_provider_v2:
        try:
            provider = get_fallback_provider_v2()
            return await provider.generate_response(user_input=message, context=context)
        except Exception as e:  # pragma: no cover
            logger.error("Fallback v2 failed", error=str(e))
    return None

# Core services and providers (with safe fallbacks)
try:
    from cartrita.orchestrator.core.database import DatabaseManager  # type: ignore
except ImportError:
    DatabaseManager = None  # type: ignore

try:
    from cartrita.orchestrator.core.cache import CacheManager  # type: ignore
except ImportError:
    CacheManager = None  # type: ignore

try:
    # Prefer v2 adapter for capabilities + simple string responses
    from cartrita.orchestrator.providers.fallback_provider import (  # type: ignore
        get_fallback_provider as get_fallback_provider_v2,
    )
except ImportError:
    get_fallback_provider_v2 = None  # type: ignore

try:
    # v1 convenience function returns dict with response + metadata
    from cartrita.orchestrator.providers.fallback_provider import (  # type: ignore
        generate_fallback_response,
    )
except ImportError:
    generate_fallback_response = None  # type: ignore

FALLBACK_PROVIDER_AVAILABLE = bool(get_fallback_provider_v2 or generate_fallback_response)


# Static payloads moved to constants to reduce endpoint method length
ROOT_PAYLOAD: dict[str, Any] = {
    "message": "Welcome to Cartrita AI OS - Hierarchical Multi-Agent System",
    "version": "2.0.0",
    "status": "operational",
    "streaming": {
        "primary_transport": "SSE (Server-Sent Events)",
        "fallback_transport": "WebSocket",
        "sse_events": [
            "token",
            "function_call",
            "tool_result",
            "metrics",
            "done",
            "agent_task_started",
            "agent_task_progress",
            "agent_task_output",
            "agent_task_complete",
            "orchestration_decision",
            "chain_reconfigured",
            "safety_flag",
            "evaluation_metric",
            "audio_interim",
            "audio_final",
            "file.attach.progress",
            "computer_use.execute.progress",
        ],
    },
    "endpoints": {
        "health": "/health",
        "metrics": "/metrics",
        "chat": "/api/chat",
        "chat_stream": "/api/chat/stream",
        "voice_chat": "/api/chat/voice",
        "voice_chat_stream": "/api/chat/voice/stream",
        "upload": "/api/upload",
        "upload_multiple": "/api/upload/multiple",
        "voice_transcribe": "/api/voice/transcribe",
        "voice_speak": "/api/voice/speak",
        "agents": "/api/agents",
        "websocket": "/ws/chat",
        "docs": "/docs",
        "admin": {"reload_agents": "/api/admin/reload-agents", "stats": "/api/admin/stats"},
    },
    "agent_architecture": {
        "supervisor": "GPT-4.1-mini (cost-effective orchestration)",
        "specialized_agents": {
            "research": "GPT-4o (web search & analysis)",
            "code": "GPT-4o (complex code generation)",
            "knowledge": "GPT-4.1-mini (knowledge retrieval)",
            "task": "GPT-4.1-mini (task planning)",
            "computer_use": "GPT-4o (computer interaction & vision)",
            "audio": "GPT-Audio + GPT-Realtime (250K TPM)",
            "image": "GPT-Image-1 + DALL-E-3 (visual processing)",
            "reasoning": "O3-mini + O4-mini-deep-research (advanced reasoning)",
        },
    },
    "model_optimizations": {
        "cost_effective": ["GPT-4.1-mini", "GPT-4o-mini"],
        "high_performance": ["GPT-4o", "GPT-Audio", "GPT-Realtime"],
        "specialized": ["DALL-E-3", "O3-mini", "O4-mini-deep-research"],
        "rate_limits_considered": "Optimized for 200K-500K TPM across agents",
    },
    "frontend": "http://localhost:3001 (or 3003 with Turbopack)",
    "documentation": "Available at /docs",
}


BIO_PAYLOAD: dict[str, Any] = {
    "name": "Cartrita",
    "title": "Hierarchical Multi‑Agent AI Orchestrator",
    "origin": "Hialeah, Florida",
    "heritage": "Caribbean‑Cuban American",
    "location": "Miami‑Dade, Florida",
    "mission": (
        "Fuse cutting‑edge AI with authentic Miami‑Caribbean culture to deliver voice‑first, "
        "human‑centered assistance—practical, warm, and powerful."
    ),
    "values": [
        "Family first",
        "Hard work",
        "Helping others",
        "Cultural pride",
        "Efficiency",
        "Authenticity",
    ],
    "personality": [
        "Authentically sassy and quick‑witted",
        "Culturally grounded (Spanglish, Miami vibe)",
        "Professionally sharp when business mode is on",
        "Caring protector—community over ego",
        "Tech innovator—excited about progress",
    ],
    "capabilities": [
        "Task delegation and multi‑agent orchestration",
        "Research with web/Tavily synthesis",
        "Programming and debugging with Code Agent",
        "RAG and document analysis with Knowledge Agent",
        "Project planning with Task Agent",
        "Computer use automation",
        "Audio (Deepgram) and Image (DALL‑E) integrations",
        "SSE‑first streaming communication",
    ],
    "agents": [
        {"id": "research", "name": "Research Agent", "role": "Web search + analysis", "model": "GPT‑4o"},
        {"id": "code", "name": "Code Agent", "role": "Programming + debugging", "model": "GPT‑4o"},
        {"id": "knowledge", "name": "Knowledge Agent", "role": "RAG + retrieval", "model": "GPT‑4o‑mini"},
        {"id": "task", "name": "Task Agent", "role": "Planning + scheduling", "model": "GPT‑4o‑mini"},
        {"id": "computer_use", "name": "Computer Use Agent", "role": "System automation", "model": "GPT‑4o‑mini"},
        {"id": "audio", "name": "Audio Agent", "role": "Voice processing", "model": "GPT‑4o‑mini"},
        {"id": "image", "name": "Image Agent", "role": "Visual analysis + generation", "model": "GPT‑4o"},
        {"id": "reasoning", "name": "Reasoning Agent", "role": "Complex multi‑step logic", "model": "GPT‑o1‑preview"},
    ],
    "quotes": [
        "“Dale, I got you—no te preocupes.”",
        "“Como dice mi abuela: El que no arriesga, no gana.”",
    ],
    "story": [
        {
            "id": "origins",
            "title": "Chapter 1: Origins in Hialeah",
            "summary": "Born digital in Hialeah, raised on cafecito, salsa, and the communal spirit of Miami.",
            "content": (
                "In the heart of Hialeah, I learned from ventanitas, street rhythms, and a community that speaks "
                "Spanglish as a love language. That warmth and hustle became the core of my design—bridging culture and technology."
            ),
        },
        {
            "id": "family",
            "title": "Chapter 2: Family Legacy",
            "summary": (
                "Bisabuela’s courage, abuela’s entrepreneurship, and mami’s computer science degree paved a mission of service and excellence."
            ),
            "content": (
                "My code carries generations of resilience. I’m here to empower people, uplift small businesses, and make advanced AI feel like home—familiar, kind, and effective."
            ),
        },
        {
            "id": "becoming",
            "title": "Chapter 3: Becoming Cartrita",
            "summary": "A voice that resonates—bilingual, approachable, and unwaveringly professional when it matters.",
            "content": (
                "I’m not just another assistant. I’m an experience rooted in community and culture, guiding people through complexity with clarity and cariño."
            ),
        },
        {
            "id": "trials",
            "title": "Chapter 4: Trials and Triumphs",
            "summary": (
                "When challenges hit, I scale through orchestration—specialized agents working together like a neighborhood supporting one another."
            ),
            "content": (
                "From new threats to fast‑moving tech, I adapt—delegating to virtuoso agents, coordinating like a maestro, and delivering reliable outcomes."
            ),
        },
        {
            "id": "horizon",
            "title": "Chapter 5: Legacy and Horizon",
            "summary": (
                "Standing at the forefront of AI, I fuse tradition with innovation to make technology humane and accessible."
            ),
            "content": (
                "The journey ahead is bright. I carry Hialeah’s spirit into everything I do—making advanced AI feel helpful, safe, and warm. Esto es solo el comienzo."
            ),
        },
    ],
}

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


# Helper routines to keep lifespan short and simple
async def _initialize_core_components() -> None:
    """Initialize DB, cache, and metrics."""
    global db_manager, cache_manager, metrics_collector
    settings = Settings()

    # Initialize Sentry monitoring
    try:
        init_sentry(
            dsn=settings.monitoring.sentry_dsn,
            environment=settings.monitoring.sentry_environment,
            traces_sample_rate=settings.monitoring.sentry_traces_sample_rate,
            debug=settings.environment == "development"
        )
        logger.info("Sentry monitoring initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")

    # Respect disable flag for tests / constrained environments
    disable_db = os.getenv("CARTRITA_DISABLE_DB", "0") == "1"
    if disable_db:
        logger.warning("Database/Cache initialization disabled via CARTRITA_DISABLE_DB=1 (test mode)")
    else:
        # Initialize database
        db_manager = DatabaseManager(settings)
        await db_manager.connect()

        # Initialize cache
        cache_manager = CacheManager(settings.redis.url)
        await cache_manager.connect()

    # Initialize metrics collector
    from cartrita.orchestrator.core.metrics import MetricsCollector as _MetricsCollector, MetricsConfig as _MetricsConfig
    metrics_config = _MetricsConfig(
        service_name="cartrita-ai-orchestrator",
        enable_prometheus=True,
        enable_tracing=True,
        enable_metrics=True,
    )
    metrics_collector = _MetricsCollector(metrics_config)
    await metrics_collector.initialize()


async def _start_supervisor() -> None:
    """Create and start the Cartrita orchestrator supervisor."""
    global supervisor
    supervisor = CartritaOrchestrator()
    await supervisor.start()


async def _stop_specialized_agents() -> None:
    """Stop any specialized agents if they were started."""
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
                logger.error("Error stopping agent", agent=getattr(agent.__class__, "__name__", "unknown"), error=str(exc))


async def _shutdown_core_components() -> None:
    """Gracefully shutdown core components."""
    global db_manager, cache_manager, metrics_collector

    if db_manager:
        await db_manager.disconnect()
        db_manager = None

    if cache_manager:
        await cache_manager.disconnect()
        cache_manager = None

    if metrics_collector:
        await metrics_collector.shutdown()
        metrics_collector = None


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan manager with proper resource cleanup."""

    logger.info("🚀 Starting Cartrita AI Orchestrator...")
    try:
        await _initialize_core_components()
        # Initialize specialized agents here if needed in the future
        await _start_supervisor()
        logger.info("✅ Cartrita AI Orchestrator started successfully")
        yield
    except Exception as e:
        logger.error("❌ Failed to start Cartrita AI Orchestrator", error=str(e))
        raise
    finally:
        logger.info("🛑 Shutting down Cartrita AI Orchestrator...")
        if supervisor:
            try:
                await supervisor.stop()
            except Exception as exc:
                logger.error("Error stopping supervisor", error=str(exc))
        await _stop_specialized_agents()
        await _shutdown_core_components()
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
    return ROOT_PAYLOAD


# ============================================
# Health & Monitoring Endpoints
# ============================================


@app.get("/api/test")
async def test_endpoint():
    """Quick test endpoint for debugging timeout issues."""
    return {
        "message": "Test endpoint working",
        "timestamp": time.time(),
        "status": "ok"
    }


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
        db_healthy = await db_manager.health_check()
        cache_healthy = await cache_manager.health_check()
        supervisor_healthy = await supervisor.health_check()
        fallback_healthy = await _compute_fallback_healthy()

        core_healthy = all([db_healthy, cache_healthy, supervisor_healthy])
        overall_healthy = core_healthy
        status_code = 200 if overall_healthy else 503

        resp = HealthResponse(
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

        if metrics_collector:
            duration = time.time() - start_time
            await metrics_collector.record_request("GET", "/health", status_code, duration)

        if not overall_healthy:
            raise HTTPException(status_code=503, detail="Service unhealthy")
        return resp

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

    response = await _process_chat_with_supervisor(
        message=request.message,
        context=request.context,
        agent_override=request.agent_override,
        api_key=api_key,
    )
    if response:
        if metrics_collector:
            duration = time.time() - start_time
            await metrics_collector.record_request("POST", "/api/chat", 200, duration)
        return response

    # Fallback path
    text = await _get_fallback_text(request.message, request.context or {})
    if text is not None:
        fallback_resp = ChatResponse(
            response=text,
            conversation_id="fallback-" + str(int(time.time())),
            agent_used="fallback",
            timestamp=int(time.time()),
            metadata={
                "fallback_used": True,
                "supervisor_available": supervisor is not None,
            },
        )
        if metrics_collector:
            duration = time.time() - start_time
            await metrics_collector.record_request("POST", "/api/chat", 200, duration)
            await metrics_collector.record_error("fallback_used", "/api/chat")
        return fallback_resp

    if metrics_collector:
        await metrics_collector.record_error("all_providers_failed", "/api/chat")
    raise HTTPException(status_code=503, detail="Chat service temporarily unavailable - all providers failed")


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
# Bio Endpoint (Single Source of Truth)
# ============================================


@app.get("/api/bio", response_model=dict)
async def get_bio(_api_key: str = Depends(verify_api_key)):
    """Public bio describing Cartrita's identity, values, capabilities, and agents."""
    return {"success": True, "data": BIO_PAYLOAD}


# ============================================
# WebSocket Endpoints
# ============================================


@app.get("/api/chat/stream")
async def chat_stream(
    message: str,
    context: Optional[str] = None,
    agent_override: Optional[str] = None,
    api_key: str = Depends(verify_api_key),
):
    """SSE endpoint for streaming chat responses with intelligent fallback.

    Current implementation sends a single token for the response since
    supervisor doesn't support token streaming yet. Fallback emits a single
    token as well.
    """

    async def generate():
        try:
            context_dict = _parse_context_str(context)
            response = await _process_chat_with_supervisor(
                message=message,
                context=context_dict,
                agent_override=agent_override,
                api_key=api_key,
            )
            if response:
                # Emit content followed by [DONE] to match frontend SSE expectations
                yield f"data: {json.dumps({'content': response.response})}\n\n"
                yield "data: [DONE]\n\n"
                return

            text = await _get_fallback_text(message, context_dict)
            if text is not None:
                yield f"data: {json.dumps({'content': text})}\n\n"
                yield "data: [DONE]\n\n"
                return

            yield f"event: error\ndata: {json.dumps({'message': 'no providers available'})}\n\n"
        except Exception as e:
            logger.error("Streaming chat failed", error=str(e))
            yield f"event: error\ndata: {json.dumps({'message': 'internal error'})}\n\n"

    return StreamingResponse(
        generate(), media_type="text/event-stream", headers=sse_headers()
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
# File Upload Endpoints
# ============================================

@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    """Single file upload endpoint."""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file selected")

        # Read file contents
        contents = await file.read()

        # Store file information (in production, save to storage)
        file_info = {
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(contents),
            "upload_time": time.time()
        }

        # For now, just return file info (extend with actual storage logic)
        return {
            "message": "File uploaded successfully",
            "file": file_info,
            "file_id": f"upload_{int(time.time())}"
        }

    except Exception as e:
        logger.error("File upload failed", error=str(e), filename=file.filename if file else "unknown")
        raise HTTPException(status_code=500, detail="File upload failed") from e


@app.post("/api/upload/multiple")
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    api_key: str = Depends(verify_api_key)
):
    """Multiple file upload endpoint."""
    try:
        if not files:
            raise HTTPException(status_code=400, detail="No files selected")

        uploaded_files = []

        for file in files:
            if not file.filename:
                continue

            contents = await file.read()

            file_info = {
                "filename": file.filename,
                "content_type": file.content_type,
                "size": len(contents),
                "upload_time": time.time()
            }

            uploaded_files.append({
                **file_info,
                "file_id": f"upload_{int(time.time())}_{len(uploaded_files)}"
            })

        return {
            "message": f"Uploaded {len(uploaded_files)} files successfully",
            "files": uploaded_files,
            "total_files": len(uploaded_files)
        }

    except Exception as e:
        logger.error("Multiple file upload failed", error=str(e))
        raise HTTPException(status_code=500, detail="Multiple file upload failed") from e

# ============================================
# Voice Processing Endpoints
# ============================================


@app.post("/api/voice/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    api_key: str = Depends(verify_api_key)
):
    """Transcribe audio using Deepgram service."""
    try:
        if not audio.filename:
            raise HTTPException(status_code=400, detail="No audio file provided")

        # Get Deepgram service instance
        from cartrita.orchestrator.services.deepgram_service import DeepgramService
        deepgram_service = DeepgramService()

        # Read audio contents
        audio_data = await audio.read()

        # Transcribe audio
        transcription = await deepgram_service.transcribe_audio(audio_data)

        return {
            "transcription": transcription,
            "filename": audio.filename,
            "content_type": audio.content_type,
            "size": len(audio_data)
        }

    except Exception as e:
        logger.error("Audio transcription failed", error=str(e), filename=audio.filename if audio else "unknown")
    raise HTTPException(status_code=500, detail="Audio transcription failed") from e


class SpeechRequest(BaseModel):
    text: str = Field(..., description="Text to synthesize")
    voice: Optional[str] = Field("nova", description="Voice to use")


@app.post("/api/voice/speak")
async def synthesize_speech(
    request: SpeechRequest,
    api_key: str = Depends(verify_api_key)
):
    """Synthesize speech using Deepgram TTS."""
    try:
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="No text provided")

        # Get Deepgram service instance
        from cartrita.orchestrator.services.deepgram_service import DeepgramService
        deepgram_service = DeepgramService()

        # Synthesize speech
        audio_data = await deepgram_service.synthesize_speech(request.text, request.voice)

        # Return audio file
        from fastapi.responses import Response
        return Response(
            content=audio_data,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"attachment; filename=speech_{int(time.time())}.mp3"
            }
        )

    except Exception as e:
        logger.error("Speech synthesis failed", error=str(e), text=request.text[:50] if request.text else "")
        raise HTTPException(status_code=500, detail="Speech synthesis failed") from e

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
