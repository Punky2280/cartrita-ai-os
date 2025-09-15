import sys
import types
import pytest

# Defer heavy imports (SupervisorOrchestrator) until after stubbing structlog.twisted
from cartrita.orchestrator.models.schemas import AgentType
from cartrita.orchestrator.utils.config import get_settings


class _NoopDB:
    async def start(self):  # pragma: no cover - not invoked
        pass

    async def stop(self):  # pragma: no cover - not invoked
        pass


class _NoopCache:
    async def start(self):  # pragma: no cover - not invoked
        pass

    async def stop(self):  # pragma: no cover - not invoked
        pass


class _NoopMetrics:
    async def start(self):  # pragma: no cover - not invoked
        pass

    async def stop(self):  # pragma: no cover - not invoked
        pass


class _FakeCodeAgent:
    async def execute(self, messages, context, metadata):
        return {"response": "Code action result", "metadata": {"test": True}}

    async def get_status(self):  # pragma: no cover - simple accessor
        return {"id": "code", "name": "Code Agent", "type": "code", "status": "active"}

    async def start(self):  # pragma: no cover - not used in test
        pass

    async def stop(self):  # pragma: no cover - not used in test
        pass

    async def health_check(self):  # pragma: no cover - not used in test
        return True


@pytest.mark.asyncio
async def test_supervisor_process_chat_request_basic(monkeypatch):
    """Exercise a full supervisor workflow path with deterministic agent selection.

    The test patches the internal analysis method to force selection of the CODE
    agent and supplies a lightweight fake agent implementation. This avoids any
    external network/model calls while validating that:
      - process_chat_request orchestrates a workflow execution
      - execution_history is populated
      - assistant response produced by the agent is surfaced in ChatResponse
      - agent_type on ChatResponse reflects the chosen agent
    """

    # Provide a lightweight stub for structlog.twisted to avoid importing twisted
    if 'structlog.twisted' not in sys.modules:
        sys.modules['structlog.twisted'] = types.ModuleType('structlog.twisted')

    from cartrita.orchestrator.core.supervisor import SupervisorOrchestrator  # imported after stub

    settings = get_settings()

    orchestrator = SupervisorOrchestrator(
        db_manager=_NoopDB(),
        cache_manager=_NoopCache(),
        metrics_collector=_NoopMetrics(),
        settings=settings,
    )

    # Replace agents with a single deterministic fake agent and rebuild workflow
    orchestrator.agents = {AgentType.CODE: _FakeCodeAgent()}
    orchestrator.workflow = orchestrator._create_workflow_graph()

    async def _fake_analyze(_state):  # noqa: D401 - internal patch
        return {
            "agent_type": AgentType.CODE,
            "confidence": 1.0,
            "reasoning": "deterministic test",
            "context": {"test": True},
        }

    monkeypatch.setattr(orchestrator, "_analyze_request_with_gpt4", _fake_analyze)

    response = await orchestrator.process_chat_request(
        "Write a function to add two numbers", stream=False
    )

    assert response.agent_type == AgentType.CODE
    assert "Code action result" in response.response
    assert response.metadata["execution_history"], "Execution history should not be empty"
    assert any(m.role.value == "assistant" for m in response.messages)
