"""Tracks deprecated Pydantic orm_mode usage (xfail until migration complete)."""
from pathlib import Path
import re
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TARGET_DIR = REPO_ROOT / "services" / "ai-orchestrator" / "cartrita"
PATTERN = re.compile(r"orm_mode\s*=")

@pytest.mark.xfail(reason="Migration in progress; tracking remaining orm_mode usages", strict=False)
def test_no_orm_mode_usage():
    if not TARGET_DIR.exists():
        pytest.skip("Target directory missing.")
    hits = []
    for py_file in TARGET_DIR.rglob("*.py"):
        try:
            text = py_file.read_text(encoding="utf-8")
        except Exception:
            continue
        if PATTERN.search(text):
            hits.append(str(py_file.relative_to(REPO_ROOT)))
    assert not hits, f"Deprecated orm_mode usage remains in: {hits}"
