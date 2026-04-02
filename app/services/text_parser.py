"""
Wine text parser.

Converts raw menu strings like:
  "2019 Chateau Margaux, Margaux"
  "Dom Perignon NV Champagne"
  "Screaming Eagle Cab Sauv 2018 - Napa Valley"

into structured ParsedWine objects used by the fuzzy-match identifier.
"""
import re
import unicodedata
from dataclasses import dataclass
from typing import Optional


# ---------------------------------------------------------------------------
# Data class for parsed components
# ---------------------------------------------------------------------------

@dataclass
class ParsedWine:
    raw_text: str
    vintage: Optional[int] = None
    non_vintage: bool = False           # Champagne NV etc.
    producer: Optional[str] = None
    wine_name: Optional[str] = None
    region: Optional[str] = None
    varietal: Optional[str] = None
    wine_type: Optional[str] = None     # red/white/rose/sparkling/dessert/fortified
    format_ml: Optional[int] = None
    # Pre-normalised string ready for fuzzy comparison
    normalized_search: str = ""
    # Clean text after stripping prices, volumes, cruft
    cleaned_text: str = ""


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

_VINTAGE_RE = re.compile(r"\b(19[5-9]\d|20[0-3]\d)\b")
_NV_RE = re.compile(r"\bN\.?V\.?\b", re.IGNORECASE)
_PRICE_RE = re.compile(r"\$[\d,]+(?:\.\d{2})?|\b\d{2,4}\s*(?:dollars|USD)\b", re.IGNORECASE)
_FORMAT_RE = re.compile(
    r"\b(?P<vol>\d+(?:\.\d+)?)\s*(?P<unit>ml|cl|l|ltr|litre|liter)\b", re.IGNORECASE
)
_DOTS_DASHES = re.compile(r"[\s\-–—/\\|,;:\.]{2,}")  # runs of separators


# ---------------------------------------------------------------------------
# Abbreviation expansion (applied before normalisation)
# ---------------------------------------------------------------------------

_ABBREVIATIONS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bch(?:at(?:eau)?|t)?\.?\s+", re.IGNORECASE), "chateau "),
    (re.compile(r"\bdom(?:aine)?\.?\s+", re.IGNORECASE), "domaine "),
    (re.compile(r"\bcab(?:ernet)?\.?\s+sauv(?:ignon)?\.?\b", re.IGNORECASE), "cabernet sauvignon"),
    (re.compile(r"\bcab(?:ernet)?\.?\s+franc\.?\b", re.IGNORECASE), "cabernet franc"),
    (re.compile(r"\bpinot\s+n(?:oir)?\.?\b", re.IGNORECASE), "pinot noir"),
    (re.compile(r"\bpinot\s+g(?:rigio|ris)?\.?\b", re.IGNORECASE), "pinot grigio"),
    (re.compile(r"\bsauv(?:ignon)?\.?\s+blanc\.?\b", re.IGNORECASE), "sauvignon blanc"),
    (re.compile(r"\bchard(?:onnay)?\.?\b", re.IGNORECASE), "chardonnay"),
    (re.compile(r"\bries(?:ling)?\.?\b", re.IGNORECASE), "riesling"),
    (re.compile(r"\bgsm\b", re.IGNORECASE), "grenache syrah mourvedre"),
    (re.compile(r"\bdrc\b", re.IGNORECASE), "domaine de la romanee conti"),
    (re.compile(r"\be\.?\s*guigal\b", re.IGNORECASE), "e guigal"),
    (re.compile(r"\bj\.?j\.?\s*prum\b", re.IGNORECASE), "jj prum"),
    (re.compile(r"\bst\.?\s+", re.IGNORECASE), "saint "),
    (re.compile(r"\bste\.?\s+", re.IGNORECASE), "sainte "),
]

# ---------------------------------------------------------------------------
# Known region keywords  →  canonical region name
# ---------------------------------------------------------------------------

