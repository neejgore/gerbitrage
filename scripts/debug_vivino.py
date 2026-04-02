#!/usr/bin/env python3
"""Debug script: inspect Vivino page text to understand DOM/price structure."""
import asyncio
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

async def main():
    from playwright.async_api import async_playwright

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            ),
            locale="en-US",
        )
        page = await context.new_page()

        url = "https://www.vivino.com/search/wines?q=Opus+One+Winery"
        print(f"Loading: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        await page.wait_for_timeout(3500)

        # Get rendered text
        text = await page.evaluate("() => document.body.innerText")
        prices = re.findall(r"\$[\d,]+(?:\.\d{2})?", text)
        print(f"\nAll price strings on page: {prices[:20]}")
        print("\n--- First 60 non-empty lines of page text ---")
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        for line in lines[:60]:
            print(repr(line[:120]))

        # Also try to get any anchor hrefs with /wines/ pattern
        wine_links = await page.evaluate("""
            () => Array.from(document.querySelectorAll('a[href*="/wines/"], a[href*="/w/"]'))
                       .slice(0, 10)
                       .map(a => ({href: a.href, text: a.innerText.trim().slice(0, 80)}))
        """)
        print("\n--- Wine links found ---")
        for link in wine_links:
            print(f"  {link['href'][:80]}  →  {link['text'][:50]}")

        # Check what class names exist with "price" in them
        price_classes = await page.evaluate("""
            () => {
                const els = document.querySelectorAll('*');
                const seen = new Set();
                for (const el of els) {
                    for (const cls of el.classList) {
                        if (cls.toLowerCase().includes('price')) seen.add(cls);
                    }
                }
                return Array.from(seen).slice(0, 20);
            }
        """)
        print("\n--- CSS classes containing 'price' ---")
        for cls in price_classes:
            print(f"  .{cls}")

        await browser.close()

asyncio.run(main())
