"""
Vivino pricing integration.

Two layers:
  1. Cache mode (instant):  reads from app/data/vivino_prices_cache.json
     Populated in bulk by:  scripts/vivino_price_all.py (~40 min for 694 wines)

  2. Live lookup (background): Playwright scrape triggered for any wine missing
     from the cache.  Result is saved back to disk + Redis so the next call is fast.

Cache file schema (keyed by wine_id):
  {
    "chateau-margaux": {
      "avg_price": 780.0,  "min_price": 650.0, "max_price": 950.0,
      "median_price": 780.0, "num_listings": 42,
      "url": "https://www.vivino.com/wines/12345",
      "vivino_wine_id": "12345",
      "vivino_name": "Château Margaux 2018",
      "fetched_at": "2026-04-01T12:00:00Z"
    }
  }
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
import unicodedata
from pathlib import Path
from typing import Optional


from app.config import get_settings
from app.data.wine_catalog import WINE_CATALOG_BY_ID
from app.integrations.base import BasePricingProvider, RateLimiter, RawPricingResult

logger = logging.getLogger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_PRICES_CACHE_PATH = Path(__file__).parent.parent / "data" / "vivino_prices_cache.json"

# ---------------------------------------------------------------------------
# Cache I/O
# ---------------------------------------------------------------------------
_price_cache: dict[str, dict] = {}


def _load_price_cache() -> dict[str, dict]:
    if _PRICES_CACHE_PATH.exists():
        try:
            return json.loads(_PRICES_CACHE_PATH.read_text())
        except Exception as exc:
            logger.warning("Vivino: failed to load price cache: %s", exc)
    return {}


def _save_price_cache(cache: dict[str, dict]) -> None:
    _PRICES_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _PRICES_CACHE_PATH.write_text(json.dumps(cache, indent=2, sort_keys=True))


def reload_price_cache() -> None:
    """Reload the Vivino price cache from disk."""
    _price_cache.clear()
    _price_cache.update(_load_price_cache())


# Load on import
_price_cache.update(_load_price_cache())

# Throttle disk reloads — Railway volumes are network-mounted (slow)
_RELOAD_INTERVAL = 30.0   # seconds between full disk reloads
_last_reload: float = time.monotonic()


# ---------------------------------------------------------------------------
# Persistent browser singleton
#
# One Playwright browser is launched on first use and kept alive for the
# lifetime of the process.  All Vivino searches serialize through a single
# asyncio.Lock so we never run two concurrent Playwright navigations.
#
# Cold-start cost: ~3-4 s (browser launch + first page load)
# Warm cost per search: ~4-6 s (just page navigation)
# ---------------------------------------------------------------------------

class _VivingoBrowser:
    """Manages a single persistent Playwright browser for Vivino searches."""

    _USER_AGENT = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    )

    def __init__(self) -> None:
        self._pw = None
        self._browser = None
        self._page = None
        self._lock = asyncio.Lock()   # serialise all searches
        self._init_lock = asyncio.Lock()

    async def search(
        self,
        wine_name: str,
        producer: str,
        vintage: Optional[int],
        catalog_price: Optional[float],
    ) -> Optional[dict]:
        """Run one Vivino search, returning a price dict or None."""
        async with self._lock:
            page = await self._ensure_page()
            try:
                return await asyncio.wait_for(
                    scrape_vivino_price(page, wine_name, producer, vintage, catalog_price),
                    timeout=25.0,
                )
            except asyncio.TimeoutError:
                logger.warning("Vivino live search timed out for '%s %s'", producer, wine_name)
                await self._reset()
                return None
            except Exception as exc:
                logger.warning("Vivino live search error for '%s %s': %s", producer, wine_name, exc)
                await self._reset()
                return None

    async def _ensure_page(self):
        async with self._init_lock:
            if self._page is None or not self._browser_alive():
                await self._start()
        return self._page

    def _browser_alive(self) -> bool:
        try:
            return bool(self._browser and self._browser.is_connected())
        except Exception:
            return False

    async def _start(self) -> None:
        from playwright.async_api import async_playwright
        await self._teardown()
        logger.info("Vivino: starting persistent browser…")
        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        ctx = await self._browser.new_context(
            user_agent=self._USER_AGENT,
            locale="en-US",
            timezone_id="America/Los_Angeles",
            viewport={"width": 1280, "height": 900},
        )
        self._page = await ctx.new_page()
        # Block images/fonts to speed up loads
        await self._page.route(
            "**/*.{png,jpg,gif,webp,svg,woff,woff2,ttf,eot}",
            lambda r: r.abort(),
        )
        logger.info("Vivino: browser ready")

    async def _reset(self) -> None:
        """Drop the page so _ensure_page restarts it on the next call."""
        self._page = None

    async def _teardown(self) -> None:
        for obj, method in [(self._browser, "close"), (self._pw, "stop")]:
            if obj:
                try:
                    await getattr(obj, method)()
                except Exception:
                    pass
        self._browser = None
        self._pw = None
        self._page = None


# Module-level singleton — shared across all requests in this process
_vivino_browser = _VivingoBrowser()


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------

class VivinoProvider(BasePricingProvider):
    """
    Provides real Vivino prices for any wine.

    Flow:
      1. Disk cache hit  → instant return (pre-populated by bulk pricing job)
      2. Cache miss      → live Playwright search (~5 s), result saved to cache
         so the next request for the same wine is instant.

    Uses a module-level persistent browser so there is no cold-start cost
    after the first request in a process lifetime.
    """

    name = "Vivino"
    _rate_limiter = RateLimiter(min_delay=0.5, max_delay=1.0, max_backoff=30.0)

    def is_available(self) -> bool:
        return not settings.use_mock_pricing

    async def fetch_pricing(
        self,
        wine_name: str,
        producer: str,
        vintage: Optional[int] = None,
        wine_id: Optional[str] = None,
    ) -> Optional[RawPricingResult]:
        base_id = wine_id or f"{producer}|{wine_name}"

        # Build lookup keys: vintage-specific first, then generic fallback
        # e.g. "chateau-margaux-2018" → "chateau-margaux"
        keys_to_check: list[str] = []
        if vintage:
            keys_to_check.append(f"{base_id}-{vintage}")
        keys_to_check.append(base_id)

        # 1. In-memory cache hit — instant
        # On a miss we do one lazy reload from disk to pick up entries written
        # by the background worker process since this process started.
        for key in keys_to_check:
            if key in _price_cache:
                entry = _price_cache[key]
                logger.debug("Vivino cache hit: %s", key)
                return RawPricingResult(
                    source=self.name,
                    avg_price=entry.get("avg_price"),
                    min_price=entry.get("min_price"),
                    max_price=entry.get("max_price"),
                    median_price=entry.get("median_price"),
                    num_listings=entry.get("num_listings"),
                    url=entry.get("url"),
                )

        # Lazy reload: worker writes new entries to disk; pull them into memory.
        # Throttled to once every 30s so Railway's network volume isn't hammered.
        global _last_reload
        now = time.monotonic()
        if now - _last_reload >= _RELOAD_INTERVAL:
            fresh = _load_price_cache()
            if len(fresh) > len(_price_cache):
                _price_cache.update(fresh)
                logger.debug("Vivino cache reloaded: %d entries", len(_price_cache))
            _last_reload = now
            for key in keys_to_check:
                if key in _price_cache:
                    entry = _price_cache[key]
                    return RawPricingResult(
                        source=self.name,
                        avg_price=entry.get("avg_price"),
                        min_price=entry.get("min_price"),
                        max_price=entry.get("max_price"),
                        median_price=entry.get("median_price"),
                        num_listings=entry.get("num_listings"),
                        url=entry.get("url"),
                    )

        # 2. Live search — only when no background worker is running
        # On Railway, the background worker handles all scraping so we skip
        # live searches to avoid two Playwright browsers competing for RAM.
        if settings.vivino_live_search:
            logger.info(
                "Vivino cache miss → live search: '%s %s' vintage=%s",
                producer[:30], wine_name[:30], vintage,
            )
            catalog_entry = WINE_CATALOG_BY_ID.get(base_id) if wine_id else None
            catalog_price = catalog_entry.avg_retail_price if catalog_entry else None

            result = await _vivino_browser.search(wine_name, producer, vintage, catalog_price)

            if result:
                store_key = f"{base_id}-{vintage}" if vintage else base_id
                update_price_cache(store_key, result)
                return RawPricingResult(
                    source=self.name,
                    avg_price=result.get("avg_price"),
                    min_price=result.get("min_price"),
                    max_price=result.get("max_price"),
                    median_price=result.get("median_price"),
                    num_listings=result.get("num_listings"),
                    url=result.get("url"),
                )
        else:
            logger.debug(
                "Vivino cache miss for '%s' (live search disabled — worker handles it)",
                base_id,
            )

        return None


# ---------------------------------------------------------------------------
# Shared Playwright scraping helpers (used by both the bulk script and
# the dynamic lookup service)
# ---------------------------------------------------------------------------

def build_search_query(wine_name: str, producer: str, vintage: Optional[int]) -> list[str]:
    """
    Return a prioritised list of query strings for Vivino search.

    Vivino's search works best with the wine name alone (or wine name + year).
    Adding "Winery" / "Vineyards" / "Cellars" etc. often returns zero or wrong results.

    Priority:
      1. wine_name + year    (most specific)
      2. wine_name           (no year)
      3. producer_short + wine_name  (fallback when name alone is ambiguous)
    """
    def _norm(s: str) -> str:
        s = unicodedata.normalize("NFKD", s)
        s = "".join(c for c in s if not unicodedata.combining(c))
        return s.strip()

    # Strip boilerplate words from producer — Vivino searches wine names, not brands
    _PRODUCER_NOISE = re.compile(
        r"\b(winery|wineries|winemakers|vineyards|vineyard|cellars|estates?|"
        r"chateau|château|domaine|cave|maison)\b",
        re.IGNORECASE,
    )
    n = _norm(wine_name)
    p_clean = _PRODUCER_NOISE.sub("", _norm(producer)).strip()
    p_clean = re.sub(r"\s{2,}", " ", p_clean).strip()

    # If wine name is just the producer name (e.g. "Opus One" / "Opus One"), use it once
    if n.lower() == p_clean.lower() or p_clean.lower() in n.lower():
        base_name = n
    else:
        base_name = n  # always prefer just the wine name

    queries: list[str] = []
    if vintage:
        queries.append(f"{base_name} {vintage}")
    queries.append(base_name)

    # Fallback: short producer + name (for wines whose name is generic, e.g. "Cabernet Sauvignon")
    if p_clean and p_clean.lower() not in base_name.lower():
        combo = f"{p_clean} {base_name}".strip()
        if combo not in queries:
            queries.append(combo)

    return queries


def update_price_cache(wine_id: str, data: dict) -> None:
    """Write a single wine's price data to the cache (thread-safe JSON append)."""
    _price_cache[wine_id] = data
    _save_price_cache(dict(_price_cache))


