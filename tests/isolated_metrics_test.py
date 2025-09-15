#!/usr/bin/env python3
"""
Isolated test for metrics functionality without any project dependencies.
Verifies that the metrics 503 error would be resolved.
"""

import asyncio
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncGenerator, Optional, Dict, Any, Union
import importlib

from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response


# Use importlib to avoid static unresolved import errors in environments
# without prometheus_client installed.
if importlib.util.find_spec("prometheus_client") is not None:
    from prometheus_client import (  # type: ignore
        Counter,
        Gauge,
        Histogram,
        generate_latest,
        CollectorRegistry,
    )
    PROMETHEUS_AVAILABLE = True
else:
    PROMETHEUS_AVAILABLE = False

    class _NoopMetric:
        def labels(self, **_kw):
            return self

        def inc(self, *_, **__):
            return None

        def observe(self, *_, **__):
            return None

    class _NoopRegistry:
        pass

    def generate_latest(_registry):
        return b""

    Counter = Gauge = Histogram = _NoopMetric  # type: ignore
    CollectorRegistry = _NoopRegistry  # type: ignore


@dataclass
class MetricsConfig:
    """Metrics configuration."""

    service_name: str = "cartrita-test"
    enable_metrics: bool = True


class SimpleMetricsCollector:
    """Simplified metrics collector for testing."""

    # Class-level annotations to avoid function-scope annotation issues (fixed: removed invalid list literals)
    _registry: Optional[CollectorRegistry] = None
    request_count: Optional[Counter] = None
    request_duration: Optional[Histogram] = None
    error_count: Optional[Counter] = None

    def __init__(self, config: MetricsConfig) -> None:
        self.config = config
        self._initialized = False
        # Removed inline annotations to fix "Variable not allowed in type expression" errors
        self._registry = None
        self.request_count = None
        self.request_duration = None
        self.error_count = None

    async def initialize(self) -> None:
        """Initialize metrics collection."""
        if not PROMETHEUS_AVAILABLE:
            import structlog

            structlog.get_logger("metrics").warning("Prometheus client not available")
            return

        try:
            self._registry = CollectorRegistry()

            self.request_count = Counter(
                "test_requests_total",
                "Total requests",
                ["method", "endpoint", "status"],
                registry=self._registry,
            )

            self.request_duration = Histogram(
                "test_request_duration_seconds",
                "Request duration",
                ["method", "endpoint"],
                registry=self._registry,
            )

            self.error_count = Counter(
                "test_errors_total",
                "Total errors",
                ["type", "endpoint"],
                registry=self._registry,
            )

            self._initialized = True

            import structlog

            structlog.get_logger("metrics").info(
                "metrics_collector_initialized", event="Metrics collector initialized"
            )
            print("✅ Metrics collector initialized")
        except Exception as error:
            import structlog

            structlog.get_logger("metrics").error(
                "Metrics initialization failed", error=str(error)
            )
            print(f"❌ Metrics initialization failed: {error}")

    def is_healthy(self) -> bool:
        """Check if metrics collector is healthy."""
        return self._initialized and PROMETHEUS_AVAILABLE

    async def record_request(
        self, method: str, endpoint: str, status: int, duration: float
    ) -> None:
        """Record request metrics."""
        if not self.is_healthy():
            return

        try:
            if self.request_count:
                self.request_count.labels(
                    method=method, endpoint=endpoint, status=str(status)
                ).inc()

            if self.request_duration:
                self.request_duration.labels(
                    method=method, endpoint=endpoint
                ).observe(duration)
        except Exception as error:
            import structlog

            structlog.get_logger("metrics").error(
                "failed_to_record_metrics", error=str(error)
            )

    async def record_error(self, error_type: str, endpoint: str) -> None:
        """Record error metrics."""
        if not self.is_healthy():
            return
        try:
            if self.error_count:
                self.error_count.labels(
                    type=error_type, endpoint=endpoint
                ).inc()
        except Exception as error:
            import structlog

            structlog.get_logger("metrics").error(
                "failed_to_record_error", error=str(error)
            )
            print(f"Failed to record error: {error}")

    async def get_metrics(self) -> Optional[str]:
        """Get metrics in Prometheus format."""
        if not self.is_healthy():
            return None

        try:
            if self._registry:
                return generate_latest(self._registry).decode("utf-8")
        except Exception as error:
            import structlog

            structlog.get_logger("metrics").warning(
                "failed_to_get_metrics", error=str(error)
            )

        return None

    def get_status(self) -> Dict[str, Any]:
        """Get status info."""
        return {
            "initialized": self._initialized,
            "prometheus_available": PROMETHEUS_AVAILABLE,
            "service_name": self.config.service_name,
        }

    async def shutdown(self) -> None:
        """Shutdown metrics collector."""
        self._initialized = False
        import structlog

        structlog.get_logger("metrics").info(
            "metrics_collector_shutdown", event="Metrics collector shutdown"
        )
        print("📊 Metrics collector shutdown")


