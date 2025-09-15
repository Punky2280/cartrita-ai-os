"""
Cartrita AI OS - Optimized Main FastAPI Application
High-performance hierarchical multi-agent system with GPT-4.1 orchestration.
"""

import asyncio
import json
import os
import shutil
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

import structlog
import uvicorn
from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
import time  # Added for timestamp in /health response

# Conditional imports with graceful fallbacks
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass

import sys
_repo_root = os.path.dirname(os.path.abspath(__file__))
_ai_path = os.path.join(_repo_root, "services", "ai-orchestrator")
if os.path.isdir(os.path.join(_ai_path, "cartrita")) and _ai_path not in sys.path:
    sys.path.insert(0, _ai_path)

# Core service imports
from cartrita.orchestrator.core.supervisor import SupervisorOrchestrator  # noqa: E402
from cartrita.orchestrator.core.database import DatabaseManager  # noqa: E402
from cartrita.orchestrator.core.cache import CacheManager  # noqa: E402
from cartrita.orchestrator.core.metrics import MetricsCollector  # noqa: E402
from cartrita.orchestrator.services.auth import verify_api_key  # noqa: E402
from cartrita.orchestrator.services.jwt_auth import verify_api_key_or_jwt, jwt_manager  # noqa: E402
from jose import jwt  # noqa: E402
from cartrita.orchestrator.services.rate_limiter import check_api_rate_limit, check_auth_rate_limit  # noqa: E402
from cartrita.orchestrator.services.openai_service import OpenAIService  # noqa: E402
from cartrita.orchestrator.utils.config import Settings  # noqa: E402
from cartrita.orchestrator.utils.logger import setup_logging  # noqa: E402
from cartrita.orchestrator.models.schemas import (  # noqa: E402
    AgentStatusResponse,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    Message,
    MessageRole,
)
from cartrita.orchestrator.models.auth_schemas import (  # noqa: E402
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    AuthStatusResponse,
)

# Configure logging
# Initialize structured logging configuration for the application (sets up structlog, log level, handlers, etc.)
setup_logging()
logger = structlog.get_logger(__name__)

# Temporary instrumentation to capture Pydantic v2 orm_mode deprecation stacks.
# Captures first few occurrences and logs structured stack traces for remediation.
import warnings  # noqa: E402
import traceback  # noqa: E402

_ORM_MODE_CAPTURE_LIMIT = int(os.getenv("ORM_MODE_CAPTURE_LIMIT", "5"))
_orm_mode_captured = 0
_original_showwarning = warnings.showwarning


def _orm_mode_showwarning(message, category, filename, lineno, file=None, line=None):  # type: ignore[override]
    global _orm_mode_captured
    text = str(message)
    if "orm_mode" in text and _orm_mode_captured < _ORM_MODE_CAPTURE_LIMIT:
        _orm_mode_captured += 1
        stack_str = "".join(traceback.format_stack(limit=25))
        logger.warning(
            "pydantic.orm_mode.deprecation",
            occurrence=_orm_mode_captured,
            message=text,
            file=filename,
            line=lineno,
            stack=stack_str,
        )
    return _original_showwarning(message, category, filename, lineno, file, line)


warnings.showwarning = _orm_mode_showwarning  # type: ignore[assignment]

# Global service instances
services: dict[str, Optional[Any]] = {
    "supervisor": None,
    "db_manager": None,
    "cache_manager": None,
    "metrics_collector": None,
    "openai_service": None,
}


class VoiceChatRequest(BaseModel):
    """Voice conversation request model."""
    conversationId: str = Field(..., description="Unique conversation identifier")
    transcribedText: str = Field(..., description="Transcribed speech text")
    conversationHistory: Optional[List[Dict[str, Any]]] = Field(
        None, description="Previous conversation context"
    )
    voiceMode: bool = Field(True, description="Voice conversation flag")


