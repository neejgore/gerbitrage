"""
Wine-Searcher integration.

Calls the Wine-Searcher Pro API when WINE_SEARCHER_API_KEY is set.
Returns None when the key is absent — no fabricated fallback data.

Real API docs: https://www.wine-searcher.com/api
"""
from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.config import get_settings
from app.integrations.base import BasePricingProvider, RawPricingResult

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
        if not self.is_available():
            return None
        return await self._real(wine_name, producer, vintage)

    async def _real(
        self,
        wine_name: str,
        producer: str,
        vintage: Optional[int],
    ) -> Optional[RawPricingResult]:
        params: dict = {
            "apikey": settings.wine_searcher_api_key,
            "q": f"{producer} {wine_name}".strip(),
            "vintage": str(vintage) if vintage else "",
            "currency": "USD",
            "format": "json",
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(_SEARCH_URL, params=params)
                resp.raise_for_status()
                data = resp.json()

            offers = data.get("offers", [])
            if not offers:
                return None

            prices = [float(o["price"]) for o in offers if o.get("price") is not None]
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
