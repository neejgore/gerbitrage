"""
POST /menu/upload    – upload a wine menu (PDF or image) and get deal analysis
POST /menu/from-url  – fetch a wine menu from a URL (PDF link or HTML page)
"""
from __future__ import annotations

import asyncio
import html as _html_entities
import io
import logging
import re
from typing import Optional

import httpx
from fastapi import APIRouter, Body, File, HTTPException, UploadFile
from pydantic import BaseModel

from app.api.routes.analyze import _run_analysis
from app.schemas.analysis import AnalyzeRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/menu", tags=["Menu"])


# ── Text extraction ────────────────────────────────────────────────────────────

def _pdf_to_text(data: bytes) -> str:
    import pdfplumber
    pages: list[str] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for pg in pdf.pages:
            t = pg.extract_text()
            if t:
                pages.append(t)
    return "\n".join(pages)


def _image_to_text(data: bytes) -> str:
    try:
        from PIL import Image, ImageFilter, ImageEnhance
        import pytesseract
    except ImportError:
        raise HTTPException(
            status_code=422,
            detail=(
                "Image OCR requires pytesseract. "
                "Please upload a PDF instead, or install pytesseract on the server."
            ),
        )
    img = Image.open(io.BytesIO(data)).convert("RGB")
    # Light sharpening + contrast boost helps with phone photos
    img = ImageEnhance.Contrast(img).enhance(1.3)
    img = img.filter(ImageFilter.SHARPEN)
    return pytesseract.image_to_string(img, config="--psm 6")


def _html_to_text(html: str) -> str:
    """Strip HTML tags and return readable plain text suitable for wine parsing."""
    # Drop script / style blocks entirely
    html = re.sub(r'<(?:script|style)[^>]*>.*?</(?:script|style)>', '', html, flags=re.DOTALL | re.IGNORECASE)
    # Convert block elements → newlines so price patterns stay on separate lines
    html = re.sub(r'<(?:br|p|div|tr|li|h[1-6]|section|article)[^/>]*/?>','\n', html, flags=re.IGNORECASE)
    html = re.sub(r'</(?:p|div|tr|li|h[1-6]|section|article)>', '\n', html, flags=re.IGNORECASE)
    # Strip remaining tags
    text = re.sub(r'<[^>]+>', ' ', html)
    # Decode HTML entities (&amp; → &, &#8211; → –, etc.)
    text = _html_entities.unescape(text)
    # Collapse horizontal whitespace; keep newlines
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n[ \t]*\n+', '\n', text)
    return text.strip()


