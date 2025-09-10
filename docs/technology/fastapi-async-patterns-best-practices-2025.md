# FastAPI Async Patterns and Best Practices (2025)

## Overview
This document outlines modern FastAPI async patterns, Python asyncio best practices, and performance optimization techniques as of 2025.

## Core Async Principles

### When to Use Async vs Sync

#### Use Async For:
- **I/O-bound operations**: Database queries, HTTP requests, file operations
- **Network calls**: External API integrations
- **Database operations**: Using async drivers like asyncpg, databases
- **High-concurrency scenarios**: Multiple concurrent requests

#### Use Sync For:
- **CPU-bound operations**: Data processing, image manipulation, complex calculations
- **Simple operations**: Where concurrency won't improve performance
- **Legacy integrations**: When working with sync-only libraries

### Performance Metrics (2025)
- FastAPI with async can handle **3,000+ requests per second**
- Asyncio matches Node.js and Go performance for I/O operations
- Ideal for real-time applications and high-load systems

## Modern Async Patterns

### Basic Async Endpoint Pattern
```python
from fastapi import FastAPI
import asyncio
import httpx

app = FastAPI()

@app.get("/async-endpoint")
async def async_endpoint():
    # Good: Non-blocking I/O operation
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/data")
        return response.json()
```

### Database Integration Pattern
```python
import asyncpg
from fastapi import Depends

async def get_db_pool():
    return await asyncpg.create_pool(
        "postgresql://user:password@localhost/db"
    )

@app.get("/users/{user_id}")
async def get_user(user_id: int, pool = Depends(get_db_pool)):
    async with pool.acquire() as conn:
        result = await conn.fetchrow(
            "SELECT * FROM users WHERE id = $1", user_id
        )
        return dict(result) if result else None
```

### CPU-Bound Task Pattern
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Thread pool for CPU-bound tasks
thread_pool = ThreadPoolExecutor(max_workers=4)

def cpu_intensive_task(data):
    # Heavy computation here
    result = complex_calculation(data)
    return result

@app.post("/process-data")
async def process_data(data: dict):
    loop = asyncio.get_event_loop()
    
    # Offload CPU-bound work to thread pool
    result = await loop.run_in_executor(
        thread_pool, 
        cpu_intensive_task, 
        data
    )
    
    return {"result": result}
```

## Advanced Patterns

### Streaming Response Pattern
```python
from fastapi.responses import StreamingResponse
import json

async def generate_data():
    for i in range(1000):
        data = {"item": i, "value": f"data_{i}"}
        yield f"data: {json.dumps(data)}\n\n"
        await asyncio.sleep(0.01)  # Simulate processing time

@app.get("/stream")
async def stream_data():
    return StreamingResponse(
        generate_data(),
        media_type="text/plain"
    )
```

### WebSocket Pattern
```python
from fastapi import WebSocket, WebSocketDisconnect

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Message: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

### Background Tasks Pattern
```python
from fastapi import BackgroundTasks
import smtplib

async def send_email(email: str, message: str):
    # Simulate email sending
    await asyncio.sleep(2)
    print(f"Email sent to {email}: {message}")

@app.post("/send-notification")
async def send_notification(
    email: str, 
    message: str, 
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(send_email, email, message)
    return {"message": "Email will be sent in background"}
```

## Error Handling and Resilience

### Async Exception Handling
```python
from fastapi import HTTPException
import asyncio

@app.get("/resilient-endpoint")
async def resilient_endpoint():
    try:
        # Multiple async operations with timeout
        async with asyncio.timeout(5.0):
            result1 = await external_api_call_1()
            result2 = await external_api_call_2()
            
        return {"result1": result1, "result2": result2}
        
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=408, 
            detail="Request timeout"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Internal error: {str(e)}"
        )
```

### Retry Pattern with Exponential Backoff
```python
import asyncio
from typing import Optional

async def retry_with_backoff(
    func,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0
):
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            
            delay = min(base_delay * (2 ** attempt), max_delay)
            await asyncio.sleep(delay)
```