_REGION_KEYWORDS: dict[str, list[str]] = {
    "bordeaux": [
        "bordeaux", "medoc", "pauillac", "margaux", "saint julien",
        "saint estephe", "graves", "pessac leognan", "pomerol",
        "saint emilion", "sauternes", "barsac", "listrac", "moulis",
    ],
    "burgundy": [
        "burgundy", "bourgogne", "cote de nuits", "gevrey chambertin",
        "chambolle musigny", "vosne romanee", "nuits saint georges",
        "morey saint denis", "clos vougeot", "echezeaux", "chambertin",
        "musigny", "romanee conti", "cote de beaune", "meursault",
        "puligny montrachet", "chassagne montrachet", "corton",
        "chablis", "macon", "pouilly fuisse",
    ],
    "rhone": [
        "rhone", "cote rotie", "hermitage", "saint joseph",
        "crozes hermitage", "cornas", "chateauneuf du pape",
        "gigondas", "vacqueyras",
    ],
    "champagne": ["champagne", "reims", "epernay", "blanc de blancs", "blanc de noirs"],
    "alsace": ["alsace", "alsatian"],
    "loire": ["loire", "sancerre", "pouilly fume", "chinon", "vouvray", "muscadet"],
    "napa": [
        "napa", "napa valley", "rutherford", "oakville", "stags leap",
        "howell mountain", "spring mountain", "diamond mountain", "mount veeder",
    ],
    "sonoma": [
        "sonoma", "alexander valley", "russian river", "dry creek", "carneros",
    ],
    "tuscany": [
        "tuscany", "toscana", "chianti", "brunello", "montalcino",
        "bolgheri", "vino nobile",
    ],
    "piedmont": ["piedmont", "piemonte", "barolo", "barbaresco", "langhe"],
    "veneto": ["veneto", "valpolicella", "amarone", "soave", "lugana", "bardolino", "franciacorta"],
    "friuli": ["friuli", "collio", "friuli venezia giulia", "colli orientali", "isonzo", "ribolla", "tocai"],
    "alto adige": ["alto adige", "sudtirol", "trentino"],
    "campania": [
        "campania", "irpinia", "taurasi", "fiano di avellino", "greco di tufo",
        "aglianico del vulture", "campi flegrei", "costa d amalfi", "amalfi",
        "falerno", "terre del volturno",
    ],
    "basilicata": ["basilicata", "aglianico del vulture", "vulture"],
    "sicily": [
        "sicily", "sicilia", "etna", "vittoria", "cerasuolo di vittoria",
        "marsala", "faro", "pantelleria", "terre siciliane", "nerello",
    ],
    "calabria": ["calabria", "ciro", "cirò", "gaglioppo"],
    "puglia": ["puglia", "apulia", "primitivo", "negroamaro", "salento", "manduria"],
    "sardinia": ["sardinia", "sardegna", "cannonau", "vermentino di sardegna"],
    "abruzzo": ["abruzzo", "montepulciano d abruzzo", "trebbiano d abruzzo"],
    "umbria": ["umbria", "montefalco", "sagrantino", "orvieto"],
    "marche": ["marche", "verdicchio", "conero", "rosso piceno"],
    "lazio": ["lazio", "frascati", "cesanese"],
    "emilia romagna": ["emilia romagna", "lambrusco", "sangiovese di romagna", "pignoletto"],
    "rioja": ["rioja", "la rioja"],
    "ribera del duero": ["ribera del duero"],
    "priorat": ["priorat", "priorat doca"],
    "bierzo": ["bierzo", "mencia", "mencía"],
    "rias baixas": ["rias baixas", "albarino", "albariño"],
    "ribeira sacra": ["ribeira sacra"],
    "galicia": ["galicia", "galician"],
    "barossa": ["barossa", "eden valley"],
    "south australia": ["mclaren vale", "coonawarra", "clare valley", "south australia"],
    "marlborough": ["marlborough"],
    "central otago": ["central otago"],
    "mendoza": ["mendoza", "valle de uco"],
    "mosel": ["mosel", "saar", "ruwer", "ahr"],
    "nahe": ["nahe"],
    "rheingau": ["rheingau"],
    "pfalz": ["pfalz", "palatinate"],
    "wachau": ["wachau", "kamptal", "kremstal"],
    "burgenland": ["burgenland", "neusiedlersee"],
    "provence": ["provence", "cotes de provence"],
    "beaujolais": ["beaujolais", "morgon", "fleurie", "moulin a vent", "brouilly", "cote de brouilly", "julienas", "chiroubles", "regnie", "chenas"],
    "jura": ["jura", "arbois", "cotes du jura", "vin jaune", "savagnin", "poulsard", "trousseau"],
    "languedoc": ["languedoc", "pic saint loup", "faugeres", "terrasses du larzac", "corbieres", "minervois"],
    "roussillon": ["roussillon", "cotes catalanes", "collioure", "banyuls"],
    "southwest france": ["cahors", "madiran", "jurançon", "bergerac", "gaillac"],
    "douro": ["douro", "porto", "port"],
    "dao": ["dao", "dão"],
    "alentejo": ["alentejo"],
    "vinho verde": ["vinho verde"],
}

