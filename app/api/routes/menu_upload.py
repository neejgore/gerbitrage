"""
POST /menu/upload  – upload a wine menu (PDF or image) and get deal analysis
"""
from __future__ import annotations

import asyncio
import io
import logging
import re
from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
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

    wines = _parse_wines(text)
    if not wines:
        raise HTTPException(
            status_code=422,
            detail=(
                "No wine entries found in the uploaded file. "
                "Make sure prices appear at the end of each wine line (e.g. '… 2019 145')."
            ),
        )

    # Limit to 150 entries to avoid timeout
    wines = wines[:150]

    # Analyze concurrently (10 at a time)
    sem = asyncio.Semaphore(10)

    async def _analyze(w: dict) -> MenuWineResult:
        async with sem:
            req = AnalyzeRequest(
                menu_text=w["desc"],
                menu_price=w["menu_price"],
                vintage=w["vintage"],
            )
            try:
                resp = await _run_analysis(req, db=None)
            except Exception as exc:
                logger.warning("analysis error for %r: %s", w["desc"], exc)
                return MenuWineResult(
                    raw_text=w["desc"],
                    vintage=w["vintage"],
                    menu_price=w["menu_price"],
                    matched=False,
                )

            ep = resp.effective_pricing
            ident = resp.identification
            retail = ep.avg_retail if ep else None
            markup = w["menu_price"] / retail if retail else None

            return MenuWineResult(
                raw_text=w["desc"],
                vintage=w["vintage"],
                menu_price=w["menu_price"],
                matched=ident.matched,
                wine_name=ident.name,
                producer=ident.producer,
                region=ident.region,
                varietal=ident.varietal,
                retail_price=round(retail, 2) if retail else None,
                wholesale_est=round(ep.estimated_wholesale, 2) if ep and ep.estimated_wholesale else None,
                min_retail=ep.min_retail if ep else None,
                max_retail=ep.max_retail if ep else None,
                markup=round(markup, 2) if markup else None,
                confidence=ident.confidence,
                confidence_level=ident.confidence_level,
                deal_rating=_deal_rating(markup),
                data_confidence=ep.data_confidence if ep else None,
                price_source=ep.price_source.value if ep and ep.price_source else None,
            )

    results: list[MenuWineResult] = list(
        await asyncio.gather(*[_analyze(w) for w in wines])
    )

    return MenuUploadResponse(
        filename=filename,
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
