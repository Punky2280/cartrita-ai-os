# Cartrita AI OS - Rate Limiting Service
# Secure rate limiting with proper storage and cleanup

"""
Rate limiting service for Cartrita AI OS.
Provides configurable rate limiting with memory-based storage and automatic cleanup.
"""

import os
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple

from fastapi import HTTPException, Request, status


class RateLimiter:
    """
    In-memory rate limiter with sliding window and automatic cleanup.
    In production, consider using Redis for distributed rate limiting.
    """

    def __init__(self):
        # Storage: {identifier: deque of request timestamps}
        self._requests: Dict[str, deque] = defaultdict(deque)
        self._last_cleanup = datetime.now(timezone.utc)
        self._cleanup_interval = timedelta(minutes=5)

        # Default limits (can be overridden per endpoint)
        self.default_limits = {
            "requests_per_minute": int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
            "requests_per_hour": int(os.getenv("RATE_LIMIT_PER_HOUR", "1000")),
            "requests_per_day": int(os.getenv("RATE_LIMIT_PER_DAY", "10000")),
        }

    def _cleanup_old_requests(self):
        """Remove old request timestamps to prevent memory leaks."""
        now = datetime.now(timezone.utc)

        if now - self._last_cleanup < self._cleanup_interval:
            return

        # Remove requests older than 24 hours (our longest window)
        cutoff = now - timedelta(hours=24)

        for identifier in list(self._requests.keys()):
            request_times = self._requests[identifier]

            # Remove old timestamps
            while request_times and request_times[0] < cutoff:
                request_times.popleft()

            # Remove empty entries
            if not request_times:
                del self._requests[identifier]

        self._last_cleanup = now

    def _get_request_count(self, identifier: str, window: timedelta) -> int:
        """Get the number of requests in the given time window."""
        now = datetime.now(timezone.utc)
        cutoff = now - window

        request_times = self._requests[identifier]

        # Remove old requests
        while request_times and request_times[0] < cutoff:
            request_times.popleft()

        return len(request_times)

    def _record_request(self, identifier: str):
        """Record a new request timestamp."""
        now = datetime.now(timezone.utc)
        self._requests[identifier].append(now)

    def check_rate_limit(
        self,
        identifier: str,
        requests_per_minute: Optional[int] = None,
        requests_per_hour: Optional[int] = None,
        requests_per_day: Optional[int] = None,
    ) -> Tuple[bool, Dict[str, int]]:
        """
        Check if request is within rate limits.

        Args:
            identifier: Unique identifier for the client (IP, user ID, etc.)
            requests_per_minute: Custom per-minute limit
            requests_per_hour: Custom per-hour limit
            requests_per_day: Custom per-day limit

        Returns:
            Tuple of (is_allowed, current_counts)
        """
        self._cleanup_old_requests()

        # Use provided limits or defaults
        limits = {
            "minute": requests_per_minute or self.default_limits["requests_per_minute"],
            "hour": requests_per_hour or self.default_limits["requests_per_hour"],
            "day": requests_per_day or self.default_limits["requests_per_day"],
        }

        # Check each time window
        windows = {
            "minute": timedelta(minutes=1),
            "hour": timedelta(hours=1),
            "day": timedelta(days=1),
        }

        current_counts = {}

        for period, window in windows.items():
            count = self._get_request_count(identifier, window)
            current_counts[f"requests_per_{period}"] = count

            if count >= limits[period]:
                return False, current_counts

        # All checks passed - record the request
        self._record_request(identifier)

        # Update counts to include this request
        for period in current_counts:
            current_counts[period] += 1

        return True, current_counts

    def get_reset_times(self, identifier: str) -> Dict[str, datetime]:
        """Get the reset times for each rate limit window."""
        now = datetime.now(timezone.utc)
        request_times = self._requests[identifier]


        if not request_times:
            return {
                "minute_reset": now,
                "hour_reset": now,
                "day_reset": now,
            }

        # Find the oldest request in each window
        minute_cutoff = now - timedelta(minutes=1)
        hour_cutoff = now - timedelta(hours=1)
        day_cutoff = now - timedelta(days=1)

        minute_reset = now
        hour_reset = now
        day_reset = now

        for req_time in request_times:
            if req_time >= day_cutoff and day_reset == now:
                day_reset = req_time + timedelta(days=1)
            if req_time >= hour_cutoff and hour_reset == now:
                hour_reset = req_time + timedelta(hours=1)
            if req_time >= minute_cutoff and minute_reset == now:
                minute_reset = req_time + timedelta(minutes=1)

        return {
            "minute_reset": minute_reset,
            "hour_reset": hour_reset,
            "day_reset": day_reset,
        }


# Global rate limiter instance
rate_limiter = RateLimiter()