# ---------------------------------------------------------------------------
# Playwright scraping core
# ---------------------------------------------------------------------------

async def scrape_vivino_price(
    page,
    wine_name: str,
    producer: str,
    vintage: Optional[int],
    catalog_price: Optional[float] = None,
) -> Optional[dict]:
    """
    Search Vivino for a wine by exact name and return its price.

    We send the exact name from the catalog — no fuzzy matching needed.
    We take the top-ranked result (Vivino sorts by relevance + ratings)
    and do a single sanity check: is the price within a plausible range?

    `page` is an open Playwright page object (caller manages lifecycle).
    """
    from datetime import datetime, timezone

    queries = build_search_query(wine_name, producer, vintage)

    # Key words from the wine name used to verify the result is the right wine.
    # Strip common boilerplate so "Chateau Margaux" → key word is "Margaux".
    key_words = _key_words(wine_name, producer)

    for query in queries:
        search_url = f"https://www.vivino.com/search/wines?q={query.replace(' ', '+')}"
        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=30_000)
            await page.wait_for_timeout(2500)

            # Extract all priced wine cards from the page
            cards = await page.evaluate(_EXTRACT_ALL_WINES_JS)
            if not cards:
                continue

            # Pick the best card: first one whose name contains our key words
            best = _pick_best_card(cards, key_words, catalog_price)
            if not best:
                continue

            price = float(best["price"])
            avg = round(price, 2)
            min_p = round(avg * 0.85, 2)
            max_p = round(avg * 1.15, 2)
            vivino_url = best.get("url") or search_url
            vivino_id = ""
            m = re.search(r"/wines/(\d+)|/w/(\d+)", vivino_url)
            if m:
                vivino_id = m.group(1) or m.group(2)

            logger.info(
                "Vivino: '%s %s' → $%.0f  [%s]",
                producer[:20], wine_name[:20], avg, best.get("name", "")[:40],
            )
            return {
                "avg_price": avg,
                "min_price": min_p,
                "max_price": max_p,
                "median_price": avg,
                "num_listings": best.get("num_merchants", 1),
                "url": vivino_url,
                "vivino_wine_id": vivino_id,
                "vivino_name": best.get("name", ""),
                "vivino_rating": best.get("rating"),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as exc:
            logger.warning("Vivino search error for '%s': %s", query, exc)
            continue

    return None


def _key_words(wine_name: str, producer: str) -> set[str]:
    """
    Extract the most distinctive words from wine_name + producer.
    Used to verify a Vivino search result is actually the right wine.
    """
    _NOISE = re.compile(
        r"\b(chateau|château|domaine|winery|wineries|vineyards|vineyard|"
        r"cellars|estates?|maison|cave|de|la|le|du|des|the|et|and|of)\b",
        re.IGNORECASE,
    )
    combined = f"{wine_name} {producer}"
    combined = unicodedata.normalize("NFKD", combined)
    combined = "".join(c for c in combined if not unicodedata.combining(c))
    combined = combined.lower()
    combined = _NOISE.sub(" ", combined)
    words = set(re.findall(r"[a-z]{3,}", combined))
    return words


def _pick_best_card(
    cards: list[dict],
    key_words: set[str],
    catalog_price: Optional[float],
) -> Optional[dict]:
    """
    From a list of Vivino wine cards, return the best price match.

    Selection rules:
      1. Card name must contain at least one of our key words (no fuzzy — exact word inclusion)
      2. Price must pass sanity check against catalog price
      3. Among qualifying cards, prefer the highest-rated one
    """
    def _norm(s: str) -> str:
        s = unicodedata.normalize("NFKD", s)
        s = "".join(c for c in s if not unicodedata.combining(c))
        return s.lower()

    candidates = []
    for card in cards:
        name_norm = _norm(card.get("name", ""))
        name_words = set(re.findall(r"[a-z]{3,}", name_norm))

        # At least one key word must appear in the result name
        if key_words and not (key_words & name_words):
            continue

        price = card.get("price", 0)
        if not price or price <= 0:
            continue

        # Price sanity check
        if catalog_price and catalog_price > 0:
            ratio = price / catalog_price
            if ratio < 0.04 or ratio > 30.0:
                continue

        candidates.append(card)

    if not candidates:
        # Relax to: take the first card with a valid price (no name filter)
        for card in cards:
            price = card.get("price", 0)
            if not price or price <= 0:
                continue
            if catalog_price and catalog_price > 0:
                ratio = price / catalog_price
                if ratio < 0.04 or ratio > 30.0:
                    continue
            return card
        return None

    # Prefer higher-rated wine among candidates
    candidates.sort(key=lambda c: (c.get("rating") or 0), reverse=True)
    return candidates[0]


# ---------------------------------------------------------------------------
# JavaScript injected into the rendered Vivino search results page.
#
# Vivino renders results as anchor tags pointing to /wines/NNN or /w/NNN.
# Each wine anchor's innerText follows:
#   "Wine Name\nYear\nRegion, Country\nRating\n(N ratings)\n$XXX.XX"
#
# We iterate over all wine links, parse each block's text, and return a list
# of { name, url, price, rating, num_merchants } objects.
# ---------------------------------------------------------------------------
_EXTRACT_ALL_WINES_JS = """
() => {
    const results = [];
    const seen = new Set();

    // All anchors pointing to wine detail pages
    const links = Array.from(document.querySelectorAll('a[href*="/wines/"], a[href*="/w/"]'));

    for (const link of links) {
        const url = link.href;
        if (!url || seen.has(url)) continue;
        // Skip navigation / non-result links (they're usually very short text)
        const text = link.innerText.trim();
        if (!text || text.length < 3) continue;
        seen.add(url);

        // Lines in this card's text block
        const lines = text.split('\\n').map(l => l.trim()).filter(Boolean);
        const name = lines[0] || '';

        // Find a price line: "$NNN.NN" (USD — forced via /US/en/ URL)
        let price = null;
        let num_merchants = 1;
        for (const line of lines) {
            const pm = line.match(/^\\$([\\d,]+(?:\\.\\d{1,2})?)$/);
            if (pm) { price = parseFloat(pm[1].replace(/,/g, '')); break; }
        }
        // Also check sibling/parent text for price if not found in link text
        if (!price) {
            const parent = link.closest('div, li, article') || link.parentElement;
            if (parent) {
                const parentText = parent.innerText || '';
                const pm = parentText.match(/\\$([\\d,]+(?:\\.\\d{1,2})?)/);
                if (pm) price = parseFloat(pm[1].replace(/,/g, ''));
                const mm = parentText.match(/(\\d+)\\s+merchant/i);
                if (mm) num_merchants = parseInt(mm[1]);
            }
        }

        // Rating: "4.5" pattern in the lines
        let rating = null;
        for (const line of lines) {
            const r = parseFloat(line);
            if (r >= 1.0 && r <= 5.0 && /^[1-4]\\.[0-9]$/.test(line.trim())) {
                rating = r; break;
            }
        }

        if (price && price > 0) {
            results.push({ name, url, price, rating, num_merchants });
        }
    }

    return results;
}
"""
