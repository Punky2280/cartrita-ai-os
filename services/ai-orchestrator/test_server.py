#!/usr/bin/env python3
"""
Minimal FastAPI server for testing CORS configuration and health endpoint.
"""

import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="Cartrita AI OS - Test Server",
    description="Minimal test server for CORS and connectivity testing",
    version="1.0.0",
)

# CORS middleware with updated origins
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


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: float
    services: dict


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Cartrita AI OS Test Server",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": {
            "health": "/health",
            "chat": "/api/chat"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=time.time(),
        services={
            "api": "healthy",
            "cors": "configured"
        }
    )


@app.post("/api/chat")
async def chat(request: dict):
    """Simple chat endpoint for testing."""
    return {
        "response": f"Echo: {request.get('message', 'No message')}",
        "status": "success",
        "timestamp": time.time()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
