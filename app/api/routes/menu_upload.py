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


# ── Step 1: extract wines exactly as printed ──────────────────────────────────
_EXTRACT_SYSTEM = (
    "You are a menu scanner. Report ONLY text that is literally visible in the image. "
    "Never add, infer, or substitute wine names from your own knowledge. "
    "Copy names exactly as printed, even if they look unusual. "
    "Include sake, beer, spirits, and other beverages exactly as printed — do not skip them. "
    "The next step will decide what to keep."
)
_EXTRACT_PROMPT = "List every beverage item on this menu exactly as printed, including name, vintage, and price."

# ── Step 2: normalise raw names for catalog matching ──────────────────────────
_NORMALISE_SYSTEM = (
    "You are a wine expert. Given a raw list of wines exactly as printed on a menu, "
    "reformat each one into standard wine catalog format: Producer, Wine Name, so it "
    "can be looked up in a database. Keep the vintage and price unchanged."
)
_NORMALISE_PROMPT_TPL = """\
Here are items extracted from a wine menu. Reformat WINE entries only into:
PRODUCER WINE_NAME | VINTAGE | PRICE

Rules:
- One line per wine, nothing else
- SKIP any item that is sake, beer, spirits, cocktail, water, juice, tea, coffee, or a flight/package
- SKIP section headers, descriptions, restaurant policies, or lines with no wine name
- CRITICAL: The GRAPE/VARIETAL must ALWAYS be included in the output. Never drop it.
- If the entry is GRAPE - PRODUCER VINTAGE CUVEE - REGION PRICE, the output MUST be "PRODUCER GRAPE CUVEE":
    "Chardonnay- Sequoia Grove 2023 Estate- Napa Valley 75"    → "SEQUOIA GROVE CHARDONNAY ESTATE | 2023 | 75"
    "Merlot- Freemark Abbey 2017 Stagecoach- Atlas Peak 135"   → "FREEMARK ABBEY MERLOT STAGECOACH | 2017 | 135"
    "Pinot Noir- Boars View 2020- Ft Ross 105"                 → "BOARS VIEW PINOT NOIR | 2020 | 105"
    "Cabernet Sauvignon- Aquinas 2021- North Coast 55"         → "AQUINAS CABERNET SAUVIGNON | 2021 | 55"
    "Sauvignon Blanc- Joseph Cellars 2024- Napa Valley 65"     → "JOSEPH CELLARS SAUVIGNON BLANC | 2024 | 65"
- If the entry is GRAPE, PRODUCER PRICE (e.g. "AGLIANICO, CONTRADE DI TAURAUSI 20/38"), output "CONTRADE DI TAURAUSI AGLIANICO"
- Keep the vintage and price EXACTLY as extracted — do NOT add, change, or invent any information
- PRICE: use the bottle price. If the wine appears in BOTH a by-the-glass section AND a bottle section, output it ONCE with the price as GLASS/BOTTLE (e.g. 21/75). If only a glass price is given, output as GLASS_PRICE | GLASS (4th column).
- If a wine name is unclear, copy it exactly as printed — never substitute a different wine name
- Output nothing else

Wines:
{wines}
"""


async def _claude_call(
    client: "anthropic.AsyncAnthropic",
    system: str,
    messages: list,
    model: str,
    max_tokens: int = 4096,
) -> str:
    msg = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=messages,
    )
    for block in (msg.content or []):
        if hasattr(block, "text"):
            return block.text
    return ""


async def _normalise_text_wines(text: str) -> str:
    """
    Single-step Claude pipeline for text-based menus (HTML, PDF, plain text).
    The text is already extracted — we just need Claude to normalise it into
    PRODUCER WINE_NAME | VINTAGE | PRICE format.
    """
    import os
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    client = anthropic.AsyncAnthropic(api_key=api_key)
    _MODELS = ["claude-sonnet-4-6", "claude-haiku-4-5", "claude-sonnet-4-5"]

    last_err: Exception | None = None
    for model in _MODELS:
        try:
            result = await _claude_call(
                client,
                system=_NORMALISE_SYSTEM,
                messages=[{"role": "user", "content": _NORMALISE_PROMPT_TPL.format(wines=text)}],
                model=model,
                max_tokens=8192,
            )
            logger.info("Text normalise output (%s):\n%s", model, result[:2000])
            return result
        except Exception as exc:
            last_err = exc
            logger.warning("Model %s failed: %s", model, exc)
            continue

    raise RuntimeError(f"All Claude models failed: {last_err}")


async def _extract_and_normalise_wines(data: bytes, media_type: str) -> str:
    """
    Two-step Claude pipeline:
      1. Ask Claude to read what wines are literally printed on the menu image.
      2. Ask Claude to reformat those raw names into standard catalog format.

    Separating these steps prevents hallucination: step 1 is anchored to the
    image; step 2 is pure text reformatting with no image involved.
    """
    import base64
    import os
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    b64 = base64.standard_b64encode(data).decode()
    client = anthropic.AsyncAnthropic(api_key=api_key)

    _MODELS = [
        "claude-sonnet-4-6",
        "claude-haiku-4-5",
        "claude-sonnet-4-5",
    ]

    last_err: Exception | None = None
    for model in _MODELS:
        try:
            # ── Step 1: extract from image ────────────────────────────────────
            raw = await _claude_call(
                client,
                system=_EXTRACT_SYSTEM,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64",
                                                       "media_type": media_type, "data": b64}},
                        {"type": "text", "text": _EXTRACT_PROMPT},
                    ],
                }],
                model=model,
            )
            if not raw.strip():
                continue

            logger.info("Step 1 (extract) output:\n%s", raw[:2000])

            # ── Step 2: normalise for catalog matching ────────────────────────
            normalised = await _claude_call(
                client,
                system=_NORMALISE_SYSTEM,
                messages=[{
                    "role": "user",
                    "content": _NORMALISE_PROMPT_TPL.format(wines=raw),
                }],
                model=model,
            )

            logger.info("Step 2 (normalise) output:\n%s", normalised[:2000])
            return normalised

        except Exception as exc:
            if "not_found_error" in str(exc) or "404" in str(exc):
                last_err = exc
                continue
            raise

    raise RuntimeError(f"No Claude vision model available. Last error: {last_err}")