# Flat reverse-lookup: normalised keyword → canonical region label
_KEYWORD_TO_REGION: dict[str, str] = {
    kw: region
    for region, keywords in _REGION_KEYWORDS.items()
    for kw in keywords
}

# ---------------------------------------------------------------------------
# Known varietal keywords
# ---------------------------------------------------------------------------

_VARIETAL_KEYWORDS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bcabernet sauvignon\b", re.IGNORECASE), "cabernet sauvignon"),
    (re.compile(r"\bcabernet franc\b", re.IGNORECASE), "cabernet franc"),
    (re.compile(r"\b(?:cab|cabernet)\b(?!\s+franc)", re.IGNORECASE), "cabernet sauvignon"),
    (re.compile(r"\bmerlot\b", re.IGNORECASE), "merlot"),
    (re.compile(r"\bpinot noir\b", re.IGNORECASE), "pinot noir"),
    (re.compile(r"\bpinot grigio\b", re.IGNORECASE), "pinot grigio"),
    (re.compile(r"\bsauvignon blanc\b", re.IGNORECASE), "sauvignon blanc"),
    (re.compile(r"\bchardonnay\b|\bchard\b", re.IGNORECASE), "chardonnay"),
    (re.compile(r"\briesling\b", re.IGNORECASE), "riesling"),
    (re.compile(r"\bsyrah\b|\bshiraz\b", re.IGNORECASE), "syrah"),
    (re.compile(r"\bgrenache\b|\bgarnacha\b", re.IGNORECASE), "grenache"),
    (re.compile(r"\bzinfandel\b|\bzin\b|\bprimitivo\b", re.IGNORECASE), "zinfandel"),
    (re.compile(r"\bmalbec\b", re.IGNORECASE), "malbec"),
    (re.compile(r"\btempranillo\b|\btinto fino\b", re.IGNORECASE), "tempranillo"),
    (re.compile(r"\bnebbiolo\b", re.IGNORECASE), "nebbiolo"),
    (re.compile(r"\bsangiovese\b", re.IGNORECASE), "sangiovese"),
    (re.compile(r"\bviognier\b", re.IGNORECASE), "viognier"),
    (re.compile(r"\bgewurztraminer\b|\bgewurz\b", re.IGNORECASE), "gewurztraminer"),
    (re.compile(r"\bchenin blanc\b|\bchenin\b", re.IGNORECASE), "chenin blanc"),
    (re.compile(r"\bgruner veltliner\b|\bgrüner\b", re.IGNORECASE), "gruner veltliner"),
    (re.compile(r"\bglera\b|\bprosecco(?!\s+doc)\b", re.IGNORECASE), "glera"),
    # Italian varietals
    (re.compile(r"\bbarbera\b", re.IGNORECASE), "barbera"),
    (re.compile(r"\bdolcetto\b", re.IGNORECASE), "dolcetto"),
    (re.compile(r"\bnegroamaro\b", re.IGNORECASE), "negroamaro"),
    (re.compile(r"\baglianico\b", re.IGNORECASE), "aglianico"),
    (re.compile(r"\bfiano\b", re.IGNORECASE), "fiano"),
    (re.compile(r"\bgreco\b", re.IGNORECASE), "greco"),
    (re.compile(r"\bpallagrello\b", re.IGNORECASE), "pallagrello"),
    (re.compile(r"\bpiedirosso\b", re.IGNORECASE), "piedirosso"),
    (re.compile(r"\bfalanghina\b", re.IGNORECASE), "falanghina"),
    (re.compile(r"\bcoda di volpe\b", re.IGNORECASE), "coda di volpe"),
    (re.compile(r"\bnerello mascalese\b|\bnerello\b", re.IGNORECASE), "nerello mascalese"),
    (re.compile(r"\bcarricante\b", re.IGNORECASE), "carricante"),
    (re.compile(r"\bfrappato\b", re.IGNORECASE), "frappato"),
    (re.compile(r"\bnero d.avola\b|\bnerello d.avola\b", re.IGNORECASE), "nero d'avola"),
    (re.compile(r"\bgaglioppo\b", re.IGNORECASE), "gaglioppo"),
    (re.compile(r"\bmontepulciano\b", re.IGNORECASE), "montepulciano"),
    (re.compile(r"\btrebbiano(?: abruzzese| d.abruzzo| spoletino)?\b", re.IGNORECASE), "trebbiano"),
    (re.compile(r"\bpecorino\b", re.IGNORECASE), "pecorino"),
    (re.compile(r"\bverdicchio\b", re.IGNORECASE), "verdicchio"),
    (re.compile(r"\bsagrantino\b", re.IGNORECASE), "sagrantino"),
    (re.compile(r"\bmalvasia\b", re.IGNORECASE), "malvasia"),
    (re.compile(r"\bgarganega\b", re.IGNORECASE), "garganega"),
    (re.compile(r"\bribolla(?: gialla)?\b", re.IGNORECASE), "ribolla gialla"),
    (re.compile(r"\bteroldego\b", re.IGNORECASE), "teroldego"),
    (re.compile(r"\blagrein\b", re.IGNORECASE), "lagrein"),
    (re.compile(r"\bschiava\b|\bvernatsch\b", re.IGNORECASE), "schiava"),
    (re.compile(r"\bcorvina\b|\bcorvine\b", re.IGNORECASE), "corvina"),
    # Beaujolais / Loire / Jura
    (re.compile(r"\bgamay\b", re.IGNORECASE), "gamay"),
    (re.compile(r"\bpinot meunier\b|\bmeunier\b", re.IGNORECASE), "pinot meunier"),
    (re.compile(r"\bmelon de bourgogne\b|\bmelon\b(?!\s+de\s+bourgogne)", re.IGNORECASE), "melon de bourgogne"),
    (re.compile(r"\bsavagnin\b", re.IGNORECASE), "savagnin"),
    (re.compile(r"\bpoulsard\b|\bploussard\b", re.IGNORECASE), "poulsard"),
    (re.compile(r"\btrousseau\b", re.IGNORECASE), "trousseau"),
    # Iberian
    (re.compile(r"\bmencia\b|\bmencía\b", re.IGNORECASE), "mencía"),
    (re.compile(r"\bgodello\b", re.IGNORECASE), "godello"),
    (re.compile(r"\bverdejo\b", re.IGNORECASE), "verdejo"),
    (re.compile(r"\balbarino\b|\balbariño\b", re.IGNORECASE), "albariño"),
    (re.compile(r"\btxakoli\b|\btxakolina\b", re.IGNORECASE), "txakoli"),
    (re.compile(r"\bmonastrell\b|\bmourvedre\b|\bmouvèdre\b", re.IGNORECASE), "mourvedre"),
    # Rhône / Southern France
    (re.compile(r"\bmarouvrèdre\b|\bmarsanne\b", re.IGNORECASE), "marsanne"),
    (re.compile(r"\broussanne\b", re.IGNORECASE), "roussanne"),
    (re.compile(r"\bcinsault\b|\bcinsaut\b", re.IGNORECASE), "cinsault"),
    (re.compile(r"\bcarignan\b|\bcariñena\b", re.IGNORECASE), "carignan"),
]

