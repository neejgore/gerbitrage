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
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            locale="en-US",
            timezone_id="America/Los_Angeles",
            viewport={"width": 1280, "height": 900},
        )
        page = await context.new_page()

        try:
            result = await scrape_vivino_price(
                page, wine_name, producer, vintage, catalog_price
            )
        finally:
            await browser.close()

    if result:
        # Persist under vintage-specific key when available
        disk_key = f"{wine_id}-{vintage}" if vintage else wine_id
        update_price_cache(disk_key, result)

        # Also update Redis
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
            cache_key_str = pricing_cache_key(wine_id, vintage)
            await cache_set(cache_key_str, breakdown.model_dump(), ttl=43200)

        # Add to extended catalog so future fuzzy-match queries find it
        if wine_name and wine_id:
            _add_to_extended_catalog(
                wine_id=wine_id,
                wine_name=wine_name,
                producer=producer,
                avg_price=result.get("avg_price"),
                vivino_url=result.get("url"),
                vivino_rating=result.get("vivino_rating"),
                vivino_id=result.get("vivino_wine_id", ""),
            )

        logger.info(
            "Dynamic Vivino: cached '%s' → avg $%.0f (added to catalog)",
            wine_id, result.get("avg_price", 0),
        )
    else:
        logger.info("Dynamic Vivino: no result for '%s'", wine_id)


def _add_to_extended_catalog(
    wine_id: str,
    wine_name: str,
    producer: str,
    avg_price: Optional[float],
    vivino_url: Optional[str],
    vivino_rating: Optional[float],
    vivino_id: str,
) -> None:
    """Add a newly discovered wine to extended_catalog.json."""
    import json as _json
    import re
    import unicodedata
    from datetime import datetime, timezone
    from pathlib import Path

    catalog_path = Path(__file__).parent.parent / "data" / "extended_catalog.json"
    try:
        catalog: dict = _json.loads(catalog_path.read_text()) if catalog_path.exists() else {}
    except Exception:
        catalog = {}

    if wine_id in catalog:
        return  # already present

    def _price_tier(p: float) -> str:
        if p <= 25: return "budget"
        if p <= 75: return "mid"
        if p <= 200: return "premium"
        if p <= 600: return "luxury"
        return "ultra"

    catalog[wine_id] = {
        "id": wine_id,
        "name": wine_name,
        "producer": producer,
        "region": "",
        "country": "",
        "appellation": "",
        "varietal": "",
        "wine_type": "red",
        "avg_retail_price": avg_price or 0.0,
        "price_tier": _price_tier(avg_price or 0.0),
        "vivino_wine_id": vivino_id,
        "vivino_url": vivino_url or "",
        "vivino_rating": vivino_rating,
        "vivino_ratings_count": None,
        "vintage": None,
        "discovered_at": datetime.now(timezone.utc).isoformat(),
        "source": "dynamic_lookup",
    }

    try:
        catalog_path.write_text(_json.dumps(catalog, indent=2, ensure_ascii=False))
        logger.info("Extended catalog: added '%s' (%s)", wine_name, wine_id)
    except Exception as exc:
        logger.warning("Could not update extended catalog: %s", exc)


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
