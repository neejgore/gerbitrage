"""
Dynamic wine lookup for catalog misses.

When the fuzzy-match catalog cannot identify a wine above the confidence
threshold, this module provides two fallback tiers:

  Tier 1 – Wine-Searcher live search (requires WINE_SEARCHER_API_KEY)
            Calls the Wine-Searcher Pro API with the raw wine name, returns
            real market pricing, and caches the result in Redis.

  Tier 2 – Regional proxy pricing (always available)
            Uses the parsed appellation / region / varietal to look up a
            pre-built table of typical retail prices for that category and
            returns a plausible mid-point estimate with a wide confidence
            interval.  No external calls required.

Both tiers store results in Redis with a configurable TTL (default 24 h for
live data, 72 h for regional proxy) so repeated queries don't burn API quota.
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

from app.config import get_settings
from app.services.cache import cache_get, cache_set
from app.services.text_parser import ParsedWine

logger = logging.getLogger(__name__)
settings = get_settings()

_LIVE_TTL = 86_400       # 24 h
_PROXY_TTL = 259_200     # 72 h


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

class DynamicPricingResult:
    """Pricing result for a wine not found in the static catalog."""

    def __init__(
        self,
        *,
        avg_retail: Optional[float],
        min_retail: Optional[float],
        max_retail: Optional[float],
        estimated_wholesale: Optional[float],
        data_source: str,          # "wine_searcher_live" | "regional_proxy"
        data_confidence: str,      # "high" | "medium" | "low"
        price_tier: str,
        num_listings: Optional[int] = None,
        url: Optional[str] = None,
        notes: Optional[str] = None,
        last_updated: Optional[datetime] = None,
    ):
        self.avg_retail = avg_retail
        self.min_retail = min_retail
        self.max_retail = max_retail
        self.estimated_wholesale = estimated_wholesale
        self.data_source = data_source
        self.data_confidence = data_confidence
        self.price_tier = price_tier
        self.num_listings = num_listings
        self.url = url
        self.notes = notes
        self.last_updated = last_updated or datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "avg_retail": self.avg_retail,
            "min_retail": self.min_retail,
            "max_retail": self.max_retail,
            "estimated_wholesale": self.estimated_wholesale,
            "data_source": self.data_source,
            "data_confidence": self.data_confidence,
            "price_tier": self.price_tier,
            "num_listings": self.num_listings,
            "url": self.url,
            "notes": self.notes,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "DynamicPricingResult":
        lu = d.get("last_updated")
        return cls(
            avg_retail=d.get("avg_retail"),
            min_retail=d.get("min_retail"),
            max_retail=d.get("max_retail"),
            estimated_wholesale=d.get("estimated_wholesale"),
            data_source=d.get("data_source", "unknown"),
            data_confidence=d.get("data_confidence", "low"),
            price_tier=d.get("price_tier", "mid"),
            num_listings=d.get("num_listings"),
            url=d.get("url"),
            notes=d.get("notes"),
            last_updated=datetime.fromisoformat(lu) if lu else None,
        )


# ---------------------------------------------------------------------------
# Cache key helper
# ---------------------------------------------------------------------------

def _dynamic_cache_key(raw_text: str, vintage: Optional[int] = None) -> str:
    slug = raw_text.lower().strip()
    if vintage:
        slug = f"{slug}:{vintage}"
    h = hashlib.md5(slug.encode()).hexdigest()[:12]
    return f"dynamic_lookup:{h}"


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def dynamic_lookup(
    raw_text: str,
    parsed: ParsedWine,
) -> Optional[DynamicPricingResult]:
    """
    Try to get pricing for a wine that wasn't found in the static catalog.

    Returns None only if both tiers fail entirely (very unlikely for a
    recognisable wine name).
    """
    cache_key = _dynamic_cache_key(raw_text, parsed.vintage)
    cached = await cache_get(cache_key)
    if cached:
        logger.debug("Dynamic lookup cache hit: %s", raw_text[:50])
        return DynamicPricingResult.from_dict(cached)

    # Tier 1 – live Wine-Searcher search
    result: Optional[DynamicPricingResult] = None
    if settings.wine_searcher_api_key and not settings.use_mock_pricing:
        result = await _wine_searcher_search(raw_text, parsed.vintage)

    # Tier 2 – regional proxy (with producer-aware premium adjustment)
    if result is None:
        result = _regional_proxy(parsed, raw_text=raw_text)

    if result:
        ttl = _LIVE_TTL if result.data_source == "wine_searcher_live" else _PROXY_TTL
        await cache_set(cache_key, result.to_dict(), ttl=ttl)

    return result


# ---------------------------------------------------------------------------
# Tier 1 – Wine-Searcher live search
# ---------------------------------------------------------------------------

_WS_SEARCH_URL = "https://api.wine-searcher.com/api/v2/wine/search"


async def _wine_searcher_search(
    raw_text: str,
    vintage: Optional[int] = None,
) -> Optional[DynamicPricingResult]:
    """Call Wine-Searcher search API and parse pricing from the results."""
    params: dict = {
        "apikey": settings.wine_searcher_api_key,
        "q": raw_text,
        "currency": "USD",
        "format": "json",
    }
    if vintage:
        params["vintage"] = str(vintage)

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.get(_WS_SEARCH_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        # Wine-Searcher Pro response: list of wine entries, each with offers.
        # We use the first result (best match) and aggregate its offer prices.
        wines = data.get("search", []) or data.get("results", []) or []
        if not wines:
            return None

        top = wines[0]
        offers = top.get("offers", []) or top.get("prices", [])
        prices = sorted(
            [float(o.get("price", 0)) for o in offers if o.get("price")],
        )
        if not prices:
            # Sometimes Wine-Searcher returns a avg directly on the wine obj
            avg_raw = top.get("avg_price") or top.get("price")
            if not avg_raw:
                return None
            prices = [float(avg_raw)]

        avg = round(sum(prices) / len(prices), 2)
        tier = _price_to_tier(avg)
        wholesale = _estimate_wholesale(avg, tier)
        url = (
            f"https://www.wine-searcher.com/find/{raw_text.replace(' ', '+')}"
        )

        logger.info(
            "Wine-Searcher live lookup: '%s' → avg $%.2f (%d listings)",
            raw_text[:50], avg, len(prices),
        )

        return DynamicPricingResult(
            avg_retail=avg,
            min_retail=prices[0],
            max_retail=prices[-1],
            estimated_wholesale=wholesale,
            data_source="wine_searcher_live",
            data_confidence="high" if len(prices) >= 5 else "medium",
            price_tier=tier,
            num_listings=len(prices),
            url=url,
        )

    except httpx.HTTPStatusError as exc:
        logger.warning(
            "Wine-Searcher live search HTTP %s for '%s'",
            exc.response.status_code, raw_text[:40],
        )
        return None
    except Exception as exc:
        logger.warning("Wine-Searcher live search error: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Tier 2 – Regional proxy pricing
# ---------------------------------------------------------------------------

# fmt: off
# (low, midpoint, high) USD retail for an appellation / region key
# Keys are lower-case, diacritic-free, space-normalised – same as normalize_text output
_REGIONAL_PROXY: dict[str, tuple[float, float, float]] = {
    # ── Champagne ──────────────────────────────────────────────────────────
    "champagne nv":                         (38,  65,  110),
    "champagne":                            (45,  75,  200),
    "champagne blanc de blancs":            (50,  90,  250),
    "champagne blanc de noirs":             (55,  95,  250),
    "champagne prestige cuvee":             (120, 200, 800),
    "champagne grower":                     (55,  95,  200),
    "champagne brut nature":                (55,  90,  200),
    # ── Burgundy ──────────────────────────────────────────────────────────
    "bourgogne":                            (25,  40,   80),
    "macon":                                (18,  28,   55),
    "chablis":                              (22,  40,   90),
    "chablis premier cru":                  (45,  70,  150),
    "chablis grand cru":                    (80, 140,  350),
    "beaune":                               (45,  75,  200),
    "gevrey chambertin":                    (50,  90,  350),
    "chambolle musigny":                    (60, 110,  450),
    "vosne romanee":                        (70, 140,  600),
    "nuits saint georges":                  (50,  90,  300),
    "pommard":                              (45,  80,  250),
    "volnay":                               (50,  90,  280),
    "meursault":                            (55,  95,  300),
    "puligny montrachet":                   (70, 130,  500),
    "chassagne montrachet":                 (60, 110,  400),
    "burgundy village":                     (35,  60,  150),
    "burgundy premier cru":                 (80, 160,  500),
    "burgundy grand cru":                   (200,400, 2000),
    # ── Rhône ─────────────────────────────────────────────────────────────
    "cotes du rhone":                       (12,  20,   40),
    "crozes hermitage":                     (22,  40,   90),
    "hermitage":                            (80, 160,  500),
    "cote rotie":                           (80, 150,  450),
    "chateauneuf du pape":                  (40,  80,  300),
    "condrieu":                             (50,  90,  200),
    "cornas":                               (45,  85,  250),
    "saint joseph":                         (30,  55,  130),
    "gigondas":                             (25,  45,  110),
    "vacqueyras":                           (20,  35,   80),
    # ── Loire ─────────────────────────────────────────────────────────────
    "sancerre":                             (28,  50,  120),
    "pouilly fume":                         (25,  45,  100),
    "muscadet":                             (12,  20,   40),
    "vouvray":                              (18,  30,   80),
    "chinon":                               (20,  35,   90),
    "bourgueil":                            (18,  30,   70),
    "anjou":                                (15,  25,   60),
    "savennieres":                          (30,  55,  120),
    "muscadet sevre et maine":              (12,  20,   40),
    # ── Alsace ────────────────────────────────────────────────────────────
    "alsace riesling":                      (18,  32,   80),
    "alsace grand cru":                     (40,  75,  200),
    "alsace gewurztraminer":                (18,  32,   80),
    "alsace pinot gris":                    (20,  35,   90),
    # ── Beaujolais ────────────────────────────────────────────────────────
    "beaujolais":                           (12,  20,   40),
    "beaujolais villages":                  (14,  22,   45),
    "morgon":                               (20,  38,   75),
    "fleurie":                              (20,  38,   75),
    "moulin a vent":                        (22,  40,   80),
    "brouilly":                             (18,  30,   65),
    "cote de brouilly":                     (20,  35,   70),
    "julienas":                             (18,  30,   65),
    "chiroubles":                           (18,  30,   65),
    "regnie":                               (16,  25,   55),
    # ── Jura ──────────────────────────────────────────────────────────────
    "arbois":                               (25,  45,  100),
    "cotes du jura":                        (22,  40,   90),
    "vin jaune":                            (55,  90,  200),
    "savagnin":                             (25,  50,  130),
    "poulsard":                             (25,  45,   90),
    "trousseau":                            (30,  55,  110),
    # ── Languedoc-Roussillon ──────────────────────────────────────────────
    "languedoc":                            (14,  25,   60),
    "pic saint loup":                       (20,  38,   80),
    "terrasses du larzac":                  (25,  50,  110),
    "faugeres":                             (18,  30,   70),
    "bandol":                               (28,  50,  120),
    "priorat":                              (35,  70,  200),
    "roussillon":                           (18,  35,   80),
    # ── Bordeaux ──────────────────────────────────────────────────────────
    "bordeaux":                             (15,  30,  100),
    "saint emilion":                        (30,  65,  300),
    "pomerol":                              (55, 120,  600),
    "saint estephe":                        (40,  90,  400),
    "pauillac":                             (55, 120,  800),
    "saint julien":                         (50, 110,  600),
    "margaux":                              (55, 120,  800),
    "pessac leognan":                       (40,  80,  400),
    "sauternes":                            (35,  70,  300),
    # ── Italy – Piedmont ──────────────────────────────────────────────────
    "barolo":                               (45,  90,  450),
    "barolo riserva":                       (100,200,  800),
    "barbaresco":                           (40,  80,  350),
    "barbera d alba":                       (18,  30,   70),
    "barbera d asti":                       (16,  28,   65),
    "dolcetto d alba":                      (15,  25,   55),
    "langhe nebbiolo":                      (25,  45,  120),
    "gattinara":                            (35,  65,  180),
    "ghemme":                               (30,  55,  150),
    "roero":                                (25,  45,  100),
    "moscato d asti":                       (18,  28,   55),
    # ── Italy – Tuscany ───────────────────────────────────────────────────
    "brunello di montalcino":               (55, 110,  600),
    "brunello riserva":                     (100,220,  900),
    "rosso di montalcino":                  (25,  42,   90),
    "vino nobile di montepulciano":         (25,  45,  120),
    "chianti classico":                     (20,  38,  120),
    "chianti classico gran selezione":      (45,  85,  250),
    "chianti classico riserva":             (30,  55,  160),
    "chianti":                              (14,  22,   55),
    "bolgheri":                             (35,  70,  200),
    "bolgheri superiore":                   (80, 150,  500),
    "super tuscan":                         (45,  95,  500),
    "carmignano":                           (30,  55,  130),
    "morellino di scansano":                (18,  30,   70),
    "vernaccia di san gimignano":           (16,  25,   60),
    # ── Italy – Northeast ─────────────────────────────────────────────────
    "amarone della valpolicella":           (60, 120,  450),
    "valpolicella ripasso":                 (22,  40,   90),
    "valpolicella":                         (15,  25,   60),
    "soave classico":                       (16,  28,   65),
    "soave":                                (12,  20,   50),
    "alto adige":                           (18,  35,   90),
    "franciacorta":                         (28,  50,  130),
    "lugana":                               (18,  32,   75),
    "collio":                               (22,  40,   90),
    "friuli":                               (20,  35,   80),
    # ── Italy – Campania ──────────────────────────────────────────────────
    "campania":                             (20,  38,  120),
    "taurasi":                              (40,  70,  200),
    "fiano di avellino":                    (22,  38,   90),
    "fiano":                                (22,  38,   90),
    "greco di tufo":                        (20,  35,   80),
    "greco":                                (20,  35,   80),
    "aglianico del vulture":                (25,  45,  120),
    "aglianico":                            (25,  50,  150),
    "irpinia":                              (20,  35,   90),
    "campi flegrei":                        (18,  30,   70),
    "costa d amalfi":                       (30,  55,  140),
    "terre del volturno":                   (30,  60,  160),
    "falerno":                              (25,  45,  110),
    "falanghina":                           (18,  30,   75),
    "piedirosso":                           (18,  32,   80),
    "pallagrello":                          (25,  45,  120),
    "coda di volpe":                        (18,  30,   70),
    # ── Italy – Basilicata ────────────────────────────────────────────────
    "basilicata":                           (20,  38,  100),
    "vulture":                              (22,  42,  110),
    # ── Italy – Sicily ────────────────────────────────────────────────────
    "etna rosso":                           (28,  55,  200),
    "etna bianco":                          (22,  45,  180),
    "etna":                                 (25,  50,  200),
    "cerasuolo di vittoria":                (22,  40,   90),
    "sicilia":                              (15,  25,   70),
    "sicily":                               (15,  25,   70),
    "nerello mascalese":                    (30,  60,  220),
    "nerello":                              (30,  60,  220),
    "carricante":                           (22,  45,  180),
    "nero d avola":                         (15,  28,   80),
    "frappato":                             (20,  38,   90),
    "terre siciliane":                      (18,  30,   85),
    "faro":                                 (50,  90,  200),
    # ── Italy – Calabria / Puglia / Sardinia ──────────────────────────────
    "calabria":                             (15,  25,   65),
    "gaglioppo":                            (15,  25,   65),
    "ciro":                                 (15,  25,   60),
    "puglia":                               (14,  24,   65),
    "apulia":                               (14,  24,   65),
    "negroamaro":                           (14,  24,   65),
    "salento":                              (14,  24,   65),
    "manduria":                             (18,  32,   80),
    "sardinia":                             (15,  28,   80),
    "sardegna":                             (15,  28,   80),
    "cannonau":                             (18,  32,   90),
    "vermentino":                           (18,  30,   75),
    # ── Italy – Central & South ───────────────────────────────────────────
    "abruzzo":                              (15,  30,   90),
    "montepulciano d abruzzo":              (15,  28,   80),
    "montepulciano":                        (15,  28,   80),
    "trebbiano d abruzzo":                  (20,  40,  180),
    "trebbiano abruzzo":                    (20,  40,  180),
    "trebbiano":                            (20,  40,  180),
    "pecorino":                             (18,  32,   80),
    "verdicchio":                           (15,  25,   60),
    "sagrantino di montefalco":             (35,  65,  180),
    "sagrantino":                           (35,  65,  180),
    "montefalco":                           (30,  55,  160),
    "umbria":                               (20,  35,   90),
    "marche":                               (18,  30,   80),
    "lazio":                                (18,  30,   75),
    "emilia romagna":                       (15,  25,   65),
    "primitivo":                            (14,  24,   65),
    "salice salentino":                     (12,  20,   50),
    "ciro":                                 (15,  25,   60),
    # ── Italy – Barbera / Dolcetto / Piedmont extras ──────────────────────
    "barbera":                              (18,  32,   80),
    "dolcetto":                             (15,  25,   60),
    "corvina":                              (20,  35,  100),
    "garganega":                            (15,  25,   60),
    "malvasia":                             (18,  32,   80),
    "ribolla gialla":                       (18,  35,   90),
    "gamay":                                (18,  35,   75),
    "pinot meunier":                        (45,  80,  180),
    "meunier":                              (45,  80,  180),
    "savagnin":                             (25,  50,  130),
    "poulsard":                             (25,  45,   90),
    "trousseau":                            (30,  55,  110),
    "mencía":                               (20,  38,   90),
    "mencia":                               (20,  38,   90),
    "godello":                              (18,  35,   90),
    "verdejo":                              (18,  30,   75),
    "mourvedre":                            (25,  50,  150),
    "carignan":                             (18,  35,   90),
    "cinsault":                             (18,  30,   75),
    # ── Spain ─────────────────────────────────────────────────────────────
    "rioja crianza":                        (14,  22,   50),
    "rioja reserva":                        (22,  40,  120),
    "rioja gran reserva":                   (45,  85,  250),
    "rioja":                                (15,  30,  120),
    "ribera del duero":                     (20,  45,  200),
    "bierzo":                               (18,  35,   90),
    "rias baixas":                          (18,  28,   60),
    "albarino":                             (18,  28,   60),
    "cava":                                 (12,  20,   55),
    "penedes":                              (15,  28,   75),
    "ribeira sacra":                        (22,  40,   90),
    "mencia":                               (20,  38,   90),
    "garnacha":                             (18,  35,  100),
    "toro":                                 (18,  35,  100),
    # ── Germany / Austria ─────────────────────────────────────────────────
    "mosel riesling":                       (20,  38,  200),
    "mosel spatlese":                       (28,  50,  150),
    "mosel auslese":                        (45,  90,  350),
    "mosel trockenbeerenauslese":           (200,500, 2000),
    "rheingau riesling":                    (22,  40,  180),
    "pfalz riesling":                       (20,  38,  150),
    "nahe riesling":                        (22,  42,  160),
    "saar riesling":                        (22,  40,  150),
    "ruwer riesling":                       (22,  40,  150),
    "gruner veltliner":                     (18,  32,  100),
    "austria riesling":                     (25,  50,  200),
    "wachau":                               (28,  55,  200),
    "kamptal":                              (22,  40,  120),
    "kremstal":                             (20,  35,  100),
    "blaufrankisch":                        (20,  40,  120),
    # ── Portugal ──────────────────────────────────────────────────────────
    "douro":                                (18,  35,  120),
    "dao":                                  (18,  30,   90),
    "alentejo":                             (15,  28,   80),
    "vinho verde":                          (12,  20,   50),
    "bairrada":                             (18,  32,   90),
    "port":                                 (25,  55,  250),
    "madeira":                              (30,  65,  300),
    # ── New World ─────────────────────────────────────────────────────────
    "napa valley cabernet":                 (55, 120,  800),
    "napa valley":                          (45, 100,  600),
    "sonoma pinot noir":                    (35,  65,  200),
    "sonoma chardonnay":                    (28,  50,  160),
    "santa barbara":                        (28,  55,  180),
    "willamette valley pinot noir":         (30,  60,  200),
    "washington cabernet":                  (30,  60,  200),
    "argentina malbec":                     (15,  30,  120),
    "mendoza":                              (18,  35,  150),
    "chile carmenere":                      (15,  25,   80),
    "chile cabernet":                       (18,  30,   90),
    "barossa shiraz":                       (20,  45,  200),
    "hunter valley semillon":              (18,  35,  100),
    "marlborough sauvignon blanc":         (18,  30,   70),
    "central otago pinot noir":             (30,  60,  180),
    "south africa":                         (15,  28,   80),
}
# fmt: on


# ---------------------------------------------------------------------------
# Producer-aware premium table
# When the catalog misses a wine but we can parse the producer name, apply
# a multiplier to the regional base so the estimate reflects who made it.
# Format: normalized producer alias → (avg_multiplier, confidence_note)
# ---------------------------------------------------------------------------
_PRODUCER_PREMIUMS: dict[str, tuple[float, str]] = {
    # ── Burgundy – ultra-cult ────────────────────────────────────────────
    "drc":                          (18.0, "DRC ultra-cult pricing"),
    "domaine de la romanee conti":  (18.0, "DRC ultra-cult pricing"),
    "romanee conti":                (18.0, "DRC ultra-cult pricing"),
    "leroy":                        (10.0, "Domaine Leroy ultra-cult pricing"),
    "domaine leroy":                (10.0, "Domaine Leroy ultra-cult pricing"),
    "lalou bize leroy":             (10.0, "Domaine Leroy ultra-cult pricing"),
    "d auvenay":                    (14.0, "Domaine d'Auvenay ultra-cult pricing"),
    "domaine d auvenay":            (14.0, "Domaine d'Auvenay ultra-cult pricing"),
    # ── Burgundy – top domaines ─────────────────────────────────────────
    "armand rousseau":              (6.0,  "Rousseau top-producer premium"),
    "domaine armand rousseau":      (6.0,  "Rousseau top-producer premium"),
    "coche dury":                   (9.0,  "Coche-Dury ultra-premium pricing"),
    "domaine coche dury":           (9.0,  "Coche-Dury ultra-premium pricing"),
    "roumier":                      (7.0,  "Roumier top-producer premium"),
    "georges roumier":              (7.0,  "Roumier top-producer premium"),
    "arnoux lachaux":               (5.0,  "Arnoux-Lachaux top-producer premium"),
    "domaine arnoux lachaux":       (5.0,  "Arnoux-Lachaux top-producer premium"),
    "mugnier":                      (5.0,  "Mugnier top-producer premium"),
    "jacques frederic mugnier":     (5.0,  "Mugnier top-producer premium"),
    "frederic mugnier":             (5.0,  "Mugnier top-producer premium"),
    "sylvain cathiard":             (4.5,  "Cathiard top-producer premium"),
    "domaine sylvain cathiard":     (4.5,  "Cathiard top-producer premium"),
    "meo camuzet":                  (4.0,  "Méo-Camuzet top-producer premium"),
    "domaine meo camuzet":          (4.0,  "Méo-Camuzet top-producer premium"),
    "dujac":                        (3.5,  "Dujac top-producer premium"),
    "domaine dujac":                (3.5,  "Dujac top-producer premium"),
    "ponsot":                       (3.5,  "Ponsot top-producer premium"),
    "domaine ponsot":               (3.5,  "Ponsot top-producer premium"),
    "comte de vogue":               (4.0,  "De Vogüé top-producer premium"),
    "domaine comte georges de vogue": (4.0,"De Vogüé top-producer premium"),
    "de vogue":                     (4.0,  "De Vogüé top-producer premium"),
    "mugneret gibourg":             (3.5,  "Mugneret-Gibourg top-producer premium"),
    "georges mugneret gibourg":     (3.5,  "Mugneret-Gibourg top-producer premium"),
    "comtes lafon":                 (3.5,  "Comtes Lafon top-producer premium"),
    "domaine des comtes lafon":     (3.5,  "Comtes Lafon top-producer premium"),
    "roulot":                       (3.5,  "Roulot top-producer premium"),
    "domaine roulot":               (3.5,  "Roulot top-producer premium"),
    "jean marc roulot":             (3.5,  "Roulot top-producer premium"),
    "chandon de briailles":         (2.5,  "Chandon de Briailles premium"),
    "fourrier":                     (2.5,  "Fourrier premium"),
    "domaine fourrier":             (2.5,  "Fourrier premium"),
    "jean marie fourrier":          (2.5,  "Fourrier premium"),
    # ── Chablis – top domaines ──────────────────────────────────────────
    "raveneau":                     (4.5,  "Raveneau Chablis top-producer premium"),
    "domaine raveneau":             (4.5,  "Raveneau Chablis top-producer premium"),
    "dauvissat":                    (4.0,  "Dauvissat Chablis top-producer premium"),
    "vincent dauvissat":            (4.0,  "Dauvissat Chablis top-producer premium"),
    "rene et vincent dauvissat":    (4.0,  "Dauvissat Chablis top-producer premium"),
    # ── Champagne – prestige ────────────────────────────────────────────
    "krug":                         (3.0,  "Krug prestige Champagne premium"),
    "salon":                        (8.0,  "Salon ultra-rare Champagne premium"),
    "selosse":                      (6.0,  "Selosse cult-grower premium"),
    "jacques selosse":              (6.0,  "Selosse cult-grower premium"),
    "anselme selosse":              (6.0,  "Selosse cult-grower premium"),
    "prevost":                      (5.0,  "Prévost cult-grower premium"),
    "jerome prevost":               (5.0,  "Prévost cult-grower premium"),
    "egly ouriet":                  (2.5,  "Egly-Ouriet grower premium"),
    "cedric bouchard":              (2.5,  "Bouchard grower premium"),
    "ulysse collin":                (2.5,  "Ulysse Collin grower premium"),
    "larmandier bernier":           (2.0,  "Larmandier-Bernier grower premium"),
    "agrapart":                     (2.0,  "Agrapart grower premium"),
    # ── Northern Rhône ──────────────────────────────────────────────────
    "chave":                        (5.0,  "Chave Hermitage top-producer premium"),
    "jean louis chave":             (5.0,  "Chave Hermitage top-producer premium"),
    "allemand":                     (5.0,  "Allemand Cornas cult premium"),
    "thierry allemand":             (5.0,  "Allemand Cornas cult premium"),
    "clape":                        (3.5,  "Clape Cornas top-producer premium"),
    "auguste clape":                (3.5,  "Clape Cornas top-producer premium"),
    "rostaing":                     (2.5,  "Rostaing Côte-Rôtie premium"),
    "rene rostaing":                (2.5,  "Rostaing Côte-Rôtie premium"),
    # ── Bordeaux – ultra-rare ───────────────────────────────────────────
    "petrus":                       (12.0, "Pétrus ultra-cult pricing"),
    "le pin":                       (20.0, "Le Pin ultra-cult pricing"),
    "lafleur":                      (8.0,  "Château Lafleur cult pricing"),
    "ausone":                       (8.0,  "Château Ausone cult pricing"),
    "cheval blanc":                 (7.0,  "Cheval Blanc cult pricing"),
    # ── Loire – cult ────────────────────────────────────────────────────
    "clos rougeard":                (6.0,  "Clos Rougeard Loire cult premium"),
    "foucault":                     (6.0,  "Clos Rougeard Loire cult premium"),
    "dagueneau":                    (5.0,  "Dagueneau Pouilly-Fumé cult premium"),
    "didier dagueneau":             (5.0,  "Dagueneau Pouilly-Fumé cult premium"),
    "vatan":                        (3.0,  "Vatan Sancerre premium"),
    "edmond vatan":                 (3.0,  "Vatan Sancerre premium"),
    # ── California cult ─────────────────────────────────────────────────
    "screaming eagle":              (18.0, "Screaming Eagle ultra-cult pricing"),
    "harlan":                       (12.0, "Harlan Estate ultra-cult pricing"),
    "harlan estate":                (12.0, "Harlan Estate ultra-cult pricing"),
    "bond":                         (6.0,  "Bond Estates cult pricing"),
    "bond estates":                 (6.0,  "Bond Estates cult pricing"),
    "colgin":                       (5.0,  "Colgin cult pricing"),
    "colgin cellars":               (5.0,  "Colgin cult pricing"),
    "hundred acre":                 (6.0,  "Hundred Acre cult pricing"),
    "scarecrow":                    (4.0,  "Scarecrow cult pricing"),
    "sine qua non":                 (5.0,  "Sine Qua Non cult pricing"),
    "kongsgaard":                   (4.0,  "Kongsgaard Chardonnay cult premium"),
    "abreu":                        (5.0,  "Abreu Vineyard cult pricing"),
    "promontory":                   (4.5,  "Promontory Harlan cult pricing"),
    "dalla valle":                  (4.0,  "Dalla Valle cult pricing"),
    "dominus":                      (2.5,  "Dominus premium pricing"),
    "eisele":                       (4.5,  "Eisele Vineyard cult pricing"),
    "grace family":                 (3.0,  "Grace Family cult pricing"),
    "continuum":                    (3.5,  "Continuum Estate cult pricing"),
    "marcassin":                    (6.0,  "Marcassin ultra-rare pricing"),
    "kosta browne":                 (2.0,  "Kosta Browne premium pricing"),
    "mount eden":                   (2.0,  "Mount Eden premium pricing"),
    "rochioli":                     (3.5,  "Rochioli cult pricing"),
    # ── Oregon cult ─────────────────────────────────────────────────────
    "antica terra":                 (3.0,  "Antica Terra cult Oregon premium"),
    "kelley fox":                   (2.5,  "Kelley Fox premium Oregon"),
    # ── Italy – cult ────────────────────────────────────────────────────
    "quintarelli":                  (7.0,  "Quintarelli ultra-cult Amarone pricing"),
    "giuseppe quintarelli":         (7.0,  "Quintarelli ultra-cult Amarone pricing"),
    "dal forno":                    (5.0,  "Dal Forno Amarone cult pricing"),
    "dal forno romano":             (5.0,  "Dal Forno Amarone cult pricing"),
    "gaja":                         (3.0,  "Gaja top-producer premium"),
    "le macchiole":                 (2.5,  "Le Macchiole Bolgheri premium"),
    "soldera":                      (6.0,  "Soldera Brunello ultra-cult pricing"),
    "biondi santi":                 (5.0,  "Biondi-Santi Brunello cult pricing"),
    "valentini":                    (5.0,  "Valentini Abruzzo cult pricing"),
    "emidio pepe":                  (4.0,  "Emidio Pepe cult pricing"),
    "giacomo conterno":             (4.0,  "Giacomo Conterno top-producer premium"),
    "roberto voerzio":              (3.5,  "Voerzio Barolo top-producer premium"),
    "bartolo mascarello":           (3.5,  "Bartolo Mascarello top-producer premium"),
    "giuseppe mascarello":          (3.0,  "Giuseppe Mascarello premium"),
    "arnaldo caprai":               (2.0,  "Caprai Sagrantino premium"),
    # ── Spain cult ──────────────────────────────────────────────────────
    "pingus":                       (8.0,  "Pingus ultra-cult pricing"),
    "dominio de pingus":            (8.0,  "Pingus ultra-cult pricing"),
    "vega sicilia":                 (5.0,  "Vega Sicilia cult pricing"),
    "alvaro palacios":              (4.0,  "Álvaro Palacios Priorat premium"),
    # ── Germany cult ────────────────────────────────────────────────────
    "egon muller":                  (6.0,  "Egon Müller ultra-cult pricing"),
    "keller":                       (3.0,  "Weingut Keller premium"),
    "weingut keller":               (3.0,  "Weingut Keller premium"),
    # ── Australia cult ──────────────────────────────────────────────────
    "henschke":                     (2.5,  "Henschke premium pricing"),
    "penfolds":                     (2.0,  "Penfolds premium tiers"),
    # ── South Africa cult ───────────────────────────────────────────────
    "sadie family":                 (2.5,  "Sadie Family premium pricing"),
    "sadie":                        (2.5,  "Sadie Family premium pricing"),
    # ── Hungary cult ────────────────────────────────────────────────────
    "szepsy":                       (5.0,  "Szepsy Tokaji ultra-premium"),
    "istvan szepsy":                (5.0,  "Szepsy Tokaji ultra-premium"),
}


# When a wine mentions only the producer (no appellation text to match the proxy
# table), use this mapping to synthesise the correct regional base key.
_PRODUCER_REGION_HINTS: dict[str, str] = {
    "screaming eagle":              "napa valley cabernet",
    "harlan":                       "napa valley cabernet",
    "harlan estate":                "napa valley cabernet",
    "bond":                         "napa valley cabernet",
    "bond estates":                 "napa valley cabernet",
    "colgin":                       "napa valley cabernet",
    "colgin cellars":               "napa valley cabernet",
    "hundred acre":                 "napa valley cabernet",
    "scarecrow":                    "napa valley cabernet",
    "abreu":                        "napa valley cabernet",
    "promontory":                   "napa valley cabernet",
    "dalla valle":                  "napa valley cabernet",
    "grace family":                 "napa valley cabernet",
    "continuum":                    "napa valley cabernet",
    "sine qua non":                 "napa valley",
    "marcassin":                    "sonoma chardonnay",
    "kosta browne":                 "sonoma pinot noir",
    "rochioli":                     "sonoma pinot noir",
    "kongsgaard":                   "sonoma chardonnay",
    "quintarelli":                  "amarone della valpolicella",
    "giuseppe quintarelli":         "amarone della valpolicella",
    "dal forno":                    "amarone della valpolicella",
    "dal forno romano":             "amarone della valpolicella",
    "egon muller":                  "mosel auslese",   # fallback; TBA handled below
    "soldera":                      "brunello di montalcino",
    "biondi santi":                 "brunello di montalcino",
    "valentini":                    "trebbiano d abruzzo",
    "emidio pepe":                  "montepulciano d abruzzo",
    "petrus":                       "pomerol",
    "le pin":                       "pomerol",
    "lafleur":                      "pomerol",
    "ausone":                       "saint emilion",
    "cheval blanc":                 "saint emilion",
    "pingus":                       "ribera del duero",
    "dominio de pingus":            "ribera del duero",
    "vega sicilia":                 "ribera del duero",
    "sadie":                        "south africa",
    "sadie family":                 "south africa",
    "szepsy":                       "madeira",  # Tokaji – best proxy
    "istvan szepsy":                "madeira",
    "selosse":                      "champagne prestige cuvee",
    "salon":                        "champagne prestige cuvee",
    "prevost":                      "champagne grower",
    "jerome prevost":               "champagne grower",
    "krug":                         "champagne prestige cuvee",
    "dagueneau":                    "pouilly fume",
    "didier dagueneau":             "pouilly fume",
    "clos rougeard":                "bourgueil",
    "foucault":                     "bourgueil",
}

# Common abbreviations to expand before proxy lookup
_WINE_ABBREVIATIONS: dict[str, str] = {
    r"\btba\b":   "trockenbeerenauslese",
    r"\bba\b":    "beerenauslese",
    r"\bspat\b":  "spatlese",
    r"\baus\b":   "auslese",
    r"\bkab\b":   "kabinett",
    r"\bgc\b":    "grand cru",
    r"\bpc\b":    "premier cru",
    r"\b1er\b":   "premier cru",
    r"\bvv\b":    "vieilles vignes",
}


def _apply_producer_premium(
    base: DynamicPricingResult,
    raw_text: str,
) -> DynamicPricingResult:
    """
    If the raw wine text contains a known premium producer name, scale the
    regional proxy estimate by that producer's multiplier and upgrade confidence.
    Returns the original result unchanged if no premium producer is found.
    """
    import unicodedata

    def norm(s: str) -> str:
        import re as _re
        nfkd = unicodedata.normalize("NFD", s.lower())
        ascii_str = "".join(c for c in nfkd if unicodedata.category(c) != "Mn")
        ascii_str = _re.sub(r"[-'']", " ", ascii_str)
        ascii_str = _re.sub(r"[^a-z0-9 ]", "", ascii_str)
        return " ".join(ascii_str.split())

    raw_norm = norm(raw_text)

    matched_multiplier: float = 1.0
    matched_note: str = ""

    for producer_key, (multiplier, note) in _PRODUCER_PREMIUMS.items():
        if producer_key in raw_norm and multiplier > matched_multiplier:
            matched_multiplier = multiplier
            matched_note = note

    if matched_multiplier <= 1.0:
        return base  # no premium producer found

    new_avg = round((base.avg_retail or 50.0) * matched_multiplier, 0)
    new_min = round((base.min_retail or 30.0) * matched_multiplier * 0.6, 0)
    new_max = round((base.max_retail or 100.0) * matched_multiplier * 1.5, 0)
    tier = _price_to_tier(new_avg)
    wholesale = _estimate_wholesale(new_avg, tier)

    logger.info(
        "Producer-premium applied: '%s' × %.1fx → avg=$%.0f (%s)",
        raw_text[:50], matched_multiplier, new_avg, matched_note,
    )

    return DynamicPricingResult(
        avg_retail=new_avg,
        min_retail=new_min,
        max_retail=new_max,
        estimated_wholesale=wholesale,
        data_source="producer_adjusted_estimate",
        data_confidence="medium",
        price_tier=tier,
        notes=(
            f"Producer-adjusted estimate: {matched_note}. "
            f"Regional base ×{matched_multiplier:.1f}. "
            f"Typical retail: ${new_min:.0f}–${new_max:.0f}."
        ),
    )


def _regional_proxy(parsed: ParsedWine, raw_text: str = "") -> Optional[DynamicPricingResult]:
    """
    Use parsed region / appellation / varietal to estimate a retail price range.
    Returns None only when we cannot form any useful match.
    """
    # Build a list of candidate keys from most-specific to least-specific
    candidates: list[str] = []

    region = (parsed.region or "").lower().strip()
    varietal = (parsed.varietal or "").lower().strip()
    wine_type = (parsed.wine_type or "").lower().strip()

    if region:
        candidates.append(region)
    if varietal:
        candidates.append(varietal)

    # Combined attempts: "region varietal"
    if region and varietal:
        candidates.append(f"{region} {varietal}")

    # Wine-type fallback
    if wine_type == "sparkling":
        candidates.append("champagne")

    import re
    import unicodedata

    def _norm_key(s: str) -> str:
        nfkd = unicodedata.normalize("NFD", s.lower())
        ascii_str = "".join(c for c in nfkd if unicodedata.category(c) != "Mn")
        # Replace hyphens/punctuation with spaces so "Vosne-Romanée" → "vosne romanee"
        ascii_str = re.sub(r"[-'']", " ", ascii_str)
        ascii_str = re.sub(r"[^a-z0-9 ]", "", ascii_str)
        return " ".join(ascii_str.split())

    # Normalise each candidate and look up the table
    for raw_key in candidates:
        key = _norm_key(raw_key)
        if key in _REGIONAL_PROXY:
            low, mid, high = _REGIONAL_PROXY[key]
            tier = _price_to_tier(mid)
            wholesale = _estimate_wholesale(mid, tier)
            note = (
                f"No exact catalog match. Regional estimate for "
                f"'{raw_key}' (typical retail: ${low}–${high})."
            )
            logger.info("Regional proxy: '%s' → key='%s' avg=$%.0f", raw_key[:50], key, mid)
            base = DynamicPricingResult(
                avg_retail=float(mid),
                min_retail=float(low),
                max_retail=float(high),
                estimated_wholesale=wholesale,
                data_source="regional_proxy",
                data_confidence="low",
                price_tier=tier,
                notes=note,
            )
            # Apply producer premium if the raw wine text contains a known producer
            return _apply_producer_premium(base, raw_text) if raw_text else base

    # Partial / substring match – scan both parsed fields AND raw text
    from app.services.text_parser import normalize_text
    full_norm = normalize_text(" ".join(filter(None, [region, varietal])))
    # Also scan the raw input text directly (catches specific appellations the
    # parser doesn't extract, e.g. "Vosne-Romanée" inside a full wine name).
    # Expand common abbreviations (TBA → trockenbeerenauslese, etc.) first.
    expanded_raw = raw_text
    for pattern, expansion in _WINE_ABBREVIATIONS.items():
        expanded_raw = re.sub(pattern, expansion, expanded_raw, flags=re.IGNORECASE)
    raw_norm = _norm_key(expanded_raw) if expanded_raw else ""
    combined_norm = f"{full_norm} {raw_norm}".strip()

    # Also add any producer-implied region hint to improve the match surface
    for prod_key, implied_region in _PRODUCER_REGION_HINTS.items():
        if prod_key in raw_norm:
            combined_norm = f"{combined_norm} {implied_region}"
            break

    best_key: Optional[str] = None
    best_len = 0
    for table_key in _REGIONAL_PROXY:
        if table_key in combined_norm and len(table_key) > best_len:
            best_key = table_key
            best_len = len(table_key)

    if best_key:
        low, mid, high = _REGIONAL_PROXY[best_key]
        tier = _price_to_tier(mid)
        wholesale = _estimate_wholesale(mid, tier)
        note = (
            f"No exact catalog match. Regional estimate for "
            f"'{best_key}' (typical retail: ${low}–${high})."
        )
        base = DynamicPricingResult(
            avg_retail=float(mid),
            min_retail=float(low),
            max_retail=float(high),
            estimated_wholesale=wholesale,
            data_source="regional_proxy",
            data_confidence="low",
            price_tier=tier,
            notes=note,
        )
        return _apply_producer_premium(base, raw_text) if raw_text else base

    return None


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _price_to_tier(price: float) -> str:
    if price <= 25:
        return "budget"
    if price <= 75:
        return "mid"
    if price <= 200:
        return "premium"
    if price <= 600:
        return "luxury"
    return "ultra"


_WHOLESALE_RATIOS = {
    "budget": 0.50,
    "mid": 0.52,
    "premium": 0.55,
    "luxury": 0.58,
    "ultra": 0.62,
}


def _estimate_wholesale(retail: float, tier: str) -> float:
    ratio = _WHOLESALE_RATIOS.get(tier, 0.53)
    return round(retail * ratio, 2)