# ---------------------------------------------------------------------------
# Wine-type detection
# ---------------------------------------------------------------------------
# Each entry is a compiled word-boundary pattern to avoid substring false
# positives like "rose" matching "rosenblum" or "port" matching "portofino".

def _make_wine_type_pattern(keyword: str) -> re.Pattern:
    """Wrap keyword in word boundaries, escaping any special chars."""
    return re.compile(r"\b" + re.escape(keyword) + r"\b", re.IGNORECASE)


_WINE_TYPE_PATTERNS: dict[str, list[re.Pattern]] = {
    "sparkling": [_make_wine_type_pattern(k) for k in [
        "champagne", "prosecco", "cava", "cremant", "sekt",
        "sparkling", "petillant", "blanc de blancs", "blanc de noirs",
        "brut", "extra brut", "demi-sec",
    ]],
    "dessert": [_make_wine_type_pattern(k) for k in [
        "sauternes", "beerenauslese", "trockenbeerenauslese",
        "eiswein", "ice wine", "icewine", "late harvest",
        "vendange tardive", "passito", "vin de paille", "pedro ximenez",
    ]],
    "fortified": [_make_wine_type_pattern(k) for k in [
        "port", "porto", "sherry", "madeira", "marsala", "vin doux naturel",
    ]],
    # "rosé" is intentionally absent: normalize_text strips diacritics so the
    # input always arrives as "rose" before the regex fires.
    "rose": [_make_wine_type_pattern(k) for k in [
        "rosato", "rosado", "rose",
    ]],
}