def _parse_claude_natural(raw: str) -> list[dict]:
    """
    Parse Claude's natural conversational output when asked "what wines are on this menu?"

    Claude naturally responds with lines like:
      • Aglianico, Contrade di Taurausi — Irpinia, Italy 2019 — $20/38
      • Cabernet Sauvignon, Anakota — Knights Valley, California 2022 — $45/88
      Leos Cuvée Augusta - Provence, France 2023 - $16/28
      Japan Flight (3oz of each) — $59

    Strategy: for each non-empty line, strip bullets/markdown, find the price at the
    end, find the vintage year, and treat the remainder as the wine name.
    """
    _POURS = 5
    entries: list[dict] = []
    seen: set[tuple] = set()

    # Detect glass-section context from headers in the output
    _in_glass = False

    for raw_line in raw.splitlines():
        line = raw_line.strip()
        # Strip leading markdown bullets, dashes, numbers
        line = re.sub(r"^[\-\*•·▸►\d\.]+\s*", "", line).strip()
        if not line or len(line) < 4:
            continue

        # Detect glass-section headers like "Rosé (5oz/9oz)" or "Red (5oz/9oz)"
        if re.search(r"\b\d+\s*oz\b", line, re.I) and len(line) < 40:
            _in_glass = True
            continue
        if re.search(r"\bby\s+the\s+(glass|bottle)\b", line, re.I):
            _in_glass = True if "glass" in line.lower() else False
            continue

        # Skip pure section headers with no price
        if re.match(r"^(here'?s?\s+what|here are|the\s+menu|wines?\s+list|rosé?|red|white|sparkling|dessert|fortified)\b.*$", line, re.I):
            if not re.search(r"\$?\d{2,}", line):
                continue

        # ----- Extract price -----
        # Look for price patterns at the end: $20/38, $16/28, $59, 20/38, 45/88
        price_match = re.search(
            r"\$?(\d{1,3}(?:\.\d{2})?)\s*/\s*(\d{1,3}(?:\.\d{2})?)(?:\s*/\s*(\d{1,3}(?:\.\d{2})?))?(?:\s*$|\s*[\(\[])",
            line,
        )
        single_price_match = re.search(r"\$(\d{2,5}(?:\.\d{2})?)\s*(?:$|[\(\[])", line)

        is_glass = _in_glass
        price: float | None = None

        if price_match:
            vals = [float(price_match.group(g)) for g in (1, 2, 3) if price_match.group(g)]
            if len(vals) == 3 and vals[0] < vals[1] < vals[2]:
                price = vals[2]          # X/Y/Z → bottle price
                is_glass = False
            else:
                price = min(vals)        # X/Y → smaller = glass price
                is_glass = True
            # Trim price from line
            line = line[:price_match.start()].strip()
        elif single_price_match:
            price = float(single_price_match.group(1))
            line = line[:single_price_match.start()].strip()

        if price is None or not (8 <= price <= 50_000):
            continue

        # ----- Extract vintage -----
        vt_match = re.search(r"\b((?:19|20)\d{2}|NV|MV)\b", line, re.I)
        vintage: int | None = None
        if vt_match:
            raw_vt = vt_match.group(1).upper()
            if re.match(r"^\d{4}$", raw_vt):
                vintage = int(raw_vt)
            line = (line[:vt_match.start()] + line[vt_match.end():]).strip()

        # ----- Extract wine name (strip region after dash separators) -----
        # Pattern: "Wine Name — Region, Country" or "Wine Name - Region"
        # Keep only the part before the first " — " or " - Region" pattern
        name = line
        for sep in (" — ", " – ", " - "):
            if sep in name:
                parts = name.split(sep)
                # The wine name is before the first separator that leads into a region/country
                name = parts[0].strip()
                break

        # Clean trailing punctuation
        name = re.sub(r"[\s,\-–—:;]+$", "", name).strip()
        # Strip parenthetical pour sizes from name
        name = re.sub(r"\s*\(\s*\d+\s*oz[^)]*\)", "", name, flags=re.I).strip()

        if not name or len(name) < 3:
            continue
        if not _looks_like_wine_name(name):
            continue
        if _SKIP_RE.match(name):
            continue
        if _REGION_LINE_RE.match(name):
            continue
        if _SPIRITS_RE.search(name):
            continue

        menu_price = round(price * _POURS, 2) if is_glass else price
        if not (8 <= menu_price <= 50_000):
            continue

        display = f"{name} (by glass)" if is_glass else name
        key = (name.lower()[:45], vintage, int(menu_price))
        if key in seen:
            continue
        seen.add(key)
        entries.append({
            "desc": display,
            "vintage": vintage,
            "menu_price": menu_price,
            "glass_price": price if is_glass else None,
        })

    return entries


def _parse_claude_output(raw: str) -> list[dict]:
    """
    Convert Claude's structured output (Name | Vintage | Price) into the same
    list-of-dicts format that _parse_wines produces.
    """
    _POURS_PER_BOTTLE = 5  # standard 5oz pour → 5 pours per 750ml bottle

    entries: list[dict] = []
    seen: set[tuple] = set()
    for line in raw.splitlines():
        line = line.strip().strip("-").strip()
        if "|" not in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < 3:
            continue
        desc = parts[0]
        vintage_raw = parts[1]
        price_raw = parts[2]
        is_glass = len(parts) >= 4 and "GLASS" in parts[3].upper()

        if not desc or len(desc) < 3:
            continue

        price_raw = price_raw.replace(",", "").replace("$", "").strip()
        # Handle X/Y/Z or X/Y price formats
        if "/" in price_raw:
            price_parts = [p.strip() for p in price_raw.split("/") if p.strip()]
            try:
                vals = [float(p) for p in price_parts]
            except ValueError:
                continue
            if len(vals) >= 3 and vals[0] < vals[1] < vals[2]:
                # Three-tier: glass/half/bottle — use bottle price
                price = vals[-1]
                is_glass = False
            else:
                # Two-tier: glass pours — use smaller (5oz)
                price = min(vals)
                is_glass = True
        else:
            try:
                price = float(price_raw)
            except ValueError:
                continue

        if not (3 <= price <= 50_000):
            continue

        # Scale glass price to bottle-equivalent for markup analysis
        menu_price = round(price * _POURS_PER_BOTTLE, 2) if is_glass else price
        if not (8 <= menu_price <= 50_000):
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

        # Annotate name so UI can show glass context
        display_desc = f"{desc} (by glass)" if is_glass else desc

        key = (desc.lower()[:45], vintage, int(menu_price))
        if key in seen:
            continue
        seen.add(key)
        entries.append({
            "desc": display_desc,
            "vintage": vintage,
            "menu_price": menu_price,
            "glass_price": price if is_glass else None,
        })
    return entries


