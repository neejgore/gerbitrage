"""
Wine-Searcher integration.

When a real API key is set, this provider calls the Wine-Searcher API.
Without a key it falls back to realistic mock data derived from the catalog
so the rest of the application works end-to-end out of the box.

Real API docs: https://www.wine-searcher.com/api
"""
from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.config import get_settings
from app.data.wine_catalog import WINE_CATALOG_BY_ID
from app.integrations.base import BasePricingProvider, RawPricingResult, _mock_price_from_base

logger = logging.getLogger(__name__)
settings = get_settings()

_API_BASE = "https://api.wine-searcher.com/api/v2"
_SEARCH_URL = f"{_API_BASE}/wine/search"


class WineSearcherProvider(BasePricingProvider):
    name = "Wine-Searcher"

    def is_available(self) -> bool:
        return bool(settings.wine_searcher_api_key)

    async def fetch_pricing(
        self,
        wine_name: str,
        producer: str,
        vintage: Optional[int] = None,
        wine_id: Optional[str] = None,
    ) -> Optional[RawPricingResult]:

        if settings.use_mock_pricing or not self.is_available():
            return self._mock(wine_id, vintage)

        return await self._real(wine_name, producer, vintage)

    # ── Real implementation ────────────────────────────────────────────────

    async def _real(
        self,
        wine_name: str,
        producer: str,
        vintage: Optional[int],
    ) -> Optional[RawPricingResult]:
        params: dict = {
            "apikey": settings.wine_searcher_api_key,
            "q": wine_name,
            "vintage": str(vintage) if vintage else "",
            "currency": "USD",
            "format": "json",
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(_SEARCH_URL, params=params)
                resp.raise_for_status()
                data = resp.json()

            # Wine-Searcher returns a list of merchant offers.
            # Parse the list and compute aggregate statistics.
            offers = data.get("offers", [])
            if not offers:
                return None

            prices = [
                float(o["price"]) for o in offers if o.get("price") is not None
            ]
            if not prices:
                return None

            prices.sort()
            avg = round(sum(prices) / len(prices), 2)
            median = prices[len(prices) // 2]

            return RawPricingResult(
                source=self.name,
                avg_price=avg,
                min_price=prices[0],
                max_price=prices[-1],
                median_price=median,
                num_listings=len(prices),
                url=f"https://www.wine-searcher.com/find/{wine_name.replace(' ', '+')}",
            )

        except httpx.HTTPError as exc:
            logger.warning("Wine-Searcher HTTP error: %s", exc)
            return None
        except Exception as exc:
            logger.error("Wine-Searcher unexpected error: %s", exc)
            return None

    # ── Mock fallback ──────────────────────────────────────────────────────

    def _mock(
        self,
        wine_id: Optional[str],
        vintage: Optional[int],
    ) -> Optional[RawPricingResult]:
        base_price: Optional[float] = None
        if wine_id and wine_id in WINE_CATALOG_BY_ID:
            base_price = WINE_CATALOG_BY_ID[wine_id].avg_retail_price

        if base_price is None:
            return None

        result = _mock_price_from_base(base_price, vintage, self.name, spread_factor=0.14, seed_key=wine_id or "")
        result.url = (
            f"https://www.wine-searcher.com/find/{wine_id.replace('-', '+')}"
            if wine_id else None
        )
        return result
