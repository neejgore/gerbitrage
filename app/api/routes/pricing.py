"""
GET /wine/{id}/pricing  –  fetch current market pricing for a known wine.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.data.wine_catalog import WINE_CATALOG_BY_ID
from app.schemas.pricing import WinePricingResponse
from app.services.pricing_aggregator import get_pricing

router = APIRouter(prefix="/wine", tags=["Pricing"])


@router.get(
    "/{wine_id}/pricing",
    response_model=WinePricingResponse,
    summary="Get market pricing for a wine",
)
async def get_wine_pricing(
    wine_id: str,
    vintage: Optional[int] = Query(
        None,
        ge=1900,
        le=2030,
        description="Vintage year; omit for non-vintage / base price",
    ),
) -> WinePricingResponse:
    """
    Retrieve aggregated retail pricing and estimated wholesale for a wine
    identified by its catalog ID.

    Use `GET /search` to find a wine's ID first.
    """
    wine = WINE_CATALOG_BY_ID.get(wine_id)
    if not wine:
        raise HTTPException(status_code=404, detail=f"Wine '{wine_id}' not found in catalog.")

    pricing = await get_pricing(
        wine_id=wine.id,
        wine_name=wine.name,
        producer=wine.producer,
        avg_retail_base=wine.avg_retail_price,
        price_tier=wine.price_tier or "mid",
        vintage=vintage,
    )

    return WinePricingResponse(
        wine_id=wine.id,
        name=wine.name,
        vintage=vintage,
        pricing=pricing,
    )