def get_client_identifier(request: Request) -> str:
    """
    Get a unique identifier for rate limiting.
    Uses X-Forwarded-For if available, falls back to client IP.
    """
    # Check for forwarded IP (from proxy/load balancer)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP in the chain (original client)
        return forwarded_for.split(",")[0].strip()

    # Fall back to direct client IP
    if request.client:
        return request.client.host

    return "unknown"


async def check_rate_limit(
    request: Request,
    requests_per_minute: Optional[int] = None,
    requests_per_hour: Optional[int] = None,
    requests_per_day: Optional[int] = None,
):
    """
    FastAPI dependency for rate limiting.

    Usage:
        @app.get("/api/endpoint")
        async def endpoint(request: Request, _: None = Depends(check_rate_limit)):
            return {"message": "success"}

    Or with custom limits:
        @app.get("/api/endpoint")
        async def endpoint(
            request: Request,
            _: None = Depends(lambda r: check_rate_limit(r, requests_per_minute=10))
        ):
            return {"message": "success"}
    """
    client_id = get_client_identifier(request)

    is_allowed, current_counts = rate_limiter.check_rate_limit(
        client_id,
        requests_per_minute,
        requests_per_hour,
        requests_per_day
    )

    if not is_allowed:
        reset_times = rate_limiter.get_reset_times(client_id)

        # Find which limit was exceeded and when it resets
        limits = rate_limiter.default_limits
        if requests_per_minute:
            limits["requests_per_minute"] = requests_per_minute
        if requests_per_hour:
            limits["requests_per_hour"] = requests_per_hour
        if requests_per_day:
            limits["requests_per_day"] = requests_per_day

        # Determine retry-after header
        retry_after = 60  # Default to 1 minute

        if current_counts["requests_per_minute"] >= limits["requests_per_minute"]:
            retry_after = int((reset_times["minute_reset"] - datetime.now(timezone.utc)).total_seconds())
        elif current_counts["requests_per_hour"] >= limits["requests_per_hour"]:
            retry_after = int((reset_times["hour_reset"] - datetime.now(timezone.utc)).total_seconds())
        elif current_counts["requests_per_day"] >= limits["requests_per_day"]:
            retry_after = int((reset_times["day_reset"] - datetime.now(timezone.utc)).total_seconds())

        retry_after = max(retry_after, 1)  # Ensure positive value

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "current_usage": current_counts,
                "limits": limits,
                "reset_times": {
                    "minute_reset": reset_times["minute_reset"].isoformat(),
                    "hour_reset": reset_times["hour_reset"].isoformat(),
                    "day_reset": reset_times["day_reset"].isoformat(),
                }
            },
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit-Minute": str(limits["requests_per_minute"]),
                "X-RateLimit-Limit-Hour": str(limits["requests_per_hour"]),
                "X-RateLimit-Limit-Day": str(limits["requests_per_day"]),
                "X-RateLimit-Remaining-Minute": str(max(0, limits["requests_per_minute"] - current_counts["requests_per_minute"])),
                "X-RateLimit-Remaining-Hour": str(max(0, limits["requests_per_hour"] - current_counts["requests_per_hour"])),
                "X-RateLimit-Remaining-Day": str(max(0, limits["requests_per_day"] - current_counts["requests_per_day"])),
            }
        )

    # Add rate limit headers to successful responses
    request.state.rate_limit_headers = {
        "X-RateLimit-Limit-Minute": str(rate_limiter.default_limits["requests_per_minute"]),
        "X-RateLimit-Limit-Hour": str(rate_limiter.default_limits["requests_per_hour"]),
        "X-RateLimit-Limit-Day": str(rate_limiter.default_limits["requests_per_day"]),
        "X-RateLimit-Remaining-Minute": str(max(0, rate_limiter.default_limits["requests_per_minute"] - current_counts["requests_per_minute"])),
        "X-RateLimit-Remaining-Hour": str(max(0, rate_limiter.default_limits["requests_per_hour"] - current_counts["requests_per_hour"])),
        "X-RateLimit-Remaining-Day": str(max(0, rate_limiter.default_limits["requests_per_day"] - current_counts["requests_per_day"])),
    }


# Convenience functions for common rate limit patterns
async def check_auth_rate_limit(request: Request):
    """Stricter rate limiting for authentication endpoints."""
    return await check_rate_limit(
        request,
        requests_per_minute=5,   # Only 5 auth attempts per minute
        requests_per_hour=20,    # 20 per hour
        requests_per_day=100     # 100 per day
    )


async def check_api_rate_limit(request: Request):
    """Standard rate limiting for API endpoints."""
    return await check_rate_limit(request)


async def check_heavy_rate_limit(request: Request):
    """More restrictive rate limiting for resource-intensive endpoints."""
    return await check_rate_limit(
        request,
        requests_per_minute=10,   # Only 10 requests per minute
        requests_per_hour=100,    # 100 per hour
        requests_per_day=500      # 500 per day
    )