def _prepare_image_for_claude(data: bytes, ext: str) -> tuple[bytes, str]:
    """
    Prepare an image for the Claude API.

    - For HEIC/HEIF: convert to JPEG (Claude doesn't accept HEIC natively).
    - For JPEG/PNG/WebP: pass through at original quality whenever possible.
    - Only resize if the base64-encoded payload would exceed Claude's 5 MB limit
      (~3.75 MB raw).  Use quality=95 to preserve text legibility.

    Returns (image_bytes, media_type).
    """
    from PIL import Image as _PIL

    MAX_BYTES = 3_500_000  # conservative limit below the 5 MB base64 cap

    # HEIC must be converted; everything else can stay in its original format
    needs_conversion = ext in ("heic", "heif")

    if needs_conversion:
        try:
            from pillow_heif import register_heif_opener
            register_heif_opener()
        except ImportError:
            pass
        img = _PIL.open(io.BytesIO(data)).convert("RGB")
        # Only downscale if the output would exceed the size cap
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=95, optimize=True)
        if buf.tell() > MAX_BYTES:
            # Shrink until it fits, losing as little quality as possible
            for max_px in (3000, 2400, 2000, 1600):
                if max(img.width, img.height) <= max_px:
                    continue
                img.thumbnail((max_px, max_px), _PIL.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=95, optimize=True)
                if buf.tell() <= MAX_BYTES:
                    break
        return buf.getvalue(), "image/jpeg"

    # Non-HEIC: use original bytes if they fit, otherwise resize minimally.
    # Detect actual format from bytes (not extension) — files from phones often
    # have .png extension but are actually JPEG, which causes a 400 from Claude API.
    if len(data) <= MAX_BYTES:
        try:
            detected = _PIL.open(io.BytesIO(data))
            fmt = (detected.format or "").upper()
            media_type = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}.get(fmt, "image/jpeg")
        except Exception:
            media_type = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                          "png": "image/png", "webp": "image/webp"}.get(ext, "image/jpeg")
        return data, media_type

    # Oversized non-HEIC — shrink just enough to fit
    img = _PIL.open(io.BytesIO(data)).convert("RGB")
    for max_px in (3000, 2400, 2000, 1600):
        if max(img.width, img.height) <= max_px:
            continue
        img.thumbnail((max_px, max_px), _PIL.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=95, optimize=True)
        if buf.tell() <= MAX_BYTES:
            return buf.getvalue(), "image/jpeg"

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95, optimize=True)
    return buf.getvalue(), "image/jpeg"


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

# Vintage token: 19xx / 20xx, NV, MV, N.V., M.V.
_VINTAGE_RE = re.compile(r"\b((?:19|20)\d{2}|N\.?V\.?|M\.?V\.?)\b", re.I)

# Price token: $NNN, NNN, NNN.NN  (2–5 digits, no year-shaped numbers)
_PRICE_RE = re.compile(r"(?<!\d)\$?(\d{2,5}(?:\.\d{1,2})?)(?!\d)")

_SKIP_RE = re.compile(
    # Standalone section headers — must match the WHOLE string ($ anchor prevents
    # blocking real wine names that start with a grape variety, e.g.
    # "Cabernet Sauvignon, Anakota" must NOT be blocked by "CABERNET$")
    r"^(\d+$|WINE\s+BY\s+THE\s+GLASS$|BY\s+THE\s+GLASS$|HALF\s+BOTTLES?$|MAGNUM$"
    r"|SPARKLING$|ROSÉ?$|WHITE$|RED$|ORANGE$"
    r"|BEER$|COCKTAILS?$|MOCKTAILS?$|SPIRITS?$|VODKA$|GIN$|TEQUILA$|MEZCAL$|RUM$|BOURBON$"
    r"|WHISKEY$|SCOTCH$|COGNAC$"
    r"|CHARDONNAY$|PINOT\s+NOIR$|CABERNET$|CABERNET\s+SAUVIGNON$|ZINFANDEL$"
    r"|MERLOT$|SYRAH$|SAUVIGNON\s+BLANC$|PINOT\s+GRIGIO$|RIESLING$|GRENACHE$"
    r"|FRANCE$|SPAIN$|ITALY$|GERMANY$|AUSTRIA$|CHAMPAGNE$|BURGUNDY$"
    r"|BORDEAUX$|RHONE$|RHÔNE$|DESSERT$|FORTIFIED$"
    r"|GLASS\s*[/|]\s*BOTTLE|BOTTLE\s*[/|]\s*GLASS|PER\s+GLASS|PER\s+BOTTLE"
    r"|PAGE\s*\d|TABLE\s*OF\s*CONTENTS|WINE\s+LIST|\d{1,3}$)",
    re.I,
)

# Region/appellation lines: "irpinia, italy 2019", "napa, california 2022" etc.
# These appear BELOW the wine name line and must not be used as wine names.
_REGION_LINE_RE = re.compile(
    r"^[\w\s\'\-\.]+,\s*"  # place name + comma
    r"(?:california|italy|france|spain|germany|austria|portugal|argentina|chile|"
    r"australia|new\s+zealand|oregon|washington|new\s+york|greece|hungary|"
    r"napa|sonoma|burgundy|bordeaux|champagne|rhone|loire|alsace|tuscany|piedmont|"
    r"ca|ny|or|wa)\b",
    re.I,
)
_SPIRITS_KW = (
    "vodka", "gin", "rum", "whiskey", "bourbon", "scotch",
    "tequila", "mezcal", "cognac", "beer", "ale", "lager",
    "pilsner", "ipa", "stout", "soda", "sake", "junmai",
)
# Word-boundary spirits filter — prevents substring false-positives
# (e.g. "ale" ⊄ "aleatico", "beer" ⊄ "beerenauslese")
_SPIRITS_RE = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in _SPIRITS_KW) + r")\b", re.I
)

# Wine critic scores that look like prices — strip BEFORE price detection
_SCORE_RE = re.compile(
    r"\b(?:RP|WS|JS|VM|AG|JD|NT|TP|ST|JR|BH)\s*\d{2,3}\b"  # critic initials + score
    r"|\b\d{2,3}\s*(?:pts?|points?)\b"                         # "92 pts", "92 points"
    r"|\b(?:8\d|9\d)\s*/\s*100\b",                             # scores 80-99/100 (avoids stripping e.g. "16/100" bottle price)
    re.I,
)

# Market / seasonal price markers — no retail price available
_MARKET_PRICE_RE = re.compile(
    r"\b(MP|MKT|Market\s+Price|Market|SEA|Seasonal|Upon\s+Request|TBD)\b\s*$", re.I
)

# Leading decoration: bullets, arrows, decorative dashes at start of line
_LEAD_DECOR_RE = re.compile(r"^[•·\-–—►▶→✦◆◇▪▸★☆✓✗\s]+")

