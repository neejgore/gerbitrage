"""
Wine Identification Engine.

Given a raw menu string (and optional price), returns the best-matching wine
from the catalog using a multi-factor fuzzy scoring algorithm.

Scoring pipeline
────────────────
1. Token pre-filter  – discard catalog entries with zero shared tokens
2. Fuzzy text score  – weighted combination of four RapidFuzz metrics
3. Alias bonus       – best match across all aliases for the candidate
4. Structural bonuses – vintage, region, varietal, wine-type boosts
5. Confidence level  – very_high / high / medium / low / none
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from rapidfuzz import fuzz
from rapidfuzz.distance import JaroWinkler

from app.config import get_settings
from app.data.wine_catalog import WINE_CATALOG, WINE_CATALOG_BY_ID, WineCatalogEntry, _derive_price_tier
from app.services.text_parser import ParsedWine, normalize_text, parse_wine_text


settings = get_settings()


# ---------------------------------------------------------------------------
# Thresholds
# ---------------------------------------------------------------------------

VERY_HIGH_THRESHOLD = 0.90
HIGH_THRESHOLD = settings.high_confidence_threshold       # default 0.85
MEDIUM_THRESHOLD = settings.medium_confidence_threshold   # default 0.65
LOW_THRESHOLD = settings.min_match_threshold              # default 0.45
MIN_TOKEN_LENGTH = 3   # tokens shorter than this are excluded from pre-filter


# ---------------------------------------------------------------------------
# Internal result type
# ---------------------------------------------------------------------------

@dataclass
class WineMatch:
    wine: WineCatalogEntry
    score: float            # 0.0 – 1.0
    confidence_level: str   # very_high / high / medium / low / none
    score_breakdown: dict   # diagnostic detail


# ---------------------------------------------------------------------------
# Token pre-filter helpers
# ---------------------------------------------------------------------------

_STOP_WORDS = frozenset(
    [
        "de", "du", "des", "la", "le", "les", "et", "the", "a", "an",
        "and", "or", "of", "in", "at", "by", "to", "for", "with",
        "chateau", "domaine",  # too common to be discriminating on their own
        # These appear in hundreds of producer names and add no search signal
        "wine", "winery", "wines", "cellars", "vineyard", "vineyards",
        "estate", "estates",
    ]
)


def _significant_tokens(text: str) -> set[str]:
    return {
        t for t in text.split()
        if len(t) >= MIN_TOKEN_LENGTH and t not in _STOP_WORDS
    }


def _token_overlap(tokens_a: set[str], tokens_b: set[str]) -> int:
    """Number of shared significant tokens between two sets."""
    return len(tokens_a & tokens_b)


# ---------------------------------------------------------------------------
# Build an enriched catalog index at module load time
# ---------------------------------------------------------------------------

@dataclass
class _CatalogEntry:
    wine: WineCatalogEntry
    normalized_name: str          # full name normalised
    normalized_producer: str
    normalized_aliases: list[str]
    tokens: set[str]              # significant tokens across name + aliases


_INDEX: list[_CatalogEntry] = []
_INDEX_IDS: set[str] = set()   # fast duplicate check


def _index_entry(wine: WineCatalogEntry) -> None:
    """Add a single WineCatalogEntry to _INDEX (skips duplicates)."""
    if wine.id in _INDEX_IDS:
        return
    norm_name = normalize_text(wine.name)
    norm_producer = normalize_text(wine.producer)
    norm_aliases = [normalize_text(a) for a in wine.aliases]
    all_text = " ".join([norm_name] + norm_aliases)
    tokens = _significant_tokens(all_text)
    _INDEX.append(
        _CatalogEntry(
            wine=wine,
            normalized_name=norm_name,
            normalized_producer=norm_producer,
            normalized_aliases=norm_aliases,
            tokens=tokens,
        )
    )
    _INDEX_IDS.add(wine.id)


def _build_index() -> None:
    """Index the static catalog + any previously discovered wines on disk."""
    import json
    from pathlib import Path

    for wine in WINE_CATALOG:
        _index_entry(wine)

    # Load any wines already discovered at runtime and saved to extended_catalog.json
    catalog_path = Path(__file__).parent.parent / "data" / "extended_catalog.json"
    if catalog_path.exists():
        try:
            data: dict = json.loads(catalog_path.read_text())
            for wine_id, e in data.items():
                _index_entry(WineCatalogEntry(
                    id=e.get("id", wine_id),
                    name=e.get("name", ""),
                    producer=e.get("producer", ""),
                    region=e.get("region", ""),
                    country=e.get("country", ""),
                    appellation=e.get("appellation", ""),
                    varietal=e.get("varietal", ""),
                    wine_type=e.get("wine_type", "red"),
                    avg_retail_price=float(e.get("avg_retail_price") or 0),
                    price_tier=e.get("price_tier", "mid"),
                    aliases=e.get("aliases", []),
                ))
        except Exception:
            pass  # non-critical; static catalog still usable


def register_discovered_wine(
    wine_id: str,
    name: str,
    producer: str,
    avg_price: float,
    region: str = "",
    varietal: str = "",
    wine_type: str = "red",
) -> None:
    """
    Immediately add a freshly discovered wine to the live search index.
    Called by vivino_dynamic after a successful Vivino scrape so that the
    very next search for this wine finds it without a server restart.
    """
    _index_entry(WineCatalogEntry(
        id=wine_id,
        name=name,
        producer=producer,
        region=region,
        country="",
        appellation="",
        varietal=varietal,
        wine_type=wine_type,
        avg_retail_price=avg_price or 0.0,
        price_tier=_derive_price_tier(avg_price or 0.0),
        aliases=[],
    ))


_build_index()


# ---------------------------------------------------------------------------
# Core scorer
# ---------------------------------------------------------------------------

def _score_candidate(
    parsed: ParsedWine,
    entry: _CatalogEntry,
) -> tuple[float, dict]:
    """
    Compute a composite match score in [0, 1] between the parsed query
    and a catalog entry, plus a breakdown dict for diagnostics.
    """
    q = parsed.normalized_search

    # ── A. Fuzzy text similarity (four metrics, weighted) ──────────────────
    ts = fuzz.token_sort_ratio(q, entry.normalized_name) / 100.0
    tset = fuzz.token_set_ratio(q, entry.normalized_name) / 100.0
    wr = fuzz.WRatio(q, entry.normalized_name) / 100.0
    jw = JaroWinkler.similarity(q, entry.normalized_name)

    # partial_ratio rewards substring matches (e.g. "wood" in both "brasswood"
    # and "moss wood") which produces false positives on proper nouns. Removed.
    name_score = 0.35 * ts + 0.30 * tset + 0.25 * wr + 0.10 * jw

    # ── B. Producer-only score ──────────────────────────────────────────────
    producer_ts = fuzz.token_sort_ratio(q, entry.normalized_producer) / 100.0
    producer_set = fuzz.token_set_ratio(q, entry.normalized_producer) / 100.0
    producer_score = 0.60 * producer_ts + 0.40 * producer_set

    # ── C. Alias score – best match across all aliases ─────────────────────
    alias_score = 0.0
    for alias in entry.normalized_aliases:
        a_ts = fuzz.token_sort_ratio(q, alias) / 100.0
        a_tset = fuzz.token_set_ratio(q, alias) / 100.0
        candidate = 0.55 * a_ts + 0.45 * a_tset
        if candidate > alias_score:
            alias_score = candidate

    # ── D. Combined text score ──────────────────────────────────────────────
    base_text = max(name_score, producer_score * 0.85, alias_score * 0.90)

    # ── E. Structural bonuses ───────────────────────────────────────────────
    bonus = 0.0
    breakdown: dict = {
        "name_score": round(name_score, 4),
        "producer_score": round(producer_score, 4),
        "alias_score": round(alias_score, 4),
        "base_text": round(base_text, 4),
        "bonuses": {},
    }

    # Vintage
    if parsed.vintage:
        # We don't store per-vintage catalog data; the wine's avg_retail_price
        # is for a "standard" vintage.  We give a bonus when the parsed vintage
        # is in a plausible range (1950–current) so that "2019 Margaux" vs
        # "Margaux" still scores correctly.
        if 1950 <= parsed.vintage <= 2030:
            bonus += 0.04
            breakdown["bonuses"]["vintage_plausible"] = 0.04

    # Region
    if parsed.region and entry.wine.region:
        region_norm = normalize_text(entry.wine.region)
        region_match = fuzz.token_set_ratio(parsed.region, region_norm) / 100.0
        if region_match >= 0.80:
            bonus += 0.06
            breakdown["bonuses"]["region_match"] = 0.06
        elif region_match >= 0.50:
            bonus += 0.02
            breakdown["bonuses"]["region_partial"] = 0.02

    # Varietal
    if parsed.varietal and entry.wine.varietal:
        var_norm = normalize_text(entry.wine.varietal)
        if parsed.varietal in var_norm:
            bonus += 0.03
            breakdown["bonuses"]["varietal_match"] = 0.03

    # Wine type
    if parsed.wine_type and entry.wine.wine_type == parsed.wine_type:
        bonus += 0.02
        breakdown["bonuses"]["wine_type_match"] = 0.02

    # ── F. Final score ──────────────────────────────────────────────────────
    final = min(1.0, base_text + bonus)
    breakdown["final"] = round(final, 4)

    return final, breakdown


# ---------------------------------------------------------------------------
# Public identifier
# ---------------------------------------------------------------------------

def _confidence_level(score: float) -> str:
    if score >= VERY_HIGH_THRESHOLD:
        return "very_high"
    if score >= HIGH_THRESHOLD:
        return "high"
    if score >= MEDIUM_THRESHOLD:
        return "medium"
    if score >= LOW_THRESHOLD:
        return "low"
    return "none"


def identify_wine(
    raw_text: str,
    vintage_override: Optional[int] = None,
    top_k: int = 5,
) -> tuple[Optional[WineMatch], list[WineMatch]]:
    """
    Identify the best-matching wine from the catalog.

    Returns:
        (best_match, alternatives)
        where best_match is None when confidence is "none".
        alternatives is a list of up to (top_k - 1) runner-up matches.
    """
    parsed = parse_wine_text(raw_text)
    if vintage_override:
        parsed.vintage = vintage_override

    query_tokens = _significant_tokens(parsed.normalized_search)

    # ── Pre-filter: only score entries with ≥1 shared token ────────────────
    # Always require at least one overlapping significant token. Wine names
    # are proper nouns — if the query word isn't in the candidate's tokens
    # at all, it cannot be the right wine.
    candidates: list[tuple[float, dict, _CatalogEntry]] = []
    for entry in _INDEX:
        if query_tokens and _token_overlap(query_tokens, entry.tokens) == 0:
            continue
        score, breakdown = _score_candidate(parsed, entry)
        if score >= LOW_THRESHOLD:
            candidates.append((score, breakdown, entry))

    # Sort descending
    candidates.sort(key=lambda x: x[0], reverse=True)
    candidates = candidates[:top_k]

    if not candidates:
        return None, []

    best_score, best_breakdown, best_entry = candidates[0]
    best_level = _confidence_level(best_score)

    best_match = WineMatch(
        wine=best_entry.wine,
        score=best_score,
        confidence_level=best_level,
        score_breakdown=best_breakdown,
    )

    alternatives = [
        WineMatch(
            wine=entry.wine,
            score=score,
            confidence_level=_confidence_level(score),
            score_breakdown=brkdn,
        )
        for score, brkdn, entry in candidates[1:]
    ]

    # If even the best candidate did not clear LOW_THRESHOLD return None
    if best_level == "none":
        return None, alternatives

    return best_match, alternatives


def search_wines(
    query: str,
    limit: int = 10,
    wine_type: Optional[str] = None,
    country: Optional[str] = None,
) -> list[WineMatch]:
    """
    Free-text search over the wine catalog.
    Returns up to `limit` matches regardless of confidence threshold.
    """
    parsed = parse_wine_text(query)
    query_tokens = _significant_tokens(parsed.normalized_search)

    candidates: list[tuple[float, dict, _CatalogEntry]] = []
    for entry in _INDEX:
        # Apply hard filters
        if wine_type and entry.wine.wine_type != wine_type:
            continue
        if country and normalize_text(entry.wine.country) != normalize_text(country):
            continue

        score, breakdown = _score_candidate(parsed, entry)
        candidates.append((score, breakdown, entry))

    candidates.sort(key=lambda x: x[0], reverse=True)
    candidates = candidates[:limit]

    return [
        WineMatch(
            wine=entry.wine,
            score=score,
            confidence_level=_confidence_level(score),
            score_breakdown=brkdn,
        )
        for score, brkdn, entry in candidates
    ]


def get_wine_by_id(wine_id: str) -> Optional[WineCatalogEntry]:
    return WINE_CATALOG_BY_ID.get(wine_id)
