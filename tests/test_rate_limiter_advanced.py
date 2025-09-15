import importlib.util
import os
from datetime import datetime, timedelta, timezone
import pytest

# Keep async marker for potential future async dependency variants
pytestmark = pytest.mark.asyncio

MODULE_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    "..",
    "services",
    "ai-orchestrator",
    "cartrita",
    "orchestrator",
    "services",
    "rate_limiter.py",
))

spec = importlib.util.spec_from_file_location("_rate_limiter_isolated_adv", MODULE_PATH)
rate_limiter_module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(rate_limiter_module)  # type: ignore
RateLimiter = rate_limiter_module.RateLimiter


def _inject_requests(rl: "RateLimiter", identifier: str, timestamps):
    """Helper: directly append historical timestamps (UTC aware)."""
    dq = rl._requests[identifier]
    for ts in timestamps:
        dq.append(ts)


async def test_rate_limiter_minute_window_rollover_allows_after_expiry():
    rl = RateLimiter()
    rl.default_limits["requests_per_minute"] = 2
    # Two immediate requests consume the minute quota.
    assert rl.check_rate_limit("clientM")[0] is True
    assert rl.check_rate_limit("clientM")[0] is True
    blocked, counts = rl.check_rate_limit("clientM")
    assert blocked is False
    assert counts["requests_per_minute"] == 2

    # Simulate passage of >1 minute by injecting an old timestamp and pruning
    # We directly manipulate stored deque to simulate time shift without sleep.
    old_ts = datetime.now(timezone.utc) - timedelta(minutes=2)
    rl._requests["clientM"][0] = old_ts
    rl._get_request_count("clientM", timedelta(minutes=1))  # triggers pruning

    # Now only 1 recent request remains; a new request should succeed.
    allowed_after, counts_after = rl.check_rate_limit("clientM")
    assert allowed_after is True
    assert counts_after["requests_per_minute"] == 2  # (1 previous recent + this one)


async def test_rate_limiter_hour_block_when_minute_ok():
    rl = RateLimiter()
    rl.default_limits["requests_per_minute"] = 5
    rl.default_limits["requests_per_hour"] = 3

    # Consume hour quota quickly (minute limit higher so not constraining)
    assert rl.check_rate_limit("clientH")[0] is True
    assert rl.check_rate_limit("clientH")[0] is True
    assert rl.check_rate_limit("clientH")[0] is True
    blocked, counts = rl.check_rate_limit("clientH")
    assert blocked is False
    assert counts["requests_per_hour"] == 3
    # Minute window should show same count but hour limit triggers block


async def test_rate_limiter_day_block_independent_of_hour():
    rl = RateLimiter()
    rl.default_limits["requests_per_minute"] = 100
    rl.default_limits["requests_per_hour"] = 100
    rl.default_limits["requests_per_day"] = 3

    assert rl.check_rate_limit("clientD")[0] is True
    assert rl.check_rate_limit("clientD")[0] is True
    assert rl.check_rate_limit("clientD")[0] is True
    blocked, counts = rl.check_rate_limit("clientD")
    assert blocked is False
    assert counts["requests_per_day"] == 3


async def test_rate_limiter_isolation_high_volume_multiple_clients():
    rl = RateLimiter()
    rl.default_limits["requests_per_minute"] = 3

    # Interleave requests across clients; ensure each has its own quota.
    for _ in range(3):
        assert rl.check_rate_limit("A")[0] is True
        assert rl.check_rate_limit("B")[0] is True

    # Both now at limit; further calls should block independently
    blocked_a, counts_a = rl.check_rate_limit("A")
    blocked_b, counts_b = rl.check_rate_limit("B")
    assert blocked_a is False and counts_a["requests_per_minute"] == 3
    assert blocked_b is False and counts_b["requests_per_minute"] == 3


async def test_rate_limiter_pruning_does_not_leak_memory():
    rl = RateLimiter()
    rl.default_limits["requests_per_minute"] = 10
    ident = "pruneClient"
    now = datetime.now(timezone.utc)
    # Inject 3 old (>24h) and 2 recent timestamps
    old = now - timedelta(days=2)
    recent1 = now - timedelta(minutes=2)
    recent2 = now - timedelta(seconds=10)
    _inject_requests(rl, ident, [old, old + timedelta(hours=1), old + timedelta(hours=2), recent1, recent2])

    # Force cleanup interval bypass by retroactively setting last cleanup far in past
    rl._last_cleanup = now - timedelta(minutes=10)
    # Trigger cleanup via a limit check
    rl.check_rate_limit(ident)
    # After cleanup, only recent (within 24h) timestamps + recorded new request should remain
    remaining = len(rl._requests[ident])
    assert remaining <= 4  # 2 old pruned, 2 recent + maybe new

