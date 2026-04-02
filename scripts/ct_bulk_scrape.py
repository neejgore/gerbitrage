#!/usr/bin/env python3
"""
CellarTracker Bulk Price Scraper
=================================
Fetches real retail prices for every wine in the catalog using the
CellarTracker marketplace API, then writes results to:

  app/data/ct_wine_id_map.json  — catalog_id → iWine integer
  app/data/ct_prices_cache.json — catalog_id → price data

Usage
-----
  python scripts/ct_bulk_scrape.py               # full run
  python scripts/ct_bulk_scrape.py --ids opus-one chateau-margaux  # specific wines
  python scripts/ct_bulk_scrape.py --skip-known  # only wines with no iWine yet
  python scripts/ct_bulk_scrape.py --login-only  # just refresh the PWHash in .env

The script uses Playwright (headless Chrome) to:
  1. Log in to CellarTracker and extract the PWHash cookie
  2. Search for each wine to resolve its iWine ID
  3. Call the marketplace API using httpx (no browser needed)

Requirements
------------
  pip install playwright httpx
  playwright install chromium
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import re
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.data.wine_catalog import WINE_CATALOG_BY_ID, WineCatalogEntry
from app.integrations.cellartracker_marketplace import (
    _WINE_ID_MAP_PATH,
    _extract_bottle_prices,
    _save_wine_id_map,
    reload_wine_id_map,
)

# ── Paths ─────────────────────────────────────────────────────────────────────
_PRICES_PATH = Path(__file__).parent.parent / "app" / "data" / "ct_prices_cache.json"

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("ct_scrape")

# ── Constants ─────────────────────────────────────────────────────────────────
CT_LOGIN_URL = "https://www.cellartracker.com/password.asp"
CT_SEARCH_URL = "https://www.cellartracker.com/search.asp"
CT_MARKETPLACE_URL = "https://api.cellartracker.com/wheretobuy/{iWine}/marketplace"
CT_USERNAME = "neejkid"
CT_PASSWORD = "Tennis4all"

MIN_DELAY = 4.0   # seconds between marketplace API calls
MAX_DELAY = 7.0
SEARCH_DELAY_MIN = 3.0   # seconds between CT search requests
SEARCH_DELAY_MAX = 6.0


# ──────────────────────────────────────────────────────────────────────────────
# Step 1: Login → get PWHash
# ──────────────────────────────────────────────────────────────────────────────

async def get_pwhash(username: str, password: str) -> str:
    """Login to CellarTracker with Playwright and return the PWHash cookie."""
    from playwright.async_api import async_playwright

    log.info("Launching browser to fetch PWHash…")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        )
        page = await context.new_page()
        await page.goto(CT_LOGIN_URL, wait_until="domcontentloaded")
        await page.fill('input[name="szUser"]', username)
        await page.fill('input[name="szPassword"]', password)
        await page.click('input[value="Sign In"]')
        await page.wait_for_load_state("networkidle")

        cookies = await context.cookies()
        pwhash = next((c["value"] for c in cookies if c["name"] == "PWHash"), None)
        await browser.close()

    if not pwhash:
        raise RuntimeError("Login failed — PWHash cookie not found")

    log.info("PWHash obtained: %s…", pwhash[:16])
    return pwhash


# ──────────────────────────────────────────────────────────────────────────────
# Step 2: Search CellarTracker for a wine → iWine ID
# ──────────────────────────────────────────────────────────────────────────────

async def search_iwine(
    entry: WineCatalogEntry,
    page,  # playwright page
    recent_year: int = 2019,
) -> int | None:
    """
    Search CellarTracker for `entry` and return the best-matching iWine ID.

    Strategy:
      1. Search with producer + name (+ recent year for active listings).
      2. Extract ALL wine rows from the search results page.
      3. Score each row by how closely the wine name matches the expected producer.
      4. Pick the highest-scoring match above a minimum threshold.
      5. Validate the price range against the catalog avg_retail_price.
    """
    import difflib
    from urllib.parse import urlencode
    import unicodedata

    def _normalize(s: str) -> str:
        """Lowercase, strip accents, remove punctuation."""
        s = unicodedata.normalize("NFD", s)
        s = "".join(c for c in s if unicodedata.category(c) != "Mn")
        return re.sub(r"[^a-z0-9 ]", " ", s.lower()).strip()

    async def _get_candidates(query: str) -> list[tuple[int, str]]:
        """Search and return [(iWine, wine_name_text), …] from all result rows."""
        params = {"QTable": "AllWines", "S": query, "SaveSearch": "True"}
        full_url = CT_SEARCH_URL + "?" + urlencode(params)
        await page.goto(full_url, wait_until="networkidle")
        await asyncio.sleep(SEARCH_DELAY_MIN)

        all_rows = await page.query_selector_all('tr[id^="W"]')

        seen: set[int] = set()
        candidates: list[tuple[int, str]] = []
        for row in all_rows:
            row_id = await row.get_attribute("id") or ""
            m = re.search(r"W(\d+)_", row_id)
            if not m:
                continue
            iwine = int(m.group(1))
            if iwine in seen:
                continue
            seen.add(iwine)

            # Wine name is in the td.name cell (index 2): "2019 Opus One\nNapa Valley\n..."
            # Try td.name first, fall back to cells[2]
            name_cell = await row.query_selector("td.name")
            if name_cell:
                # Prefer the h3 text (just the wine name without varietal noise)
                h3 = await name_cell.query_selector("h3")
                if h3:
                    name_text = (await h3.inner_text()).strip()
                else:
                    name_text = (await name_cell.inner_text()).strip().split("\n")[0]
            else:
                cells = await row.query_selector_all("td")
                name_text = (await cells[2].inner_text()).strip().split("\n")[0] if len(cells) >= 3 else ""

            if name_text and len(name_text) > 3:
                candidates.append((iwine, name_text))

        return candidates

    STOP_WORDS = {"chateau", "domaine", "cave", "wines", "winery", "estate",
                  "de", "du", "la", "le", "les", "et", "of", "the", "e"}

    def _score(wine_text: str) -> float:
        norm_text = _normalize(wine_text)
        norm_producer = _normalize(entry.producer)

        # Remove year prefix from wine_text (e.g. "2019 Château Margaux …")
        norm_text_no_year = re.sub(r"^\d{4}\s+", "", norm_text)

        # Sequence matcher: compare full producer to the start of the wine name
        window = norm_text_no_year[:len(norm_producer) + 25]
        producer_ratio = difflib.SequenceMatcher(None, norm_producer, window).ratio()

        # Token overlap: key producer words in wine text
        producer_tokens = set(norm_producer.split()) - STOP_WORDS
        # Also use significant name tokens
        name_tokens = set(_normalize(entry.name).split()) - STOP_WORDS
        all_key_tokens = producer_tokens | name_tokens
        token_hits = sum(1 for t in all_key_tokens if t in norm_text_no_year and len(t) > 2)
        token_ratio = token_hits / max(len(all_key_tokens), 1)

        return producer_ratio * 0.5 + token_ratio * 0.5

    # Build the best single query: avoid duplicating producer in name
    norm_producer = _normalize(entry.producer)
    norm_name = _normalize(entry.name)
    # If name already starts with producer (e.g. "Domaine Roulot Meursault Perrières")
    # use just the wine name, else join both
    if norm_name.startswith(norm_producer[:len(norm_producer)//2]):
        base = entry.name
    else:
        base = f"{entry.producer} {entry.name}"

    queries = [
        f"{base} {recent_year}",   # with recent vintage
        base,                       # without vintage
        f"{entry.producer} {recent_year}",  # just producer + year
        entry.producer,             # just producer
    ]
    # Deduplicate while preserving order
    seen_q: list[str] = []
    for q in queries:
        if q not in seen_q:
            seen_q.append(q)
    queries = seen_q

    for query in queries:
        candidates = await _get_candidates(query)
        if not candidates:
            continue

        # Score all candidates and pick best
        scored = [(iwine, text, _score(text)) for iwine, text in candidates]
        scored.sort(key=lambda x: -x[2])

        best_iwine, best_text, best_score = scored[0]
        log.debug("  Best match (q=%r): iWine=%d score=%.2f '%s'",
                  query[:40], best_iwine, best_score, best_text[:60])

        if best_score >= 0.35:
            log.debug("  → Accepted")
            return best_iwine

    log.warning("  No confident iWine match for '%s %s'", entry.producer, entry.name)
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Step 3: Fetch marketplace prices for an iWine
# ──────────────────────────────────────────────────────────────────────────────

async def fetch_market_prices(
    iwine: int,
    username: str,
    pwhash: str,
    client: httpx.AsyncClient,
) -> dict | None:
    """Call the marketplace API and return parsed price stats."""
    url = CT_MARKETPLACE_URL.format(iWine=iwine)
    params = {
        "u": username,
        "h": pwhash,
        "currency": "USD",
        "location": "USA",
        "state": "CA",
        "winecount": "10",
    }
    try:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        log.warning("  Marketplace API error for iWine=%d: %s", iwine, exc)
        return None

    listings = data.get("marketplaceArray", [])
    if not listings:
        return None

    prices = _extract_bottle_prices(listings)
    if not prices:
        return None

    prices.sort()
    avg = round(sum(prices) / len(prices), 2)
    median = prices[len(prices) // 2]

    merchants = [l.get("merchant-name", "") for l in listings]

    return {
        "iwine": iwine,
        "avg_price": avg,
        "min_price": prices[0],
        "max_price": prices[-1],
        "median_price": median,
        "num_listings": len(prices),
        "prices": prices,
        "merchants": merchants,
        "source": "CellarTrackerMarket",
        "is_real": True,
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


# ──────────────────────────────────────────────────────────────────────────────
# Main run loop
# ──────────────────────────────────────────────────────────────────────────────

async def run(args: argparse.Namespace) -> None:
    from playwright.async_api import async_playwright

    # --- Get or reuse PWHash ---
    pwhash = args.pwhash
    if not pwhash:
        pwhash = await get_pwhash(CT_USERNAME, CT_PASSWORD)
        log.info("Got PWHash. Add to .env: CELLARTRACKER_PWHASH=%s", pwhash)

    if args.login_only:
        print(f"\nCELLARTRACKER_PWHASH={pwhash}")
        return

    # --- Load existing maps/cache ---
    wine_id_map: dict[str, int] = {}
    if _WINE_ID_MAP_PATH.exists():
        wine_id_map = json.loads(_WINE_ID_MAP_PATH.read_text())
        log.info("Loaded %d existing iWine ID mappings", len(wine_id_map))

    prices_cache: dict[str, dict] = {}
    if _PRICES_PATH.exists():
        prices_cache = json.loads(_PRICES_PATH.read_text())
        log.info("Loaded %d existing price records", len(prices_cache))

    # --- Determine wines to process ---
    if args.ids:
        target_ids = [w for w in args.ids if w in WINE_CATALOG_BY_ID]
        missing = [w for w in args.ids if w not in WINE_CATALOG_BY_ID]
        if missing:
            log.warning("Unknown wine IDs: %s", missing)
    else:
        target_ids = list(WINE_CATALOG_BY_ID.keys())

    if args.skip_known:
        target_ids = [wid for wid in target_ids if wid not in wine_id_map]
        log.info("Skipping %d wines already in iWine map; %d remaining",
                 len(WINE_CATALOG_BY_ID) - len(target_ids), len(target_ids))

    if args.prices_only:
        # Only re-fetch prices for wines that already have iWine IDs
        target_ids = [wid for wid in target_ids if wid in wine_id_map]
        log.info("Prices-only mode: %d wines with iWine IDs", len(target_ids))

    total = len(target_ids)
    log.info("Processing %d wines…", total)

    # --- Phase 1: Resolve iWine IDs via browser search ---
    if not args.prices_only:
        needs_search = [wid for wid in target_ids if wid not in wine_id_map]
        if needs_search:
            log.info("Phase 1: Resolving iWine IDs for %d wines via browser…", len(needs_search))
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    )
                )
                page = await context.new_page()

                # Login
                await page.goto(CT_LOGIN_URL, wait_until="domcontentloaded")
                await page.fill('input[name="szUser"]', CT_USERNAME)
                await page.fill('input[name="szPassword"]', CT_PASSWORD)
                await page.click('input[value="Sign In"]')
                await page.wait_for_load_state("networkidle")
                log.info("Logged in to CellarTracker")

                found = 0
                for i, wid in enumerate(needs_search):
                    entry = WINE_CATALOG_BY_ID[wid]
                    log.info("[%d/%d] Searching iWine for: %s %s",
                             i + 1, len(needs_search), entry.producer, entry.name)

                    iwine = await search_iwine(entry, page)
                    if iwine:
                        wine_id_map[wid] = iwine
                        found += 1
                        log.info("  → iWine=%d", iwine)
                    else:
                        log.warning("  → NOT FOUND")

                    # Save map incrementally
                    if (i + 1) % 10 == 0:
                        _save_wine_id_map(wine_id_map)
                        log.info("  Saved map (%d/%d found)", found, i + 1)

                    # Polite delay between searches
                    delay = SEARCH_DELAY_MIN + (SEARCH_DELAY_MAX - SEARCH_DELAY_MIN) * 0.5
                    await asyncio.sleep(delay)

                await browser.close()

            _save_wine_id_map(wine_id_map)
            reload_wine_id_map()
            log.info("Phase 1 complete: %d/%d iWine IDs resolved", found, len(needs_search))
        else:
            log.info("Phase 1 skipped — all wines already have iWine IDs")

    # --- Phase 2: Fetch marketplace prices ---
    priced_ids = [wid for wid in target_ids if wid in wine_id_map]
    log.info("Phase 2: Fetching marketplace prices for %d wines…", len(priced_ids))

    success = 0
    failed = 0
    bad_map: list[str] = []   # wines where price validates as wrong match

    async with httpx.AsyncClient(
        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
        timeout=15.0,
        follow_redirects=True,
    ) as client:
        for i, wid in enumerate(priced_ids):
            entry = WINE_CATALOG_BY_ID[wid]
            iwine = wine_id_map[wid]

            log.info("[%d/%d] Pricing: iWine=%d  %s %s",
                     i + 1, len(priced_ids), iwine, entry.producer[:30], entry.name[:30])

            price_data = await fetch_market_prices(iwine, CT_USERNAME, pwhash, client)

            if price_data:
                # Validate: is the price roughly in the expected range?
                catalog_price = entry.avg_retail_price
                returned_price = price_data["avg_price"]
                ratio = returned_price / catalog_price if catalog_price else 1.0

                if ratio < 0.1 or ratio > 10.0:
                    # Price is more than 10x off — likely a wrong wine match
                    log.warning(
                        "  → PRICE MISMATCH: got $%.0f vs catalog $%.0f (ratio=%.2f) — rejecting",
                        returned_price, catalog_price, ratio
                    )
                    bad_map.append(wid)
                    del wine_id_map[wid]
                    failed += 1
                else:
                    prices_cache[wid] = price_data
                    success += 1
                    log.info("  → avg=$%.2f  range=$%.0f–$%.0f  (%d listings)",
                             price_data["avg_price"], price_data["min_price"],
                             price_data["max_price"], price_data["num_listings"])
            else:
                # No active listings — keep the iWine mapping but no price data yet
                failed += 1
                log.warning("  → No active marketplace listings")

            # Save incrementally
            if (i + 1) % 20 == 0:
                _PRICES_PATH.write_text(json.dumps(prices_cache, indent=2))
                _save_wine_id_map(wine_id_map)
                log.info("  Saved prices (%d/%d ok, %d bad maps)", success, i + 1, len(bad_map))

            # Rate limit
            delay = MIN_DELAY + (MAX_DELAY - MIN_DELAY) * 0.5
            await asyncio.sleep(delay)

    if bad_map:
        log.warning("Rejected %d bad iWine mappings: %s", len(bad_map), bad_map[:10])

    _PRICES_PATH.write_text(json.dumps(prices_cache, indent=2))

    total_wines = len(WINE_CATALOG_BY_ID)
    covered = len(prices_cache)
    coverage = covered / total_wines * 100

    log.info("=" * 60)
    log.info("Done! Prices fetched: %d ok, %d failed", success, failed)
    log.info("Total cached: %d / %d wines  (%.1f%% catalog coverage)",
             covered, total_wines, coverage)
    log.info("Results: %s", _PRICES_PATH)
    log.info("iWine map: %s", _WINE_ID_MAP_PATH)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="CellarTracker bulk price scraper")
    p.add_argument("--ids", nargs="+", metavar="WINE_ID",
                   help="Only process specific catalog IDs (e.g. opus-one chateau-margaux)")
    p.add_argument("--skip-known", action="store_true",
                   help="Skip wines that already have an iWine ID in the map")
    p.add_argument("--prices-only", action="store_true",
                   help="Skip iWine ID discovery; only refresh prices for mapped wines")
    p.add_argument("--login-only", action="store_true",
                   help="Just print a fresh PWHash and exit (use to update .env)")
    p.add_argument("--pwhash",
                   help="Use this PWHash instead of logging in (overrides auto-login)")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run(args))