# Magnum section (1.5L = 2× standard bottle — divide by 2 for per-bottle comparison)
_MAGNUM_SECTION_RE = re.compile(r"\b(magnums?|1\.5\s*[Ll](?:itre)?s?)\b", re.I)

# Geographic/regional words that identify a mid-line as a continuation (not a new wine)
_GEO_WORDS_RE = re.compile(
    r"\b(valley|coast|mountain|county|hills?|creek|vineyard|estate|village|"
    r"district|appellation|peninsula|plateau|canyon|highlands?|lowlands?|"
    r"clos|ch[aâ]teau|domaine|cave|cellars?|winery|"
    r"alsace|burgundy|bordeaux|champagne|rh[oô]ne|loire|provence|languedoc|"
    r"tuscany|piedmont|veneto|barossa|marlborough|"
    r"napa|sonoma|mendocino|carneros|monterey|paso|columbia|willamette|"
    r"france|italy|spain|germany|austria|portugal|argentina|chile|"
    r"australia|zealand|africa|california|oregon|washington)\b",
    re.I,
)

# "Ask quote" price marker — remove from lines before parsing
_AQ_RE = re.compile(r"\bAQ\b\s*$", re.I)

# Bin number prefix: "42." or "42)" at start of line — 1-3 digits only to avoid stripping years
_BIN_RE = re.compile(r"^\d{1,3}[\.\)]\s+")

# European thousands separator: "3.100" = 3,100 — 1-3 digits, dot, exactly 3 digits
# Must NOT be followed by another digit (excludes "3.1000" or decimal "78.00")
_EURO_THOUSANDS_RE = re.compile(r"(?<!\d)(\d{1,3})\.(\d{3})(?!\d)")

_POURS_PER_BOTTLE = 5  # 5oz pour × 5 = 750ml bottle equivalent

# Vintage normalization pattern for stripping from desc strings
_VINTAGE_STRIP_RE = re.compile(r"\s+((?:19|20)\d{2}|N\.?V\.?|M\.?V\.?)\s*$", re.I)
_VINTAGE_INLINE_RE = re.compile(r"\s+((?:19|20)\d{2}|N\.?V\.?|M\.?V\.?)\b", re.I)


def _clean_line(raw: str) -> str:
    """Normalize a raw line: pipes, fill chars, bullets, score markers, whitespace."""
    # Pipe-separated table rows: "Name | 2019 | 145" → "Name 2019 145"
    if "|" in raw:
        raw = " ".join(p.strip() for p in raw.split("|") if p.strip())
    # US comma-thousands: "1,250" → "1250" (before other processing)
    raw = re.sub(r"(?<!\d)(\d{1,3}),(\d{3})(?!\d)", r"\1\2", raw)
    # European dot-thousands: "3.100" → "3100" (only 3 digits after dot)
    raw = _EURO_THOUSANDS_RE.sub(lambda m: m.group(1) + m.group(2), raw)
    line = _FILL_RE.sub(" ", raw)
    line = re.sub(r"\s{2,}", " ", line).strip()
    line = _LEAD_DECOR_RE.sub("", line).strip()    # strip leading bullets/dashes
    line = _AQ_RE.sub("", line).strip()             # remove "ask quote" markers
    line = _MARKET_PRICE_RE.sub("", line).strip()  # remove market/seasonal price markers
    line = _SCORE_RE.sub("", line).strip()          # remove critic score numbers
    line = re.sub(r"\s{2,}", " ", line).strip()    # collapse again after substitutions
    return line


def _is_wine_price(val: float) -> bool:
    return 8 <= val <= 50_000


# OCR garbage characters not found in real wine names (pipe handled in _clean_line)
_GARBAGE_CHARS = re.compile(r"[~=<>{}\[\]\\@#%^*_\x00-\x1f]")


def _looks_like_wine_name(desc: str) -> bool:
    """
    Return True only if `desc` looks like a plausible wine / producer name.
    Rejects OCR garbage like 'a af Se ~ OX BSS Ss Yo. f sage. Sy = Sf = < =S'.
    """
    if not desc or len(desc) < 4:
        return False
    if _GARBAGE_CHARS.search(desc):
        return False
    alpha = sum(c.isalpha() or c.isspace() for c in desc)
    if alpha / len(desc) < 0.65:
        return False
    words = [w for w in desc.split() if w.isalpha()]
    if not words:
        return False
    avg_word_len = sum(len(w) for w in words) / len(words)
    if avg_word_len < 2.8:
        return False
    if not any(len(w) >= 3 for w in words):
        return False
    return True


# Detects "by the glass" section headers, including spaced-out text and pour-size labels
_GLASS_SECTION_RE = re.compile(
    r"\b(by\s+the\s+glass|glass\s+pour|wine\s+by\s+glass|btg|per\s+glass|per\s+the\s+glass)\b"
    r"|b\s*y\s+t\s*h\s*e\s+g\s*l\s*a\s*s\s*s"  # spaced-out: "B Y T H E G L A S S"
    r"|\b\d+\s*(?:oz|ounce)s?\b",               # pour-size labels: "5 Ounces", "6 oz"
    re.I,
)
# Detects half-bottle sections (375ml bottles — scale ×2 vs full-bottle retail)
_HALF_BOTTLE_SECTION_RE = re.compile(
    r"\b(half\s+bottles?|demi\s+bouteille|375\s*ml)\b", re.I
)
_BOTTLE_SECTION_RE = re.compile(
    r"\b(by\s+the\s+bottle|bottle\s+list|bottle\s+selection|full\s+bottle)\b", re.I
)
# X/Y/Z three-tier price (glass/half-bottle/bottle) — use the LAST (bottle) price
_TRIPLE_PRICE_RE = re.compile(r"(?<!\d)(\d{1,3})/(\d{1,3})/(\d{1,3})(?!\d)")
# X/Y dual-price format (e.g. 16/28) — max 3 digits each to exclude years
_DUAL_PRICE_RE = re.compile(r"(?<!\d)(\d{1,3})/(\d{1,3})(?!\d)")


