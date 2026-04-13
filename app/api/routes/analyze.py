"""
POST /analyze       – analyse a single wine menu entry
POST /analyze/batch – analyse a list of wine menu entries
"""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.pricing import AnalysisLog
from app.schemas.analysis import (
    AnalysisMetadata,
    AnalyzeRequest,
    AnalyzeResponse,
    BatchAnalyzeRequest,
    BatchAnalyzeResponse,
    DynamicPricingBreakdown,
    EffectivePricing,
    IdentificationAlternative,
    IdentificationResult,
    ParsedComponents,
    PriceSource,
)
from app.services.dynamic_lookup import DynamicPricingResult, dynamic_lookup
from app.services.markup_analyzer import analyze_markup
from app.services.pricing_aggregator import get_pricing
from app.services.wine_identifier import identify_wine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analyze", tags=["Analysis"])


# ---------------------------------------------------------------------------
# Core analysis helper
# ---------------------------------------------------------------------------

async def _run_analysis(
    req: AnalyzeRequest,
    db: Optional[AsyncSession] = None,
) -> AnalyzeResponse:
    start = time.monotonic()

    # ── 1. Identify wine ────────────────────────────────────────────────────
    # If the caller supplies a wine_id (e.g. picked from autocomplete) we skip
    # fuzzy re-identification and use that wine directly.  This guarantees the
    # result always matches what the autocomplete showed.
    if req.wine_id:
        from app.services.wine_identifier import get_wine_by_id_full, _confidence_level
        from app.services.wine_identifier import WineMatch
        pinned = get_wine_by_id_full(req.wine_id)
        if pinned:
            from app.services.text_parser import parse_wine_text
            _parsed = parse_wine_text(req.menu_text)
            _vintage = req.vintage or _parsed.vintage
            best = WineMatch(
                wine=pinned,
                score=1.0,
                confidence_level="very_high",
                score_breakdown={"pinned_wine_id": req.wine_id},
            )
            alternatives = []
        else:
            best, alternatives = identify_wine(req.menu_text, vintage_override=req.vintage)
    else:
        best, alternatives = identify_wine(req.menu_text, vintage_override=req.vintage)

    # Build IdentificationResult
    ident = _build_identification(req.menu_text, best, alternatives, vintage_override=req.vintage)

    # ── 2. Fetch pricing ─────────────────────────────────────────────────────
    pricing = None
    markup = None
    dynamic_pricing: Optional[DynamicPricingResult] = None

    if ident.matched and ident.wine_id:
        from app.services.wine_identifier import get_wine_by_id_full
        wine = get_wine_by_id_full(ident.wine_id)
        if wine:
            pricing = await get_pricing(
                wine_id=wine.id,
                wine_name=wine.name,
                producer=wine.producer,
                avg_retail_base=wine.avg_retail_price,
                price_tier=wine.price_tier or "mid",
                vintage=ident.vintage,
            )

            # ── 3. Markup analysis ─────────────────────────────────────────
            if req.menu_price and pricing.avg_retail and pricing.estimated_wholesale:
                markup = analyze_markup(
                    menu_price=req.menu_price,
                    avg_retail=pricing.avg_retail,
                    estimated_wholesale=pricing.estimated_wholesale,
                    price_tier=wine.price_tier or "mid",
                    wine_name=wine.name,
                )
    else:
        # ── Dynamic lookup for catalog misses ─────────────────────────────
        from app.services.text_parser import parse_wine_text
        parsed = parse_wine_text(req.menu_text)
        if req.vintage:
            parsed.vintage = req.vintage
        dynamic_pricing = await dynamic_lookup(req.menu_text, parsed)

        if dynamic_pricing and req.menu_price:
            avg = dynamic_pricing.avg_retail
            wholesale = dynamic_pricing.estimated_wholesale
            if avg and wholesale:
                markup = analyze_markup(
                    menu_price=req.menu_price,
                    avg_retail=avg,
                    estimated_wholesale=wholesale,
                    price_tier=dynamic_pricing.price_tier,
                    wine_name=req.menu_text,
                )

    # ── 4. Log to DB (best-effort, never blocks response) ───────────────────
    if db:
        await _log_analysis(
            db=db,
            menu_text=req.menu_text,
            menu_price=req.menu_price,
            wine_id=ident.wine_id,
            confidence=ident.confidence,
            fairness_score=markup.fairness_score if markup else None,
            verdict=markup.verdict if markup else None,
            venue_id=req.venue_id,
        )

    elapsed_ms = round((time.monotonic() - start) * 1000)

    # ── Convert DynamicPricingResult → schema ───────────────────────────────
    dynamic_pricing_schema: Optional[DynamicPricingBreakdown] = None
    if dynamic_pricing:
        dynamic_pricing_schema = DynamicPricingBreakdown(
            avg_retail=dynamic_pricing.avg_retail,
            min_retail=dynamic_pricing.min_retail,
            max_retail=dynamic_pricing.max_retail,
            estimated_wholesale=dynamic_pricing.estimated_wholesale,
            data_source=dynamic_pricing.data_source,
            data_confidence=dynamic_pricing.data_confidence,
            price_tier=dynamic_pricing.price_tier,
            num_listings=dynamic_pricing.num_listings,
            url=dynamic_pricing.url,
            notes=dynamic_pricing.notes,
            last_updated=dynamic_pricing.last_updated,
        )

    # ── Build EffectivePricing (single canonical pricing object) ────────────
    effective: Optional[EffectivePricing] = None

    if ident.matched and pricing and pricing.avg_retail is not None:
        # Path A: catalog hit with real pricing data
        wine_name = ident.name or req.menu_text
        # Map aggregator confidence to EffectivePricing levels
        agg_conf = pricing.data_confidence or "low"
        eff_conf: str = agg_conf if agg_conf in ("high", "medium", "low") else "low"
        # Describe where the price came from
        source_note = (
            f"Matched '{wine_name}' in curated catalog "
            f"(confidence {ident.confidence:.0%}). "
            f"Price from: {pricing.source}."
        )
        effective = EffectivePricing(
            avg_retail=pricing.avg_retail,
            min_retail=pricing.min_retail,
            max_retail=pricing.max_retail,
            estimated_wholesale=pricing.estimated_wholesale,
            price_tier=ident.price_tier,
            currency=pricing.currency,
            price_source=PriceSource.market_live if pricing.source != "no_data" else PriceSource.unavailable,
            price_basis_note=source_note,
            data_confidence=eff_conf,  # type: ignore[arg-type]
            last_updated=pricing.last_updated,
        )

    elif ident.matched and ident.wine_id:
        # Path A2: catalog hit but no live pricing yet — fall back to the
        # catalog's hand-curated reference price so users always see a number.
        from app.services.wine_identifier import get_wine_by_id_full as _get_wine
        from app.services.pricing_aggregator import _estimate_wholesale
        _wine = _get_wine(ident.wine_id)
        if _wine and _wine.avg_retail_price and _wine.avg_retail_price > 0:
            _base = _wine.avg_retail_price
            _tier = _wine.price_tier or "mid"
            effective = EffectivePricing(
                avg_retail=_base,
                min_retail=round(_base * 0.85, 2),
                max_retail=round(_base * 1.15, 2),
                estimated_wholesale=_estimate_wholesale(_base, _tier),
                price_tier=_tier,
                price_source=PriceSource.catalog,
                price_basis_note=(
                    f"Catalog reference price for '{_wine.name}'. "
                    f"Live market data not yet cached — refresh for a real-time quote."
                ),
                data_confidence="low",
            )

    elif dynamic_pricing:
        # Path B: catalog miss → dynamic lookup
        ds = dynamic_pricing.data_source

        if ds == "wine_searcher_live":
            source_enum = PriceSource.market_live
            confidence_level = "high"
            listings_note = (
                f" ({dynamic_pricing.num_listings} listings)" if dynamic_pricing.num_listings else ""
            )
            basis_note = (
                f"Live Wine-Searcher market data{listings_note}. "
                f"Wine not in catalog – retrieved in real time."
            )
        elif ds == "producer_adjusted_estimate":
            source_enum = PriceSource.producer_adjusted_estimate
            confidence_level = "medium"
            basis_note = dynamic_pricing.notes or (
                "Regional price scaled by known-producer premium. "
                "Directionally accurate; not live market data."
            )
        else:
            # plain regional_proxy
            source_enum = PriceSource.regional_estimate
            confidence_level = "low"
            _lo = f"${dynamic_pricing.min_retail:.0f}" if dynamic_pricing.min_retail is not None else "?"
            _hi = f"${dynamic_pricing.max_retail:.0f}" if dynamic_pricing.max_retail is not None else "?"
            basis_note = (
                f"Regional bucket estimate only – producer unknown. "
                f"Range: {_lo}–{_hi}. "
                f"Wide confidence interval; verify before acting."
            )

        effective = EffectivePricing(
            avg_retail=dynamic_pricing.avg_retail,
            min_retail=dynamic_pricing.min_retail,
            max_retail=dynamic_pricing.max_retail,
            estimated_wholesale=dynamic_pricing.estimated_wholesale,
            price_tier=dynamic_pricing.price_tier,
            price_source=source_enum,
            price_basis_note=basis_note,
            data_confidence=confidence_level,  # type: ignore[arg-type]
            num_listings=dynamic_pricing.num_listings,
            url=dynamic_pricing.url,
            last_updated=dynamic_pricing.last_updated,
        )

    return AnalyzeResponse(
        input=req,
        identification=ident,
        effective_pricing=effective,
        pricing=pricing,
        dynamic_pricing=dynamic_pricing_schema,
        markup_analysis=markup,
        metadata=AnalysisMetadata(
            analyzed_at=datetime.now(timezone.utc),
            processing_time_ms=elapsed_ms,
        ),
    )


