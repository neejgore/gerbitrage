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


_CLAUDE_PROMPT = """\
You are extracting wine entries from a restaurant wine list photo.

For EVERY wine that has a visible price, output exactly one line in this format:
  WINE NAME | VINTAGE | PRICE

Rules:
- WINE NAME: producer + wine name as printed (e.g. "Opus One", "Château Margaux", "Stag's Leap Wine Cellars Artemis")
- VINTAGE: 4-digit year (e.g. 2019) or NV for non-vintage; write NONE if no vintage is shown
- PRICE: the number only, no $ sign, no commas (e.g. 145 or 1250.00)
- Skip cocktails, spirits, beer, food, and any item without a price
- Output ONLY the data lines, no headers, no explanations

Example output:
Opus One | 2019 | 290
Krug Grande Cuvée | NV | 380
Stag's Leap Artemis Cabernet | 2021 | 95
"""


async def _image_to_text_claude(data: bytes, media_type: str = "image/jpeg") -> str:
    """Use Claude Vision to extract wine list entries from an image."""
    import base64
    import os
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    b64 = base64.standard_b64encode(data).decode()
    client = anthropic.AsyncAnthropic(api_key=api_key)

    message = await client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": b64,
                        },
                    },
                    {"type": "text", "text": _CLAUDE_PROMPT},
                ],
            }
        ],
    )
    for block in (message.content or []):
        if hasattr(block, "text"):
            return block.text
    return ""


def _parse_claude_output(raw: str) -> list[dict]:
    """
    Convert Claude's structured output (Name | Vintage | Price) into the same
    list-of-dicts format that _parse_wines produces.
    """
    entries: list[dict] = []
    seen: set[tuple] = set()
    for line in raw.splitlines():
        line = line.strip().strip("-").strip()
        if "|" not in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 3:
            continue
        desc, vintage_raw, price_raw = parts[0], parts[1], parts[2]
        if not desc or len(desc) < 3:
            continue
        try:
            price = float(price_raw.replace(",", "").replace("$", ""))
        except ValueError:
            continue
        if not (8 <= price <= 50_000):
            continue
        vintage_raw = vintage_raw.upper().strip()
        if vintage_raw in ("NONE", "N/A", "", "-"):
            vintage: int | None = None
        elif vintage_raw in ("NV", "MV"):
            vintage = None
        elif re.match(r"^(?:19|20)\d{2}$", vintage_raw):
            vintage = int(vintage_raw)
        else:
            vintage = None
        key = (desc.lower()[:45], vintage, int(price))
        if key in seen:
            continue
        seen.add(key)
        entries.append({"desc": desc, "vintage": vintage, "menu_price": price})
    return entries


def _image_to_text_tesseract(data: bytes) -> str:
    """Fallback OCR using Tesseract (used when Claude is unavailable)."""
    try:
        from PIL import Image, ImageFilter, ImageEnhance, ImageOps
        import pytesseract
    except ImportError:
        raise HTTPException(
            status_code=422,
            detail="Image OCR is unavailable. Please upload a PDF instead.",
        )
    try:
        from pillow_heif import register_heif_opener
        register_heif_opener()
    except ImportError:
        pass

    try:
        img = Image.open(io.BytesIO(data)).convert("RGB")
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Could not open image ({exc}). Supported formats: JPG, PNG, HEIC, WebP.",
        )
    max_px = 2400
    if max(img.width, img.height) > max_px:
        img.thumbnail((max_px, max_px), Image.LANCZOS)
    min_px = 800
    if max(img.width, img.height) < min_px:
        scale = min_px / max(img.width, img.height)
        img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
    img = img.convert("L")
    img = ImageOps.autocontrast(img, cutoff=2)
    img = ImageEnhance.Contrast(img).enhance(1.5)
    img = img.filter(ImageFilter.SHARPEN)
    text = pytesseract.image_to_string(img, config="--psm 4 --oem 1")
    if len(text.strip()) < 50:
        text = pytesseract.image_to_string(img, config="--psm 6 --oem 1")
    return text


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
        return _image_to_text_tesseract(data)
    # Default: treat as HTML / plain text
    try:
        text = data.decode("utf-8", errors="replace")
    except Exception:
        text = data.decode("latin-1", errors="replace")

    if "<html" in text[:2000].lower() or "<body" in text[:2000].lower():
        return _html_to_text(text)
    return text  # plain text — return as-is