def _parse_wines(text: str) -> list[dict]:
    """
    Extract (desc, vintage, menu_price) triples from raw OCR / PDF text.

    Line-structure formats handled:
      1-line:  "Name 2019 145"                           classic
      1-line:  "Name ........... 145"                    dot leaders
      1-line:  "Name $145"                               dollar sign
      1-line:  "Name 16/28"                              dual pour (5oz×5 for markup)
      1-line:  "Name 14/22/75"                           glass/half/bottle → bottle price
      2-line:  "Name"        / "2019 145"                name then year+price
      2-line:  "Name 2019"   / "145"                     year on name line, price next
      2-line:  "Name 145"    / "Region 2019"             price on line 1, vintage lookahead
      3-line:  "Name,"       / "Region" / "2019 145"     trailing-comma continuation
      3-line:  "Name 2019"   / "Region"  / "145"         geo-word continuation heuristic
      3-line:  "Name"        / "Region"  / "2019 145"    short mid-line heuristic

    Section modifiers:
      HALF BOTTLES   → price ×2  vs full-bottle retail
      MAGNUM         → price ÷2  vs full-bottle retail
      BY THE GLASS / "5 Ounces" → glass section (×5 for markup)
      "W I N E S B Y T H E G L A S S" → spaced-out header
    """
    # Avoid calling _clean_line twice per line (walrus operator)
    lines = [c for l in text.splitlines() if (c := _clean_line(l))]
    entries: list[dict] = []
    seen: set[tuple] = set()
    used: set[int] = set()

    # Precompute per-line section state (glass / half-bottle / magnum)
    _glass_state: list[bool] = []
    _half_bottle_state: list[bool] = []
    _magnum_state: list[bool] = []
    _in_glass = _in_half = _in_magnum = False
    for _l in lines:
        if _GLASS_SECTION_RE.search(_l):
            _in_glass, _in_half, _in_magnum = True, False, False
        elif _HALF_BOTTLE_SECTION_RE.search(_l):
            _in_glass, _in_half, _in_magnum = False, True, False
        elif _MAGNUM_SECTION_RE.search(_l):
            _in_glass, _in_half, _in_magnum = False, False, True
        elif _BOTTLE_SECTION_RE.search(_l):
            _in_glass, _in_half, _in_magnum = False, False, False
        # ALL-CAPS section headers (including accented chars like RHÔNE) reset to bottle mode.
        # Use str.upper() comparison which handles Unicode correctly (no ASCII-only regex needed).
        elif (_l == _l.upper() and 3 <= len(_l) <= 45
              and not _PRICE_RE.search(_l) and not _DUAL_PRICE_RE.search(_l)
              and not any(fn(_l) for fn in (_GLASS_SECTION_RE.search,
                                             _HALF_BOTTLE_SECTION_RE.search,
                                             _MAGNUM_SECTION_RE.search))):
            _in_glass, _in_half, _in_magnum = False, False, False
        _glass_state.append(_in_glass)
        _half_bottle_state.append(_in_half)
        _magnum_state.append(_in_magnum)

    def _non_year_prices(line: str) -> list[tuple[int, str]]:
        """Return (pos, str) tuples for real prices — exclude year-shaped numbers."""
        return [
            (m.start(), m.group(1))
            for m in _PRICE_RE.finditer(line)
            if not re.match(r"^(?:19|20)\d{2}$", m.group(1))
            and _is_wine_price(float(m.group(1).replace(",", "")))
        ]

    def _has_real_price(line: str) -> bool:
        return bool(_non_year_prices(line)
                    or _DUAL_PRICE_RE.search(line)
                    or _TRIPLE_PRICE_RE.search(line))

    def _vt_from(text: str) -> str | None:
        """Extract last vintage token, normalising N.V. → NV, M.V. → MV."""
        vm = list(_VINTAGE_RE.finditer(text))
        if not vm:
            return None
        raw = vm[-1].group(1)
        return re.sub(r"\.", "", raw.upper())  # "N.V." → "NV", "2019" → "2019"

    def _strip_vt_inline(s: str) -> str:
        """Remove all inline vintage tokens from a name string."""
        return _VINTAGE_INLINE_RE.sub("", s).strip()

    def _add(desc: str, vintage_str: str | None, price: float, idx: int,
             is_glass: bool = False, is_half_bottle: bool = False,
             is_magnum: bool = False) -> bool:
        """Normalise and store one wine entry. Returns True if successfully added."""
        desc = _BIN_RE.sub("", desc)
        desc = re.sub(r"\s*[|\-–—,;:]+\s*$", "", desc).strip()
        desc = _VINTAGE_STRIP_RE.sub("", desc).strip()
        # Strip duplicate consecutive years: "2023 2023" → "2023"
        desc = re.sub(r"\b((?:19|20)\d{2})\s+\1\b", r"\1", desc).strip()
        if not _looks_like_wine_name(desc):
            return False
        if _SKIP_RE.match(desc):
            return False
        # Reject section-header lines that contain wine-service keywords
        # e.g. "WINE BY THE GLASS", "HALF BOTTLE LIST", "MAGNUM SELECTIONS"
        if (_GLASS_SECTION_RE.search(desc)
                or _HALF_BOTTLE_SECTION_RE.search(desc)
                or _MAGNUM_SECTION_RE.search(desc)
                or _BOTTLE_SECTION_RE.search(desc)):
            return False
        # Reject region/appellation lines like "irpinia, italy" or "napa, california"
        if _REGION_LINE_RE.match(desc):
            return False
        # Reject ALL-CAPS section headers like "FRANCE – BURGUNDY" or "RHÔNE VALLEY"
        # Real wine names are always mixed-case (e.g. "Château Pétrus", not "CHÂTEAU PÉTRUS")
        desc_alpha = re.sub(r"[^a-zA-Z]", "", desc)
        if desc_alpha and desc_alpha == desc_alpha.upper() and re.search(r"[-–—]", desc):
            return False
        # Word-boundary check prevents substring hits (ale ⊄ aleatico, beer ⊄ beerenauslese)
        if _SPIRITS_RE.search(desc):
            return False
        if is_half_bottle:
            menu_price = round(price * 2, 2)
            display = f"{desc} (half btl)"
        elif is_magnum:
            menu_price = round(price / 2, 2)
            display = f"{desc} (magnum ÷2)"
        elif is_glass:
            menu_price = round(price * _POURS_PER_BOTTLE, 2)
            display = f"{desc} (by glass)"
        else:
            menu_price = price
            display = desc
        if not _is_wine_price(menu_price):
            return False
        vintage = int(vintage_str) if vintage_str and vintage_str.isdigit() else None
        key = (desc.lower()[:45], vintage, int(menu_price))
        if key in seen:
            return False
        seen.add(key)
        used.add(idx)
        entries.append({
            "desc": display,
            "vintage": vintage,
            "menu_price": menu_price,
            "glass_price": price if is_glass else None,
        })
        return True

    # ── Pass 1: single-line entries ─────────────────────────────────────────
    for i, line in enumerate(lines):
        is_gl = _glass_state[i]
        is_hb = _half_bottle_state[i]
        is_mg = _magnum_state[i]

        # Triple-price X/Y/Z (glass / half / bottle) — take bottle (last)
        triple = _TRIPLE_PRICE_RE.search(line)
        if triple:
            p1, p2, p3 = float(triple.group(1)), float(triple.group(2)), float(triple.group(3))
            if p1 <= p2 < p3 and _is_wine_price(p3):
                desc_raw = line[:triple.start()].strip()
                vt = _vt_from(desc_raw)
                desc = _strip_vt_inline(desc_raw) if vt else desc_raw
                _add(desc, vt, p3, i, is_glass=False, is_half_bottle=False, is_magnum=False)
            continue

        # Dual-price X/Y — glass pricing, take the SMALLER of the two values (5oz pour)
        dual = _DUAL_PRICE_RE.search(line)
        if dual:
            v1, v2 = float(dual.group(1)), float(dual.group(2))
            lo, hi = min(v1, v2), max(v1, v2)
            # Only treat as glass/bottle dual if BOTH values are valid wine prices.
            # If not credible (e.g. "Lot 19/20 285"), fall through to single-price.
            if _is_wine_price(lo) and _is_wine_price(hi):
                desc_raw = line[:dual.start()].strip()
                vt = _vt_from(desc_raw)
                # Vintage lookahead: many menus put region+vintage on the line below
                # e.g. "AGLIANICO, CONTRADE DI TAURAUSI 20/38" / "irpinia, italy 2019"
                if not vt and i + 1 < len(lines) and not _has_real_price(lines[i + 1]):
                    vt = _vt_from(lines[i + 1])
                desc = _strip_vt_inline(desc_raw) if vt else desc_raw
                _add(desc, vt, lo, i, is_glass=True)
            continue
            # Not a credible dual price — fall through to single-price parsing

        # Standard single price (or two-column glass/bottle)
        pt = _non_year_prices(line)
        if not pt:
            continue

        # Two-column glass/bottle: "Name 11 42" (space-adjacent, reasonable ratio)
        # e.g. menus with "PER GLASS  PER BOTTLE" column headers
        if len(pt) >= 2:
            g_pos, g_str = pt[-2]
            b_pos, b_str = pt[-1]
            g_price = float(g_str.replace(",", ""))
            b_price = float(b_str.replace(",", ""))
            chars_between = b_pos - g_pos - len(g_str)
            if chars_between <= 6 and 2.0 <= b_price / g_price <= 8.0:
                desc_raw = line[:g_pos].strip()
                vt = _vt_from(desc_raw)
                desc = _strip_vt_inline(desc_raw) if vt else desc_raw
                _add(desc, vt, g_price, i, is_glass=True)
                _add(desc, vt, b_price, i, is_glass=False, is_half_bottle=is_hb, is_magnum=is_mg)
            continue

        price_pos, price_str = pt[-1]
        price = float(price_str.replace(",", ""))
        desc_raw = line[:price_pos].strip()
        vt = _vt_from(desc_raw)
        if vt:
            desc = _strip_vt_inline(desc_raw)
        else:
            desc = desc_raw
            # Vintage lookahead: next line has vintage but no real price of any kind
            if i + 1 < len(lines):
                nxt = lines[i + 1]
                if not _has_real_price(nxt):
                    vt = _vt_from(nxt)
        _add(desc, vt, price, i, is_glass=is_gl, is_half_bottle=is_hb, is_magnum=is_mg)

    # ── Pass 3: three-line entries (name / region-continuation / year+price) ─
    # Run BEFORE Pass 2 so continuation mid-lines are marked used and not
    # misidentified as standalone wine names by Pass 2.
    for i in range(len(lines) - 2):
        if i in used:
            continue
        name_line = lines[i]
        mid_line  = lines[i + 1]
        price_line = lines[i + 2]

        # Name line: no real price, looks like a wine name, not a known header
        if _has_real_price(name_line):
            continue
        if len(name_line) < 5 or _SKIP_RE.match(name_line):
            continue
        if _SPIRITS_RE.search(name_line):
            continue
        if (_GLASS_SECTION_RE.search(name_line) or _HALF_BOTTLE_SECTION_RE.search(name_line)
                or _MAGNUM_SECTION_RE.search(name_line) or _BOTTLE_SECTION_RE.search(name_line)):
            continue
        if i + 1 in used:
            continue

        # Middle line: no real price, not a known section header
        if _has_real_price(mid_line):
            continue
        if _SKIP_RE.match(mid_line):
            continue  # e.g. "Red" or "France" between two wine lines — it's a section header

        # Price line: must have a real price
        pt = _non_year_prices(price_line)
        if not pt:
            continue

        # Continuation heuristic — at least one must be true:
        #   A) name_line ends with comma (typographic continuation marker)
        #   B) mid_line ≤ 50 chars AND contains geographic/regional words
        #   C) mid_line is very short (≤ 30 chars, single location token like "Carneros")
        trailing_comma = name_line.endswith(",")
        geo_mid        = bool(_GEO_WORDS_RE.search(mid_line))
        short_mid      = len(mid_line) <= 50
        very_short_mid = len(mid_line) <= 30
        if not (trailing_comma or (short_mid and geo_mid) or very_short_mid):
            continue

        price_pos, price_str = pt[-1]
        price = float(price_str.replace(",", ""))
        vt = (_vt_from(price_line[:price_pos])
              or _vt_from(price_line)
              or _vt_from(name_line)
              or _vt_from(mid_line))

        # Strip vintage from name_line before combining so "Littorai 2019" → "Littorai"
        name_clean = _strip_vt_inline(name_line).rstrip(",").strip()
        combined = name_clean + " " + mid_line

        # Mark mid_line used ONLY if the entry is successfully added
        if _add(combined, vt, price, i,
                is_glass=_glass_state[i], is_half_bottle=_half_bottle_state[i],
                is_magnum=_magnum_state[i]):
            used.add(i + 1)

    # ── Pass 2: name on one line, price (+optional year) on the next ────────
    for i in range(len(lines) - 1):
        if i in used:
            continue
        name_line = lines[i]
        next_line = lines[i + 1]

        # Use _has_real_price so lines like "Jordan 2023" (year only) aren't skipped
        if _has_real_price(name_line):
            continue
        if len(name_line) < 5 or _SKIP_RE.match(name_line):
            continue
        if _SPIRITS_RE.search(name_line):
            continue
        if (_GLASS_SECTION_RE.search(name_line) or _HALF_BOTTLE_SECTION_RE.search(name_line)
                or _MAGNUM_SECTION_RE.search(name_line) or _BOTTLE_SECTION_RE.search(name_line)):
            continue
        if _REGION_LINE_RE.match(name_line):
            continue
        # If next_line was already consumed by Pass 1 as a wine entry, don't use it
        # as a price source — it means this line is a region/continuation line, not a name
        if (i + 1) in used:
            continue

        # Triple price on next line
        triple = _TRIPLE_PRICE_RE.search(next_line)
        if triple:
            p1, p2, p3 = float(triple.group(1)), float(triple.group(2)), float(triple.group(3))
            if p1 <= p2 < p3 and _is_wine_price(p3):
                vt = _vt_from(next_line[:triple.start()]) or _vt_from(name_line)
                _add(name_line, vt, p3, i, is_glass=False,
                     is_half_bottle=_half_bottle_state[i], is_magnum=_magnum_state[i])
                continue

        # Dual price on next line
        dual = _DUAL_PRICE_RE.search(next_line)
        if dual:
            dv1, dv2 = float(dual.group(1)), float(dual.group(2))
            glass_price = min(dv1, dv2)
            if _is_wine_price(glass_price) and _is_wine_price(max(dv1, dv2)):
                vt = _vt_from(next_line[:dual.start()]) or _vt_from(name_line)
                _add(name_line, vt, glass_price, i, is_glass=True)
                continue
            # Not credible — fall through to single-price

        pt = _non_year_prices(next_line)
        if not pt:
            continue
        price_pos, price_str = pt[-1]
        price = float(price_str.replace(",", ""))
        rest = next_line[:price_pos].strip()
        # Vintage: prefer next_line context, fallback to name_line (handles "Jordan 2023\n90")
        vt = _vt_from(rest or next_line) or _vt_from(name_line)
        _add(name_line, vt, price, i,
             is_glass=_glass_state[i], is_half_bottle=_half_bottle_state[i],
             is_magnum=_magnum_state[i])

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
    job_id: Optional[str] = None          # poll /menu/results/{job_id} for price updates
    pricing_pending: int = 0              # number of wines still being priced via Vivino


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
                _img_data, media_type = _prepare_image_for_claude(data, _ext)
                logger.info(
                    "Sending '%s' to Claude Vision (%.1f KB, %s)",
                    filename, len(_img_data) / 1024, media_type,
                )
                claude_raw = await _extract_and_normalise_wines(_img_data, media_type)
                wines = _parse_claude_output(claude_raw)  # pipe-delimited after step 2
                logger.info("Parsed %d wine entries from Claude transcription of '%s'", len(wines), filename)
                if not wines:
                    raise HTTPException(
                        status_code=422,
                        detail=(
                            f"No wine entries with prices found in '{filename}'. "
                            "Make sure the photo clearly shows wine names and prices visible together."
                        ),
                    )
                return await _run_batch_from_entries(wines, filename)
            except HTTPException:
                raise
            except Exception as exc:
                logger.error("Claude Vision failed for '%s': %s", filename, exc, exc_info=True)
                raise HTTPException(
                    status_code=422,
                    detail=f"Photo analysis failed: {exc}. Please try again or upload a PDF.",
                ) from exc

        # Tesseract fallback (only when no API key is configured)
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