# Volume in ml for bottle sizes
_FORMAT_VOLUME_MAP: list[tuple[re.Pattern, int]] = [
    (re.compile(r"\bmagnum\b|\b1\.5\s*l\b", re.IGNORECASE), 1500),
    (re.compile(r"\bjeroboam\b|\b3\s*l\b", re.IGNORECASE), 3000),
    (re.compile(r"\bmethuselah\b|\bimperial\b|\b6\s*l\b", re.IGNORECASE), 6000),
    (re.compile(r"\bhalf[\s-]bottle\b|\b375\s*ml\b", re.IGNORECASE), 375),
    (re.compile(r"\b750\s*ml\b", re.IGNORECASE), 750),
]


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

def _strip_diacritics(text: str) -> str:
    """Remove accents: é→e, ô→o, ü→u, etc."""
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalize_text(text: str) -> str:
    """
    Full normalisation pipeline used for fuzzy comparison:
      1. Strip diacritics
      2. Lowercase
      3. Expand abbreviations
      4. Remove non-alpha characters (keep spaces)
      5. Collapse whitespace
    """
    text = _strip_diacritics(text)
    text = text.lower()
    for pattern, replacement in _ABBREVIATIONS:
        text = pattern.sub(replacement, text)
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# ---------------------------------------------------------------------------
# Main parser
# ---------------------------------------------------------------------------