# ── Wine-entry parsing ─────────────────────────────────────────────────────────

# Visual fill characters used in printed menus as leaders (dots, dashes, etc.)
_FILL_RE = re.compile(r"[.\-_·•*]{3,}")

# Vintage token: 19xx / 20xx, NV, MV
_VINTAGE_RE = re.compile(r"\b((?:19|20)\d{2}|NV|MV)\b", re.I)

# Price token: $NNN, NNN, NNN.NN  (2–5 digits, no year-shaped numbers)
_PRICE_RE = re.compile(r"(?<!\d)\$?(\d{2,5}(?:\.\d{1,2})?)(?!\d)")

_SKIP_RE = re.compile(
    r"^(\d+$|BY THE GLASS|HALF BOTTLE|SPARKLING$|ROSE$|ROSÉ$|WHITE$|RED$|BEER"
    r"|COCKTAIL|MOCKTAIL|SPIRIT|VODKA|GIN|TEQUILA|MEZCAL|RUM|BOURBON"
    r"|WHISKEY|SCOTCH|COGNAC|CHARDONNAY|PINOT NOIR|CABERNET|ZINFANDEL"
    r"|FRANCE$|SPAIN$|ITALY$|GERMANY$|AUSTRIA$|CHAMPAGNE$|BURGUNDY$"
    r"|BORDEAUX$|DESSERT$|FORTIFIED$|MERLOT$|SYRAH$|SAUVIGNON BLANC$"
    r"|PAGE\s*\d|TABLE\s*OF\s*CONTENTS|WINE\s*LIST|^\d{1,3}$)",
    re.I,
)
_SPIRITS_KW = (
    "vodka", "gin", "rum", "whiskey", "bourbon", "scotch",
    "tequila", "mezcal", "cognac", "beer", "ale", "lager",
    "pilsner", "ipa", "stout", "soda",
)


def _clean_line(raw: str) -> str:
    """Strip visual fill characters and collapse whitespace."""
    line = _FILL_RE.sub(" ", raw)
    return re.sub(r"\s{2,}", " ", line).strip()


def _is_wine_price(val: float) -> bool:
    return 8 <= val <= 50_000


# Characters that are strong indicators of OCR garbage (not found in real wine names)
_GARBAGE_CHARS = re.compile(r"[~=<>{}\[\]\\|@#%^*_\x00-\x1f]")

def _looks_like_wine_name(desc: str) -> bool:
    """
    Return True only if `desc` looks like a plausible wine / producer name.
    Rejects OCR garbage like 'a af Se ~ OX BSS Ss Yo. f sage. Sy = Sf = < =S'.
    """
    if not desc or len(desc) < 4:
        return False
    # Reject immediately if it contains hard garbage characters
    if _GARBAGE_CHARS.search(desc):
        return False
    # Must be mostly alphabetic (letters + spaces + common punctuation)
    alpha = sum(c.isalpha() or c.isspace() for c in desc)
    if alpha / len(desc) < 0.65:
        return False
    # Average word length must be reasonable (real names have longer words)
    words = [w for w in desc.split() if w.isalpha()]
    if not words:
        return False
    avg_word_len = sum(len(w) for w in words) / len(words)
    if avg_word_len < 2.8:
        return False
    # At least one word of 3+ letters
    if not any(len(w) >= 3 for w in words):
        return False
    return True


