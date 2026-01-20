# api/middleware/rate_limit.py
"""
Rate Limiting and Cost Control Middleware for Darwin Gödel Machine API
"""

from fastapi import Request, HTTPException
from datetime import datetime
from typing import Optional
import redis.asyncio as redis


class CostController:
    """Kontrolliert API-Kosten pro User."""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def check_budget(self, user_id: str, estimated_tokens: int) -> bool:
        """Prüft ob User noch Budget hat."""
        key = f"budget:{user_id}:{datetime.utcnow().strftime('%Y-%m')}"

        current = await self.redis.get(key)
        current_tokens = int(current) if current else 0

        # Hole User Limit aus Config (in production: aus DB)
        monthly_limit = await self.get_user_limit(user_id)

        if current_tokens + estimated_tokens > monthly_limit:
            return False

        return True

    async def record_usage(self, user_id: str, tokens_used: int) -> None:
        """Zeichnet Token-Verbrauch auf."""
        key = f"budget:{user_id}:{datetime.utcnow().strftime('%Y-%m')}"
        await self.redis.incrby(key, tokens_used)
        await self.redis.expire(key, 60 * 60 * 24 * 32)  # 32 Tage TTL

    async def get_usage(self, user_id: str) -> dict:
        """Gibt aktuellen Verbrauch zurück."""
        key = f"budget:{user_id}:{datetime.utcnow().strftime('%Y-%m')}"
        current = await self.redis.get(key)
        current_tokens = int(current) if current else 0
        monthly_limit = await self.get_user_limit(user_id)

        return {
            "current_tokens": current_tokens,
            "monthly_limit": monthly_limit,
            "remaining": max(0, monthly_limit - current_tokens),
            "percentage_used": round((current_tokens / monthly_limit) * 100, 2) if monthly_limit > 0 else 0,
        }

    async def get_user_limit(self, user_id: str) -> int:
        """Gibt das monatliche Token-Limit für einen User zurück."""
        # In production: aus Datenbank laden
        # Default: 1 Million Tokens pro Monat
        return 1_000_000


class RateLimiter:
    """Rate Limiting für API Calls."""

    def __init__(self, redis_client: redis.Redis, max_calls_per_hour: int = 100):
        self.redis = redis_client
        self.max_calls = max_calls_per_hour

    async def check(self, user_id: str) -> bool:
        """Prüft ob User das Rate Limit erreicht hat."""
        key = f"rate:{user_id}:{datetime.utcnow().strftime('%Y-%m-%d-%H')}"

        current = await self.redis.incr(key)
        if current == 1:
            await self.redis.expire(key, 3600)

        return current <= self.max_calls

    async def get_remaining(self, user_id: str) -> int:
        """Gibt verbleibende Calls in dieser Stunde zurück."""
        key = f"rate:{user_id}:{datetime.utcnow().strftime('%Y-%m-%d-%H')}"
        current = await self.redis.get(key)
        current_calls = int(current) if current else 0
        return max(0, self.max_calls - current_calls)


class ConcurrencyLimiter:
    """Begrenzt gleichzeitige Runs pro User."""

    def __init__(self, redis_client: redis.Redis, max_concurrent: int = 3):
        self.redis = redis_client
        self.max_concurrent = max_concurrent

    async def acquire(self, user_id: str, run_id: str) -> bool:
        """Versucht einen Slot für einen neuen Run zu bekommen."""
        key = f"concurrent:{user_id}"

        # Füge Run zu Set hinzu
        await self.redis.sadd(key, run_id)

        # Prüfe Anzahl
        count = await self.redis.scard(key)

        if count > self.max_concurrent:
            # Zu viele Runs, entferne wieder
            await self.redis.srem(key, run_id)
            return False

        return True

    async def release(self, user_id: str, run_id: str) -> None:
        """Gibt einen Slot frei."""
        key = f"concurrent:{user_id}"
        await self.redis.srem(key, run_id)

    async def get_active_runs(self, user_id: str) -> list:
        """Gibt Liste aktiver Run-IDs zurück."""
        key = f"concurrent:{user_id}"
        runs = await self.redis.smembers(key)
        return [r.decode() if isinstance(r, bytes) else r for r in runs]


# Middleware Factory
def create_rate_limit_middleware(redis_client: redis.Redis):
    """Creates rate limiting middleware for FastAPI."""

    rate_limiter = RateLimiter(redis_client)
    cost_controller = CostController(redis_client)

    async def rate_limit_middleware(request: Request, call_next):
        # Extract user_id from request (simplified)
        user_id = request.headers.get("X-User-ID", "default_user")

        # Check rate limit
        if not await rate_limiter.check(user_id):
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": 3600,
                }
            )

        # Add rate limit headers
        response = await call_next(request)
        remaining = await rate_limiter.get_remaining(user_id)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Limit"] = str(rate_limiter.max_calls)

        return response

    return rate_limit_middleware


# Dependency for FastAPI
async def check_rate_limit(
    request: Request,
    redis_client: redis.Redis,
) -> None:
    """FastAPI dependency to check rate limits."""
    user_id = request.headers.get("X-User-ID", "default_user")

    limiter = RateLimiter(redis_client)
    if not await limiter.check(user_id):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded"
        )


async def check_budget(
    request: Request,
    redis_client: redis.Redis,
    estimated_tokens: int = 10000,
) -> None:
    """FastAPI dependency to check budget."""
    user_id = request.headers.get("X-User-ID", "default_user")

    controller = CostController(redis_client)
    if not await controller.check_budget(user_id, estimated_tokens):
        usage = await controller.get_usage(user_id)
        raise HTTPException(
            status_code=402,
            detail={
                "error": "budget_exceeded",
                "message": "Monthly token budget exceeded",
                "usage": usage,
            }
        )


async def check_concurrency(
    request: Request,
    redis_client: redis.Redis,
    run_id: str,
) -> None:
    """FastAPI dependency to check concurrency limits."""
    user_id = request.headers.get("X-User-ID", "default_user")

    limiter = ConcurrencyLimiter(redis_client)
    if not await limiter.acquire(user_id, run_id):
        active = await limiter.get_active_runs(user_id)
        raise HTTPException(
            status_code=429,
            detail={
                "error": "concurrency_limit",
                "message": "Too many concurrent runs",
                "active_runs": active,
                "max_concurrent": limiter.max_concurrent,
            }
        )