def _vivino_job_key(job_id: str) -> str:
    return f"menu_job:{job_id}"


async def _launch_vivino_background(job_id: str, wines: list[dict]) -> None:
    """
    Fire Vivino lookups for all unmatched wines as background asyncio tasks.
    Does NOT block — returns immediately after creating the tasks.

    Progress is tracked in Redis so the polling endpoint can report status.
    Each task marks itself done in Redis when it finishes (success or failure).
    """
    import unicodedata as _ud
    import uuid as _uuid
    from app.services.text_parser import parse_wine_text as _pwt
    from app.services.vivino_dynamic import dynamic_lookup as _vivino_lookup
    from app.services.cache import cache_set, cache_get

    vivino_sem = asyncio.Semaphore(4)  # max 4 concurrent Playwright browsers

    def _slugify(s: str) -> str:
        nfkd = _ud.normalize("NFD", s.lower())
        s2 = "".join(c for c in nfkd if _ud.category(c) != "Mn")
        s2 = re.sub(r"[^a-z0-9]+", "-", s2).strip("-")
        return s2[:60]

    # Store job metadata (wine list) in Redis so polling endpoint can query it
    job_data = [{"desc": w["desc"], "vintage": w.get("vintage"), "menu_price": w["menu_price"]} for w in wines]
    await cache_set(_vivino_job_key(job_id), {"wines": job_data, "done": [], "total": len(wines)}, ttl=3600)

    async def _one(w: dict) -> None:
        async with vivino_sem:
            parsed = _pwt(w["desc"])
            wine_name = parsed.wine_name or w["desc"]
            producer = parsed.producer or ""
            wine_id = _slugify(f"{producer}-{wine_name}" if producer else wine_name)
            try:
                await asyncio.wait_for(
                    _vivino_lookup(wine_id=wine_id, wine_name=wine_name,
                                   producer=producer, vintage=w.get("vintage")),
                    timeout=60,
                )
                logger.info("Vivino: priced '%s'", w["desc"][:50])
            except Exception as exc:
                logger.debug("Vivino skip '%s': %s", w["desc"][:40], exc)
            finally:
                # Mark this wine as processed regardless of outcome
                try:
                    job = await cache_get(_vivino_job_key(job_id))
                    if job:
                        job.setdefault("done", []).append(wine_id)
                        await cache_set(_vivino_job_key(job_id), job, ttl=3600)
                except Exception:
                    pass

    # Fire all tasks — they run independently in the event loop background
    for w in wines:
        asyncio.create_task(_one(w), name=f"vivino:{job_id}:{w['desc'][:20]}")