## Performance Optimization

### Connection Pooling
```python
import aioredis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

class DatabaseManager:
    def __init__(self):
        self.engine = create_async_engine(
            "postgresql+asyncpg://user:pass@localhost/db",
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True
        )
        self.redis_pool = None

    async def init_redis(self):
        self.redis_pool = aioredis.ConnectionPool.from_url(
            "redis://localhost",
            max_connections=10
        )

    async def get_session(self) -> AsyncSession:
        async with AsyncSession(self.engine) as session:
            yield session

db_manager = DatabaseManager()

@app.on_event("startup")
async def startup():
    await db_manager.init_redis()
```

### Caching Pattern
```python
from functools import wraps
import pickle
import hashlib

def async_cache(expire_time: int = 300):
    def decorator(func):
        cache = {}
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key
            key_data = f"{func.__name__}:{args}:{kwargs}"
            cache_key = hashlib.md5(key_data.encode()).hexdigest()
            
            # Check cache
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if time.time() - timestamp < expire_time:
                    return result
            
            # Execute function
            result = await func(*args, **kwargs)
            cache[cache_key] = (result, time.time())
            
            return result
        return wrapper
    return decorator

@async_cache(expire_time=600)
async def expensive_computation(param: str):
    await asyncio.sleep(2)  # Simulate expensive operation
    return f"Result for {param}"
```

## Testing Patterns

### Async Test Setup
```python
import pytest
import httpx
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
async def async_client():
    async with httpx.AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_async_endpoint(async_client):
    response = await async_client.get("/async-endpoint")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
```

### Mock Async Dependencies
```python
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_with_mock_db():
    mock_db = AsyncMock()
    mock_db.fetchrow.return_value = {"id": 1, "name": "Test"}
    
    app.dependency_overrides[get_db_pool] = lambda: mock_db
    
    async with httpx.AsyncClient(app=app) as client:
        response = await client.get("/users/1")
        assert response.json()["name"] == "Test"
```

## Deployment and Production Patterns

### Server Configuration
```python
# production.py
import uvicorn
from fastapi import FastAPI

app = FastAPI(title="Production API")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        workers=4,  # CPU cores
        loop="uvloop",  # Performance improvement
        http="httptools",  # Performance improvement
        access_log=False,  # Disable in production
        server_header=False,  # Security
    )
```

### Health Checks and Monitoring
```python
import psutil
import time

start_time = time.time()

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "uptime": time.time() - start_time,
        "memory_usage": psutil.virtual_memory().percent,
        "cpu_usage": psutil.cpu_percent(),
    }

@app.get("/ready")
async def readiness_check():
    # Check database connection
    try:
        async with db_manager.get_session() as session:
            await session.execute("SELECT 1")
        return {"status": "ready"}
    except Exception:
        raise HTTPException(status_code=503, detail="Database not ready")
```

## Best Practices Summary

### Do's
1. **Use async for I/O-bound operations**
2. **Implement proper connection pooling**
3. **Handle exceptions gracefully**
4. **Use background tasks for long-running operations**
5. **Implement caching for expensive operations**
6. **Set appropriate timeouts**
7. **Monitor performance metrics**

### Don'ts
1. **Don't use async for CPU-bound tasks without thread pools**
2. **Don't block the event loop with synchronous operations**
3. **Don't ignore proper error handling**
4. **Don't skip connection limits and pooling**
5. **Don't forget to close resources properly**

## Performance Monitoring

### Key Metrics to Track
- Response time percentiles (p50, p95, p99)
- Request throughput (requests/second)
- Error rates
- Memory usage
- Connection pool utilization
- Database query performance

### Tools and Integration
- **Prometheus**: Metrics collection
- **Grafana**: Visualization
- **Sentry**: Error tracking
- **OpenTelemetry**: Distributed tracing
- **Datadog**: Application performance monitoring

This comprehensive guide provides the foundation for building high-performance, scalable FastAPI applications using modern async patterns and best practices for 2025.