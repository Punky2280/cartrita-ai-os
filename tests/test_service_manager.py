# pyright: reportMissingImports=false
import importlib.util
import os
import pytest  # type: ignore

MODULE_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    "..",
    "services",
    "ai-orchestrator",
    "cartrita",
    "orchestrator",
    "services",
    "service_manager.py",
))

spec = importlib.util.spec_from_file_location("_service_manager_isolated", MODULE_PATH)
service_manager_module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(service_manager_module)  # type: ignore
ServiceManager = service_manager_module.ServiceManager


class DummySecret:
    def __init__(self, value: str = ""):
        self._v = value

    def get_secret_value(self):  # mimic pydantic SecretStr API
        return self._v


class DummyAI:
    openai_api_key = DummySecret("")
    huggingface_api_key = DummySecret("")
    deepgram_api_key = DummySecret("")
    tavily_api_key = DummySecret("")
    github_api_key = DummySecret("")


class DummySettings:
    ai = DummyAI()

# Now that DummySettings exists, ensure module-level settings populated
service_manager_module.settings = DummySettings()


def _patch_settings(monkeypatch):
    from cartrita.orchestrator.utils import config as config_mod
    dummy = DummySettings()
    monkeypatch.setattr(config_mod, "settings", dummy, raising=False)
    monkeypatch.setattr(config_mod, "get_settings", lambda: dummy, raising=False)
    service_manager_module.settings = dummy
    return dummy


@pytest.mark.asyncio
async def test_service_manager_lazy_initialization(monkeypatch):
    _patch_settings(monkeypatch)
    sm = ServiceManager()
    assert sm.initialized is False
    await sm.initialize_services()
    assert sm.initialized is True
    assert sm.services == {}


@pytest.mark.asyncio
async def test_service_manager_unknown_service_error(monkeypatch):
    _patch_settings(monkeypatch)
    sm = ServiceManager()
    with pytest.raises(ValueError) as exc:
        await sm.get_service("nonexistent")
    assert "nonexistent" in str(exc.value)


@pytest.mark.asyncio
async def test_service_manager_list_services_empty(monkeypatch):
    _patch_settings(monkeypatch)
    sm = ServiceManager()
    await sm.initialize_services()
    assert sm.list_services() == {}


@pytest.mark.asyncio
async def test_service_manager_idempotent_initialize_and_shutdown(monkeypatch):
    _patch_settings(monkeypatch)
    sm = ServiceManager()
    await sm.initialize_services()
    # Second initialize should not raise and not re-add services
    await sm.initialize_services()
    assert sm.initialized is True
    await sm.shutdown_services()
    assert sm.initialized is False
    assert sm.services == {}
