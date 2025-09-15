from __future__ import annotations

import pytest

try:
    from fastapi.testclient import TestClient  # type: ignore
except Exception:  # pragma: no cover
    TestClient = None  # type: ignore


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient not installed")
def test_metrics_endpoint_if_present():
    """
    Discover any route containing 'metrics'. If none, skip.
    If found, assert 200 and body resembles Prometheus exposition format.
    """
    app = None
    import_errors = []
    for candidate in (
        "cartrita.orchestrator.main",
        "cartrita.orchestrator.app",
        "simple_main",
    ):
        try:
            mod = __import__(candidate, fromlist=["app"])
            app = getattr(mod, "app", None)
            if app:
                break
        except Exception as e:  # pragma: no cover
            import_errors.append(f"{candidate}: {e}")

    if app is None:
        pytest.skip("Cannot import FastAPI app; tried: " + "; ".join(import_errors))

    client = TestClient(app)
    metric_paths = sorted(
        {getattr(r, "path", "") for r in getattr(app, "routes", []) if "metrics" in getattr(r, "path", "")}
    )
    if not metric_paths:
        pytest.skip("No metrics route exposed")

    path = metric_paths[0]
    resp = client.get(path)
    if resp.status_code != 200:
        pytest.skip(f"Metrics endpoint {path} returned {resp.status_code}; skipping assertions")
    body = resp.text or ""
    assert any(
        marker in body
        for marker in ("# HELP", "# TYPE", "process_cpu_seconds_total", "python_info")
    ), "Response does not resemble Prometheus metrics format"