class ErrorResponse(BaseModel):
    """Standardized error response."""
    error: str = Field(..., description="Error message")
    code: str = Field(..., description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Optimized application lifespan with robust initialization."""
    logger.info("🚀 Initializing Cartrita AI Orchestrator...")

    try:
        # Initialize configuration
        settings = Settings()

        # Initialize core services
        services["db_manager"] = DatabaseManager(settings)
        await services["db_manager"].connect()

        services["cache_manager"] = CacheManager(settings.redis.url)
        services["metrics_collector"] = MetricsCollector()
        services["openai_service"] = OpenAIService()

        # Initialize supervisor orchestrator
        services["supervisor"] = SupervisorOrchestrator(
            db_manager=services["db_manager"],
            cache_manager=services["cache_manager"],
            metrics_collector=services["metrics_collector"],
            settings=settings,
        )

        logger.info("✅ Cartrita AI Orchestrator initialized successfully")
        yield

    except Exception as e:
        logger.error("❌ Initialization failed", error=str(e))
        raise

    finally:
        logger.info("🛑 Shutting down Cartrita AI Orchestrator...")

        # Graceful shutdown
        for service_name, service in services.items():
            if service and hasattr(service, 'disconnect'):
                try:
                    await service.disconnect()
                except Exception as e:
                    logger.error(f"Error shutting down {service_name}", error=str(e))

        logger.info("✅ Shutdown complete")


# FastAPI application
app = FastAPI(
    title="Cartrita AI OS - Orchestrator",
    description="High-performance hierarchical multi-agent AI system",
    version="2.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://cartrita-ai-os.com"
    ],
    allow_credentials=True,
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=[
        "localhost",
        "127.0.0.1",
        "cartrita-ai-os.com"
    ]  # Restrict to known hosts for production
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured logging."""
    logger.warning(
        "HTTP exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=str(request.url.path),
        method=request.method,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            code=f"HTTP_{exc.status_code}",
            details={"path": str(request.url.path), "method": request.method},
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with comprehensive error tracking."""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=str(request.url.path),
        method=request.method,
        exc_info=True,
    )

    # Report to metrics collector
    if services["metrics_collector"]:
        try:
            await services["metrics_collector"].record_error(exc, request)
        except Exception:
            pass  # Don't fail on metrics recording

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            code="INTERNAL_ERROR",
            details={"type": type(exc).__name__},
        ).model_dump(),
    )


@app.get("/")
async def root():
    """API information and available endpoints."""
    return {
        "message": "Cartrita AI OS - Hierarchical Multi-Agent System",
        "version": "2.1.0",
        "status": "operational",
        "streaming": {
            "primary_transport": "SSE (Server-Sent Events)",
            "fallback_transport": "WebSocket",
            "events": [
                "token", "function_call", "tool_result", "metrics", "done",
                "agent_task_started", "agent_task_progress", "agent_task_complete",
                "orchestration_decision", "safety_flag", "evaluation_metric",
                "audio_interim", "audio_final", "file_attach_progress"
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
            "docs": "/docs"
        },
        "frontend": "http://localhost:3001"
    }


@app.get("/socket.io/")
async def socket_io_compatibility():
    """Socket.IO compatibility endpoint."""
    return {
        "status": "Socket.IO endpoint available",
        "transport": "polling fallback",
        "message": "Full Socket.IO support disabled for compatibility",
        "alternatives": {
            "websocket": "/ws/chat",
            "sse": "/api/chat/stream"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check."""
    if not all([services["db_manager"], services["cache_manager"]]):
        raise HTTPException(status_code=503, detail="Service not ready")

    # Check service health
    db_healthy = await services["db_manager"].health_check()
    cache_healthy = await services["cache_manager"].health_check()
    supervisor_healthy = bool(
        services["supervisor"]
        and await services["supervisor"].health_check()
    )

    overall_healthy = all([db_healthy, cache_healthy])

    return HealthResponse(
        status="healthy" if overall_healthy else "unhealthy",
        version="2.1.0",
        services={
            "database": "healthy" if db_healthy else "unhealthy",
            "cache": "healthy" if cache_healthy else "unhealthy",
            "supervisor": "healthy" if supervisor_healthy else "disabled",
        },
        timestamp=time.time(),
    )


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    if not services["metrics_collector"]:
        raise HTTPException(status_code=503, detail="Metrics not available")

    return await services["metrics_collector"].get_metrics()


# Authentication Endpoints

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    _: None = Depends(check_auth_rate_limit)
):
    """User login endpoint with JWT token generation."""
    # Simple demo implementation - in production, verify against database
    demo_users = {
        "admin@cartrita.com": {
            "password_hash": jwt_manager.hash_password("admin123"),
            "permissions": ["admin", "chat", "upload", "metrics"]
        },
        "user@cartrita.com": {
            "password_hash": jwt_manager.hash_password("user123"),
            "permissions": ["chat", "upload"]
        }
    }

    user = demo_users.get(login_data.email)
    if not user or not jwt_manager.verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Generate tokens
    access_token = jwt_manager.create_access_token(login_data.email, user["permissions"])
    refresh_token = jwt_manager.create_refresh_token(login_data.email)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=jwt_manager.access_token_expire_minutes * 60
    )


