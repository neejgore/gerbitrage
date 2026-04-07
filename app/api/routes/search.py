"""
GET /search  –  free-text wine search over the catalog.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from app.schemas.wine import WineSearchResponse, WineSearchResult
from app.services.wine_identifier import search_wines
from app.integrations.vivino import _price_cache

router = APIRouter(prefix="/search", tags=["Search"])


def _best_price(wine_id: str, catalog_price: float) -> float:
    """Return the Vivino-cached price for a wine if available, else the catalog price."""
    entry = _price_cache.get(wine_id)
    if entry:
        p = entry.get("avg_price")
        if p and p > 0:
            return p
    return catalog_price


@router.get("", response_model=WineSearchResponse, summary="Search the wine catalog")
async def search(
    q: str = Query(..., min_length=2, max_length=200, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Max results to return"),
    wine_type: Optional[str] = Query(
        None,
        description="Filter by type: red | white | rose | sparkling | dessert | fortified",
    ),
    country: Optional[str] = Query(None, description="Filter by country"),
) -> WineSearchResponse:
    """
    Search the wine catalog by name, producer, or partial description.

    Returns ranked results with a **match_score** (0–1) indicating relevance.
    Prices are sourced from the Vivino cache where available; otherwise the
    catalog base price is used.
    Use this endpoint to look up wines before calling `/analyze`.
    """
    matches = search_wines(q, limit=limit, wine_type=wine_type, country=country)

    results = [
        WineSearchResult(
            id=m.wine.id,
            name=m.wine.name,
            producer=m.wine.producer,
            region=m.wine.region,
            country=m.wine.country,
            appellation=m.wine.appellation,
            varietal=m.wine.varietal,
            wine_type=m.wine.wine_type,
            avg_retail_price=_best_price(m.wine.id, m.wine.avg_retail_price),
            price_tier=m.wine.price_tier,
            match_score=round(m.score, 4),
        )
        for m in matches
    ]

    return WineSearchResponse(query=q, results=results, total=len(results))
