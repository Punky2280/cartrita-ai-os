#!/usr/bin/env python3
"""
Smoke test for frontend-backend communication.
Tests basic chat functionality without full dependencies.
"""

import asyncio
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, List
import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field


# Models for testing
class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role (user/assistant)")
    content: str = Field(..., description="Message content")
    timestamp: float = Field(default_factory=time.time)


class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    conversation_id: str = Field(default="test-conversation")
    stream: bool = Field(default=False)


class ChatResponse(BaseModel):
    message: str = Field(..., description="Assistant response")
    conversation_id: str = Field(..., description="Conversation ID")
    agent_used: str = Field(default="supervisor")
    timestamp: float = Field(default_factory=time.time)


# Simple in-memory storage for testing
conversations: Dict[str, List[ChatMessage]] = {}


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Simple lifespan for testing."""
    print("🚀 Starting Cartrita Smoke Test Server...")
    yield
    print("🛑 Shutting down smoke test server...")


# Create FastAPI app
app = FastAPI(
    title="Cartrita Smoke Test API",
    description="Simple backend for frontend-backend communication testing",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Cartrita Smoke Test API",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "chat": "/api/chat",
            "chat_stream": "/api/chat/stream",
            "conversations": "/api/conversations"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": time.time(),
        "services": {
            "api": "healthy",
            "chat": "healthy"
        }
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Simple chat endpoint for testing."""
    try:
        # Add user message to conversation
        if request.conversation_id not in conversations:
            conversations[request.conversation_id] = []
        
        user_message = ChatMessage(
            role="user",
            content=request.message,
            timestamp=time.time()
        )
        conversations[request.conversation_id].append(user_message)
        
        # Generate simple response
        response_content = f"Echo: {request.message} (processed by smoke test server)"
        
        assistant_message = ChatMessage(
            role="assistant",
            content=response_content,
            timestamp=time.time()
        )
        conversations[request.conversation_id].append(assistant_message)
        
        return ChatResponse(
            message=response_content,
            conversation_id=request.conversation_id,
            agent_used="smoke_test_agent",
            timestamp=time.time()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")


async def generate_chat_stream(request: ChatRequest):
    """Generate streaming chat response."""
    # Add user message
    if request.conversation_id not in conversations:
        conversations[request.conversation_id] = []
    
    user_message = ChatMessage(
        role="user",
        content=request.message,
        timestamp=time.time()
    )
    conversations[request.conversation_id].append(user_message)
    
    # Send start event
    yield f"data: {json.dumps({'type': 'start', 'conversation_id': request.conversation_id})}\n\n"
    
    # Stream response tokens
    response_text = f"Streaming response to: {request.message}"
    for i, word in enumerate(response_text.split()):
        await asyncio.sleep(0.1)  # Simulate processing delay
        token_data = {
            'type': 'token',
            'content': word + ' ',
            'index': i
        }
        yield f"data: {json.dumps(token_data)}\n\n"
    
    # Send completion event
    completion_data = {
        'type': 'done',
        'conversation_id': request.conversation_id,
        'agent_used': 'smoke_test_streaming_agent',
        'timestamp': time.time()
    }
    yield f"data: {json.dumps(completion_data)}\n\n"
    
    # Add assistant message to conversation
    assistant_message = ChatMessage(
        role="assistant",
        content=response_text,
        timestamp=time.time()
    )
    conversations[request.conversation_id].append(assistant_message)


@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint for testing."""
    return StreamingResponse(
        generate_chat_stream(request),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/api/conversations")
async def get_conversations():
    """Get all conversations for testing."""
    return {
        "conversations": conversations,
        "total": len(conversations)
    }


@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get specific conversation."""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "conversation_id": conversation_id,
        "messages": conversations[conversation_id],
        "message_count": len(conversations[conversation_id])
    }


if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "=" * 60)
    print("🧪 CARTRITA FRONTEND-BACKEND SMOKE TEST")
    print("=" * 60)
    print("This server provides a simple backend for testing frontend communication")
    print("\n📡 API Endpoints:")
    print("  • http://localhost:8003/ - API status")
    print("  • http://localhost:8003/health - Health check")
    print("  • http://localhost:8003/api/chat - Chat endpoint")
    print("  • http://localhost:8003/api/chat/stream - Streaming chat")
    print("  • http://localhost:8003/api/conversations - All conversations")
    print("\n🎯 To test frontend integration:")
    print("  1. Update frontend API base URL to http://localhost:8003")
    print("  2. Start frontend: npm run dev")
    print("  3. Test chat functionality in browser")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8003, log_level="info")