@app.post("/api/auth/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    refresh_data: RefreshTokenRequest,
    _: None = Depends(check_auth_rate_limit)
):
    """Refresh access token using refresh token."""
    try:
        # Verify refresh token
        token_data = jwt_manager.verify_token(refresh_data.refresh_token)

        # Check if it's actually a refresh token
        payload = jwt.decode(
            refresh_data.refresh_token,
            jwt_manager.secret_key,
            algorithms=[jwt_manager.algorithm]
        )

        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=401,
                detail="Invalid token type"
            )

        # Generate new tokens
        demo_users = {
            "admin@cartrita.com": ["admin", "chat", "upload", "metrics"],
            "user@cartrita.com": ["chat", "upload"]
        }

        permissions = demo_users.get(token_data.user_id, [])
        access_token = jwt_manager.create_access_token(token_data.user_id, permissions)
        new_refresh_token = jwt_manager.create_refresh_token(token_data.user_id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            expires_in=jwt_manager.access_token_expire_minutes * 60
        )

    except Exception as e:
        logger.warning(f"Token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token"
        )


@app.get("/api/auth/status", response_model=AuthStatusResponse)
async def auth_status(
    request: Request,
    current_user: Optional[str] = Depends(verify_api_key_or_jwt)
):
    """Get current authentication status."""
    # Check if authenticated via JWT
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header.split(" ")[1]
            token_data = jwt_manager.verify_token(token)
            return AuthStatusResponse(
                authenticated=True,
                user_id=token_data.user_id,
                permissions=token_data.permissions,
                token_expires_at=token_data.expires_at,
                auth_method="jwt"
            )
        except Exception:
            pass

    # Check if authenticated via API key
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return AuthStatusResponse(
            authenticated=True,
            user_id="api_key_user",
            permissions=["api_access"],
            auth_method="api_key"
        )

    return AuthStatusResponse(
        authenticated=False,
        auth_method="none"
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    request_body: ChatRequest,
    request: Request,
    api_key: str = Depends(verify_api_key_or_jwt),
    _: None = Depends(check_api_rate_limit)
):
    """Main chat endpoint with GPT-4.1 orchestration."""
    if not services["supervisor"]:
        raise HTTPException(status_code=503, detail="Supervisor not available")

    try:
        # Record request metrics
        if services["metrics_collector"]:
            await services["metrics_collector"].record_request(request_body, api_key)

        # Process through supervisor
        response = await services["supervisor"].process_chat_request(
            message=request_body.message,
            context=request_body.context,
            agent_override=request_body.agent_override,
            stream=request_body.stream,
            api_key=api_key,
        )

        # Record response metrics
        if services["metrics_collector"]:
            await services["metrics_collector"].record_response(response)

        return response

    except Exception as e:
        logger.error("Chat request failed", error=str(e), api_key=api_key[:8] + "...")
        raise HTTPException(status_code=500, detail="Chat processing failed") from e