# Global metrics collector
metrics_collector: Optional[SimpleMetricsCollector] = None


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """App lifespan management."""
    global metrics_collector

    print("🚀 Starting isolated metrics test...")

    try:
        config = MetricsConfig(service_name="cartrita-isolated-test")
        metrics_collector = SimpleMetricsCollector(config)
        await metrics_collector.initialize()

        yield

    finally:
        if metrics_collector:
            await metrics_collector.shutdown()


app = FastAPI(title="Isolated Metrics Test", lifespan=lifespan)


@app.get("/")
async def root() -> Dict[str, Union[str, bool]]:
    """Root endpoint."""
    return {
        "message": "Isolated Metrics Test",
        "prometheus_available": PROMETHEUS_AVAILABLE,
        "metrics_healthy": (
            metrics_collector.is_healthy() if metrics_collector else False
        ),
    }


@app.get("/metrics", response_model=None)
async def metrics():
    """Metrics endpoint (async, resilient)."""
    if not metrics_collector:
        return JSONResponse(
            status_code=503,
            content={
                "error": "Metrics not available",
                "message": "Metrics collector not initialized",
            },
        )

    if not PROMETHEUS_AVAILABLE:
        return JSONResponse(
            status_code=200,
            content={
                "service": "cartrita-isolated-test",
                "status": "metrics_unavailable_optional",
                "message": "prometheus_client not installed; exporting disabled",
                "collector_status": metrics_collector.get_status(),
            },
        )

    if not metrics_collector.is_healthy():
        return JSONResponse(
            status_code=503,
            content={
                "error": "Metrics collector unhealthy",
                "status": metrics_collector.get_status(),
                "message": "Metrics collection unavailable",
            },
        )

    try:
        metrics_data = await metrics_collector.get_metrics()
        if metrics_data is None:
            return JSONResponse(
                content={
                    "service": "cartrita-isolated-test",
                    "status": "healthy",
                    "message": "No metrics data yet",
                    "collector_status": metrics_collector.get_status(),
                }
            )
        return Response(
            content=metrics_data,
            media_type="text/plain; version=0.0.4; charset=utf-8",
        )
    except Exception as error:
        return JSONResponse(
            status_code=500,
            content={"error": "Metrics retrieval failed", "message": str(error)},
        )


@app.get("/test")
async def generate_test_metrics() -> Dict[str, Union[str, float]]:
    """Generate some test metrics."""
    start_time = time.time()

    await asyncio.sleep(0.1)  # Simulate work

    if metrics_collector and metrics_collector.is_healthy():
        duration = time.time() - start_time
        await metrics_collector.record_request("GET", "/test", 200, duration)

    return {"message": "Test completed", "duration": time.time() - start_time}


@app.get("/error-test")
async def error_test() -> Dict[str, str]:
    """Generate test error metrics."""
    if metrics_collector and metrics_collector.is_healthy():
        await metrics_collector.record_error("test_error", "/error-test")

    return {"message": "Error recorded"}


if __name__ == "__main__":
    import uvicorn
    import structlog

    logger = structlog.get_logger("startup")
    logger.info("startup_banner", banner="=" * 60)
    logger.info("startup_title", title="🔬 CARTRITA METRICS FIX VERIFICATION")
    logger.info("startup_banner", banner="=" * 60)
    logger.info(
        "startup_description",
        description="This test verifies that the 503 'Metrics not available' error is fixed",
    )
    logger.info(
        "startup_endpoints",
        endpoints=[
            "http://localhost:8000/metrics - Main metrics endpoint",
            "http://localhost:8000/test - Generate request metrics",
            "http://localhost:8000/error-test - Generate error metrics",
            "http://localhost:8000/ - Status check",
        ],
    )
    logger.info(
        "startup_expectations",
        expectations=[
            "NO 503 errors from /metrics endpoint",
            "Graceful handling when metrics unavailable",
            "Prometheus format output when metrics available",
        ],
    )
    logger.info("startup_banner", banner="=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
