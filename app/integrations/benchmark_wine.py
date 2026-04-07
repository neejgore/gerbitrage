"""
Benchmark Wine Group integration.

Benchmark Wine Group (benchmarkwine.com) is a San Francisco-based fine wine
specialist with strong secondary-market inventory — Burgundy, Bordeaux, Rhône,
and California cult wines.  Their search page returns fully server-rendered HTML
with product names and prices directly in the markup (no bot protection or
JavaScript rendering required).

Coverage:
  ✓ Cult California (DRC, Screaming Eagle, Harlan, Colgin, Bond, etc.)
  ✓ Burgundy depth (older vintages, rarer cuvées)
  ✓ Bordeaux first growths and right-bank estates
  ✓ Rhône prestige (Chave, Allemand, Guigal)
  ✗ Everyday / budget wines (not their market)

Because Benchmark is a single retailer with a secondary-market focus, prices
tend to run slightly above current primary-market retail for sought-after wines.
"""
from __future__ import annotations

import logging
import re
from typing import Optional
from urllib.parse import quote_plus

import httpx

from app.integrations.base import BasePricingProvider, RateLimiter, RawPricingResult

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://www.benchmarkwine.com/search"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.benchmarkwine.com/",
}


class BenchmarkWineProvider(BasePricingProvider):
    name = "Benchmark Wine"
    # Benchmark has no bot protection — 2–4 s is polite and safe
    _rate_limiter = RateLimiter(min_delay=2.0, max_delay=4.0)

    def is_available(self) -> bool:
        return True

    async def fetch_pricing(
        self,
        wine_name: str,
        producer: str,
        vintage: Optional[int] = None,
        wine_id: Optional[str] = None,
    ) -> Optional[RawPricingResult]:
        return await self._real(wine_name, producer, vintage, wine_id)

    # ── Real scraper ──────────────────────────────────────────────────────

    async def _real(
        self,
        wine_name: str,
        producer: str,
        vintage: Optional[int],
        wine_id: Optional[str],
    ) -> Optional[RawPricingResult]:
        # Build a targeted query: producer + key wine name words + vintage
        query_parts = [producer]
        # Drop generic words that don't help narrow results
        skip = {"domaine", "chateau", "château", "estate", "winery", "cellars",
                "domain", "maison", "weingut", "tenuta", "bodegas"}
        for word in wine_name.split():
            if word.lower() not in skip and len(word) > 2:
                query_parts.append(word)
                if len(query_parts) >= 4:
                    break
        if vintage:
            query_parts.append(str(vintage))

        query = " ".join(query_parts)

        try:
            await self._rate_limiter.wait()
            async with httpx.AsyncClient(
                headers=_HEADERS,
                timeout=12.0,
                follow_redirects=True,
            ) as client:
                resp = await client.get(_SEARCH_URL, params={"q": query})
                resp.raise_for_status()
                self._rate_limiter.record_success()
                prices = _extract_prices(resp.text, vintage)

                if not prices:
                    await self._rate_limiter.wait()
                    short_query = f"{producer} {vintage}" if vintage else producer
                    resp2 = await client.get(_SEARCH_URL, params={"q": short_query})
                    resp2.raise_for_status()
                    self._rate_limiter.record_success()
                    prices = _extract_prices(resp2.text, vintage)

            if not prices:
                logger.debug("Benchmark Wine: no prices for '%s'", query[:50])
                return None

            prices.sort()
            # Filter implausible outliers (750ml bottles only; skip magnums etc.)
            # Very rough: if max is > 5× median, drop it
            if len(prices) >= 3:
                med = prices[len(prices) // 2]
                prices = [p for p in prices if p <= med * 5]

            if not prices:
                return None

            avg = round(sum(prices) / len(prices), 2)
            url = f"https://www.benchmarkwine.com/search?q={quote_plus(query)}"

            logger.info(
                "Benchmark Wine: '%s' → %d listings, avg $%.2f",
                query[:50], len(prices), avg,
            )

            return RawPricingResult(
                source=self.name,
                avg_price=avg,
                min_price=prices[0],
                max_price=prices[-1],
                median_price=prices[len(prices) // 2],
                num_listings=len(prices),
                url=url,
            )

        except httpx.HTTPStatusError as exc:
            self._rate_limiter.record_error(exc.response.status_code)
            logger.warning("Benchmark Wine HTTP %s for '%s'", exc.response.status_code, query[:40])
            return None
        except Exception as exc:
            self._rate_limiter.record_error()
            logger.warning("Benchmark Wine scrape error: %s", exc)
            return None


# ── Price extraction ──────────────────────────────────────────────────────────

def _extract_prices(html: str, vintage: Optional[int] = None) -> list[float]:
    """
    Extract product prices from Benchmark's server-rendered HTML.

    Page structure (confirmed):
      <a href="/products/{slug}">
        <h2 ...>Wine Name [Year]</h2>
      </a>
      <p ...>$PRICE</p>

    We extract all (name, price) pairs and, when a vintage is specified,
    keep only entries where the name or surrounding context matches it.
    """
    prices: list[float] = []

    # Primary pattern: product link → h2 name → dollar price nearby
    for m in re.finditer(
        r'href="(/[^"]+)"><h2[^>]*>([^<]+)</h2>.*?\$([\d,]+(?:\.\d{2})?)',
        html,
        re.DOTALL,
    ):
        _, name, price_str = m.groups()
        try:
            price = float(price_str.replace(",", ""))
        except ValueError:
            continue

        # Sanity: $10–$50,000 for a bottle of wine
        if not 10 <= price <= 50_000:
            continue

        # If a vintage is specified, only include results that match
        if vintage and str(vintage) not in name:
            continue

        prices.append(price)

    # Fallback: any dollar amount adjacent to a product heading
    if not prices:
        for m in re.finditer(
            r'<h[23][^>]*>([^<]{8,80})</h[23]>.*?\$([\d,]+(?:\.\d{2})?)',
            html[:200_000],
            re.DOTALL,
        ):
            name, price_str = m.groups()
            try:
                price = float(price_str.replace(",", ""))
            except ValueError:
                continue
            if not 10 <= price <= 50_000:
                continue
            if vintage and str(vintage) not in name:
                continue
            prices.append(price)

    return prices
