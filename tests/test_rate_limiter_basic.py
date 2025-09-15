import importlib.util
import os
import sys
import pytest

# Directly load the rate_limiter module to avoid importing other services (which require pydantic v2)
MODULE_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "services",
    "ai-orchestrator",
    "cartrita",
    "orchestrator",
    "services",
    "rate_limiter.py",
)
MODULE_PATH = os.path.abspath(MODULE_PATH)

spec = importlib.util.spec_from_file_location("_rate_limiter_isolated", MODULE_PATH)
rate_limiter_module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(rate_limiter_module)  # type: ignore
RateLimiter = rate_limiter_module.RateLimiter


def test_rate_limiter_allows_then_blocks_monotonic():
    rl = RateLimiter()
    # Override defaults to tiny limits for deterministic behavior
    rl.default_limits["requests_per_minute"] = 1
    rl.default_limits["requests_per_hour"] = 10
    rl.default_limits["requests_per_day"] = 100

    allowed1, counts1 = rl.check_rate_limit("clientA")
    assert allowed1 is True
    assert counts1["requests_per_minute"] == 1

    allowed2, counts2 = rl.check_rate_limit("clientA")
    assert allowed2 is False
    assert counts2["requests_per_minute"] == 1  # second not recorded


def test_rate_limiter_separate_clients_isolated():
    rl = RateLimiter()
    rl.default_limits["requests_per_minute"] = 1

    a1, _ = rl.check_rate_limit("A")
    b1, _ = rl.check_rate_limit("B")
    assert a1 and b1

    # Second request for A should be blocked; B still fine (but we don't need to test B again)
    a2, counts = rl.check_rate_limit("A")
    assert a2 is False
    assert counts["requests_per_minute"] == 1


@pytest.mark.parametrize("minute_limit", [1, 2])
def test_rate_limiter_parametrized_limits(minute_limit):
    rl = RateLimiter()
    allowed, _ = rl.check_rate_limit("X", requests_per_minute=minute_limit)
    assert allowed is True
    # Exceed if limit ==1
    second_allowed, _ = rl.check_rate_limit("X", requests_per_minute=minute_limit)
    if minute_limit == 1:
        assert second_allowed is False
    else:
        assert second_allowed is True


def test_rate_limiter_reset_times_present():
    rl = RateLimiter()
    rl.default_limits["requests_per_minute"] = 1
    rl.check_rate_limit("reset-client")
    resets = rl.get_reset_times("reset-client")
    assert set(["minute_reset", "hour_reset", "day_reset"]).issubset(resets.keys())