def _build_identification(
    raw_text: str,
    best,
    alternatives,
    vintage_override: Optional[int] = None,
) -> IdentificationResult:
    from app.services.text_parser import parse_wine_text

    parsed = parse_wine_text(raw_text)
    effective_vintage = vintage_override or parsed.vintage
    parsed_components = ParsedComponents(
        vintage=effective_vintage,
        producer=parsed.producer,
        wine_name=parsed.wine_name,
        region=parsed.region,
        varietal=parsed.varietal,
        wine_type=parsed.wine_type,
        format_ml=parsed.format_ml,
    )

    if not best:
        return IdentificationResult(
            matched=False,
            confidence=0.0,
            confidence_level="none",
            parsed_components=parsed_components,
        )

    wine = best.wine
    alts = [
        IdentificationAlternative(
            wine_id=a.wine.id,
            name=a.wine.name,
            producer=a.wine.producer,
            region=a.wine.region,
            confidence=round(a.score, 4),
        )
        for a in alternatives
    ]

    return IdentificationResult(
        matched=True,
        confidence=round(best.score, 4),
        confidence_level=best.confidence_level,
        wine_id=wine.id,
        name=wine.name,
        producer=wine.producer,
        vintage=effective_vintage,
        region=wine.region,
        appellation=wine.appellation,
        varietal=wine.varietal,
        wine_type=wine.wine_type,
        avg_retail_price=wine.avg_retail_price,
        price_tier=wine.price_tier,
        alternatives=alts,
        parsed_components=parsed_components,
    )


