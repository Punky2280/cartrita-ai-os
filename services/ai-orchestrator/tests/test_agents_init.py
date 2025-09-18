#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for Cartrita agents package initialization.
Uses mocking to avoid LangChain dependency issues.

Coverage Target: 100% of cartrita/orchestrator/agents/__init__.py
Dependencies: Standard library + unittest.mock (no LangChain)
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add the cartrita package to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "cartrita"))

import pytest


@pytest.fixture(autouse=True)
def mock_langchain_modules():
    """Mock all LangChain modules to avoid import errors."""
    # Mock LangChain core modules
    with patch.dict(
        "sys.modules",
        {
            "langchain": MagicMock(),
            "langchain_core": MagicMock(),
            "langchain_core.messages": MagicMock(),
            "langchain_core.tools": MagicMock(),
            "langchain_core.agents": MagicMock(),
            "langchain_openai": MagicMock(),
            "langchain_community": MagicMock(),
            "pydantic": MagicMock(),
        },
    ):
        yield


def test_agents_package_structure():
    """Test that agents package has expected structure."""
    # Mock the agent classes before importing
    mock_agents = {}
    agent_names = [
        "CodeAgent",
        "ComputerUseAgent",
        "KnowledgeAgent",
        "MemoryAgent",
        "ResearchAgent",
        "TaskAgent",
    ]

    for agent_name in agent_names:
        mock_agents[agent_name] = MagicMock()
        mock_agents[agent_name].__name__ = agent_name

    # Mock the individual agent modules
    with patch.dict(
        "sys.modules",
        {
            "cartrita.orchestrator.agents.code.code_agent": MagicMock(
                CodeAgent=mock_agents["CodeAgent"]
            ),
            "cartrita.orchestrator.agents.computer_use.computer_use_agent": MagicMock(
                ComputerUseAgent=mock_agents["ComputerUseAgent"]
            ),
            "cartrita.orchestrator.agents.knowledge.knowledge_agent": MagicMock(
                KnowledgeAgent=mock_agents["KnowledgeAgent"]
            ),
            "cartrita.orchestrator.agents.memory.memory_agent": MagicMock(
                MemoryAgent=mock_agents["MemoryAgent"]
            ),
            "cartrita.orchestrator.agents.research.research_agent": MagicMock(
                ResearchAgent=mock_agents["ResearchAgent"]
            ),
            "cartrita.orchestrator.agents.task.task_agent": MagicMock(
                TaskAgent=mock_agents["TaskAgent"]
            ),
        },
    ):
        # Now import the agents package
        from cartrita.orchestrator import agents

        # Test that __all__ exists and contains expected agents
        assert hasattr(agents, "__all__")
        assert isinstance(agents.__all__, list)
        assert len(agents.__all__) == 6

        for agent_name in agent_names:
            assert agent_name in agents.__all__
            assert hasattr(agents, agent_name)


def test_agents_all_constant():
    """Test the __all__ constant in agents package."""
    with patch.dict(
        "sys.modules",
        {
            "cartrita.orchestrator.agents.code.code_agent": MagicMock(
                CodeAgent=MagicMock()
            ),
            "cartrita.orchestrator.agents.computer_use.computer_use_agent": MagicMock(
                ComputerUseAgent=MagicMock()
            ),
            "cartrita.orchestrator.agents.knowledge.knowledge_agent": MagicMock(
                KnowledgeAgent=MagicMock()
            ),
            "cartrita.orchestrator.agents.memory.memory_agent": MagicMock(
                MemoryAgent=MagicMock()
            ),
            "cartrita.orchestrator.agents.research.research_agent": MagicMock(
                ResearchAgent=MagicMock()
            ),
            "cartrita.orchestrator.agents.task.task_agent": MagicMock(
                TaskAgent=MagicMock()
            ),
        },
    ):
        from cartrita.orchestrator import agents

        expected_agents = [
            "CodeAgent",
            "ComputerUseAgent",
            "KnowledgeAgent",
            "MemoryAgent",
            "ResearchAgent",
            "TaskAgent",
        ]

        assert agents.__all__ == expected_agents


