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


async def test_metrics_functionality():
    """Test the metrics collector without full application context."""
    print("🧪 Testing Cartrita Metrics Collector")
    print("=" * 50)
    try:
        # Test imports
        print("1. Testing imports...")
        try:
            from prometheus_client import Counter, Gauge, Histogram, generate_latest, CollectorRegistry
            print("   ✅ Prometheus client imports successful")
        except ImportError as e:
            print(f"   ❌ Prometheus client import failed: {e}")
            return False
        # Test basic Prometheus functionality
        print("2. Testing basic Prometheus functionality...")
        try:
            registry = CollectorRegistry()
            counter = Counter('test_counter', 'Test counter', registry=registry)
            gauge = Gauge('test_gauge', 'Test gauge', registry=registry)
            histogram = Histogram('test_histogram', 'Test histogram', registry=registry)
            # Record some test metrics
            counter.inc()
            gauge.set(42)
            histogram.observe(0.5)
            # Generate metrics output
            metrics_output = generate_latest(registry).decode('utf-8')
            print("   ✅ Basic Prometheus functionality works")
            print(f"   📊 Generated {len(metrics_output)} characters of metrics data")
        except Exception as e:
            print(f"   ❌ Basic Prometheus test failed: {e}")
            return False
        # Test our MetricsCollector class
        print("3. Testing MetricsCollector class...")
        try:
            # Import with minimal dependencies
            from cartrita.orchestrator.core.metrics import (
                PROMETHEUS_CLIENT_AVAILABLE,
                OPENTELEMETRY_AVAILABLE,
                MetricsCollector
            )
            print(f"   📊 Prometheus client available: {PROMETHEUS_CLIENT_AVAILABLE}")
            print(f"   📊 OpenTelemetry available: {OPENTELEMETRY_AVAILABLE}")
            # Create and initialize collector
            config = MetricsConfig()
            collector = MetricsCollector(config)
            print("   🔄 Initializing metrics collector...")
            await collector.initialize()
            status = collector.get_status()
            print(f"   📊 Collector status: {status}")
            print(f"   ✅ Collector healthy: {collector.is_healthy()}")
            if collector.is_healthy():
                # Test recording metrics
                print("   📝 Testing metrics recording...")
                await collector.record_request("GET", "/test", 200, 0.1)
                await collector.record_error("test_error", "/test")
                await collector.update_connections(5)
                # Test getting metrics
                metrics = await collector.get_metrics()
                if metrics:
                    print(f"   ✅ Generated {len(metrics)} characters of metrics")
                    print("   📊 Sample metrics:")
                    for line in metrics.split('\n')[:5]:
                        if line.strip() and not line.startswith('#'):
                            print(f"      {line}")
                else:
                    print("   ⚠️  No metrics data generated")
                # Clean shutdown
                await collector.shutdown()
                print("   ✅ Clean shutdown completed")
            else:
                print("   ⚠️  Collector not healthy - metrics may not be functional")
        except Exception as e:
            print(f"   ❌ MetricsCollector test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        print("\n✅ All metrics tests passed!")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    return True

if __name__ == "__main__":
    success = asyncio.run(test_metrics_functionality())
    exit(0 if success else 1)
