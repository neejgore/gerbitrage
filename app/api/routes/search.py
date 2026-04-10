"""
GET /search  –  free-text wine search over the catalog.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Optional

from fastapi import APIRouter, Query

from app.data.wine_catalog import WINE_CATALOG_BY_ID
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


def _normalize_simple(s: str) -> str:
    """Lowercase + strip accents, for prefix comparison."""
    nfkd = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in nfkd if unicodedata.category(c) != "Mn")


def _autocomplete_boost(q_norm: str, wine_id: str, wine_name: str, producer: str) -> float:
    """
    Extra score applied on top of the fuzzy match score for autocomplete ranking.

    Two signals:
    1. Prefix match: the query is a prefix of the wine name or producer name.
       Rewards typing "biz" → "Bizot" over a random wine called "Bi".
       Boost scales with query length (short queries get less).

    2. Static catalog: wines in the hand-curated static catalog get a fixed
       bump over dynamically-discovered extended-catalog entries.  This keeps
       well-known wines (Bizot, DRC, Opus One…) above obscure Vivino-scraped
       entries with short names.
    """
    boost = 0.0

    name_norm = _normalize_simple(wine_name)
    prod_norm = _normalize_simple(producer)
    if name_norm.startswith(q_norm) or prod_norm.startswith(q_norm):
        boost += min(0.05 + len(q_norm) * 0.02, 0.15)

    if wine_id in WINE_CATALOG_BY_ID:
        boost += 0.20
    elif len(wine_name.strip()) < 4:
        # Very short names in the extended catalog (e.g. "Bi", "Bigi") are
        # almost always low-quality discovery artifacts; suppress them.
        boost -= 0.30

    return boost


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
    # Fetch a generous pool so deduplication doesn't shrink results below limit.
    pool = search_wines(q, limit=limit * 4, wine_type=wine_type, country=country)

    # Re-rank: apply prefix-match and static-catalog boosts so curated wines
    # like "Bizot" surface above obscure extended-catalog entries like "Bi".
    q_norm = _normalize_simple(q.strip())
    boosted = [
        (m.score + _autocomplete_boost(q_norm, m.wine.id, m.wine.name, m.wine.producer), m)
        for m in pool
    ]
    boosted.sort(key=lambda x: x[0], reverse=True)

    # Deduplicate: keep only the highest-scoring entry per (name, producer-key)
    # pair so that vintage-specific extended-catalog clones don't eat all slots.
    seen_pairs: set[tuple[str, str]] = set()
    results: list[WineSearchResult] = []
    for boosted_score, m in boosted:
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
                match_score=round(boosted_score, 4),
            )
        )
        if len(results) >= limit:
            break

    return WineSearchResponse(query=q, results=results, total=len(results))
