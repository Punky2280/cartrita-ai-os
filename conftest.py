import sys
from pathlib import Path
import os
import pytest

# Provide a lightweight structlog stub for Python 3.13 test environment if the
# real structlog import would trigger twisted/zope incompatibility. This keeps
# production code unchanged while preventing ImportError during test collection.
if "structlog" not in sys.modules:  # pragma: no cover - environment guard
    try:
        import structlog  # type: ignore
    except Exception:  # pragma: no cover - fallback stub
        import types

        stub = types.ModuleType("structlog")

        class _Logger:
            def info(self, *a, **k):
                pass

            def error(self, *a, **k):
                pass

            def debug(self, *a, **k):
                pass

            def warning(self, *a, **k):
                pass

            def bind(self, *a, **k):  # chaining compatibility
                return self

        def get_logger(*a, **k):  # noqa: D401
            return _Logger()

        stub.get_logger = get_logger  # type: ignore
        sys.modules["structlog"] = stub

# Set required environment variables as early as possible (before any project imports)
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("OPENAI_EMBEDDINGS_API_KEY", "test-key")
os.environ.setdefault("AI__OPENAI_API_KEY", "test-key")
os.environ.setdefault("TAVILY_API_KEY", "test-key")
os.environ.setdefault("DEEPGRAM_API_KEY", "test-key")
os.environ.setdefault("HUGGINGFACE_API_KEY", "test-key")

# Ensure ai-orchestrator service source is on sys.path early
service_src = Path(__file__).parent / "services" / "ai-orchestrator" / "cartrita" / "orchestrator"
parent_pkg = Path(__file__).parent / "services" / "ai-orchestrator"
if service_src.exists():
    root_pkg = parent_pkg / "cartrita"
    # Insert the parent of the 'cartrita' package so imports like 'cartrita.orchestrator' work
    base_path = parent_pkg
    if str(base_path) not in sys.path:
        sys.path.insert(0, str(base_path))


@pytest.fixture(scope="session", autouse=True)
def _test_env_keys():
    # Already set above for earliest import safety; fixture kept to document intent
    yield