def _parse_wines(text: str) -> list[dict]:
    """
    Extract (desc, vintage, menu_price) triples from raw OCR / PDF text.

    Handles the many formats found on restaurant wine lists:
      • "Name 2019 145"          – classic year+price on one line
      • "Name ........... 145"   – price without year (dots as leaders)
      • "Name $145"              – explicit $ sign, no year
      • "Name 2019"  / "145"     – name+year on one line, price on next
      • "Name"  / "2019  145"    – name alone, year+price on next line
    """
    lines = [_clean_line(l) for l in text.splitlines() if _clean_line(l)]
    entries: list[dict] = []
    seen: set[tuple] = set()
    used: set[int] = set()  # line indices consumed as part of a multi-line match

    def _add(desc: str, vintage_str: str | None, price: float, idx: int) -> None:
        desc = re.sub(r"\s*[|\-–—,;:]+\s*$", "", desc).strip()
        # Strip trailing year tokens that ended up in the desc
        desc = re.sub(r"\s+((?:19|20)\d{2}|NV|MV)\s*$", "", desc, flags=re.I).strip()
        if not _looks_like_wine_name(desc):
            return
        if _SKIP_RE.match(desc):
            return
        if any(kw in desc.lower() for kw in _SPIRITS_KW):
            return
        if not _is_wine_price(price):
            return
        vintage = int(vintage_str) if vintage_str and vintage_str.isdigit() else None
        key = (desc.lower()[:45], vintage, int(price))
        if key in seen:
            return
        seen.add(key)
        used.add(idx)
        entries.append({"desc": desc, "vintage": vintage, "menu_price": price})

    # ── Pass 1: everything on one line ─────────────────────────────────────
    for i, line in enumerate(lines):
        # Find all price-shaped numbers (exclude 4-digit years)
        price_tokens = [
            (m.start(), m.group(1))
            for m in _PRICE_RE.finditer(line)
            if not re.match(r"^(?:19|20)\d{2}$", m.group(1))
            and _is_wine_price(float(m.group(1).replace(",", "")))
        ]
        if not price_tokens:
            continue

        # Use the last price token as the menu price (typically right-aligned)
        price_pos, price_str = price_tokens[-1]
        price = float(price_str.replace(",", ""))
        desc_raw = line[:price_pos].strip()

        # Find vintage in the desc portion
        vm = list(_VINTAGE_RE.finditer(desc_raw))
        if vm:
            vt = vm[-1]
            desc = (desc_raw[:vt.start()] + desc_raw[vt.end():]).strip()
            vintage_str: str | None = vt.group(1)
        else:
            desc = desc_raw
            vintage_str = None

        _add(desc, vintage_str, price, i)

    # ── Pass 2: name on one line, price (+optional year) on the next ───────
    for i in range(len(lines) - 1):
        if i in used:
            continue
        name_line = lines[i]
        next_line = lines[i + 1]

        # Name line should look like a wine name: no price, not too short
        if _PRICE_RE.search(name_line):
            continue
        if len(name_line) < 5 or _SKIP_RE.match(name_line):
            continue
        if any(kw in name_line.lower() for kw in _SPIRITS_KW):
            continue

        # Next line should have a price
        price_tokens = [
            (m.start(), m.group(1))
            for m in _PRICE_RE.finditer(next_line)
            if not re.match(r"^(?:19|20)\d{2}$", m.group(1))
            and _is_wine_price(float(m.group(1).replace(",", "")))
        ]
        if not price_tokens:
            continue

        price_pos, price_str = price_tokens[-1]
        price = float(price_str.replace(",", ""))
        rest = next_line[:price_pos].strip()

        vm = list(_VINTAGE_RE.finditer(rest or next_line))
        vintage_str = vm[-1].group(1) if vm else None

        _add(name_line, vintage_str, price, i)

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

    # Determine media type for Claude
    _ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    _mime_map = {
        "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "png": "image/png", "webp": "image/webp",
        "heic": "image/jpeg", "heif": "image/jpeg",  # Claude accepts HEIC as JPEG after conversion
        "gif": "image/gif",
    }
    media_type = _mime_map.get(_ext, "image/jpeg")

    is_pdf = filename.lower().endswith(".pdf") or "pdf" in content_type
    is_image = any(
        filename.lower().endswith(ext)
        for ext in (".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif", ".tif", ".tiff")
    ) or content_type.startswith("image/")

    # ── Image path: Claude Vision first, Tesseract as fallback ────────────
    if is_image:
        import os
        if os.environ.get("ANTHROPIC_API_KEY"):
            try:
                # HEIC/HEIF: convert to JPEG bytes before sending to Claude
                if _ext in ("heic", "heif"):
                    try:
                        from pillow_heif import register_heif_opener
                        register_heif_opener()
                    except ImportError:
                        pass
                    from PIL import Image as _PILImage
                    _buf = io.BytesIO()
                    _PILImage.open(io.BytesIO(data)).convert("RGB").save(_buf, format="JPEG", quality=90)
                    _img_data = _buf.getvalue()
                    media_type = "image/jpeg"
                else:
                    _img_data = data

                claude_raw = await _image_to_text_claude(_img_data, media_type)
                logger.debug("Claude raw output for '%s':\n%s", filename, claude_raw[:800])
                wines = _parse_claude_output(claude_raw)
                logger.info("Claude extracted %d wine entries from '%s'", len(wines), filename)
                if not wines:
                    raise HTTPException(
                        status_code=422,
                        detail=(
                            f"No wine entries with prices found in '{filename}'. "
                            "Make sure the photo shows a wine list with prices clearly visible."
                        ),
                    )
                return await _run_batch_from_entries(wines, filename)
            except HTTPException:
                raise
            except Exception as exc:
                logger.warning("Claude Vision failed for '%s': %s — falling back to Tesseract", filename, exc)
                # Fall through to Tesseract below

        # Tesseract fallback (or if no API key)
        try:
            text = _image_to_text_tesseract(data)
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"Could not read image: {exc}") from exc
        return await _run_batch(text, filename)

    # ── PDF / URL path ─────────────────────────────────────────────────────
    try:
        if is_pdf:
            text = _pdf_to_text(data)
        else:
            try:
                text = _pdf_to_text(data)
            except Exception:
                text = _image_to_text_tesseract(data)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Could not read file: {exc}") from exc

    return await _run_batch(text, filename)


