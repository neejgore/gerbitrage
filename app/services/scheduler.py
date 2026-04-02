"""
Scheduled price refresh.

Runs a background job every `price_refresh_interval_hours` hours that
pre-warms the Redis pricing cache for every wine in the catalog.  This
means the first real user request for any wine always hits the cache
rather than waiting for live provider calls.

The job uses a bounded asyncio semaphore so we never fire more than
`price_refresh_concurrency` concurrent provider fan-outs at once,
preventing us from hammering external APIs during the sweep.

Lifecycle
─────────
  start_scheduler()  – called from the FastAPI lifespan on startup
  stop_scheduler()   – called from the lifespan on shutdown
  run_price_refresh()– the job itself; also callable directly for a
                       manual trigger (e.g. from an admin endpoint).
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import get_settings
from app.data.wine_catalog import WINE_CATALOG
from app.services.cache import pricing_cache_key, cache_set
from app.services.pricing_aggregator import get_pricing

logger = logging.getLogger(__name__)
settings = get_settings()

# Cache TTL per price tier — ultra/luxury wines move faster than commodity wines
_TIER_TTL_SECONDS: dict[str, int] = {
    "ultra":   2 * 24 * 3600,   # 2 days  — cult wines (DRC, Screaming Eagle, etc.)
    "luxury":  7 * 24 * 3600,   # 7 days  — Grand Cru, First Growths
    "premium": 14 * 24 * 3600,  # 14 days — premium tier
    "mid":     30 * 24 * 3600,  # 30 days — mid-range
    "budget":  60 * 24 * 3600,  # 60 days — everyday wines barely move
}

_scheduler: Optional[AsyncIOScheduler] = None


# ---------------------------------------------------------------------------
# The refresh job
# ---------------------------------------------------------------------------

async def run_price_refresh() -> dict:
    """
    Pre-warm the pricing cache for every wine in the catalog.

    Strategy
    ────────
    Rather than fanning out all wines × all providers at once (which would
    hammer every scraper simultaneously), we process wines sequentially per
    provider via a per-provider semaphore of size 1.  This means:

      • Each scraper receives at most 1 request at a time from the batch job.
      • The scraper's own RateLimiter adds a per-request delay on top of that.
      • The result is a polite, human-paced stream of requests to each site.
      • Total wall-clock time ≈ n_wines × avg_provider_delay (runs in background,
        so latency doesn't matter as much as avoiding bans).

    Returns a summary dict surfaced by the admin endpoint.
    """
    from app.services.pricing_aggregator import _PROVIDERS

    total = len(WINE_CATALOG)
    logger.info("Price refresh started — %d wines", total)
    started_at = datetime.now(timezone.utc)

    # One semaphore per provider → serialises requests to each scraper
    provider_sems = {p.name: asyncio.Semaphore(1) for p in _PROVIDERS}

    # Global semaphore still caps total concurrent work across all providers
    global_sem = asyncio.Semaphore(settings.price_refresh_concurrency)

    success = 0
    failed = 0

    async def _refresh_one(wine) -> bool:
        async with global_sem:
            try:
                tier = wine.price_tier or "mid"
                ttl = _TIER_TTL_SECONDS.get(tier, _TIER_TTL_SECONDS["mid"])

                # Call each provider one at a time (serialised per provider)
                from app.integrations.base import RawPricingResult
                from app.services.pricing_aggregator import _aggregate, _safe_fetch

                tasks = []
                for provider in _PROVIDERS:
                    sem = provider_sems[provider.name]

                    async def _guarded(p=provider, s=sem):
                        async with s:
                            return await _safe_fetch(
                                p, wine.name, wine.producer, None, wine.id
                            )

                    tasks.append(_guarded())

                raw_results = await asyncio.gather(*tasks)
                valid = [r for r in raw_results if r is not None]

                breakdown = _aggregate(valid, None, wine.avg_retail_price, tier)
                cache_key = pricing_cache_key(wine.id, None)
                await cache_set(cache_key, breakdown.model_dump(), ttl=ttl)
                return True

            except Exception as exc:
                logger.warning("Price refresh failed for %s: %s", wine.id, exc)
                return False

    results = await asyncio.gather(*[_refresh_one(w) for w in WINE_CATALOG])
    success = sum(1 for r in results if r)
    failed = total - success

    elapsed_s = round((datetime.now(timezone.utc) - started_at).total_seconds(), 1)
    logger.info(
        "Price refresh complete — %d/%d succeeded in %.1fs",
        success, total, elapsed_s,
    )

    return {
        "started_at": started_at.isoformat(),
        "elapsed_s": elapsed_s,
        "total": total,
        "success": success,
        "failed": failed,
    }


# ---------------------------------------------------------------------------
# Scheduler lifecycle
# ---------------------------------------------------------------------------

def start_scheduler() -> None:
    """
    Start the APScheduler background scheduler.

    If `price_refresh_interval_hours` is 0 the scheduler is disabled
    (useful in tests or when you want on-demand refreshes only).
    """
    global _scheduler

    if settings.price_refresh_interval_hours <= 0:
        logger.info("Price refresh scheduler disabled (interval=0)")
        return

    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        run_price_refresh,
        trigger=IntervalTrigger(hours=settings.price_refresh_interval_hours),
        id="price_refresh",
        name="Catalog price refresh",
        replace_existing=True,
        # Run once immediately at startup so the cache is warm from the first
        # request, then repeat on the configured interval.
        next_run_time=datetime.now(timezone.utc),
    )
    _scheduler.start()
    logger.info(
        "Price refresh scheduler started — interval %dh, concurrency %d",
        settings.price_refresh_interval_hours,
        settings.price_refresh_concurrency,
    )


def stop_scheduler() -> None:
    """Gracefully shut down the scheduler on application exit."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Price refresh scheduler stopped")
    _scheduler = None


def scheduler_status() -> dict:
    """Return current scheduler state (used by the admin endpoint)."""
    if _scheduler is None or not _scheduler.running:
        return {"running": False, "interval_hours": settings.price_refresh_interval_hours}

    job = _scheduler.get_job("price_refresh")
    next_run = job.next_run_time.isoformat() if job and job.next_run_time else None

    return {
        "running": True,
        "interval_hours": settings.price_refresh_interval_hours,
        "next_run": next_run,
    }
