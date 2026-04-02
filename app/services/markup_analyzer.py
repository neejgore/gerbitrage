"""
Markup analysis and fairness scoring.

Fairness Score (0–100)
──────────────────────
Measures how reasonably a restaurant has priced a wine relative to
market norms.  100 = exceptional value.  0 = egregious markup.

Industry baseline (wholesale → menu price multiples):
  budget   (retail < $25):   fair range = 3.0×–4.5× wholesale
  mid      ($25–$75):        fair range = 2.8×–4.0× wholesale
  premium  ($75–$200):       fair range = 2.5×–3.5× wholesale
  luxury   ($200–$600):      fair range = 2.0×–3.0× wholesale
  ultra    ($600+):          fair range = 1.75×–2.5× wholesale

Wholesale ≈ 50–62% of average retail (see pricing_aggregator.py).
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from app.schemas.analysis import MarkupAnalysis


# ---------------------------------------------------------------------------
# Tier configs
# ---------------------------------------------------------------------------

@dataclass
class TierConfig:
    ideal_wholesale_multiple: float   # target markup (restaurant/wholesale)
    fair_low: float                   # lower bound – below this is "great deal"
    fair_high: float                  # upper bound – above this is "high markup"
    excessive_threshold: float        # above this → "excessive"


_TIER_CONFIG: dict[str, TierConfig] = {
    "budget": TierConfig(
        ideal_wholesale_multiple=3.50,
        fair_low=2.80,
        fair_high=4.50,
        excessive_threshold=5.50,
    ),
    "mid": TierConfig(
        ideal_wholesale_multiple=3.20,
        fair_low=2.50,
        fair_high=4.00,
        excessive_threshold=5.00,
    ),
    "premium": TierConfig(
        ideal_wholesale_multiple=2.80,
        fair_low=2.25,
        fair_high=3.50,
        excessive_threshold=4.50,
    ),
    "luxury": TierConfig(
        ideal_wholesale_multiple=2.40,
        fair_low=1.80,
        fair_high=3.00,
        excessive_threshold=4.00,
    ),
    "ultra": TierConfig(
        ideal_wholesale_multiple=2.00,
        fair_low=1.50,
        fair_high=2.50,
        excessive_threshold=3.50,
    ),
}

_DEFAULT_CONFIG = _TIER_CONFIG["mid"]


# ---------------------------------------------------------------------------
# Verdict mapping
# ---------------------------------------------------------------------------

def _verdict(score: int) -> tuple[str, str]:
    """Returns (verdict_key, verdict_label) based purely on fairness score."""
    if score >= 90:
        return "exceptional_value", "Exceptional Value"
    if score >= 75:
        return "fair", "Fair"
    if score >= 55:
        return "moderate_markup", "Moderate Markup"
    if score >= 35:
        return "high_markup", "High Markup"
    if score >= 15:
        return "excessive_markup", "Excessive Markup"
    return "price_gouging", "Price Gouging"


def _build_flags(
    menu_price: float,
    avg_retail: float,
    wholesale: float,
    wholesale_multiple: float,
    retail_multiple: float,
    tier_cfg: TierConfig,
) -> list[str]:
    flags = []
    if wholesale_multiple <= tier_cfg.fair_low:
        flags.append("below_market")
    if wholesale_multiple >= tier_cfg.excessive_threshold:
        flags.append("excessive_markup")
    if retail_multiple >= 4.0:
        flags.append("price_gouging")
    if retail_multiple <= 1.0:
        flags.append("below_retail")
    if menu_price < wholesale:
        flags.append("below_wholesale")
    return flags


def _build_insight(
    wine_name: str,
    menu_price: float,
    avg_retail: float,
    estimated_wholesale: float,
    wholesale_multiple: float,
    retail_multiple: float,
    score: int,
    tier_cfg: TierConfig,
    price_tier: str,
) -> str:
    if menu_price <= estimated_wholesale:
        return (
            f"At ${menu_price:.0f}, this wine is priced at or below estimated wholesale "
            f"(~${estimated_wholesale:.0f}).  This is an extraordinary value."
        )
    if wholesale_multiple <= tier_cfg.fair_low:
        return (
            f"Priced at {wholesale_multiple:.1f}× estimated wholesale (${estimated_wholesale:.0f}), "
            f"this is below the typical restaurant range of {tier_cfg.fair_low:.1f}–{tier_cfg.fair_high:.1f}×. "
            f"Great value relative to a retail price of ~${avg_retail:.0f}."
        )
    if wholesale_multiple <= tier_cfg.fair_high:
        return (
            f"At ${menu_price:.0f} ({wholesale_multiple:.1f}× estimated wholesale), "
            f"this falls within the typical restaurant range of "
            f"{tier_cfg.fair_low:.1f}–{tier_cfg.fair_high:.1f}×. "
            f"Retail is ~${avg_retail:.0f}."
        )
    if wholesale_multiple <= tier_cfg.excessive_threshold:
        return (
            f"At ${menu_price:.0f}, the markup is {wholesale_multiple:.1f}× estimated wholesale "
            f"(${estimated_wholesale:.0f}), above the typical range of "
            f"{tier_cfg.fair_low:.1f}–{tier_cfg.fair_high:.1f}×. "
            f"Average retail is ~${avg_retail:.0f}."
        )
    return (
        f"At ${menu_price:.0f}, the markup is {wholesale_multiple:.1f}× estimated wholesale "
        f"(${estimated_wholesale:.0f}).  Average retail is ~${avg_retail:.0f}. "
        f"This significantly exceeds the typical restaurant range of "
        f"{tier_cfg.fair_low:.1f}–{tier_cfg.fair_high:.1f}×."
    )


# ---------------------------------------------------------------------------
# Scoring function
# ---------------------------------------------------------------------------

def _compute_score(wholesale_multiple: float, tier_cfg: TierConfig) -> int:
    """
    Map the wholesale multiple to a 0–100 fairness score using an
    exponential decay curve centred around the tier's ideal multiple.

      – Below fair_low  → 85–100 (increasingly generous)
      – Between fair_low and fair_high → 60–85
      – Between fair_high and excessive → 20–60
      – Above excessive → 0–20
    """
    m = wholesale_multiple
    ideal = tier_cfg.ideal_wholesale_multiple
    fair_low = tier_cfg.fair_low
    fair_high = tier_cfg.fair_high
    excessive = tier_cfg.excessive_threshold

    if m <= fair_low:
        # Below expected – reward generously
        bonus = max(0.0, (fair_low - m) / fair_low) * 30.0
        return min(100, round(85 + bonus))

    if m <= fair_high:
        # In-range – linear interpolation from 85 → 60
        t = (m - fair_low) / (fair_high - fair_low)
        return round(85 - t * 25)

    if m <= excessive:
        # Above range – steep drop from 60 → 20
        t = (m - fair_high) / (excessive - fair_high)
        return round(60 - t * 40)

    # Above excessive threshold – exponential decay to 0
    overshoot = (m - excessive) / excessive
    score = 20.0 * math.exp(-3.0 * overshoot)
    return max(0, round(score))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_markup(
    menu_price: float,
    avg_retail: float,
    estimated_wholesale: float,
    price_tier: str,
    wine_name: str = "this wine",
) -> MarkupAnalysis:
    """
    Compute the full markup analysis for a given menu price.

    Returns a MarkupAnalysis Pydantic model ready to include in the API response.
    """
    tier_cfg = _TIER_CONFIG.get(price_tier, _DEFAULT_CONFIG)

    retail_multiple = round(menu_price / avg_retail, 3) if avg_retail else None
    wholesale_multiple = round(menu_price / estimated_wholesale, 3) if estimated_wholesale else None

    if wholesale_multiple is None:
        return MarkupAnalysis(
            menu_price=menu_price,
            avg_retail=avg_retail,
            estimated_wholesale=estimated_wholesale,
            price_tier=price_tier,
        )

    score = _compute_score(wholesale_multiple, tier_cfg)
    verdict_key, verdict_label = _verdict(score)
    flags = _build_flags(
        menu_price, avg_retail, estimated_wholesale,
        wholesale_multiple, retail_multiple or 0, tier_cfg
    )
    insight = _build_insight(
        wine_name, menu_price, avg_retail, estimated_wholesale,
        wholesale_multiple, retail_multiple or 0, score, tier_cfg, price_tier
    )

    return MarkupAnalysis(
        menu_price=menu_price,
        avg_retail=avg_retail,
        estimated_wholesale=estimated_wholesale,
        retail_multiple=retail_multiple,
        wholesale_multiple=wholesale_multiple,
        industry_standard_wholesale_range=(tier_cfg.fair_low, tier_cfg.fair_high),
        fairness_score=score,
        verdict=verdict_key,
        verdict_label=verdict_label,
        flags=flags,
        insight=insight,
        price_tier=price_tier,
    )
