#!/usr/bin/env python3
"""
Minimal FastAPI server test with just the metrics endpoint.
Tests if the 503 error is resolved.
"""

import asyncio
import sys
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response

# Add project path
sys.path.append('.')

# Global metrics collector
metrics_collector = None


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Minimal lifespan for testing metrics only."""
    global metrics_collector
    
    print("🚀 Starting minimal metrics test server...")
    
    try:
        # Initialize only metrics collector
        from cartrita.orchestrator.core.metrics import MetricsCollector, MetricsConfig
        metrics_config = MetricsConfig(
            service_name="cartrita-ai-orchestrator-test",
            enable_prometheus=True,
            enable_tracing=False,  # Disable tracing for simplicity
            enable_metrics=True
        )
        metrics_collector = MetricsCollector(metrics_config)
        await metrics_collector.initialize()
        
        if metrics_collector.is_healthy():
            print("✅ Metrics collector initialized successfully")
        else:
            print("⚠️ Metrics collector not healthy but will handle gracefully")
        
        yield
        
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        raise
    finally:
        print("🛑 Shutting down...")
        if metrics_collector:
            await metrics_collector.shutdown()


# Create minimal FastAPI app
app = FastAPI(
    title="Cartrita Metrics Test",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Cartrita Metrics Test Server", "status": "running"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint with proper error handling."""
    if not metrics_collector:
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
                    "service": "cartrita-ai-orchestrator-test",
                    "status": "healthy",
                    "message": "Metrics collection is available but no data collected yet",
                    "collector_status": metrics_collector.get_status()
                }
            )
        
        # Return Prometheus format metrics
        return Response(
            content=metrics_data,
            media_type="text/plain; version=0.0.4; charset=utf-8"
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Metrics retrieval failed",
                "message": str(e),
                "status": "internal_error"
            }
        )


@app.get("/test")
async def test_endpoint():
    """Test endpoint to generate some metrics."""
    start_time = time.time()
    
    # Record test metrics
    if metrics_collector and metrics_collector.is_healthy():
        await asyncio.sleep(0.1)  # Simulate some work
        duration = time.time() - start_time
        await metrics_collector.record_request("GET", "/test", 200, duration)
    
    return {"message": "Test endpoint", "timestamp": time.time()}


if __name__ == "__main__":
    import uvicorn
    print("🌟 Starting Cartrita Metrics Test Server...")
    print("📊 Metrics endpoint: http://localhost:8000/metrics")
    print("🧪 Test endpoint: http://localhost:8000/test")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
