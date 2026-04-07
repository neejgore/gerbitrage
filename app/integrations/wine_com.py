"""
Wine.com integration.

Wine.com has a public affiliate/partner API (Bottlenotes API v3).
Without credentials this provider falls back to mock data.

Docs: https://api.wine.com (requires partner account)
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

_API_BASE = "https://api.wine.com/api/beta/catalog.json"

# Wine.com typically lists at or just below suggested retail
_WINE_COM_FACTOR = 0.97


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

        if settings.use_mock_pricing:
            return self._mock(wine_id, vintage)
        if not self.is_available():
            return None  # No API key — don't fabricate data

        return await self._real(wine_name, producer, vintage)

    # ── Real implementation ────────────────────────────────────────────────

    async def _real(
        self,
        wine_name: str,
        producer: str,
        vintage: Optional[int],
    ) -> Optional[RawPricingResult]:
        params: dict = {
            "apikey": settings.wine_com_api_key,
            "search": f"{wine_name} {vintage or ''}".strip(),
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

        result = _mock_price_from_base(
            base_price * _WINE_COM_FACTOR,
            vintage,
            self.name,
            spread_factor=0.10,
            seed_key=wine_id or "",
        )
        result.url = f"https://www.wine.com/search/{wine_id}" if wine_id else None
        return result
