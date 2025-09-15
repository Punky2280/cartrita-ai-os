"""Guard test: ensure no direct ChatOpenAI instantiation outside the llm_factory.

All production code must obtain ChatOpenAI via create_chat_openai() factory to
centralize configuration (timeouts, retries, telemetry) and enforce policy.
"""
from __future__ import annotations

import re
from pathlib import Path


def test_no_direct_chatopenai_construction():
    repo_root = Path(__file__).resolve().parent.parent
    orchestrator_dir = repo_root / 'services' / 'ai-orchestrator'
    pattern = re.compile(r'ChatOpenAI\s*\(')
    excluded_files = {'llm_factory.py', 'test_guard_no_direct_chatopenai.py'}

    violations: list[str] = []
    for path in orchestrator_dir.rglob('*.py'):
        if path.name in excluded_files:
            continue
        try:
            content = path.read_text(encoding='utf-8')
        except Exception:
            continue
        if pattern.search(content):
            violations.append(str(path.relative_to(repo_root)))

    assert not violations, (
        "Direct ChatOpenAI constructions found in: "
        f"{violations}. Use create_chat_openai() factory instead."
    )
