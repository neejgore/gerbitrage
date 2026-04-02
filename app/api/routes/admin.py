"""
Admin endpoints.

POST /admin/refresh         – trigger an immediate full price refresh
GET  /admin/scheduler       – show scheduler status and next run time
GET  /admin/stats           – catalog + pricing coverage metrics
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from fastapi import APIRouter

from app.data.wine_catalog import WINE_CATALOG, WINE_CATALOG_BY_ID
from app.services.scheduler import run_price_refresh, scheduler_status

router = APIRouter(prefix="/admin", tags=["Admin"])

_VIVINO_CACHE = Path(__file__).parent.parent.parent / "data" / "vivino_prices_cache.json"
_EXTENDED_CATALOG = Path(__file__).parent.parent.parent / "data" / "extended_catalog.json"


@router.post(
    "/refresh",
    summary="Trigger an immediate catalog price refresh",
)
async def trigger_refresh() -> dict:
    """
    Kick off a full price refresh right now, bypassing the schedule.

    Useful after deploying with new API keys, after bulk catalog changes,
    or any time you want the cache warmed immediately.

    Returns a summary of how many wines were refreshed and how long it took.
    """
    return await run_price_refresh()


@router.get(
    "/scheduler",
    summary="Show scheduler status",
)
def get_scheduler_status() -> dict:
    """
    Returns whether the background scheduler is running, its configured
    interval, and when the next automatic refresh is due.
    """
    return scheduler_status()


@router.get("/stats", summary="Catalog and pricing coverage metrics")
def get_stats() -> dict:
    """
    Returns catalog size, regional breakdown, price-tier distribution,
    Vivino pricing coverage, and extended catalog status.
    """
    # Base catalog breakdown
    countries = dict(Counter(w.country for w in WINE_CATALOG).most_common())
    top_regions = dict(Counter(
        w.region.split(",")[0].strip() for w in WINE_CATALOG
    ).most_common(25))
    price_tiers = dict(Counter(w.price_tier for w in WINE_CATALOG))
    wine_types = dict(Counter(w.wine_type for w in WINE_CATALOG))

    # Normalize rose variants
    wine_types["rosé"] = wine_types.pop("rose", 0) + wine_types.pop("rosé", 0)

    # Vivino pricing coverage
    vivino_cache_keys: set[str] = set()
    if _VIVINO_CACHE.exists():
        try:
            vivino_cache_keys = set(json.loads(_VIVINO_CACHE.read_text()).keys())
        except Exception:
            pass

    base_ids = set(WINE_CATALOG_BY_ID.keys())
    total_base = len(WINE_CATALOG)

    # Generic priced = base wine has a non-vintage cache entry
    priced = len(vivino_cache_keys & base_ids)

    # Vintage entries = keys like "chateau-margaux-2018"
    vintage_entries = len([
        k for k in vivino_cache_keys
        if len(k) > 4 and k[-4:].isdigit() and k[:-5] in base_ids
    ])

    # A wine is "covered" if it has either a generic OR at least one vintage entry
    base_ids_with_vintage = {k[:-5] for k in vivino_cache_keys if len(k) > 4 and k[-4:].isdigit()}
    covered = len((vivino_cache_keys & base_ids) | (base_ids_with_vintage & base_ids))

    vivino_priced = vivino_cache_keys  # keep for per-country coverage below

    # Extended catalog
    extended_count = 0
    if _EXTENDED_CATALOG.exists():
        try:
            extended_count = len(json.loads(_EXTENDED_CATALOG.read_text()))
        except Exception:
            pass

    # Per-country pricing coverage
    country_coverage: dict[str, dict] = {}
    for country, count in countries.items():
        c_ids = {w.id for w in WINE_CATALOG if w.country == country}
        c_priced = len(c_ids & vivino_cache_keys)
        country_coverage[country] = {
            "total": count,
            "priced": c_priced,
            "pct": round(100 * c_priced / count) if count else 0,
        }

    # Average retail by country (catalog base price)
    avg_by_country: dict[str, float] = {}
    for country in countries:
        wines = [w for w in WINE_CATALOG if w.country == country]
        avg_by_country[country] = round(sum(w.avg_retail_price for w in wines) / len(wines), 0)

    return {
        "catalog": {
            "base_wines": total_base,
            "extended_wines": extended_count,
            "total_wines": total_base + extended_count,
        },
        "pricing": {
            "vivino_priced": priced,
            "vintage_entries": vintage_entries,
            "total_cache_entries": len(vivino_cache_keys),
            "wines_covered": covered,
            "vivino_coverage_pct": round(100 * covered / total_base) if total_base else 0,
            "unpriced": total_base - covered,
        },
        "countries": countries,
        "country_coverage": country_coverage,
        "avg_price_by_country": avg_by_country,
        "top_regions": top_regions,
        "price_tiers": price_tiers,
        "wine_types": wine_types,
    }