async def _batch_analyze(wines: list[dict], source_name: str) -> MenuUploadResponse:
    """Run parallel analysis on a list of pre-validated wine dicts."""
    import uuid as _uuid
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
            strong = ident.matched and ident.confidence_level in ("very_high", "high")

            # Only use retail price when it comes from real data — confirmed
            # catalog entry or live market fetch. Regional/varietal proxy
            # estimates are stripped out entirely: showing made-up numbers is
            # worse than showing nothing.
            _REAL_SOURCES = {"market_live", "catalog"}
            src = ep.price_source.value if ep and ep.price_source else ""
            real_price = src in _REAL_SOURCES
            retail = (ep.avg_retail if real_price else None) if ep else None
            wholesale = (ep.estimated_wholesale if real_price else None) if ep else None
            min_r = (ep.min_retail if real_price else None) if ep else None
            max_r = (ep.max_retail if real_price else None) if ep else None
            markup = w["menu_price"] / retail if retail else None

            # Always extract varietal — use catalog value for matches,
            # fall back to parsed_components (from analyze) then our own parse.
            from app.services.text_parser import parse_wine_text as _pwt2
            _parsed = _pwt2(w["desc"])
            _pc_varietal = (ident.parsed_components.varietal if ident.parsed_components else None)
            varietal = (ident.varietal if strong else None) or _pc_varietal or _parsed.varietal

            return MenuWineResult(
                raw_text=w["desc"], vintage=w["vintage"], menu_price=w["menu_price"],
                matched=strong, wine_name=ident.name if strong else None, producer=ident.producer if strong else None,
                region=ident.region if strong else None, varietal=varietal,
                retail_price=round(retail, 2) if retail is not None else None,
                wholesale_est=round(wholesale, 2) if wholesale is not None else None,
                min_retail=min_r, max_retail=max_r,
                markup=round(markup, 2) if markup is not None else None,
                confidence=ident.confidence, confidence_level=ident.confidence_level,
                deal_rating=_deal_rating(markup),
                data_confidence=ep.data_confidence if ep and real_price else None,
                price_source=src if real_price else None,
            )

    results: list[MenuWineResult] = list(await asyncio.gather(*[_analyze(w) for w in wines]))

    # Launch Vivino background tasks for wines without real pricing.
    # This is non-blocking — results trickle in and can be polled.
    unpriced = [w for w, r in zip(wines, results) if not r.retail_price]
    job_id: Optional[str] = None
    if unpriced:
        job_id = str(_uuid.uuid4())
        await _launch_vivino_background(job_id, unpriced)
        logger.info("Launched Vivino background job %s for %d wines", job_id, len(unpriced))

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
        job_id=job_id,
        pricing_pending=len(unpriced),
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
        try:
            _img_bytes, _mime2 = _prepare_image_for_claude(data, _ext2)
            claude_raw = await _extract_and_normalise_wines(_img_bytes, _mime2)
            wines = _parse_claude_output(claude_raw)
            if wines:
                return await _run_batch_from_entries(wines, source_name)
        except Exception as exc:
            logger.warning("Claude Vision failed for URL image: %s", exc)

    text = _extract_text_from_url_content(data, content_type, url)
    if not text.strip():
        raise HTTPException(422, "Could not extract any text from that URL.")

    # Use Claude to normalise the text rather than the fragile regex parser.
    # The regex parser was designed for lightly-structured OCR output; it breaks
    # badly on real HTML menus (wrong glass/bottle detection, 401(k) parsed as a
    # price, etc.).  Claude handles arbitrary formats cleanly.
    import os as _os2
    if _os2.environ.get("ANTHROPIC_API_KEY"):
        try:
            normalised = await _normalise_text_wines(text)
            wines = _parse_claude_output(normalised)
            if wines:
                logger.info("Claude normalised %d wines from URL text", len(wines))
                return await _batch_analyze(wines, source_name)
        except Exception as exc:
            logger.warning("Claude text normalisation failed, falling back to regex: %s", exc)

    # Fallback: regex parser (less reliable for complex HTML menus)
    return await _run_batch(text, source_name)


