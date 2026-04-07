"""
Pricing aggregator.

Calls all configured providers concurrently, merges the results, and returns
a single PricingBreakdown.  Results are cached in Redis.

Vivino is the primary free-tier provider.  On a cache miss it performs a live
Playwright search (~5 s) and saves the result so subsequent calls are instant.
"""
from __future__ import annotations

import asyncio
import json
import logging
import statistics
from datetime import datetime, timezone
from typing import Optional

from app.integrations.base import RawPricingResult
from app.integrations.benchmark_wine import BenchmarkWineProvider
from app.integrations.cellartracker import CellarTrackerProvider
from app.integrations.cellartracker_marketplace import CellarTrackerMarketplaceProvider
from app.integrations.vivino import VivinoProvider
from app.integrations.wine_com import WineComProvider
from app.integrations.wine_searcher import WineSearcherProvider
from app.integrations.total_wine import TotalWineProvider
from app.schemas.pricing import PricingBreakdown, PricingSource
from app.services.cache import cache_get, cache_set, pricing_cache_key

logger = logging.getLogger(__name__)

# Provider priority order.  All active providers run concurrently per-request;
# the batch job serialises them per-provider to respect rate limits.
#
# Credential requirements:
#   WineSearcher          → WINE_SEARCHER_API_KEY          ($335/mo)
#   Vivino                → none (scraper, pre-populated cache)
#   CellarTrackerMarket   → CELLARTRACKER_USERNAME + PWHASH (free, real prices)
#   CellarTracker         → CELLARTRACKER_USERNAME + _PASSWORD (community prices)
#   BenchmarkWine         → none (scraper)
#   TotalWine             → none, or TOTAL_WINE_SESSION_COOKIE
#   WineCom               → WINE_COM_API_KEY (affiliate account)
_PROVIDERS = [
    WineSearcherProvider(),               # best data, paid API
    VivinoProvider(),                     # Vivino pre-populated cache (primary free source)
    CellarTrackerMarketplaceProvider(),   # real retail listings via CT marketplace (fallback)
    CellarTrackerProvider(),              # community purchase prices (fallback)
    BenchmarkWineProvider(),              # fine wine / secondary market scraper
    TotalWineProvider(),                  # free scraper + optional session cookie
    WineComProvider(),                    # affiliate API key
]



async def get_pricing(
    wine_id: str,
    wine_name: str,
    producer: str,
    avg_retail_base: float,
    price_tier: str,
    vintage: Optional[int] = None,
) -> PricingBreakdown:
    """
    Fetch and aggregate pricing from all available providers.

    Flow:
      1. Check Redis cache.
      2. Fan out to all providers concurrently.
      3. Aggregate results (weighted average, confidence band).
      4. Estimate wholesale.
      5. If no real price found → fire background Vivino dynamic lookup.
      6. Store in cache and return.
    """
    cache_key = pricing_cache_key(wine_id, vintage)
    cached = await cache_get(cache_key)
    if cached:
        logger.debug("Cache hit for %s", cache_key)
        return PricingBreakdown(**cached)

    # ── Fan out ────────────────────────────────────────────────────────────
    tasks = [
        _safe_fetch(provider, wine_name, producer, vintage, wine_id)
        for provider in _PROVIDERS
    ]
    raw_results: list[Optional[RawPricingResult]] = await asyncio.gather(*tasks)
    valid_results = [r for r in raw_results if r is not None]

    # ── Aggregate ──────────────────────────────────────────────────────────
    breakdown = _aggregate(valid_results, vintage, avg_retail_base, price_tier)

    # ── Cache ──────────────────────────────────────────────────────────────
    await cache_set(cache_key, breakdown.model_dump())

    return breakdown


async def _safe_fetch(
    provider,
    wine_name: str,
    producer: str,
    vintage: Optional[int],
    wine_id: str,
) -> Optional[RawPricingResult]:
    try:
        return await asyncio.wait_for(
            provider.fetch_pricing(wine_name, producer, vintage, wine_id),
            timeout=8.0,
        )
    except asyncio.TimeoutError:
        logger.debug("Provider %s timed out", provider.name)
        return None
    except Exception as exc:
        logger.warning("Provider %s failed: %s", provider.name, exc)
        return None


