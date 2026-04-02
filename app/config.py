from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")

    # Application
    app_name: str = "Wine Pricing Intelligence API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str = "postgresql+asyncpg://gerbitrage:gerbitrage@localhost:5432/gerbitrage"

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 3600

    # ── Pricing integrations ─────────────────────────────────────────────────
    # Wine-Searcher Pro API  →  https://www.wine-searcher.com/trade/api
    #   Plans: $335/mo (500 calls/day) · $535/mo (1000 calls/day)
    wine_searcher_api_key: Optional[str] = None

    # CellarTracker  →  free account at cellartracker.com
    #   Community purchase prices + critic scores for 3.5M+ wines.
    cellartracker_username: Optional[str] = None
    cellartracker_password: Optional[str] = None
    # PWHash is the user's persistent auth cookie used by the marketplace API.
    # Run: python scripts/ct_bulk_scrape.py --login-only  to get/refresh it.
    cellartracker_pwhash: Optional[str] = None

    # Wine.com affiliate API  →  apply at wine.com/api (partner account)
    wine_com_api_key: Optional[str] = None

    # Total Wine session cookie  →  copy from browser devtools after logging in
    #   Paste the full value of the "pxcts" or session cookie here to bypass
    #   PerimeterX bot protection on the Total Wine scraper.
    total_wine_session_cookie: Optional[str] = None

    # Flip to False once any real credential is set
    use_mock_pricing: bool = True

    # Set to False when a background worker is already running Playwright
    # scraping in the same container — avoids two browsers competing for RAM.
    vivino_live_search: bool = True

    # Identification confidence thresholds
    high_confidence_threshold: float = 0.85
    medium_confidence_threshold: float = 0.65
    min_match_threshold: float = 0.45

    # API limits
    max_batch_size: int = 50

    # Scheduled price refresh
    # How often (in hours) to pre-warm the pricing cache for all catalog wines.
    # Set to 0 to disable the scheduler entirely.
    price_refresh_interval_hours: int = 6
    # Max concurrent provider calls during a scheduled refresh
    # (keeps us from hammering external APIs all at once).
    price_refresh_concurrency: int = 5


@lru_cache
def get_settings() -> Settings:
    return Settings()