# ── Vivino pricing poll endpoint ────────────────────────────────────────────

class PricingUpdate(BaseModel):
    wine_id: str
    desc: str
    retail_price: Optional[float] = None
    wholesale_est: Optional[float] = None
    markup: Optional[float] = None
    deal_rating: str = "unknown"
    price_source: Optional[str] = None


class JobStatusResponse(BaseModel):
    job_id: str
    total: int
    done: int
    finished: bool
    updates: list[PricingUpdate]


@router.get("/results/{job_id}", response_model=JobStatusResponse, summary="Poll Vivino pricing updates for a menu job")
async def menu_job_results(job_id: str) -> JobStatusResponse:
    """
    Returns current Vivino pricing state for a background job created by
    `/menu/upload` or `/menu/from-url`.

    Poll every 10–15 seconds.  `finished` becomes `true` when all wines
    have been attempted.  Re-run `_run_analysis` per wine so we get
    the latest Redis cache hit from any Vivino task that has completed.
    """
    from app.services.cache import cache_get

    job = await cache_get(_vivino_job_key(job_id))
    if not job:
        raise HTTPException(404, "Job not found or expired")

    wines: list[dict] = job.get("wines", [])
    done_set: set = set(job.get("done", []))
    total = job.get("total", len(wines))
    done_count = len(done_set)

    sem = asyncio.Semaphore(5)
    updates: list[PricingUpdate] = []

    async def _check(w: dict) -> Optional[PricingUpdate]:
        async with sem:
            req = AnalyzeRequest(menu_text=w["desc"], menu_price=w["menu_price"], vintage=w.get("vintage"))
            try:
                resp = await _run_analysis(req, db=None)
            except Exception:
                return None
            ep = resp.estimated_price
            if not ep or not ep.avg_retail:
                return None
            src = ep.price_source.value if ep.price_source else ""
            _REAL_SOURCES = {"market_live", "catalog"}
            if src not in _REAL_SOURCES:
                return None
            retail = ep.avg_retail
            menu_p = w["menu_price"]
            markup = menu_p / retail if retail else None
            import unicodedata as _ud2
            def _slug2(s: str) -> str:
                n = _ud2.normalize("NFD", s.lower())
                s2 = "".join(c for c in n if _ud2.category(c) != "Mn")
                s2 = re.sub(r"[^a-z0-9]+", "-", s2).strip("-")
                return s2[:60]
            parsed = resp.parsed_wine
            wname = (parsed.wine_name if parsed else None) or w["desc"]
            prod = (parsed.producer if parsed else None) or ""
            wid = _slug2(f"{prod}-{wname}" if prod else wname)
            return PricingUpdate(
                wine_id=wid,
                desc=w["desc"],
                retail_price=round(retail, 2),
                wholesale_est=round(ep.estimated_wholesale, 2) if ep.estimated_wholesale else None,
                markup=round(markup, 2) if markup else None,
                deal_rating=_deal_rating(markup),
                price_source=src,
            )

    check_tasks = [_check(w) for w in wines]
    raw = await asyncio.gather(*check_tasks, return_exceptions=True)
    for r in raw:
        if isinstance(r, PricingUpdate):
            updates.append(r)

    return JobStatusResponse(
        job_id=job_id,
        total=total,
        done=done_count,
        finished=(done_count >= total),
        updates=updates,
    )
