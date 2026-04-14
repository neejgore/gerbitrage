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

from fastapi import APIRouter, File, UploadFile

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


@router.post("/vision-debug", summary="Upload an image and see Claude's raw OCR output")
async def vision_debug(file: UploadFile = File(...)) -> dict:
    """Upload a menu image and get back Claude's raw structured output before parsing."""
    import os
    from app.api.routes.menu_upload import (
        _prepare_image_for_claude, _image_to_text_claude, _parse_wines
    )

    data = await file.read()
    filename = file.filename or "upload"
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else "jpeg"

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY not set"}

    try:
        img_data, media_type = _prepare_image_for_claude(data, ext)
        raw = await _image_to_text_claude(img_data, media_type)
        parsed = _parse_wines(raw)
        return {
            "claude_raw_output": raw,
            "parsed_entries": parsed,
            "entry_count": len(parsed),
        }
    except Exception as e:
        return {"error": str(e)}


@router.get("/vision-check", summary="Verify Claude Vision is configured and working")
async def vision_check() -> dict:
    """Quick diagnostic: verifies ANTHROPIC_API_KEY is set and Claude API responds."""
    import os
    result: dict = {}

    # 1. Check env var
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    result["api_key_set"] = bool(api_key)
    result["api_key_prefix"] = api_key[:12] + "..." if api_key else "(not set)"

    if not api_key:
        result["status"] = "FAIL — ANTHROPIC_API_KEY not found in environment"
        return result

    # 2. Check package importable
    try:
        import anthropic  # noqa: F401
        result["package_importable"] = True
        result["package_version"] = getattr(anthropic, "__version__", "unknown")
    except ImportError as e:
        result["package_importable"] = False
        result["status"] = f"FAIL — anthropic package not installed: {e}"
        return result

    # 3. Make a minimal API call — try models in descending quality order
    _CHECK_MODELS = [
        "claude-sonnet-4-6",
        "claude-haiku-4-5",
        "claude-sonnet-4-5",
        # Note: claude-3-haiku-20240307 is retired April 19 2026 — do not use
    ]
    for _model in _CHECK_MODELS:
        try:
            import anthropic as _anthropic
            client = _anthropic.AsyncAnthropic(api_key=api_key)
            msg = await client.messages.create(
                model=_model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Reply with the single word: OK"}],
            )
            reply = msg.content[0].text if msg.content else "(empty)"
            result["api_call"] = "success"
            result["api_reply"] = reply
            result["model"] = _model
            result["status"] = f"OK — Claude Vision ready (model: {_model})"
            break
        except Exception as e:
            if "not_found_error" in str(e) or "404" in str(e):
                continue
            result["api_call"] = "failed"
            result["api_error"] = str(e)
            result["status"] = f"FAIL — API call error: {e}"
            break
    else:
        result["api_call"] = "failed"
        result["status"] = "FAIL — no Claude model available on this API key"

    return result