# ── Shared batch-analysis helpers ─────────────────────────────────────────────

async def _run_batch_from_entries(wines: list[dict], source_name: str) -> MenuUploadResponse:
    """Batch-analyze pre-parsed wine entries (e.g. from Claude Vision)."""
    wines = wines[:150]
    return await _batch_analyze(wines, source_name)


async def _run_batch(text: str, source_name: str) -> MenuUploadResponse:
    """Parse wine entries from text and batch-analyze them. Shared by file and URL endpoints."""
    logger.debug("OCR/extracted text from '%s' (first 1000 chars):\n%s", source_name, text[:1000])
    wines = _parse_wines(text)
    logger.info("Parsed %d wine entries from '%s'", len(wines), source_name)
    if not wines:
        raise HTTPException(
            status_code=422,
            detail=(
                f"No wine entries found in '{source_name}'. "
                "Make sure the image shows a wine list with prices clearly visible. "
                "For best results, photograph the menu straight-on in good lighting."
            ),
        )
    wines = wines[:150]
    return await _batch_analyze(wines, source_name)


async def _batch_analyze(wines: list[dict], source_name: str) -> MenuUploadResponse:
    """Run parallel analysis on a list of pre-validated wine dicts."""
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
                retail_price=round(retail, 2) if retail is not None else None,
                wholesale_est=round(ep.estimated_wholesale, 2) if ep and ep.estimated_wholesale is not None else None,
                min_retail=ep.min_retail if ep else None, max_retail=ep.max_retail if ep else None,
                markup=round(markup, 2) if markup is not None else None,
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

    # Use the last path segment as a friendly name
    source_name = url.rstrip("/").split("/")[-1].split("?")[0] or url[:60]

    # Route image URLs through Claude Vision if available
    import os as _os
    url_lower = url.lower().split("?")[0]
    is_url_image = content_type.lower().startswith("image/") or any(
        url_lower.endswith(e) for e in (".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif")
    )
    if is_url_image and _os.environ.get("ANTHROPIC_API_KEY"):
        _ext2 = url_lower.rsplit(".", 1)[-1] if "." in url_lower else "jpeg"
        _mime2 = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
                  "webp": "image/webp"}.get(_ext2, "image/jpeg")
        _img_bytes = data
        # HEIC from URL: convert to JPEG before sending to Claude
        if _ext2 in ("heic", "heif"):
            try:
                from pillow_heif import register_heif_opener
                register_heif_opener()
            except ImportError:
                pass
            try:
                from PIL import Image as _PILImage
                _buf = io.BytesIO()
                _PILImage.open(io.BytesIO(data)).convert("RGB").save(_buf, format="JPEG", quality=90)
                _img_bytes = _buf.getvalue()
                _mime2 = "image/jpeg"
            except Exception:
                pass
        # Also use content-type header if extension is unknown
        elif not _ext2 or _mime2 == "image/jpeg":
            _ct_mime = content_type.lower().split(";")[0].strip()
            if _ct_mime in ("image/png", "image/webp", "image/gif"):
                _mime2 = _ct_mime
        try:
            claude_raw = await _image_to_text_claude(_img_bytes, _mime2)
            wines = _parse_claude_output(claude_raw)
            if wines:
                return await _run_batch_from_entries(wines, source_name)
        except Exception as exc:
            logger.warning("Claude Vision failed for URL image: %s", exc)

    text = _extract_text_from_url_content(data, content_type, url)
    return await _run_batch(text, source_name)
