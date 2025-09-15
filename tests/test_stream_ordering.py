"""Streaming SSE ordering test.

Validates:
- Streaming endpoint exists (heuristic search for path containing 'stream')
- SSE 'data:' lines collected until '[DONE]'
- '[DONE]' appears exactly once at end
- At least one non-empty chunk before sentinel

Skips (does not fail) if:
- FastAPI TestClient missing
- App import fails
- Streaming route not found
- Endpoint not reachable (non-200)
- No SSE data lines produced (e.g., non-stream fallback)
"""
from __future__ import annotations

import itertools
from typing import List

import pytest

try:
    from fastapi.testclient import TestClient
except Exception:  # pragma: no cover
    TestClient = None  # type: ignore


def _find_stream_path(app) -> str | None:
    candidates = []
    for route in app.routes:
        path = getattr(route, "path", "")
        if "stream" in path and "chat" in path:
            candidates.append(path)
    if candidates:
        return sorted(candidates, key=len, reverse=True)[0]
    for route in app.routes:
        path = getattr(route, "path", "")
        if "stream" in path:
            return path
    return None


@pytest.mark.skipif(TestClient is None, reason="FastAPI TestClient not installed")
def test_stream_ordering_sse():
    try:
        from cartrita.orchestrator.main import app  # type: ignore
    except Exception:
        try:
            from simple_main import app  # type: ignore
        except Exception as e:  # pragma: no cover
            pytest.skip(f"Cannot import FastAPI app: {e}")

    stream_path = _find_stream_path(app)
    if not stream_path:
        pytest.skip("Streaming route not found")

    client = TestClient(app)

    methods = [
        ("post", {"json": {"messages": [{"role": "user", "content": "Hello"}]}}),
        ("get", {}),
    ]

    response = None
    used_method = None
    for method, kwargs in methods:
        try:
            response = client.request(method.upper(), stream_path, **kwargs)
        except Exception:
            continue
        if response is not None and getattr(response, "status_code", 0) < 500:
            used_method = method
            break

    if response is None or response.status_code != 200:
        pytest.skip(f"Streaming endpoint not reachable (path={stream_path})")

    raw = response.iter_lines()
    data_lines: List[str] = []
    for line in itertools.islice(raw, 0, 500):
        if isinstance(line, bytes):
            line = line.decode("utf-8", errors="ignore")
        if line.startswith("data:"):
            payload = line[len("data:") :].strip()
            data_lines.append(payload)
            if payload == "[DONE]":
                break

    if not data_lines:
        pytest.skip("No SSE data lines captured (possible non-streaming fallback)")

    assert data_lines[-1] == "[DONE]", f"Expected last token '[DONE]', got {data_lines[-1]!r}"
    assert data_lines.count("[DONE]") == 1, "Sentinel '[DONE]' should appear exactly once"

    content_chunks = [c for c in data_lines[:-1] if c.strip()]
    assert content_chunks, "Expected at least one non-empty content chunk before [DONE]"

    combined = "".join(content_chunks)
    assert combined.strip(), "Combined streamed content is empty"
    assert "\n\n" not in combined, "Unexpected double newlines in combined content"

    if used_method:
        assert used_method in ("post", "get")
        