@app.post("/api/chat/voice", response_model=ChatResponse)
async def voice_chat(request: VoiceChatRequest, api_key: str = Depends(verify_api_key)):
    """Voice conversation endpoint with optimized processing."""
    if not services["openai_service"]:
        raise HTTPException(status_code=503, detail="OpenAI service not available")

    try:
        logger.info(
            "Processing voice conversation",
            conversation_id=request.conversationId,
            api_key=api_key[:8] + "..."
        )

        # Process voice conversation
        response_content = ""
        async for chunk in services["openai_service"].process_voice_conversation(
            conversation_id=request.conversationId,
            transcribed_text=request.transcribedText,
            conversation_history=request.conversationHistory
        ):
            if chunk["type"] == "content":
                response_content += chunk["content"]
            elif chunk["type"] == "error":
                raise HTTPException(status_code=500, detail=chunk["error"])

        return ChatResponse(
            response=response_content,
            conversation_id=request.conversationId,
            agent_type="openai-voice",
            messages=[Message(role=MessageRole.ASSISTANT, content=response_content)],
            context=request.conversationHistory,
            metadata={
                "voice_mode": request.voiceMode,
                "transcription_length": len(request.transcribedText)
            },
            processing_time=0.0,
            token_usage=None
        )

    except Exception as e:
        logger.error(
            "Voice chat failed",
            error=str(e),
            conversation_id=request.conversationId,
            api_key=api_key[:8] + "..."
        )
        raise HTTPException(status_code=500, detail="Voice chat processing failed") from e


