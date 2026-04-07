"""
CellarTracker Marketplace integration — real retail prices.

How it works
────────────
When a logged-in user clicks "Where to Buy" on any CellarTracker wine page,
the site calls:

  https://api.cellartracker.com/wheretobuy/{iWine}/marketplace
    ?u={username}&h={pwhash}&currency=USD&location=USA&state=CA&winecount=6

`pwhash` is the user's `PWHash` cookie — a persistent, user-specific token
that doesn't change unless the user changes their password.

The response is JSON like:
  {
    "currency": "USD",
    "marketplaceArray": [
      {"merchant-name": "K&L Wine Merchants", "price": 265, "price-ebp": 265,
       "ebp-unit": "750ml", "bottle-size": "Bottle (750ml)", ...},
      ...
    ]
  }

iWine ID discovery
──────────────────
Each catalog wine must be mapped to a CellarTracker `iWine` integer ID.
The mapping is cached in `app/data/ct_wine_id_map.json`.
If a wine is not in the map, the provider returns None.

Rate limiting
─────────────
We use 4–8 s delays to stay well below CellarTracker's scraping threshold.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

import httpx

from app.config import get_settings
from app.integrations.base import BasePricingProvider, RateLimiter, RawPricingResult

logger = logging.getLogger(__name__)
settings = get_settings()

_MARKETPLACE_URL = "https://api.cellartracker.com/wheretobuy/{iWine}/marketplace"
_WINE_ID_MAP_PATH = Path(__file__).parent.parent / "data" / "ct_wine_id_map.json"

# Loaded once at module import; updated by the bulk scraper
_WINE_ID_MAP: dict[str, int] = {}


def _load_wine_id_map() -> dict[str, int]:
    if _WINE_ID_MAP_PATH.exists():
        try:
            return json.loads(_WINE_ID_MAP_PATH.read_text())
        except Exception as exc:
            logger.warning("Failed to load CT wine ID map: %s", exc)
    return {}


def _save_wine_id_map(mapping: dict[str, int]) -> None:
    _WINE_ID_MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
    _WINE_ID_MAP_PATH.write_text(json.dumps(mapping, indent=2, sort_keys=True))


# Load on import
_WINE_ID_MAP.update(_load_wine_id_map())


def reload_wine_id_map() -> None:
    """Reload the iWine ID map from disk (call after bulk scraper updates it)."""
    _WINE_ID_MAP.clear()
    _WINE_ID_MAP.update(_load_wine_id_map())


class CellarTrackerMarketplaceProvider(BasePricingProvider):
    """
    Provides real retail prices from CellarTracker's marketplace API.

    Requires:
      - CELLARTRACKER_USERNAME  (env var)
      - CELLARTRACKER_PWHASH   (env var) — the user's persistent PWHash cookie
      - ct_wine_id_map.json    (built by scripts/ct_bulk_scrape.py)
    """
    name = "CellarTrackerMarket"
    _rate_limiter = RateLimiter(min_delay=4.0, max_delay=8.0, max_backoff=180.0)

    def is_available(self) -> bool:
        return bool(
            settings.cellartracker_username
            and settings.cellartracker_pwhash
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

        iwine = wine_id and _WINE_ID_MAP.get(wine_id)
        if not iwine:
            logger.debug("CTMarket: no iWine ID for '%s'", wine_id)
            return None  # No ID mapping — skip rather than fabricate

        return await self._fetch_market_prices(iwine, wine_name, vintage)

    async def _fetch_market_prices(
        self,
        iwine: int,
        wine_name: str,
        vintage: Optional[int],
    ) -> Optional[RawPricingResult]:
        url = _MARKETPLACE_URL.format(iWine=iwine)
        params = {
            "u": settings.cellartracker_username,
            "h": settings.cellartracker_pwhash,
            "currency": "USD",
            "location": "USA",
            "state": "CA",
            "winecount": "10",
        }
        try:
            await self._rate_limiter.wait()
            async with httpx.AsyncClient(
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
                timeout=15.0,
            ) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                self._rate_limiter.record_success()
                data = resp.json()

            listings = data.get("marketplaceArray", [])
            if not listings:
                logger.debug("CTMarket: no listings for iWine=%d", iwine)
                return None

            prices = _extract_bottle_prices(listings)
            if not prices:
                return None

            prices.sort()
            avg = round(sum(prices) / len(prices), 2)
            median = prices[len(prices) // 2]

            logger.info(
                "CTMarket: iWine=%d '%s' → %d listings, avg $%.2f (range $%.0f–$%.0f)",
                iwine, wine_name[:40], len(prices), avg, prices[0], prices[-1],
            )

            return RawPricingResult(
                source=self.name,
                avg_price=avg,
                min_price=prices[0],
                max_price=prices[-1],
                median_price=median,
                num_listings=len(prices),
                url=f"https://www.cellartracker.com/wine.asp?iWine={iwine}",
            )

        except httpx.HTTPStatusError as exc:
            self._rate_limiter.record_error(exc.response.status_code)
            logger.warning("CTMarket HTTP %s for iWine=%d", exc.response.status_code, iwine)
            return None
        except Exception as exc:
            self._rate_limiter.record_error()
            logger.warning("CTMarket error for iWine=%d: %s", iwine, exc)
            return None



def _extract_bottle_prices(listings: list[dict]) -> list[float]:
    """
    Extract 750ml bottle prices from marketplace listings.

    Only include 750ml equivalents — skip multi-litre or case formats unless
    we can normalise to per-bottle price via `price-ebp`.
    """
    prices: list[float] = []
    for listing in listings:
        ebp = listing.get("price-ebp")
        unit = listing.get("ebp-unit", "")
        if ebp and "750ml" in unit:
            try:
                price = float(ebp)
                if 5 <= price <= 50_000:
                    prices.append(round(price, 2))
            except (ValueError, TypeError):
                continue
    return prices
