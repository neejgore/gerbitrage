"""
Dynamic Vivino lookup service.

Called as a background `asyncio.create_task()` when a wine is not found in
any pre-populated pricing cache.  Results are written back to:
  - app/data/vivino_prices_cache.json  (persists across restarts)
  - Redis pricing cache                (fast access on next request)

Usage (from pricing_aggregator):
  asyncio.create_task(dynamic_lookup(wine_id, wine_name, producer, vintage))

The task is "fire and forget":
  - The current request returns mock prices (or catalog base price)
  - The background task runs in parallel
  - The *next* request for the same wine gets real prices from cache

Rate limiting: a module-level asyncio.Semaphore ensures we never run more
than MAX_CONCURRENT Playwright tabs at once.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Only run this many concurrent Playwright lookups at once
MAX_CONCURRENT = 2
_semaphore = asyncio.Semaphore(MAX_CONCURRENT)

# Track wines currently being looked up to avoid duplicate tasks
_in_flight: set[str] = set()


async def dynamic_lookup(
    wine_id: str,
    wine_name: str,
    producer: str,
    vintage: Optional[int],
    avg_retail_base: Optional[float] = None,
) -> None:
    """
    Background task: search Vivino for this wine and cache the result.

    Safe to call multiple times for the same wine_id; duplicate tasks are
    dropped via the `_in_flight` set.
    """
    if wine_id in _in_flight:
        return
    _in_flight.add(wine_id)

    try:
        async with _semaphore:
            await _run_lookup(wine_id, wine_name, producer, vintage, avg_retail_base)
    except Exception as exc:
        logger.warning("Dynamic Vivino lookup failed for '%s': %s", wine_id, exc)
    finally:
        _in_flight.discard(wine_id)


async def _run_lookup(
    wine_id: str,
    wine_name: str,
    producer: str,
    vintage: Optional[int],
    catalog_price: Optional[float],
) -> None:
    from datetime import datetime, timezone

    from playwright.async_api import async_playwright

    from app.integrations.vivino import scrape_vivino_price, update_price_cache
    from app.services.cache import cache_set, pricing_cache_key
    from app.integrations.base import RawPricingResult

    logger.info("Dynamic Vivino lookup: '%s %s' (id=%s)", producer, wine_name, wine_id)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="America/Los_Angeles",
        )
        page = await context.new_page()

        try:
            result = await scrape_vivino_price(
                page, wine_name, producer, vintage, catalog_price
            )
        finally:
            await browser.close()

    if result:
        # Persist under vintage-specific key when available so the next
        # request for the same wine+year is an instant cache hit
        disk_key = f"{wine_id}-{vintage}" if vintage else wine_id
        update_price_cache(disk_key, result)

        # Also update Redis so the aggregator finds it on next call
        avg = result.get("avg_price")
        if avg:
            from app.schemas.pricing import PricingBreakdown, PricingSource
            from app.services.pricing_aggregator import _estimate_wholesale

            price_tier = _get_tier(avg)
            breakdown = PricingBreakdown(
                avg_retail=avg,
                min_retail=result.get("min_price"),
                max_retail=result.get("max_price"),
                median_retail=result.get("median_price"),
                estimated_wholesale=_estimate_wholesale(avg, price_tier),
                vintage=vintage,
                source="aggregated",
                last_updated=datetime.now(timezone.utc),
                data_confidence="medium",
                sources=[
                    PricingSource(
                        name="Vivino",
                        avg_price=avg,
                        min_price=result.get("min_price"),
                        max_price=result.get("max_price"),
                        num_listings=result.get("num_listings"),
                        url=result.get("url"),
                    )
                ],
            )
            cache_key = pricing_cache_key(wine_id, vintage)
            await cache_set(cache_key, breakdown.model_dump(), ttl=43200)  # 12 h

        logger.info(
            "Dynamic Vivino: cached '%s' → avg $%.0f",
            wine_id, result.get("avg_price", 0),
        )
    else:
        logger.info("Dynamic Vivino: no result for '%s'", wine_id)


def _get_tier(price: float) -> str:
    if price <= 25:
        return "budget"
    if price <= 75:
        return "mid"
    if price <= 200:
        return "premium"
    if price <= 600:
        return "luxury"
    return "ultra"