@app.get("/api/agents")
async def list_agents(api_key: str = Depends(verify_api_key)):
    """List all available agents and their status."""
    _ = api_key  # noqa: F841 (auth enforced via dependency)
    if not services["supervisor"]:
        raise HTTPException(status_code=503, detail="Supervisor not available")

    try:
        return await services["supervisor"].get_agent_statuses()
    except Exception as e:
        logger.error("Failed to list agents", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve agents") from e


@app.get("/api/agents/{agent_id}", response_model=AgentStatusResponse)
async def get_agent_status(agent_id: str, api_key: str = Depends(verify_api_key)):
    """Get detailed status of a specific agent."""
    _ = api_key  # noqa: F841
    if not services["supervisor"]:
        raise HTTPException(status_code=503, detail="Supervisor not available")

    try:
        agent_status = await services["supervisor"].get_agent_status(agent_id)
        if not agent_status:
            raise HTTPException(status_code=404, detail="Agent not found")
        return agent_status
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get agent status", error=str(e), agent_id=agent_id)
        raise HTTPException(status_code=500, detail="Failed to retrieve agent status") from e


@app.get("/api/chat/stream")
async def chat_stream(
    message: str,
    context: Optional[str] = None,
    agent_override: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """SSE endpoint for streaming chat responses."""
    if not services["supervisor"]:
        raise HTTPException(status_code=503, detail="Supervisor not available")

    async def generate():
        try:
            # Parse context
            context_dict = {}
            if context:
                try:
                    context_dict = json.loads(context)
                except json.JSONDecodeError:
                    context_dict = {"raw_context": context}

            # Process through supervisor
            response = await services["supervisor"].process_chat_request(
                message=message,
                context=context_dict,
                agent_override=agent_override,
                stream=False,
                api_key=api_key,
            )

            # Send response as SSE
            try:
                response_dict = response.model_dump() if hasattr(response, 'model_dump') else response.dict()
                yield f"data: {json.dumps(response_dict, default=str, ensure_ascii=False)}\n\n"
            except Exception as serialize_error:
                logger.error("Failed to serialize response", error=str(serialize_error))
                simple_response = {
                    "response": str(getattr(response, 'response', response)),
                    "conversation_id": str(getattr(response, 'conversation_id', 'unknown')),
                    "agent_type": str(getattr(response, 'agent_type', 'supervisor')),
                    "status": "completed"
                }
                yield f"data: {json.dumps(simple_response)}\n\n"

            yield "data: [DONE]\n\n"

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
    if not services["supervisor"]:
        raise HTTPException(status_code=503, detail="Supervisor not available")

    # Parse conversation history
    history = []
    if conversationHistory:
        try:
            history = json.loads(conversationHistory)
        except json.JSONDecodeError:
            history = []

    async def generate():
        try:
            response = await services["supervisor"].process_chat_request(
                message=transcribedText,
                context={
                    "conversation_id": conversationId,
                    "conversation_history": history,
                    "voice_mode": True
                },
                stream=False,
                api_key=api_key,
            )

            # Send voice-specific response
            response_dict = response.model_dump() if hasattr(response, 'model_dump') else response.dict()
            event_data = {
                **response_dict,
                "conversationId": conversationId,
                "timestamp": asyncio.get_event_loop().time(),
                "voiceMode": True
            }
            yield f"data: {json.dumps(event_data, default=str)}\n\n"
            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error("Voice streaming failed", error=str(e))
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


@app.post("/upload/multiple")
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    conversationId: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """Upload multiple files endpoint."""
    _ = api_key  # noqa: F841
    try:
        logger.info(f"Processing {len(files)} file uploads", conversation_id=conversationId)

        upload_dir = "/tmp/uploads"
        os.makedirs(upload_dir, exist_ok=True)

        uploaded_files = []
        for file in files:
            if file.filename:
                file_path = os.path.join(upload_dir, file.filename)
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)

                uploaded_files.append({
                    "filename": file.filename,
                    "size": os.path.getsize(file_path),
                    "path": file_path,
                    "content_type": file.content_type,
                    "url": f"/files/{file.filename}"
                })

        return {
            "success": True,
            "data": uploaded_files,
            "message": f"Successfully uploaded {len(uploaded_files)} files",
            "conversationId": conversationId
        }

    except Exception as e:
        logger.error("File upload failed", error=str(e), conversation_id=conversationId)
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


@app.post("/upload")
async def upload_single_file(
    file: UploadFile = File(...),
    conversationId: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """Upload single file endpoint."""
    _ = api_key  # noqa: F841
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")

        logger.info(f"Processing file upload: {file.filename}", conversation_id=conversationId)

        upload_dir = "/tmp/uploads"
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_info = {
            "filename": file.filename,
            "size": os.path.getsize(file_path),
            "path": file_path,
            "content_type": file.content_type,
            "url": f"/files/{file.filename}"
        }

        return {
            "success": True,
            "data": file_info,
            "message": f"Successfully uploaded {file.filename}",
            "conversationId": conversationId
        }

    except Exception as e:
        logger.error("File upload failed", error=str(e), conversation_id=conversationId)
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket endpoint for real-time chat."""
    await websocket.accept()

    try:
        # Authenticate connection
        auth_message = await websocket.receive_json()
        api_key = auth_message.get("api_key")

        if not api_key:
            await websocket.send_json({"error": "API key required"})
            await websocket.close()
            return

        # Verify API key
        try:
            await verify_api_key(api_key)
        except HTTPException:
            await websocket.send_json({"error": "Invalid API key"})
            await websocket.close()
            return

        while True:
            # Receive and process messages
            data = await websocket.receive_json()
            message = data.get("message", "")
            context = data.get("context", {})

            if not message:
                continue

            if not services["supervisor"]:
                await websocket.send_json({"error": "Supervisor not available"})
                continue

            # Process through supervisor
            response = await services["supervisor"].process_chat_request(
                message=message,
                context=context,
                stream=False,
                api_key=api_key
            )

            # Send response
            await websocket.send_json({
                "response": response.response,
                "conversation_id": response.conversation_id,
                "agent_type": response.agent_type,
                "processing_time": response.processing_time,
                "done": True,
            })

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


@app.post("/api/admin/reload-agents")
async def reload_agents(api_key: str = Depends(verify_api_key)):
    """Reload all agents (admin only)."""
    _ = api_key  # noqa: F841
    if not services["supervisor"]:
        raise HTTPException(status_code=503, detail="Supervisor not available")

    try:
        await services["supervisor"].reload_agents()
        return {"message": "Agents reloaded successfully"}
    except Exception as e:
        logger.error("Failed to reload agents", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to reload agents") from e


@app.get("/api/admin/stats")
async def get_system_stats(api_key: str = Depends(verify_api_key)):
    """Get system statistics (admin only)."""
    _ = api_key  # noqa: F841
    if not services["metrics_collector"]:
        raise HTTPException(status_code=503, detail="Metrics not available")

    try:
        return await services["metrics_collector"].get_metrics_summary()
    except Exception as e:
        logger.error("Failed to get system stats", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve system stats") from e


if __name__ == "__main__":
    # Application entrypoint (run: python main.py)
    # Enable reload only if explicitly set (development usage)
    reload_enabled = os.getenv("AI_ORCHESTRATOR_RELOAD", "false").lower() == "true"
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=int(os.getenv("AI_ORCHESTRATOR_PORT", "8000")),
        reload=reload_enabled,
        log_level="info",
        access_log=True,
    )