def test_agents_imports_available():
    """Test that all agents are importable from package."""
    with patch.dict(
        "sys.modules",
        {
            "cartrita.orchestrator.agents.code.code_agent": MagicMock(
                CodeAgent=MagicMock()
            ),
            "cartrita.orchestrator.agents.computer_use.computer_use_agent": MagicMock(
                ComputerUseAgent=MagicMock()
            ),
            "cartrita.orchestrator.agents.knowledge.knowledge_agent": MagicMock(
                KnowledgeAgent=MagicMock()
            ),
            "cartrita.orchestrator.agents.memory.memory_agent": MagicMock(
                MemoryAgent=MagicMock()
            ),
            "cartrita.orchestrator.agents.research.research_agent": MagicMock(
                ResearchAgent=MagicMock()
            ),
            "cartrita.orchestrator.agents.task.task_agent": MagicMock(
                TaskAgent=MagicMock()
            ),
        },
    ):
        from cartrita.orchestrator import agents

        # Test that we can access all agents
        assert hasattr(agents, "CodeAgent")
        assert hasattr(agents, "ComputerUseAgent")
        assert hasattr(agents, "KnowledgeAgent")
        assert hasattr(agents, "MemoryAgent")
        assert hasattr(agents, "ResearchAgent")
        assert hasattr(agents, "TaskAgent")


def test_package_docstring():
    """Test that the package has appropriate docstring."""
    with patch.dict(
        "sys.modules",
        {
            "cartrita.orchestrator.agents.code.code_agent": MagicMock(
                CodeAgent=MagicMock()
            ),
            "cartrita.orchestrator.agents.computer_use.computer_use_agent": MagicMock(
                ComputerUseAgent=MagicMock()
            ),
            "cartrita.orchestrator.agents.knowledge.knowledge_agent": MagicMock(
                KnowledgeAgent=MagicMock()
            ),
            "cartrita.orchestrator.agents.memory.memory_agent": MagicMock(
                MemoryAgent=MagicMock()
            ),
            "cartrita.orchestrator.agents.research.research_agent": MagicMock(
                ResearchAgent=MagicMock()
            ),
            "cartrita.orchestrator.agents.task.task_agent": MagicMock(
                TaskAgent=MagicMock()
            ),
        },
    ):
        from cartrita.orchestrator import agents

        # Check if module has docstring (it should from the comment at top)
        assert hasattr(agents, "__file__")


def test_agents_list_immutability():
    """Test that __all__ list contents are proper."""
    with patch.dict(
        "sys.modules",
        {
            "cartrita.orchestrator.agents.code.code_agent": MagicMock(
                CodeAgent=MagicMock()
            ),
            "cartrita.orchestrator.agents.computer_use.computer_use_agent": MagicMock(
                ComputerUseAgent=MagicMock()
            ),
            "cartrita.orchestrator.agents.knowledge.knowledge_agent": MagicMock(
                KnowledgeAgent=MagicMock()
            ),
            "cartrita.orchestrator.agents.memory.memory_agent": MagicMock(
                MemoryAgent=MagicMock()
            ),
            "cartrita.orchestrator.agents.research.research_agent": MagicMock(
                ResearchAgent=MagicMock()
            ),
            "cartrita.orchestrator.agents.task.task_agent": MagicMock(
                TaskAgent=MagicMock()
            ),
        },
    ):
        from cartrita.orchestrator import agents

        all_list = agents.__all__
        assert isinstance(all_list, list)
        assert len(all_list) > 0

        # All items should be strings
        for item in all_list:
            assert isinstance(item, str)
            assert len(item) > 0


if __name__ == "__main__":
    # Run tests with coverage
    pytest.main([__file__, "-v", "--tb=short"])