async def _log_analysis(
    db: AsyncSession,
    menu_text: str,
    menu_price: Optional[float],
    wine_id: Optional[str],
    confidence: float,
    fairness_score: Optional[int],
    verdict: Optional[str],
    venue_id: Optional[str],
) -> None:
    try:
        log = AnalysisLog(
            menu_text=menu_text,
            menu_price=menu_price,
            identified_wine_id=wine_id,
            confidence_score=confidence,
            fairness_score=fairness_score,
            verdict=verdict,
            venue_id=venue_id,
        )
        db.add(log)
        await db.commit()
    except Exception as exc:
        logger.warning("Failed to log analysis (non-critical): %s", exc)
        try:
            await db.rollback()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("", response_model=AnalyzeResponse, summary="Analyse a single wine")
async def analyze_single(
    req: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
) -> AnalyzeResponse:
    """
    Identify a wine from menu text, fetch market pricing, and evaluate markup.

    - **menu_text**: Raw wine name as it appears on the menu
    - **menu_price**: Price listed on the menu (USD); required for markup analysis
    - **vintage**: Optional year override (overrides what is parsed from menu_text)
    - **venue_id**: Optional identifier for tracking analytics per venue
    """
    return await _run_analysis(req, db)


@router.post(
    "/batch",
    response_model=BatchAnalyzeResponse,
    summary="Analyse a batch of wines",
)
async def analyze_batch(
    req: BatchAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
) -> BatchAnalyzeResponse:
    """
    Analyse up to 50 wine entries from a menu in a single request.
    Results are processed concurrently for low latency.
    """
    # Don't share the DB session across concurrent tasks (race condition);
    # analysis logging is skipped in batch mode.
    tasks = [_run_analysis(item, None) for item in req.items]
    results = await asyncio.gather(*tasks, return_exceptions=False)

    return BatchAnalyzeResponse(
        results=list(results),
        total=len(results),
        venue_id=req.venue_id,
    )
