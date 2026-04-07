"""
Total Wine integration.

Total Wine has no public API, but their search endpoint returns structured
JSON for product listings — it is the same data their website uses.
No authentication is required; the endpoint is publicly accessible.

No authentication required — Total Wine's search endpoint is public.
Returns None when no pricing data is found.
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

_SEARCH_URL = "https://www.totalwine.com/search/all"

# Browser-like headers to avoid trivial bot detection
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.totalwine.com/",
}


def _build_cookies() -> dict[str, str]:
    """Include session cookie if configured — helps bypass PerimeterX."""
    cookies: dict[str, str] = {}
    if settings.total_wine_session_cookie:
        # The cookie string from devtools may contain multiple key=value pairs;
        # parse them all so httpx can send them correctly.
        for part in settings.total_wine_session_cookie.split(";"):
            part = part.strip()
            if "=" in part:
                k, _, v = part.partition("=")
                cookies[k.strip()] = v.strip()
    return cookies

class TotalWineProvider(BasePricingProvider):
    name = "Total Wine"
    # Total Wine has PerimeterX — longer delays reduce challenge frequency
    _rate_limiter = RateLimiter(min_delay=4.0, max_delay=8.0, max_backoff=300.0)

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
        query = f"{producer} {wine_name}"
        if vintage:
            query = f"{query} {vintage}"

        params = {
            "text": query,
            "spiritstype": "wine",
        }

        try:
            await self._rate_limiter.wait()
            async with httpx.AsyncClient(
                headers=_HEADERS,
                cookies=_build_cookies(),
                timeout=12.0,
                follow_redirects=True,
            ) as client:
                resp = await client.get(_SEARCH_URL, params=params)
                resp.raise_for_status()
                self._rate_limiter.record_success()

                # Total Wine returns HTML for browsers but JSON when the
                # Accept header includes application/json or when the
                # request comes through their internal search API path.
                # If HTML is returned, parse price from structured data.
                content_type = resp.headers.get("content-type", "")
                if "json" in content_type:
                    data = resp.json()
                    prices = _extract_json_prices(data)
                else:
                    prices = _extract_html_prices(resp.text)

            if not prices:
                logger.debug("Total Wine: no prices found for '%s'", query[:50])
                return None

            prices.sort()
            avg = round(sum(prices) / len(prices), 2)
            url = f"https://www.totalwine.com/search/all?text={quote_plus(query)}"

            logger.info(
                "Total Wine scrape: '%s' → %d listings, avg $%.2f",
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
            logger.warning("Total Wine HTTP %s for '%s'", exc.response.status_code, query[:40])
            return None
        except Exception as exc:
            self._rate_limiter.record_error()
            logger.warning("Total Wine scrape error: %s", exc)
            return None


# ── HTML / JSON price extractors ──────────────────────────────────────────────

def _extract_json_prices(data: dict) -> list[float]:
    """Parse prices from Total Wine's JSON search response."""
    prices: list[float] = []
    products = (
        data.get("products")
        or data.get("items")
        or data.get("results")
        or []
    )
    for p in products:
        for key in ("price", "listPrice", "salePrice", "priceValue"):
            val = p.get(key)
            if val is not None:
                try:
                    prices.append(float(str(val).replace("$", "").replace(",", "")))
                    break
                except (ValueError, TypeError):
                    continue
    return prices


def _extract_html_prices(html: str) -> list[float]:
    """
    Parse prices from Total Wine's HTML search page.
    Looks for JSON-LD structured data and inline price patterns.
    """
    import json
    import re

    prices: list[float] = []

    # Strategy 1: JSON-LD blocks (<script type="application/ld+json">)
    for block in re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        re.DOTALL | re.IGNORECASE,
    ):
        try:
            obj = json.loads(block)
            items = obj if isinstance(obj, list) else [obj]
            for item in items:
                offers = item.get("offers") or item.get("Offers") or []
                if isinstance(offers, dict):
                    offers = [offers]
                for offer in offers:
                    price_str = offer.get("price") or offer.get("Price")
                    if price_str:
                        try:
                            prices.append(float(str(price_str).replace(",", "")))
                        except (ValueError, TypeError):
                            pass
        except (json.JSONDecodeError, AttributeError):
            continue

    # Strategy 2: data-price attributes and common price CSS patterns
    if not prices:
        for match in re.findall(
            r'data-price=["\'](\d+\.?\d*)["\']|'
            r'"price":\s*"?(\d+\.?\d*)"?|'
            r'class="[^"]*price[^"]*"[^>]*>\s*\$?([\d,]+\.?\d*)',
            html,
            re.IGNORECASE,
        ):
            raw = next((m for m in match if m), None)
            if raw:
                try:
                    prices.append(float(raw.replace(",", "")))
                except (ValueError, TypeError):
                    pass

    # Filter out implausible values (< $5 or > $50,000)
    return [p for p in prices if 5 <= p <= 50_000]