async def _fetch_url(url: str) -> tuple[bytes, str]:
    """
    Download a URL and return (raw_bytes, content_type).
    Uses a browser-like User-Agent to avoid basic bot blocks.
    Raises HTTPException on network or HTTP errors.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/pdf,application/xhtml+xml,*/*;q=0.9",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        async with httpx.AsyncClient(timeout=25, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.content, resp.headers.get("content-type", "")
    except httpx.TimeoutException:
        raise HTTPException(408, "Request timed out fetching the URL.")
    except httpx.HTTPStatusError as exc:
        raise HTTPException(exc.response.status_code, f"URL returned HTTP {exc.response.status_code}.")
    except Exception as exc:
        raise HTTPException(422, f"Could not fetch URL: {exc}")


def _extract_text_from_url_content(data: bytes, content_type: str, url: str) -> str:
    """Detect content type and extract plain text."""
    ct = content_type.lower()
    url_lower = url.lower().split("?")[0]

    is_pdf = "pdf" in ct or url_lower.endswith(".pdf")
    is_image = ct.startswith("image/") or any(
        url_lower.endswith(e) for e in (".jpg", ".jpeg", ".png", ".webp")
    )

    if is_pdf:
        return _pdf_to_text(data)
    if is_image:
        return _image_to_text(data)
    # Default: treat as HTML / plain text
    try:
        text = data.decode("utf-8", errors="replace")
    except Exception:
        text = data.decode("latin-1", errors="replace")

    if "<html" in text[:2000].lower() or "<body" in text[:2000].lower():
        return _html_to_text(text)
    return text  # plain text — return as-is


# ── Wine-entry parsing ─────────────────────────────────────────────────────────

# Matches lines ending in "YEAR PRICE" or "NV PRICE" or "MV PRICE"
_WINE_RE = re.compile(
    r"^(.{8,}?)\s+((?:19|20)\d{2}|NV|MV)\s+\$?(\d+(?:\.\d{1,2})?)\s*$"
)
_SKIP_RE = re.compile(
    r"^(\d+$|BY THE GLASS|HALF BOTTLE|SPARKLING$|ROSE$|WHITE$|RED$|BEER"
    r"|COCKTAIL|MOCKTAIL|SPIRIT|VODKA|GIN|TEQUILA|MEZCAL|RUM|BOURBON"
    r"|WHISKEY|SCOTCH|COGNAC|CHARDONNAY|PINOT NOIR|CABERNET|ZINFANDEL"
    r"|FRANCE$|SPAIN$|ITALY$|GERMANY$|AUSTRIA$|CHAMPAGNE$|BURGUNDY$"
    r"|BORDEAUX$|DESSERT$|FORTIFIED$|MERLOT$|SYRAH$|SAUVIGNON BLANC$)",
    re.I,
)
_SPIRITS_KW = (
    "vodka", "gin", "rum", "whiskey", "bourbon", "scotch",
    "tequila", "mezcal", "cognac", "beer", "ale", "lager",
    "pilsner", "ipa", "stout", "soda",
)


def _parse_wines(text: str) -> list[dict]:
    entries: list[dict] = []
    seen: set[tuple] = set()
    for line in text.splitlines():
        line = line.strip()
        m = _WINE_RE.match(line)
        if not m:
            continue
        desc, vintage_str, price_str = m.group(1).strip(), m.group(2), m.group(3)
        if _SKIP_RE.match(desc) or len(desc) < 10:
            continue
        if any(kw in desc.lower() for kw in _SPIRITS_KW):
            continue
        menu_price = float(price_str)
        if menu_price < 10 or menu_price > 50_000:
            continue
        vintage = int(vintage_str) if vintage_str.isdigit() else None
        key = (desc.lower()[:45], vintage, int(menu_price))
        if key in seen:
            continue
        seen.add(key)
        entries.append({"desc": desc, "vintage": vintage, "menu_price": menu_price})
    return entries


# ── Response schemas ───────────────────────────────────────────────────────────

class MenuWineResult(BaseModel):
    raw_text: str
    vintage: Optional[int] = None
    menu_price: float
    matched: bool
    wine_name: Optional[str] = None
    producer: Optional[str] = None
    region: Optional[str] = None
    varietal: Optional[str] = None
    retail_price: Optional[float] = None
    wholesale_est: Optional[float] = None
    min_retail: Optional[float] = None
    max_retail: Optional[float] = None
    markup: Optional[float] = None
    confidence: Optional[float] = None
    confidence_level: Optional[str] = None
    deal_rating: str = "unknown"   # steal | good | fair | expensive | unknown
    data_confidence: Optional[str] = None
    price_source: Optional[str] = None


class MenuUploadResponse(BaseModel):
    filename: str
    total_parsed: int
    matched: int
    unmatched: int
    with_price: int
    steals: int
    good_deals: int
    fair_deals: int
    expensive: int
    results: list[MenuWineResult]


def _deal_rating(markup: Optional[float]) -> str:
    if markup is None:
        return "unknown"
    if markup < 0.8:
        return "steal"
    if markup <= 1.5:
        return "good"
    if markup <= 2.5:
        return "fair"
    return "expensive"


# ── Route ──────────────────────────────────────────────────────────────────────

@router.post("/upload", response_model=MenuUploadResponse, summary="Analyze a wine menu file")
async def upload_menu(file: UploadFile = File(...)) -> MenuUploadResponse:
    """
    Upload a wine menu as a **PDF** or **image** (JPG / PNG / HEIC).

    Returns every detected wine entry with:
    - Retail & wholesale pricing from the Vivino cache
    - Markup ratio (menu price ÷ retail)
    - Deal rating: **steal** (<0.8×), **good** (≤1.5×), **fair** (≤2.5×), **expensive** (>2.5×)
    """
    filename = file.filename or "upload"
    content_type = (file.content_type or "").lower()
    data = await file.read()

    # Detect and extract text
    is_pdf = filename.lower().endswith(".pdf") or "pdf" in content_type
    is_image = any(
        filename.lower().endswith(ext)
        for ext in (".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".tif", ".tiff")
    ) or content_type.startswith("image/")

    try:
        if is_pdf:
            text = _pdf_to_text(data)
        elif is_image:
            text = _image_to_text(data)
        else:
            # Unknown type — attempt PDF first, fall back to image OCR
            try:
                text = _pdf_to_text(data)
            except Exception:
                text = _image_to_text(data)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not read file: {exc}") from exc

    return await _run_batch(text, filename)


# ── Shared batch-analysis helper ───────────────────────────────────────────────

async def _run_batch(text: str, source_name: str) -> MenuUploadResponse:
    """Parse wine entries from text and batch-analyze them. Shared by file and URL endpoints."""
    wines = _parse_wines(text)
    if not wines:
        raise HTTPException(
            status_code=422,
            detail=(
                f"No wine entries found in '{source_name}'. "
                "Wine lines should end with a year and price (e.g. '… 2019 145')."
            ),
        )
    wines = wines[:150]
    sem = asyncio.Semaphore(10)

    async def _analyze(w: dict) -> MenuWineResult:
        async with sem:
            req = AnalyzeRequest(menu_text=w["desc"], menu_price=w["menu_price"], vintage=w["vintage"])
            try:
                resp = await _run_analysis(req, db=None)
            except Exception as exc:
                logger.warning("analysis error for %r: %s", w["desc"], exc)
                return MenuWineResult(raw_text=w["desc"], vintage=w["vintage"], menu_price=w["menu_price"], matched=False)
            ep = resp.effective_pricing
            ident = resp.identification
            retail = ep.avg_retail if ep else None
            markup = w["menu_price"] / retail if retail else None
            return MenuWineResult(
                raw_text=w["desc"], vintage=w["vintage"], menu_price=w["menu_price"],
                matched=ident.matched, wine_name=ident.name, producer=ident.producer,
                region=ident.region, varietal=ident.varietal,
                retail_price=round(retail, 2) if retail else None,
                wholesale_est=round(ep.estimated_wholesale, 2) if ep and ep.estimated_wholesale else None,
                min_retail=ep.min_retail if ep else None, max_retail=ep.max_retail if ep else None,
                markup=round(markup, 2) if markup else None,
                confidence=ident.confidence, confidence_level=ident.confidence_level,
                deal_rating=_deal_rating(markup),
                data_confidence=ep.data_confidence if ep else None,
                price_source=ep.price_source.value if ep and ep.price_source else None,
            )

    results: list[MenuWineResult] = list(await asyncio.gather(*[_analyze(w) for w in wines]))
    return MenuUploadResponse(
        filename=source_name,
        total_parsed=len(results),
        matched=sum(1 for r in results if r.matched),
        unmatched=sum(1 for r in results if not r.matched),
        with_price=sum(1 for r in results if r.retail_price),
        steals=sum(1 for r in results if r.deal_rating == "steal"),
        good_deals=sum(1 for r in results if r.deal_rating == "good"),
        fair_deals=sum(1 for r in results if r.deal_rating == "fair"),
        expensive=sum(1 for r in results if r.deal_rating == "expensive"),
        results=results,
    )


# ── URL endpoint ───────────────────────────────────────────────────────────────

class UrlMenuRequest(BaseModel):
    url: str


@router.post("/from-url", response_model=MenuUploadResponse, summary="Analyze a wine menu from a URL")
async def menu_from_url(req: UrlMenuRequest) -> MenuUploadResponse:
    """
    Fetch a wine menu from a **URL** and return deal analysis.

    Supports:
    - Direct PDF links (e.g. `https://restaurant.com/wine-list.pdf`)
    - HTML pages with wine lists rendered as text
    - Image URLs (JPG/PNG — requires Tesseract OCR)

    The URL is fetched server-side with a browser User-Agent.
    JavaScript-rendered pages (SPAs) may return limited results.
    """
    url = req.url.strip()
    if not url.startswith(("http://", "https://")):
        raise HTTPException(400, "URL must start with http:// or https://")

    logger.info("Fetching menu from URL: %s", url[:120])
    data, content_type = await _fetch_url(url)
    text = _extract_text_from_url_content(data, content_type, url)

    # Use the last path segment as a friendly name
    source_name = url.rstrip("/").split("/")[-1].split("?")[0] or url[:60]
    return await _run_batch(text, source_name)
