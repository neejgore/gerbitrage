"""
Redis cache service.

Uses a single connection pool that is initialised once on startup.
Falls back gracefully when Redis is unavailable (returns None on get).
"""
from __future__ import annotations

import json
import logging
from typing import Any, Optional

import redis.asyncio as aioredis

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_redis_client: Optional[aioredis.Redis] = None


async def init_cache() -> None:
    global _redis_client
    try:
        _redis_client = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            socket_connect_timeout=3,
        )
        await _redis_client.ping()
        logger.info("Redis cache connected at %s", settings.redis_url)
    except Exception as exc:
        logger.warning("Redis unavailable (%s); caching disabled.", exc)
        _redis_client = None


async def close_cache() -> None:
    global _redis_client
    if _redis_client:
        await _redis_client.aclose()
        _redis_client = None


async def cache_get(key: str) -> Optional[Any]:
    if not _redis_client:
        return None
    try:
        raw = await _redis_client.get(key)
        return json.loads(raw) if raw else None
    except Exception as exc:
        logger.debug("Cache GET error for %s: %s", key, exc)
        return None


async def cache_set(key: str, value: Any, ttl: Optional[int] = None) -> None:
    if not _redis_client:
        return
    ttl = ttl or settings.cache_ttl_seconds
    try:
        await _redis_client.setex(key, ttl, json.dumps(value, default=str))
    except Exception as exc:
        logger.debug("Cache SET error for %s: %s", key, exc)


async def cache_delete(key: str) -> None:
    if not _redis_client:
        return
    try:
        await _redis_client.delete(key)
    except Exception as exc:
        logger.debug("Cache DELETE error for %s: %s", key, exc)


def pricing_cache_key(wine_id: str, vintage: Optional[int]) -> str:
    v = vintage or "nv"
    return f"pricing:{wine_id}:{v}"
