import os
import importlib
os.environ.setdefault("CARTRITA_DISABLE_DB", "1")


def test_main_module_import_and_app_attribute():
    mod = importlib.import_module("cartrita.orchestrator.main")
    # Accept either an 'app' attribute or a function that creates it
    has_app = hasattr(mod, "app")
    create_fn = getattr(mod, "create_app", None)
    assert has_app or callable(create_fn)
