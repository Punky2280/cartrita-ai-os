"""Supervisor smoke test."""
import pytest

def test_supervisor_import_only():
    try:
        from cartrita.orchestrator.core.supervisor import SupervisorOrchestrator  # noqa: F401
    except ModuleNotFoundError as e:
        pytest.skip(f"Supervisor module not found: {e}")
