"""
Wine.com integration.

Calls the Wine.com partner API when WINE_COM_API_KEY is set.
Returns None when the key is absent — no fabricated fallback data.

Docs: https://api.wine.com (requires partner account)
"""
from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.config import get_settings
from app.integrations.base import BasePricingProvider, RawPricingResult

logger = logging.getLogger(__name__)
settings = get_settings()

_API_BASE = "https://api.wine.com/api/beta/catalog.json"


class WineComProvider(BasePricingProvider):
    name = "Wine.com"

    def is_available(self) -> bool:
        return bool(settings.wine_com_api_key)

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
            "apikey": settings.wine_com_api_key,
            "search": f"{producer} {wine_name} {vintage or ''}".strip(),
            "size": "10",
            "offset": "0",
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(_API_BASE, params=params)
                resp.raise_for_status()
                data = resp.json()

            products = data.get("catalog", {}).get("products", [])
            if not products:
                return None

            prices = [
                float(p["priceMax"])
                for p in products
                if p.get("priceMax") is not None
            ]
            if not prices:
                return None

            prices.sort()
            avg = round(sum(prices) / len(prices), 2)

            return RawPricingResult(
                source=self.name,
                avg_price=avg,
                min_price=prices[0],
                max_price=prices[-1],
                median_price=prices[len(prices) // 2],
                num_listings=len(prices),
                url=f"https://www.wine.com/search/{wine_name.replace(' ', '%20')}",
            )

        except httpx.HTTPError as exc:
            logger.warning("Wine.com HTTP error: %s", exc)
            return None
        except Exception as exc:
            logger.error("Wine.com unexpected error: %s", exc)
            return None
