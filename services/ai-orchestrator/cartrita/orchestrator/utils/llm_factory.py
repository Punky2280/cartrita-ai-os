from typing import Any

try:  # defer structlog import to avoid twisted/zope issues in Python 3.13 test env
    import structlog  # type: ignore

    logger = structlog.get_logger(__name__)
except Exception:  # pragma: no cover - fallback lightweight logger

    class _FallbackLogger:  # minimal interface
        def error(self, *args, **kwargs):
            pass

    logger = _FallbackLogger()

SUPPORTED_MAX_PARAM = "max_tokens"  # canonical param used by most providers

# Exposed attribute for tests to monkeypatch; real class imported lazily in factory.
ChatOpenAI = None  # type: ignore


def create_chat_openai(
    **kwargs: Any,
):  # return type omitted to avoid import at module load
    """Create a ChatOpenAI instance normalizing token limit parameter.

    Accepts either max_completion_tokens or max_tokens. If both provided, prefers max_completion_tokens.
    Silently maps to the currently supported param to avoid runtime warnings.
    """
    max_completion = kwargs.pop("max_completion_tokens", None)
    legacy = kwargs.pop("max_tokens", None)

    # Prefer explicit completion setting
    token_limit = max_completion if max_completion is not None else legacy
    if token_limit is not None:
        kwargs[SUPPORTED_MAX_PARAM] = token_limit
    else:
        # Provide a sane default if not set to prevent unbounded responses
        kwargs.setdefault(SUPPORTED_MAX_PARAM, 4096)

    # Remove any leftover unexpected fields that could trigger warnings
    # (Defensive: if future caller reintroduces max_completion_tokens)
    if "max_completion_tokens" in kwargs:
        kwargs.pop("max_completion_tokens", None)

    # Lazy import to reduce import cost & allow environments without langchain_openai during certain tests
    global ChatOpenAI
    if ChatOpenAI is None:
        try:  # pragma: no cover - import guarded
            from langchain_openai import ChatOpenAI as _RealChatOpenAI  # type: ignore

            ChatOpenAI = _RealChatOpenAI  # type: ignore
        except Exception as import_err:  # pragma: no cover
            logger.error("Failed to import ChatOpenAI", error=str(import_err))
            raise RuntimeError(
                "ChatOpenAI dependency unavailable; ensure langchain-openai installed"
            ) from import_err

    try:
        return ChatOpenAI(**kwargs)
    except TypeError as e:
        logger.error(
            "ChatOpenAI initialization failed due to parameter mismatch",
            error=str(e),
            params=list(kwargs.keys()),
        )
        raise
