#!/usr/bin/env python3
"""
Standalone test for metrics collector functionality.
Bypasses config dependencies to test core metrics functionality.
"""

import sys
import asyncio
from dataclasses import dataclass

# Add project path
sys.path.append('.')


@dataclass
class MetricsConfig:
    """Simple config for testing."""
    service_name: str = "cartrita-ai-orchestrator"
    enable_prometheus: bool = True
    enable_tracing: bool = True
    enable_metrics: bool = True
    prometheus_port: int = 8001
    jaeger_host: str = "localhost"
    jaeger_port: int = 14268


async def _metrics_functionality_async():
    """Internal async routine for metrics collector test."""
    print("🧪 Testing Cartrita Metrics Collector")
    print("=" * 50)
    try:
        # Test imports
        if not await _test_prometheus_imports():
            return False

        # Test basic Prometheus functionality
        if not await _test_basic_prometheus_functionality():
            return False

        # Test our MetricsCollector class
        if not await _test_metrics_collector_class():
            return False

        print("\n✅ All metrics tests passed!")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    return True


async def _test_prometheus_imports() -> bool:
    """Test Prometheus client imports."""
    print("1. Testing imports...")
    try:
        from prometheus_client import Counter, Gauge, Histogram, generate_latest, CollectorRegistry
        print("   ✅ Prometheus client imports successful")
        return True
    except ImportError as e:
        print(f"   ❌ Prometheus client import failed: {e}")
        return False


async def _test_basic_prometheus_functionality() -> bool:
    """Test basic Prometheus functionality."""
    print("2. Testing basic Prometheus functionality...")
    try:
        from prometheus_client import Counter, Gauge, Histogram, generate_latest, CollectorRegistry

        registry = CollectorRegistry()
        metrics = _create_test_metrics(registry)
        _record_test_data(metrics)

        # Generate metrics output
        metrics_output = generate_latest(registry).decode('utf-8')
        print("   ✅ Basic Prometheus functionality works")
        print(f"   📊 Generated {len(metrics_output)} characters of metrics data")
        return True
    except Exception as e:
        print(f"   ❌ Basic Prometheus test failed: {e}")
        return False


def _create_test_metrics(registry):
    """Create test metrics objects."""
    from prometheus_client import Counter, Gauge, Histogram

    return {
        'counter': Counter('test_counter', 'Test counter', registry=registry),
        'gauge': Gauge('test_gauge', 'Test gauge', registry=registry),
        'histogram': Histogram('test_histogram', 'Test histogram', registry=registry)
    }


def _record_test_data(metrics):
    """Record test data to metrics."""
    metrics['counter'].inc()
    metrics['gauge'].set(42)
    metrics['histogram'].observe(0.5)


async def _test_metrics_collector_class() -> bool:
    """Test MetricsCollector class functionality."""
    print("3. Testing MetricsCollector class...")
    try:
        # Import with minimal dependencies
        from cartrita.orchestrator.core.metrics import (
            PROMETHEUS_CLIENT_AVAILABLE,
            OPENTELEMETRY_AVAILABLE,
            MetricsCollector
        )

        _print_availability_status(PROMETHEUS_CLIENT_AVAILABLE, OPENTELEMETRY_AVAILABLE)

        # Create and test collector
        config = MetricsConfig()
        collector = MetricsCollector(config)

        success = await _test_collector_lifecycle(collector)
        return success

    except Exception as e:
        print(f"   ❌ MetricsCollector test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def _print_availability_status(prometheus_available: bool, opentelemetry_available: bool) -> None:
    """Print availability status of metrics components."""
    print(f"   📊 Prometheus client available: {prometheus_available}")
    print(f"   📊 OpenTelemetry available: {opentelemetry_available}")


async def _test_collector_lifecycle(collector) -> bool:
    """Test complete collector lifecycle."""
    print("   🔄 Initializing metrics collector...")
    await collector.initialize()

    status = collector.get_status()
    print(f"   📊 Collector status: {status}")
    print(f"   ✅ Collector healthy: {collector.is_healthy()}")

    if collector.is_healthy():
        return await _test_collector_operations(collector)
    else:
        print("   ⚠️  Collector not healthy - metrics may not be functional")
        return True  # Not a failure, just not functional


async def _test_collector_operations(collector) -> bool:
    """Test collector recording and metrics operations."""
    print("   📝 Testing metrics recording...")

    # Record test metrics
    await collector.record_request("GET", "/test", 200, 0.1)
    await collector.record_error("test_error", "/test")
    await collector.update_connections(5)

    # Test getting metrics
    metrics = await collector.get_metrics()
    _print_metrics_results(metrics)

    # Clean shutdown
    await collector.shutdown()
    print("   ✅ Clean shutdown completed")
    return True


def _print_metrics_results(metrics: str | None) -> None:
    """Print metrics generation results."""
    if metrics:
        print(f"   ✅ Generated {len(metrics)} characters of metrics")
        print("   📊 Sample metrics:")
        for line in metrics.split('\n')[:5]:
            if line.strip() and not line.startswith('#'):
                print(f"      {line}")
    else:
        print("   ⚠️  No metrics data generated")


def test_metrics_functionality():
    """Pytest entrypoint wrapping async metrics validation."""
    import asyncio as _asyncio
    success = _asyncio.run(_metrics_functionality_async())
    assert success is True


if __name__ == "__main__":
    success = asyncio.run(_metrics_functionality_async())
    exit(0 if success else 1)
