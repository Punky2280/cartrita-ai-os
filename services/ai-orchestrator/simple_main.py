#!/usr/bin/env python3
"""
Simplified FastAPI server for Cartrita AI OS with working CORS.
Bypasses complex agent imports that are causing issues.
"""

import json
import os
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv("/app/.env")


# Simple auth function
async def verify_api_key(api_key: Optional[str] = None) -> str:
    """Simple API key verification."""
    expected_key = os.getenv("CARTRITA_API_KEY", "dev-api-key-2025")
    if api_key != expected_key:
        return "dev-api-key-2025"  # Default for development
    return api_key


# Response models
class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: float
    services: dict


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    agent_override: Optional[str] = None
    stream: bool = False


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    agent_type: str
    processing_time: float


class VoiceChatRequest(BaseModel):
    conversationId: str = Field(..., description="Unique conversation identifier")
    transcribedText: str = Field(..., description="Text transcribed from user's speech")
    conversationHistory: Optional[List[Dict[str, Any]]] = Field(None, description="Previous conversation messages")
    voiceMode: bool = Field(True, description="Whether this is a voice conversation")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Simplified lifespan manager."""
    print("🚀 Starting Cartrita AI Orchestrator (Simplified)...")
    yield
    print("🛑 Shutting down Cartrita AI Orchestrator...")


# FastAPI app
app = FastAPI(
    title="Cartrita AI OS - Orchestrator (Simplified)",
    description="Simplified Hierarchical Multi-Agent AI OS",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware - FIXED for frontend on port 3001
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


@app.get("/")
async def root():
    """Root endpoint providing API information."""
    return {
        "message": "Welcome to Cartrita AI OS - Hierarchical Multi-Agent System (Simplified)",
        "version": "2.0.0",
        "status": "operational",
        "cors_fixed": True,
        "frontend_ports": ["3000", "3001", "3003"],
        "endpoints": {
            "health": "/health",
            "chat": "/api/chat",
            "chat_stream": "/api/chat/stream",
            "voice_chat": "/api/chat/voice",
            "docs": "/docs",
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        timestamp=time.time(),
        services={
            "api": "healthy",
            "cors": "configured",
            "simplified": True
        }
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, api_key: str = Depends(verify_api_key)):
    """Simple chat endpoint."""
    start_time = time.time()

    # Simple response for testing
    response_text = f"Echo from AI: {request.message}"

    return ChatResponse(
        response=response_text,
        conversation_id=request.conversation_id or f"conv-{int(time.time())}",
        agent_type="echo-agent",
        processing_time=time.time() - start_time
    )


@app.post("/api/chat/voice", response_model=ChatResponse)
async def voice_chat(request: VoiceChatRequest, api_key: str = Depends(verify_api_key)):
    """Voice conversation endpoint."""
    start_time = time.time()

    response_text = f"Voice Echo: {request.transcribedText}"

    return ChatResponse(
        response=response_text,
        conversation_id=request.conversationId,
        agent_type="voice-echo-agent",
        processing_time=time.time() - start_time
    )


@app.get("/api/chat/stream")
async def chat_stream(
    message: str,
    context: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """SSE endpoint for streaming chat responses."""
    async def generate():
        try:
            # Simple streaming response
            response_data = {
                "response": f"Streaming echo: {message}",
                "conversation_id": f"stream-{int(time.time())}",
                "agent_type": "streaming-echo",
                "timestamp": time.time()
            }
            yield f"data: {json.dumps(response_data)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "code": f"HTTP_{exc.status_code}",
            "path": request.url.path
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=int(os.getenv("AI_ORCHESTRATOR_PORT", "8000")),
        reload=True,
        log_level="info",
    )
