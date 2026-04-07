"""
CellarTracker integration.

CellarTracker (cellartracker.com) is the largest wine community database —
3.5M+ wines, 7M+ tasting notes, and community-reported purchase prices from
members who log what they paid.  Their API is available to account holders.

Authentication
──────────────
Set CELLARTRACKER_USERNAME and CELLARTRACKER_PASSWORD in .env.
A free account is sufficient.  Sign up at https://www.cellartracker.com/

Returns None when credentials are absent — no fabricated fallback data.
"""
from __future__ import annotations

import logging
from typing import Optional
from urllib.parse import quote_plus

import httpx

from app.config import get_settings
from app.integrations.base import BasePricingProvider, RateLimiter, RawPricingResult

logger = logging.getLogger(__name__)
settings = get_settings()

_API_URL = "https://www.cellartracker.com/api.asp"


class CellarTrackerProvider(BasePricingProvider):
    name = "CellarTracker"
    _rate_limiter = RateLimiter(min_delay=3.0, max_delay=6.0, max_backoff=180.0)

    def is_available(self) -> bool:
        return bool(
            settings.cellartracker_username
            and settings.cellartracker_password
        )

    async def fetch_pricing(
        self,
        wine_name: str,
        producer: str,
        vintage: Optional[int] = None,
        wine_id: Optional[str] = None,
    ) -> Optional[RawPricingResult]:
        if not self.is_available():
            return None
        return await self._real(wine_name, producer, vintage, wine_id)

    async def _real(
        self,
        wine_name: str,
        producer: str,
        vintage: Optional[int],
        wine_id: Optional[str],
    ) -> Optional[RawPricingResult]:
        query = f"{producer} {wine_name}"
        if vintage:
            query = f"{query} {vintage}"

        params = {
            "m": "list",
            "q": query,
            "fmt": "json",
            "u": settings.cellartracker_username,
            "p": settings.cellartracker_password,
        }

        try:
            await self._rate_limiter.wait()
            async with httpx.AsyncClient(timeout=12.0) as client:
                resp = await client.get(_API_URL, params=params)
                resp.raise_for_status()
                self._rate_limiter.record_success()
                data = resp.json()

            wines = data if isinstance(data, list) else data.get("wines", []) or []
            if not wines:
                logger.debug("CellarTracker: no results for '%s'", query[:50])
                return None

            prices = _extract_prices(wines, vintage)
            if not prices:
                return None

            prices.sort()
            avg = round(sum(prices) / len(prices), 2)

            logger.info(
                "CellarTracker: '%s' → %d price points, avg $%.2f",
                query[:50], len(prices), avg,
            )

            return RawPricingResult(
                source=self.name,
                avg_price=avg,
                min_price=prices[0],
                max_price=prices[-1],
                median_price=prices[len(prices) // 2],
                num_listings=len(prices),
                url=f"https://www.cellartracker.com/list.asp?Table=List&szSearch={quote_plus(query)}",
            )

        except httpx.HTTPStatusError as exc:
            self._rate_limiter.record_error(exc.response.status_code)
            logger.warning(
                "CellarTracker HTTP %s for '%s'",
                exc.response.status_code, query[:40],
            )
            return None
        except Exception as exc:
            self._rate_limiter.record_error()
            logger.warning("CellarTracker error: %s", exc)
            return None


def _extract_prices(wines: list[dict], vintage: Optional[int] = None) -> list[float]:
    prices: list[float] = []
    for w in wines:
        if vintage:
            rec_vintage = str(w.get("Vintage") or w.get("vintage") or "")
            if rec_vintage and rec_vintage != str(vintage):
                continue

        for key in ("Price", "price", "AvgPrice", "avgprice", "ValuationPrice"):
            val = w.get(key)
            if val is not None:
                try:
                    price = float(str(val).replace("$", "").replace(",", ""))
                    if 5 <= price <= 50_000:
                        prices.append(price)
                        break
                except (ValueError, TypeError):
                    continue

    return prices
