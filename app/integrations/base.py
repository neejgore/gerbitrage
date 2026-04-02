"""
Base class for pricing integrations.

Every integration must implement `fetch_pricing()`.
The aggregator calls all available providers and merges the results.
"""
from __future__ import annotations

import asyncio
import logging
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class RawPricingResult:
    """Pricing data returned by a single integration source."""
    source: str
    avg_price: Optional[float]
    min_price: Optional[float]
    max_price: Optional[float]
    median_price: Optional[float]
    num_listings: Optional[int]
    url: Optional[str] = None
    currency: str = "USD"


class RateLimiter:
    """
    Per-provider token-bucket rate limiter with jitter.

    Ensures a minimum gap between consecutive requests to the same host,
    with random jitter so requests don't form a detectable pattern.

    Args:
        min_delay: minimum seconds between requests (default 2 s)
        max_delay: maximum seconds between requests (default 5 s)
        backoff_on: HTTP status codes that trigger exponential backoff
        max_backoff: ceiling for backoff sleep (seconds)
    """

    def __init__(
        self,
        min_delay: float = 2.0,
        max_delay: float = 5.0,
        backoff_on: frozenset[int] = frozenset({429, 503, 403}),
        max_backoff: float = 120.0,
    ):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.backoff_on = backoff_on
        self.max_backoff = max_backoff
        self._last_request: float = 0.0
        self._consecutive_errors: int = 0
        self._lock = asyncio.Lock()

    async def wait(self) -> None:
        """Wait the appropriate delay before the next request."""
        async with self._lock:
            now = time.monotonic()
            base_delay = random.uniform(self.min_delay, self.max_delay)

            # Exponential backoff after repeated errors
            if self._consecutive_errors > 0:
                backoff = min(
                    base_delay * (2 ** self._consecutive_errors),
                    self.max_backoff,
                )
                base_delay = backoff

            elapsed = now - self._last_request
            sleep_for = max(0.0, base_delay - elapsed)

            if sleep_for > 0:
                logger.debug("Rate limiter: sleeping %.1fs", sleep_for)
                await asyncio.sleep(sleep_for)

            self._last_request = time.monotonic()

    def record_success(self) -> None:
        self._consecutive_errors = 0

    def record_error(self, status_code: Optional[int] = None) -> None:
        if status_code is None or status_code in self.backoff_on:
            self._consecutive_errors += 1
        else:
            self._consecutive_errors = 0


class BasePricingProvider(ABC):
    """Abstract base for all pricing providers."""

    name: str = "unknown"

    # Subclasses may override to tune rate limiting for their target site.
    # Scrapers should use higher delays; API providers can use lower ones.
    _rate_limiter: RateLimiter = field(default_factory=RateLimiter)

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        # Give every subclass its own independent rate limiter instance
        # so Benchmark and Total Wine don't share state.
        cls._rate_limiter = RateLimiter()

    @abstractmethod
    async def fetch_pricing(
        self,
        wine_name: str,
        producer: str,
        vintage: Optional[int] = None,
        wine_id: Optional[str] = None,
    ) -> Optional[RawPricingResult]:
        """
        Fetch pricing data for a wine.

        Returns None when the provider cannot find the wine or is unavailable.
        """
        ...

    def is_available(self) -> bool:
        """Return True when the provider's API key / credentials are configured."""
        return True


# ---------------------------------------------------------------------------
# Shared mock utility – used by all providers when keys are absent
# ---------------------------------------------------------------------------

def _mock_price_from_base(
    base_price: float,
    vintage: Optional[int],
    source: str,
    spread_factor: float = 0.15,
    seed_key: str = "",
) -> RawPricingResult:
    """
    Generate a deterministic mock pricing result based on the wine's known avg_retail.

    Uses a seeded RNG (keyed on wine name + vintage + source) so the same wine
    always returns the same mock price — no drift across cache refreshes.

    Vintage adjustments reflect real-world variation:
      - Great vintages (e.g. 2015, 2016, 2019) push price up ~15–25 %
      - Off vintages push price down ~10–20 %
      - No vintage → use base_price as-is
    """
    great_vintages = {2015, 2016, 2018, 2019, 2010, 2009, 2005, 2000, 1996, 1990}
    decent_vintages = {2014, 2017, 2012, 2008, 2006, 2004}

    # Deterministic seed: same wine + vintage + source always → same number
    seed = hash(f"{seed_key}:{vintage}:{source}") & 0x7FFFFFFF
    rng = random.Random(seed)

    multiplier = 1.0
    if vintage:
        if vintage in great_vintages:
            multiplier = rng.uniform(1.15, 1.30)
        elif vintage in decent_vintages:
            multiplier = rng.uniform(1.00, 1.12)
        else:
            multiplier = rng.uniform(0.85, 1.05)

    source_noise = rng.uniform(1 - spread_factor, 1 + spread_factor)
    avg = round(base_price * multiplier * source_noise, 2)

    spread = avg * 0.18
    min_p = round(max(avg - spread, avg * 0.70), 2)
    max_p = round(avg + spread, 2)
    median_p = round((avg + min_p) / 2, 2)
    listings = rng.randint(3, 120)

    return RawPricingResult(
        source=source,
        avg_price=avg,
        min_price=min_p,
        max_price=max_p,
        median_price=median_p,
        num_listings=listings,
    )
