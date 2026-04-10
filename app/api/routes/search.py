"""
GET /search  –  free-text wine search over the catalog.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Optional

from fastapi import APIRouter, Query

from app.schemas.wine import WineSearchResponse, WineSearchResult
from app.services.wine_identifier import search_wines
from app.integrations.vivino import _price_cache

router = APIRouter(prefix="/search", tags=["Search"])

_PRODUCER_NOISE = re.compile(
    r"\b(winery|wineries|winemakers?|vineyards?|vineyard|cellars|estates?|estate|"
    r"chateau|château|domaine|cave|maison)\b",
    re.IGNORECASE,
)


def _producer_key(producer: str) -> str:
    """Normalise a producer name for deduplication (strip boilerplate words)."""
    nfkd = unicodedata.normalize("NFD", producer.lower())
    ascii_str = "".join(c for c in nfkd if unicodedata.category(c) != "Mn")
    stripped = _PRODUCER_NOISE.sub("", ascii_str)
    return re.sub(r"\s{2,}", " ", stripped).strip()


def _best_price(wine_id: str) -> Optional[float]:
    """Return the Vivino-cached price for a wine, or None if no real price exists."""
    entry = _price_cache.get(wine_id)
    if entry:
        p = entry.get("avg_price")
        if p and p > 0:
            return p
    return None


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
    # Fetch more candidates than the limit so deduplication doesn't shrink the
    # final list below what the caller wants.
    matches = search_wines(q, limit=limit * 3, wine_type=wine_type, country=country)

    # Deduplicate: when the catalog has multiple entries for the same wine
    # (e.g. vintage-specific extended-catalog entries alongside the base static
    # entry), keep only the highest-scoring one per (name, producer-key) pair.
    # Results from search_wines are already sorted by score descending, so the
    # first occurrence of each pair is always the best match.
    seen_pairs: set[tuple[str, str]] = set()
    results: list[WineSearchResult] = []
    for m in matches:
        pair = (m.wine.name.lower(), _producer_key(m.wine.producer))
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        results.append(
            WineSearchResult(
                id=m.wine.id,
                name=m.wine.name,
                producer=m.wine.producer,
                region=m.wine.region,
                country=m.wine.country,
                appellation=m.wine.appellation,
                varietal=m.wine.varietal,
                wine_type=m.wine.wine_type,
                avg_retail_price=_best_price(m.wine.id),
                price_tier=m.wine.price_tier,
                match_score=round(m.score, 4),
            )
        )
        if len(results) >= limit:
            break

    return WineSearchResponse(query=q, results=results, total=len(results))