def _aggregate(
    results: list[RawPricingResult],
    vintage: Optional[int],
    avg_retail_base: float,
    price_tier: str,
) -> PricingBreakdown:
    if not results:
        # No provider returned data – fall back to catalog base price
        wholesale = _estimate_wholesale(avg_retail_base, price_tier)
        return PricingBreakdown(
            avg_retail=avg_retail_base,
            min_retail=avg_retail_base,
            max_retail=avg_retail_base,
            median_retail=avg_retail_base,
            estimated_wholesale=wholesale,
            vintage=vintage,
            source="catalog",
            last_updated=datetime.now(timezone.utc),
            data_confidence="low",
        )

    # Filter consistently: only include records where the field is not None
    priced_results = [r for r in results if r.avg_price is not None]
    avgs = [r.avg_price for r in priced_results]
    weights = [r.num_listings or 1 for r in priced_results]

    # ── Outlier-source rejection ──────────────────────────────────────────────
    # When one source is 4x+ higher than the median of all others AND it is
    # Vivino (which pulls the actual listing price), the low sources are almost
    # certainly matching the wrong wine (e.g. a $280 regional Burgundy instead
    # of a $5,600 cult domaine bottle). In that case, trust Vivino and discard
    # the low outliers rather than averaging them down.
    if len(avgs) >= 2:
        vivino_results = [r for r in priced_results if r.source == "Vivino"]
        other_results  = [r for r in priced_results if r.source != "Vivino"]
        if vivino_results and other_results:
            vivino_avg = statistics.mean(r.avg_price for r in vivino_results)
            other_avg  = statistics.mean(r.avg_price for r in other_results)
            # If Vivino is 4x+ higher than the median of other sources,
            # the other sources are likely mis-matched — drop them.
            if vivino_avg > 0 and other_avg > 0 and vivino_avg / other_avg >= 4.0:
                import logging
                logging.getLogger(__name__).info(
                    "Pricing outlier detected: Vivino $%.0f vs others avg $%.0f — "
                    "trusting Vivino, discarding low sources",
                    vivino_avg, other_avg,
                )
                priced_results = vivino_results
                avgs    = [r.avg_price for r in priced_results]
                weights = [r.num_listings or 1 for r in priced_results]

    mins = [r.min_price for r in priced_results if r.min_price is not None]
    maxes = [r.max_price for r in priced_results if r.max_price is not None]
    medians = [r.median_price for r in priced_results if r.median_price is not None]
    total_listings = sum(r.num_listings or 0 for r in results)

    avg_retail = _weighted_mean(avgs, weights)
    min_retail = min(mins) if mins else None
    max_retail = max(maxes) if maxes else None
    median_retail = statistics.mean(medians) if medians else avg_retail

    # Round to 2dp
    avg_retail = round(avg_retail, 2) if avg_retail else None
    min_retail = round(min_retail, 2) if min_retail else None
    max_retail = round(max_retail, 2) if max_retail else None
    median_retail = round(median_retail, 2) if median_retail else None

    ref_price = avg_retail or avg_retail_base
    wholesale = _estimate_wholesale(ref_price, price_tier)

    confidence = "high" if len(results) >= 2 and total_listings >= 10 else "medium" if results else "low"

    sources = [
        PricingSource(
            name=r.source,
            avg_price=r.avg_price,
            min_price=r.min_price,
            max_price=r.max_price,
            num_listings=r.num_listings,
            url=r.url,
        )
        for r in results
    ]

    return PricingBreakdown(
        avg_retail=avg_retail,
        min_retail=min_retail,
        max_retail=max_retail,
        median_retail=median_retail,
        estimated_wholesale=wholesale,
        vintage=vintage,
        source="aggregated",
        last_updated=datetime.now(timezone.utc),
        sources=sources,
        data_confidence=confidence,
    )


def _weighted_mean(values: list[float], weights: list[int]) -> float:
    if not values:
        return 0.0
    if len(values) != len(weights):
        return statistics.mean(values)
    total_w = sum(weights)
    if total_w == 0:
        return statistics.mean(values)
    return sum(v * w for v, w in zip(values, weights)) / total_w


# ---------------------------------------------------------------------------
# Wholesale estimation
# ---------------------------------------------------------------------------

# Industry average: restaurant pays ~wholesale, which is ~50–62% of retail
# depending on tier (luxury wines have fewer distribution layers, so the
# wholesale:retail ratio is actually higher).
_WHOLESALE_RATIOS = {
    "budget": 0.50,
    "mid": 0.52,
    "premium": 0.55,
    "luxury": 0.58,
    "ultra": 0.62,
}


def _estimate_wholesale(retail_price: float, price_tier: str) -> float:
    ratio = _WHOLESALE_RATIOS.get(price_tier, 0.53)
    return round(retail_price * ratio, 2)
