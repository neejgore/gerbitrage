#!/usr/bin/env python3
"""
Vivino Bulk Price Scraper
=========================
Prices every wine in the catalog across multiple vintages using Vivino search,
then writes results to:

  app/data/vivino_prices_cache.json

  Keys:  "wine_id"          → generic (vintage-agnostic) price
         "wine_id-2018"     → price for that specific vintage

Estimated runtime: ~40 min for 694 wines × 1 vintage; ~7 h for 10 vintages.

Usage
-----
  python scripts/vivino_price_all.py                         # all wines, no vintage
  python scripts/vivino_price_all.py --skip-known            # only uncached entries
  python scripts/vivino_price_all.py --vintages 2018 2019 2020  # specific vintages
  python scripts/vivino_price_all.py --vintages all          # 2013–2023 (full matrix)
  python scripts/vivino_price_all.py --ids opus-one          # specific wine(s)
  python scripts/vivino_price_all.py --concurrency 2         # 2 parallel tabs

Requirements
------------
  pip install playwright
  playwright install chromium
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.data.wine_catalog import WINE_CATALOG, WINE_CATALOG_BY_ID
from app.integrations.vivino import (
    _PRICES_CACHE_PATH,
    _load_price_cache,
    _save_price_cache,
    scrape_vivino_price,
    build_search_query,
)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("vivino_price")

# ── Constants ─────────────────────────────────────────────────────────────────
MIN_DELAY = 3.0   # seconds between searches per tab
MAX_DELAY = 5.5
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)


# ──────────────────────────────────────────────────────────────────────────────
# Worker: one browser tab pricing a queue of wines
# ──────────────────────────────────────────────────────────────────────────────

async def price_worker(
    worker_id: int,
    queue: asyncio.Queue,
    cache: dict,
    stats: dict,
    context,
) -> None:
    """Single Playwright tab worker: pops (wine, vintage) pairs from queue."""
    page = await context.new_page()
    await page.route(
        "**/*.{png,jpg,gif,webp,svg,woff,woff2,ttf}",
        lambda r: r.abort(),
    )

    while True:
        try:
            entry, vintage = queue.get_nowait()
        except asyncio.QueueEmpty:
            break

        # Cache key is "wine_id-2018" for vintage-specific, "wine_id" for generic
        cache_key = f"{entry.id}-{vintage}" if vintage else entry.id
        vintage_label = str(vintage) if vintage else "generic"
        log.info(
            "[W%d] %d remaining | %s – %s  [%s]",
            worker_id, queue.qsize(), entry.producer[:20], entry.name[:25], vintage_label,
        )

        try:
            result = await scrape_vivino_price(
                page,
                entry.name,
                entry.producer,
                vintage,
                entry.avg_retail_price,
            )
        except Exception as exc:
            log.warning("[W%d] Error for %s: %s", worker_id, cache_key, exc)
            result = None

        if result:
            cache[cache_key] = result
            stats["found"] += 1
            log.info(
                "[W%d] ✓ %s  avg $%.0f  [%s]",
                worker_id, cache_key, result.get("avg_price", 0),
                result.get("vivino_name", "")[:30],
            )
        else:
            stats["not_found"] += 1
            log.info("[W%d] ✗ %s – no result", worker_id, cache_key)

        _save_price_cache(dict(cache))
        await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))
        queue.task_done()

    await page.close()


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

async def main(args: argparse.Namespace) -> None:
    from playwright.async_api import async_playwright

    cache = _load_price_cache()
    log.info("Loaded %d existing cache entries", len(cache))

    # ── Resolve vintages ──────────────────────────────────────────────────────
    ALL_VINTAGES = list(range(2013, 2024))  # 2013–2023 inclusive
    if not args.vintages:
        vintages: list[int | None] = [None]   # generic (no year) only
    elif args.vintages == ["all"]:
        vintages = ALL_VINTAGES                # type: ignore[assignment]
    else:
        vintages = [int(y) for y in args.vintages]  # type: ignore[assignment]

    # ── Resolve wines ─────────────────────────────────────────────────────────
    if args.ids:
        wines = [WINE_CATALOG_BY_ID[wid] for wid in args.ids if wid in WINE_CATALOG_BY_ID]
        missing = [wid for wid in args.ids if wid not in WINE_CATALOG_BY_ID]
        if missing:
            log.warning("Unknown wine IDs: %s", missing)
    else:
        wines = list(WINE_CATALOG)

    # ── Build (wine, vintage) work items ──────────────────────────────────────
    work_items: list[tuple] = []
    for w in wines:
        for v in vintages:
            cache_key = f"{w.id}-{v}" if v else w.id
            if args.skip_known and cache_key in cache:
                continue
            work_items.append((w, v))

    if not work_items:
        log.info("Nothing to process — all entries already cached.")
        return

    log.info(
        "Processing %d work items (%d wines × %d vintages) with %d worker(s)…",
        len(work_items), len(wines), len(vintages), args.concurrency,
    )

    queue: asyncio.Queue = asyncio.Queue()
    for item in work_items:
        queue.put_nowait(item)

    stats = {"found": 0, "not_found": 0}
    start = time.monotonic()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=USER_AGENT,
            locale="en-US",
            timezone_id="America/Los_Angeles",
            viewport={"width": 1280, "height": 900},
        )

        # Launch concurrent workers
        workers = [
            price_worker(i + 1, queue, cache, stats, context)
            for i in range(args.concurrency)
        ]
        await asyncio.gather(*workers)
        await browser.close()

    elapsed = time.monotonic() - start
    total = stats["found"] + stats["not_found"]
    log.info(
        "\n"
        "═══════════════════════════════════════\n"
        "  Vivino pricing complete\n"
        "  Found:     %d / %d  (%.0f%%)\n"
        "  Not found: %d\n"
        "  Runtime:   %.1f min\n"
        "═══════════════════════════════════════",
        stats["found"], total,
        100 * stats["found"] / max(total, 1),
        stats["not_found"],
        elapsed / 60,
    )

    # Final save
    _save_price_cache(dict(cache))
    log.info("Results saved to %s", _PRICES_CACHE_PATH)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Vivino bulk wine pricer")
    parser.add_argument(
        "--ids", nargs="+", metavar="WINE_ID",
        help="Only price specific wine IDs (e.g. opus-one chateau-margaux)",
    )
    parser.add_argument(
        "--skip-known", action="store_true",
        help="Skip entries that already have a cached price",
    )
    parser.add_argument(
        "--concurrency", type=int, default=1, metavar="N",
        help="Number of parallel browser tabs (default 1; max 3 before blocks)",
    )
    parser.add_argument(
        "--vintages", nargs="+", metavar="YEAR",
        help=(
            "Vintages to price per wine. Use 'all' for 2013–2023, "
            "or list years: --vintages 2018 2019 2020. "
            "Omit for generic (no-vintage) pricing only."
        ),
    )
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(main(parse_args()))
