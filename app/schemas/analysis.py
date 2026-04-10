from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.pricing import PricingBreakdown


class PriceSource(str, Enum):
    """
    How the pricing data was obtained.  Callers should use this to decide
    how much weight to place on the numbers.

    - ``catalog``                  – wine matched our curated catalog; price is
                                     the hand-verified retail reference value.
    - ``market_live``              – live Wine-Searcher market data fetched at
                                     request time; reflects real current listings.
    - ``producer_adjusted_estimate`` – wine not in catalog; regional base price
                                     scaled by a known-producer multiplier.
                                     Directionally accurate but not market data.
    - ``regional_estimate``        – wine not in catalog and producer unknown;
                                     estimate based on appellation/varietal bucket
                                     only.  Wide confidence interval; use with care.
    - ``unavailable``              – no pricing could be determined.
    """
    catalog                    = "catalog"
    market_live                = "market_live"
    producer_adjusted_estimate = "producer_adjusted_estimate"
    regional_estimate          = "regional_estimate"
    unavailable                = "unavailable"


class EffectivePricing(BaseModel):
    """
    Single unified pricing object always present on the response.
    Consumers should use this instead of toggling between ``pricing``
    and ``dynamic_pricing``.
    """
    avg_retail: Optional[float] = None
    min_retail: Optional[float] = None
    max_retail: Optional[float] = None
    estimated_wholesale: Optional[float] = None
    price_tier: Optional[str] = None
    currency: str = "USD"
    # ── provenance ──────────────────────────────────────────────────────────
    price_source: PriceSource = Field(
        description="Canonical source tag – the single field to check for data quality.",
    )
    price_basis_note: str = Field(
        description=(
            "Human-readable one-liner explaining exactly how this price was derived, "
            "e.g. 'Matched Domaine Leflaive Puligny-Montrachet in curated catalog' or "
            "'Regional proxy for Vosne-Romanée scaled by DRC producer premium (×18)'."
        ),
    )
    data_confidence: Literal["high", "medium", "low"] = Field(
        description="high = catalog or live market data; medium = producer-adjusted; low = regional bucket only.",
    )
    # ── live-market extras (populated only when price_source = market_live) ─
    num_listings: Optional[int] = None
    url: Optional[str] = None
    last_updated: Optional[datetime] = None


class DynamicPricingBreakdown(BaseModel):
    """Pricing estimate for wines not found in the static catalog."""
    avg_retail: Optional[float] = None
    min_retail: Optional[float] = None
    max_retail: Optional[float] = None
    estimated_wholesale: Optional[float] = None
    data_source: str = Field(
        description=(
            "'wine_searcher_live', 'producer_adjusted_estimate', or 'regional_proxy'"
        ),
    )
    data_confidence: str = Field(
        description="'high', 'medium', or 'low'",
    )
    price_tier: str
    num_listings: Optional[int] = None
    url: Optional[str] = None
    notes: Optional[str] = None
    last_updated: Optional[datetime] = None


class AnalyzeRequest(BaseModel):
    menu_text: str = Field(..., min_length=2, max_length=500, description="Raw wine name as it appears on the menu")
    menu_price: Optional[float] = Field(None, gt=0, description="Price listed on the menu (USD)")
    vintage: Optional[int] = Field(None, ge=1900, le=2030, description="Override vintage if known")
    venue_id: Optional[str] = Field(None, description="Optional venue identifier for analytics")
    wine_id: Optional[str] = Field(
        None,
        description=(
            "Optional catalog wine ID (from GET /search). When supplied the "
            "identification step is skipped and this wine is used directly, "
            "ensuring the result matches exactly what was shown in autocomplete."
        ),
    )


class BatchAnalyzeRequest(BaseModel):
    items: list[AnalyzeRequest] = Field(..., min_length=1, max_length=50)
    venue_id: Optional[str] = None


class ParsedComponents(BaseModel):
    """Structured breakdown of what was extracted from the raw menu text."""
    vintage: Optional[int] = None
    producer: Optional[str] = None
    wine_name: Optional[str] = None
    region: Optional[str] = None
    varietal: Optional[str] = None
    wine_type: Optional[str] = None
    format_ml: Optional[int] = None


class IdentificationAlternative(BaseModel):
    wine_id: str
    name: str
    producer: str
    region: Optional[str] = None
    confidence: float


class IdentificationResult(BaseModel):
    matched: bool
    confidence: float
    confidence_level: str  # very_high / high / medium / low / none
    wine_id: Optional[str] = None
    name: Optional[str] = None
    producer: Optional[str] = None
    vintage: Optional[int] = None
    region: Optional[str] = None
    appellation: Optional[str] = None
    varietal: Optional[str] = None
    wine_type: Optional[str] = None
    avg_retail_price: Optional[float] = None
    price_tier: Optional[str] = None
    alternatives: list[IdentificationAlternative] = []
    parsed_components: Optional[ParsedComponents] = None


class MarkupAnalysis(BaseModel):
    menu_price: float
    avg_retail: Optional[float] = None
    estimated_wholesale: Optional[float] = None
    retail_multiple: Optional[float] = None
    wholesale_multiple: Optional[float] = None
    industry_standard_wholesale_range: Optional[tuple[float, float]] = None
    fairness_score: Optional[int] = None          # 0–100
    verdict: Optional[str] = None                 # machine-readable key
    verdict_label: Optional[str] = None           # human-readable label
    flags: list[str] = []
    insight: Optional[str] = None
    price_tier: Optional[str] = None


class AnalysisMetadata(BaseModel):
    analyzed_at: datetime
    processing_time_ms: int


class AnalyzeResponse(BaseModel):
    input: AnalyzeRequest
    identification: IdentificationResult
    # ── unified pricing (always use this) ───────────────────────────────────
    effective_pricing: Optional[EffectivePricing] = Field(
        None,
        description=(
            "Single authoritative pricing object. Always populated when any "
            "pricing data is available. Use ``price_source`` to understand "
            "data quality before acting on the numbers."
        ),
    )
    # ── legacy / detailed breakdowns (kept for completeness) ────────────────
    pricing: Optional[PricingBreakdown] = Field(
        None,
        description="Detailed catalog pricing; present only when wine matched the catalog.",
    )
    dynamic_pricing: Optional[DynamicPricingBreakdown] = Field(
        None,
        description=(
            "Pricing estimate when the wine was not found in the catalog; "
            "sourced from Wine-Searcher live API, producer-adjusted proxy, "
            "or regional proxy table."
        ),
    )
    markup_analysis: Optional[MarkupAnalysis] = None
    metadata: AnalysisMetadata


class BatchAnalyzeResponse(BaseModel):
    results: list[AnalyzeResponse]
    total: int
    venue_id: Optional[str] = None