class WineTextParser:
    """
    Parses a raw wine menu string into structured ParsedWine components.

    The parser is intentionally forgiving:
    - It does not require a specific ordering of tokens.
    - Every field is Optional; downstream identifier handles missing info.
    """

    def parse(self, raw: str) -> ParsedWine:
        result = ParsedWine(raw_text=raw)

        # ── 1. Strip price annotations and leading/trailing whitespace ──
        text = _PRICE_RE.sub(" ", raw).strip()

        # ── 2. Detect bottle format ──
        result.format_ml = self._detect_format(text)
        for pat, _ in _FORMAT_VOLUME_MAP:
            text = pat.sub(" ", text)
        text = _FORMAT_RE.sub(" ", text)

        # ── 3. Extract vintage ──
        vintage_match = _VINTAGE_RE.search(text)
        if vintage_match:
            result.vintage = int(vintage_match.group(1))
            text = text[:vintage_match.start()] + " " + text[vintage_match.end():]

        # ── 4. Detect NV (non-vintage) ──
        if _NV_RE.search(text):
            result.non_vintage = True
            text = _NV_RE.sub(" ", text)

        # ── 5. Clean separators / cruft ──
        text = _DOTS_DASHES.sub(" ", text).strip()
        result.cleaned_text = text

        # ── 6. Detect varietal ──
        result.varietal = self._detect_varietal(text)

        # ── 7. Detect region ──
        result.region = self._detect_region(text)

        # ── 8. Detect wine type ──
        result.wine_type = self._detect_wine_type(text)

        # ── 9. Build normalised search string ──
        result.normalized_search = normalize_text(text)

        # ── 10. Heuristic producer / wine name split ──
        result.producer, result.wine_name = self._split_producer_wine(text)

        return result

    # ── helpers ──────────────────────────────────────────────────────────────

    def _detect_format(self, text: str) -> Optional[int]:
        for pattern, ml in _FORMAT_VOLUME_MAP:
            if pattern.search(text):
                return ml
        m = _FORMAT_RE.search(text)
        if m:
            vol = float(m.group("vol"))
            unit = m.group("unit").lower()
            if unit in ("l", "ltr", "litre", "liter"):
                return int(vol * 1000)
            elif unit == "cl":
                return int(vol * 10)
            else:
                return int(vol)
        return None

    def _detect_varietal(self, text: str) -> Optional[str]:
        # Normalize first so abbreviations are expanded (e.g. "Pinot Gris" →
        # "pinot grigio", "Ries" → "riesling") before pattern matching.
        normalised = normalize_text(text)
        for pattern, varietal in _VARIETAL_KEYWORDS:
            if pattern.search(normalised):
                return varietal
        return None

    def _detect_region(self, text: str) -> Optional[str]:
        normalised = normalize_text(text)
        # Longest-match first to avoid "bordeaux" matching inside "saint-emilion"
        best_match: Optional[str] = None
        best_len = 0
        for keyword, region in _KEYWORD_TO_REGION.items():
            if keyword in normalised and len(keyword) > best_len:
                best_match = region
                best_len = len(keyword)
        return best_match

    def _detect_wine_type(self, text: str) -> Optional[str]:
        normalised = normalize_text(text)
        for wine_type, patterns in _WINE_TYPE_PATTERNS.items():
            for pattern in patterns:
                if pattern.search(normalised):
                    return wine_type
        return None

    def _split_producer_wine(self, text: str) -> tuple[Optional[str], Optional[str]]:
        """
        Heuristic split.  For a string like:
          "Chateau Margaux, Margaux"   → producer="Chateau Margaux", wine="Margaux"
          "Domaine de la Romanée-Conti La Tâche" → producer=…, wine="La Tâche"
          "Opus One"                   → producer="Opus One", wine=None

        Strategy:
          - If there is a comma, split on first comma.
          - Otherwise use the full text as the producer (identifier adds wine context).
        """
        text = text.strip()
        if "," in text:
            parts = text.split(",", 1)
            producer = parts[0].strip() or None
            wine = parts[1].strip() or None
            return producer, wine

        return text or None, None


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_parser = WineTextParser()


def parse_wine_text(raw: str) -> ParsedWine:
    """Convenience wrapper around the module-level parser instance."""
    return _parser.parse(raw)
