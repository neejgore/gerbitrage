#!/usr/bin/env python3
"""
Vivino Catalog Builder
======================
Expands the wine catalog beyond the 694 hand-curated entries by scraping
Vivino's search / explore pages for each major wine region and style.

Output: app/data/extended_catalog.json
  {
    "slug-id": {
      "id": "slug-id",
      "name": "...",
      "producer": "...",
      "region": "...",
      "country": "...",
      "varietal": "...",
      "wine_type": "red|white|rose|sparkling|dessert",
      "avg_retail_price": 89.0,
      "price_tier": "premium",
      "vivino_wine_id": "12345",
      "vivino_url": "https://www.vivino.com/wines/12345",
      "vivino_rating": 4.2,
      "vivino_ratings_count": 15000,
      "discovered_at": "2026-04-01T12:00:00Z"
    },
    ...
  }

Estimated runtime: ~3-4 hours to build 10k+ entries.

Usage
-----
  python scripts/vivino_catalog_builder.py              # full build
  python scripts/vivino_catalog_builder.py --max 200    # quick test (200 per region)
  python scripts/vivino_catalog_builder.py --resume     # skip already-discovered wines
  python scripts/vivino_catalog_builder.py --regions bordeaux burgundy  # specific regions

Requirements
------------
  pip install playwright
  playwright install chromium
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import random
import re
import sys
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.data.wine_catalog import WINE_CATALOG_BY_ID

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("vivino_catalog")

# ── Paths ─────────────────────────────────────────────────────────────────────
_OUTPUT_PATH = Path(__file__).parent.parent / "app" / "data" / "extended_catalog.json"

# ── Constants ─────────────────────────────────────────────────────────────────
MIN_DELAY = 3.5
MAX_DELAY = 6.0
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)

# ──────────────────────────────────────────────────────────────────────────────
# Region / query definitions
# Each entry: (region_key, search_queries, country, region_label, wine_type)
# Multiple queries per region target different sub-appellations/styles.
# ──────────────────────────────────────────────────────────────────────────────
REGION_QUERIES = [
    # ── Bordeaux ──────────────────────────────────────────────────────────────
    # Use appellation names that Vivino wines are literally named after
    ("bordeaux-left-bank",  ["Pauillac", "Margaux", "Saint-Julien",
                              "Pessac-Léognan", "Saint-Estèphe"],
     "France", "Bordeaux", "red"),
    ("bordeaux-right-bank", ["Pomerol", "Saint-Émilion Grand Cru", "Fronsac"],
     "France", "Bordeaux", "red"),
    ("bordeaux-white",      ["Bordeaux Blanc", "Pessac-Léognan Blanc", "Entre-Deux-Mers"],
     "France", "Bordeaux", "white"),
    ("sauternes",           ["Sauternes", "Barsac"],
     "France", "Sauternes", "dessert"),

    # ── Burgundy ──────────────────────────────────────────────────────────────
    ("burgundy-red",        ["Gevrey-Chambertin", "Vosne-Romanée", "Chambolle-Musigny",
                              "Nuits-Saint-Georges", "Beaune", "Volnay"],
     "France", "Burgundy", "red"),
    ("burgundy-white",      ["Meursault", "Puligny-Montrachet", "Chassagne-Montrachet",
                              "Chablis Grand Cru", "Corton-Charlemagne"],
     "France", "Burgundy", "white"),
    ("burgundy-villages",   ["Bourgogne Pinot Noir", "Bourgogne Chardonnay",
                              "Mâcon-Villages", "Pouilly-Fuissé"],
     "France", "Burgundy", "red"),

    # ── Champagne – by style (surfaces all grower/NM Champagnes) ─────────────
    ("champagne",           ["Champagne Blanc de Blancs", "Champagne Blanc de Noirs",
                              "Champagne Brut Nature", "Champagne Extra Brut",
                              "Champagne Brut", "Champagne Rosé",
                              "Champagne Premier Cru", "Champagne Grand Cru"],
     "France", "Champagne", "sparkling"),

    # ── Rhône ─────────────────────────────────────────────────────────────────
    ("rhone-north",         ["Hermitage", "Côte-Rôtie", "Crozes-Hermitage",
                              "Cornas", "Saint-Joseph"],
     "France", "Rhône", "red"),
    ("rhone-south",         ["Châteauneuf-du-Pape", "Gigondas", "Vacqueyras",
                              "Côtes du Rhône Villages"],
     "France", "Rhône", "red"),

    # ── Loire ─────────────────────────────────────────────────────────────────
    ("loire",               ["Sancerre", "Pouilly-Fumé", "Vouvray",
                              "Muscadet", "Chinon", "Bourgueil"],
     "France", "Loire Valley", "white"),

    # ── Alsace ────────────────────────────────────────────────────────────────
    ("alsace",              ["Alsace Riesling Grand Cru", "Alsace Gewurztraminer",
                              "Alsace Pinot Gris"],
     "France", "Alsace", "white"),

    # ── Other France ──────────────────────────────────────────────────────────
    ("france-other",        ["Bandol", "Provence Rosé", "Roussillon",
                              "Languedoc"],
     "France", "South of France", "red"),

    # ── Napa Valley – by sub-appellation (surfaces all producers in each AVA) ──
    ("napa-oakville",       ["Oakville Cabernet Sauvignon", "Rutherford Cabernet Sauvignon",
                              "Yountville Cabernet Sauvignon", "Stags Leap District Cabernet"],
     "USA", "Napa Valley", "red"),
    ("napa-mountain",       ["Howell Mountain Cabernet", "Spring Mountain District",
                              "Mount Veeder Cabernet", "Diamond Mountain Cabernet",
                              "Atlas Peak Cabernet"],
     "USA", "Napa Valley", "red"),
    ("napa-broad",          ["Napa Valley Cabernet Sauvignon", "Napa Valley Merlot",
                              "Napa Valley Zinfandel", "Napa Valley Syrah",
                              "Napa Valley Petit Verdot"],
     "USA", "Napa Valley", "red"),
    ("napa-white",          ["Napa Valley Chardonnay", "Napa Valley Sauvignon Blanc",
                              "Carneros Chardonnay", "Carneros Pinot Noir",
                              "Napa Valley Pinot Noir"],
     "USA", "Napa Valley", "white"),

    # ── Sonoma – by sub-appellation ───────────────────────────────────────────
    ("sonoma-pinot",        ["Russian River Valley Pinot Noir", "Sonoma Coast Pinot Noir",
                              "Green Valley Pinot Noir", "Petaluma Gap Pinot Noir"],
     "USA", "Sonoma", "red"),
    ("sonoma-cab",          ["Alexander Valley Cabernet Sauvignon", "Chalk Hill Chardonnay",
                              "Sonoma Coast Chardonnay", "Dry Creek Valley Zinfandel",
                              "Knights Valley Cabernet"],
     "USA", "Sonoma", "red"),

    # ── Oregon – by sub-appellation ───────────────────────────────────────────
    ("oregon",              ["Willamette Valley Pinot Noir", "Dundee Hills Pinot Noir",
                              "Chehalem Mountains Pinot Noir", "Ribbon Ridge Pinot Noir",
                              "Eola-Amity Hills Pinot Noir", "McMinnville Pinot Noir"],
     "USA", "Oregon", "red"),

    # ── Washington – by sub-appellation ──────────────────────────────────────
    ("washington",          ["Columbia Valley Cabernet Sauvignon", "Walla Walla Cabernet",
                              "Red Mountain Cabernet Sauvignon", "Columbia Gorge Pinot Gris",
                              "Yakima Valley Riesling", "Horse Heaven Hills Cabernet"],
     "USA", "Washington", "red"),

    # ── Other USA – by appellation ────────────────────────────────────────────
    ("usa-other",           ["Paso Robles Cabernet Sauvignon", "Sta. Rita Hills Pinot Noir",
                              "Santa Barbara County Chardonnay", "Finger Lakes Riesling",
                              "Monterey Pinot Noir", "Santa Cruz Mountains Cabernet"],
     "USA", "California / USA", "red"),

    # ── Tuscany – by appellation (surfaces all producers) ────────────────────
    ("tuscany-brunello",    ["Brunello di Montalcino", "Rosso di Montalcino",
                              "Vino Nobile di Montepulciano"],
     "Italy", "Tuscany", "red"),
    ("tuscany-chianti",     ["Chianti Classico Gran Selezione", "Chianti Classico Riserva",
                              "Chianti Classico", "Chianti Rufina", "Chianti Colli Senesi"],
     "Italy", "Tuscany", "red"),
    ("tuscany-bolgheri",    ["Bolgheri Rosso", "Bolgheri Superiore",
                              "Maremma Toscana Cabernet", "Morellino di Scansano",
                              "Montecucco Sangiovese", "Val di Cornia Rosso"],
     "Italy", "Tuscany", "red"),
    ("tuscany-white",       ["Vernaccia di San Gimignano", "Bolgheri Bianco",
                              "Vermentino Toscana", "Ansonica Costa dell'Argentario"],
     "Italy", "Tuscany", "white"),

    # ── Piedmont – by appellation ─────────────────────────────────────────────
    ("piedmont-barolo",     ["Barolo DOCG", "Barolo Riserva", "Barolo Serralunga",
                              "Barolo La Morra", "Barolo Castiglione Falletto"],
     "Italy", "Piedmont", "red"),
    ("piedmont-barbaresco", ["Barbaresco DOCG", "Barbaresco Riserva",
                              "Barbaresco Treiso", "Barbaresco Neive"],
     "Italy", "Piedmont", "red"),
    ("piedmont-other",      ["Barbera d'Asti Superiore", "Barbera d'Alba",
                              "Dolcetto d'Alba", "Langhe Nebbiolo",
                              "Roero Riserva", "Nizza Barbera"],
     "Italy", "Piedmont", "red"),

    # ── Other Italy – by appellation ──────────────────────────────────────────
    ("veneto-red",          ["Amarone della Valpolicella", "Amarone Classico",
                              "Ripasso Valpolicella Superiore", "Valpolicella Classico"],
     "Italy", "Veneto", "red"),
    ("italy-south-red",     ["Taurasi DOCG", "Sagrantino di Montefalco",
                              "Etna Rosso DOC", "Cerasuolo di Vittoria",
                              "Primitivo di Manduria"],
     "Italy", "Southern Italy", "red"),

    # ── Spain ─────────────────────────────────────────────────────────────────
    ("rioja",               ["Rioja Gran Reserva", "Rioja Reserva", "Rioja Alta"],
     "Spain", "Rioja", "red"),
    ("spain-other",         ["Ribera del Duero Reserva", "Priorat red",
                              "Bierzo Mencía", "Rías Baixas Albariño",
                              "Rueda Verdejo"],
     "Spain", "Spain", "red"),

    # ── Germany ───────────────────────────────────────────────────────────────
    ("germany",             ["Mosel Riesling Spätlese", "Mosel Riesling Auslese",
                              "Rheingau Riesling Spätlese", "Pfalz Riesling"],
     "Germany", "Germany", "white"),

    # ── Austria ───────────────────────────────────────────────────────────────
    ("austria",             ["Wachau Riesling Smaragd", "Grüner Veltliner Smaragd",
                              "Burgenland Blaufränkisch"],
     "Austria", "Austria", "white"),

    # ── Argentina ─────────────────────────────────────────────────────────────
    ("argentina",           ["Mendoza Malbec", "Luján de Cuyo Malbec",
                              "Uco Valley Malbec", "Mendoza Cabernet Sauvignon"],
     "Argentina", "Mendoza", "red"),

    # ── Chile ─────────────────────────────────────────────────────────────────
    ("chile",               ["Maipo Cabernet Sauvignon", "Colchagua Carménère",
                              "Casablanca Chardonnay", "Aconcagua Cabernet"],
     "Chile", "Chile", "red"),

    # ── Australia ─────────────────────────────────────────────────────────────
    ("australia",           ["Barossa Valley Shiraz", "McLaren Vale Shiraz",
                              "Clare Valley Riesling", "Coonawarra Cabernet",
                              "Yarra Valley Pinot Noir", "Eden Valley Riesling"],
     "Australia", "Australia", "red"),

    # ── New Zealand ───────────────────────────────────────────────────────────
    ("new-zealand",         ["Marlborough Sauvignon Blanc", "Central Otago Pinot Noir",
                              "Hawke's Bay Syrah"],
     "New Zealand", "New Zealand", "white"),

    # ── South Africa ──────────────────────────────────────────────────────────
    ("south-africa",        ["Stellenbosch Cabernet Sauvignon", "Swartland Syrah",
                              "Hemel-en-Aarde Pinot Noir"],
     "South Africa", "South Africa", "red"),

    # ── Portugal ──────────────────────────────────────────────────────────────
    ("portugal",            ["Quinta do Crasto Douro", "Niepoort Douro",
                              "Vinho Verde", "Dao", "Alentejo"],
     "Portugal", "Portugal", "red"),

    # ── Port & Sherry ─────────────────────────────────────────────────────────
    ("fortified",           ["Vintage Port", "Graham's Port", "Taylor Fladgate Port",
                              "Amontillado Sherry", "Oloroso Sherry"],
     "Portugal", "Douro / Jerez", "fortified"),

    # ── Beaujolais ────────────────────────────────────────────────────────────
    ("beaujolais",          ["Morgon", "Moulin-à-Vent", "Fleurie", "Juliénas",
                              "Chénas", "Chiroubles", "Régnié", "Côte de Brouilly",
                              "Brouilly", "Beaujolais Villages"],
     "France", "Beaujolais", "red"),

    # ── Jura ──────────────────────────────────────────────────────────────────
    ("jura",                ["Vin Jaune Arbois", "Poulsard Arbois", "Trousseau Arbois",
                              "Côtes du Jura Chardonnay", "Château-Chalon"],
     "France", "Jura", "white"),

    # ── Provence ──────────────────────────────────────────────────────────────
    ("provence",            ["Bandol Rouge", "Côtes de Provence Rosé",
                              "Cassis Blanc", "Palette"],
     "France", "Provence", "rosé"),

    # ── Languedoc-Roussillon ──────────────────────────────────────────────────
    ("languedoc",           ["Pic Saint-Loup", "Terrasses du Larzac", "Faugères",
                              "Saint-Chinian", "Minervois", "Corbières",
                              "Roussillon Villages", "Collioure"],
     "France", "Languedoc-Roussillon", "red"),

    # ── Loire – reds & more ───────────────────────────────────────────────────
    ("loire-red",           ["Chinon Rouge", "Bourgueil", "Saumur-Champigny",
                              "Anjou Rouge", "Touraine Amboise"],
     "France", "Loire Valley", "red"),
    ("loire-dessert",       ["Coteaux du Layon", "Quarts de Chaume",
                              "Bonnezeaux", "Vouvray Moelleux"],
     "France", "Loire Valley", "dessert"),

    # ── Corsica ───────────────────────────────────────────────────────────────
    ("corsica",             ["Patrimonio", "Ajaccio Rouge", "Vermentino Corsica"],
     "France", "Corsica", "red"),

    # ── More Burgundy ─────────────────────────────────────────────────────────
    ("burgundy-pommard",    ["Pommard Premier Cru", "Volnay Premier Cru",
                              "Savigny-lès-Beaune", "Aloxe-Corton"],
     "France", "Burgundy", "red"),
    ("burgundy-chablis",    ["Chablis Premier Cru", "Chablis", "Petit Chablis"],
     "France", "Burgundy", "white"),

    # ── More Bordeaux ─────────────────────────────────────────────────────────
    ("bordeaux-satellites", ["Lalande-de-Pomerol", "Saint-Georges-Saint-Émilion",
                              "Listrac-Médoc", "Moulis", "Médoc"],
     "France", "Bordeaux", "red"),

    # ── Italy – Veneto ────────────────────────────────────────────────────────
    ("veneto",              ["Soave Classico", "Lugana", "Custoza",
                              "Prosecco di Valdobbiadene", "Bardolino"],
     "Italy", "Veneto", "white"),

    # ── Italy – Friuli & Alto Adige ───────────────────────────────────────────
    ("friuli-alto-adige",   ["Collio Friulano", "Collio Pinot Grigio",
                              "Alto Adige Gewürztraminer", "Alto Adige Pinot Nero",
                              "Ribolla Gialla Friuli", "Ramato Pinot Grigio"],
     "Italy", "Northeast Italy", "white"),

    # ── Italy – Campania ──────────────────────────────────────────────────────
    ("campania",            ["Fiano di Avellino", "Greco di Tufo",
                              "Taurasi", "Aglianico del Taburno",
                              "Falanghina del Sannio"],
     "Italy", "Campania", "white"),

    # ── Italy – Abruzzo & Marche ──────────────────────────────────────────────
    ("abruzzo-marche",      ["Montepulciano d'Abruzzo", "Trebbiano d'Abruzzo",
                              "Pecorino Abruzzo", "Verdicchio dei Castelli di Jesi",
                              "Verdicchio di Matelica"],
     "Italy", "Central Italy", "red"),

    # ── Italy – Puglia & Basilicata ───────────────────────────────────────────
    ("puglia-basilicata",   ["Primitivo di Manduria", "Salice Salentino",
                              "Negroamaro Salento", "Aglianico del Vulture",
                              "Negro Amaro"],
     "Italy", "Southern Italy", "red"),

    # ── Italy – Sicily ────────────────────────────────────────────────────────
    ("sicily",              ["Etna Bianco", "Nerello Mascalese Etna",
                              "Nero d'Avola Sicilia", "Cerasuolo di Vittoria",
                              "Grillo Sicilia", "Catarratto"],
     "Italy", "Sicily", "red"),

    # ── Italy – Sardinia ──────────────────────────────────────────────────────
    ("sardinia",            ["Cannonau di Sardegna", "Vermentino di Gallura",
                              "Carignano del Sulcis", "Monica di Sardegna"],
     "Italy", "Sardinia", "red"),

    # ── Italy – Umbria ────────────────────────────────────────────────────────
    ("umbria",              ["Sagrantino di Montefalco", "Montefalco Rosso",
                              "Orvieto Classico", "Torgiano Rosso"],
     "Italy", "Umbria", "red"),

    # ── Spain – more ──────────────────────────────────────────────────────────
    ("spain-northwest",     ["Albariño Rías Baixas", "Godello Valdeorras",
                              "Mencía Bierzo", "Ribeira Sacra Mencía"],
     "Spain", "Northwest Spain", "white"),
    ("spain-centre",        ["Toro Tinta de Toro", "Rueda Verdejo",
                              "Cigales Tempranillo", "Ribera del Duero Crianza"],
     "Spain", "Central Spain", "red"),
    ("spain-south",         ["Priorat Garnacha", "Montsant",
                              "Jumilla Monastrell", "Yecla Monastrell",
                              "Cava Brut Nature"],
     "Spain", "Southern Spain", "red"),
    ("sherry",              ["Fino Sherry", "Manzanilla Sherry", "Palo Cortado",
                              "Pedro Ximénez", "Cream Sherry"],
     "Spain", "Jerez", "fortified"),

    # ── Germany – more ────────────────────────────────────────────────────────
    ("germany-mosel",       ["Mosel Riesling Kabinett", "Mosel Riesling Beerenauslese",
                              "Saar Riesling", "Ruwer Riesling"],
     "Germany", "Mosel", "white"),
    ("germany-other",       ["Nahe Riesling", "Rheinhessen Riesling",
                              "Baden Spätburgunder", "Franken Silvaner",
                              "Württemberg Lemberger"],
     "Germany", "Germany", "white"),

    # ── USA – Central Coast & other ───────────────────────────────────────────
    ("usa-central-coast",   ["Paso Robles Cabernet", "Santa Barbara Pinot Noir",
                              "Santa Cruz Mountains Chardonnay", "Sta. Rita Hills Pinot Noir",
                              "Edna Valley Chardonnay", "Monterey Pinot Noir"],
     "USA", "California Central Coast", "red"),
    ("usa-east",            ["Finger Lakes Riesling", "Virginia Cabernet Franc",
                              "Long Island Merlot", "Willamette Valley Chardonnay"],
     "USA", "Eastern USA", "white"),

    # ── Greece ────────────────────────────────────────────────────────────────
    ("greece",              ["Assyrtiko Santorini", "Xinomavro Naoussa",
                              "Agiorgitiko Nemea", "Malagousia", "Moschofilero",
                              "Xinomavro Amyndeon"],
     "Greece", "Greece", "white"),

    # ── Hungary ───────────────────────────────────────────────────────────────
    ("hungary",             ["Tokaji Aszú 5 Puttonyos", "Tokaji Furmint",
                              "Egri Bikavér", "Villány Cabernet Franc",
                              "Tokaji Szamorodni"],
     "Hungary", "Hungary", "dessert"),

    # ── Japan ─────────────────────────────────────────────────────────────────
    ("japan",               ["Koshu Grace Wine", "Suntory Tomi no Oka",
                              "Château Mercian Hokushin", "Niigata Sake"],
     "Japan", "Japan", "white"),

    # ── Israel ────────────────────────────────────────────────────────────────
    ("israel",              ["Golan Heights Winery", "Yarden Cabernet Sauvignon",
                              "Domaine du Castel", "Recanati Reserve",
                              "Clos de Gat Syrah"],
     "Israel", "Israel", "red"),

    # ── Georgia (country) ─────────────────────────────────────────────────────
    ("georgia-country",     ["Rkatsiteli Kakheti", "Saperavi Kakheti",
                              "Kindzmarauli", "Mukuzani", "Tsinandali"],
     "Georgia", "Georgia", "red"),

    # ── Canada ────────────────────────────────────────────────────────────────
    ("canada",              ["Icewine Vidal Niagara", "Okanagan Pinot Noir",
                              "Inniskillin Icewine", "Mission Hill Meritage"],
     "Canada", "Canada", "dessert"),

    # ── Croatia & Slovenia ────────────────────────────────────────────────────
    ("adriatic",            ["Plavac Mali Dingač", "Pošip Korčula",
                              "Malvazija Istriana", "Teran Istria",
                              "Brda Rebula"],
     "Croatia", "Adriatic", "red"),

    # ── South America – more ──────────────────────────────────────────────────
    ("argentina-more",      ["Malbec Luján de Cuyo", "Malbec Valle de Uco",
                              "Torrontés Salta", "Bonarda Mendoza",
                              "Cabernet Franc Patagonia"],
     "Argentina", "Argentina", "red"),
    ("chile-more",          ["Carménère Colchagua", "Pinot Noir Casablanca",
                              "Syrah Elqui Valley", "Carmenere Cachapoal",
                              "Sauvignon Blanc Leyda"],
     "Chile", "Chile", "red"),

    # ── South Africa – more ───────────────────────────────────────────────────
    ("south-africa-more",   ["Chenin Blanc Stellenbosch", "Pinotage Paarl",
                              "Syrah Swartland", "Cape Blend",
                              "Elgin Pinot Noir"],
     "South Africa", "South Africa", "white"),

    # ── Australia – more ──────────────────────────────────────────────────────
    ("australia-more",      ["Hunter Valley Semillon", "Margaret River Cabernet",
                              "Mornington Peninsula Pinot Noir",
                              "Grampians Shiraz", "Adelaide Hills Chardonnay"],
     "Australia", "Australia", "white"),

    # ── New Zealand – more ────────────────────────────────────────────────────
    ("new-zealand-more",    ["Martinborough Pinot Noir", "Waipara Riesling",
                              "Gisborne Chardonnay", "Hawke's Bay Merlot"],
     "New Zealand", "New Zealand", "red"),

    # ── France – Southwest ────────────────────────────────────────────────────
    ("france-southwest",    ["Cahors Malbec", "Madiran Tannat", "Jurançon Sec",
                              "Jurançon Moelleux", "Gaillac Rouge", "Bergerac Rouge",
                              "Irouléguy Rouge", "Marcillac"],
     "France", "Southwest France", "red"),

    # ── France – Savoy & Bugey ────────────────────────────────────────────────
    ("france-savoie",       ["Roussette de Savoie", "Mondeuse Savoie",
                              "Apremont", "Chignin Bergeron", "Bugey Cerdon"],
     "France", "Savoie", "white"),

    # ── Italy – Piedmont extras ───────────────────────────────────────────────
    ("piedmont-more",       ["Gavi di Gavi", "Roero Arneis", "Barbera d'Asti Superiore",
                              "Moscato d'Asti", "Langhe Nebbiolo", "Dolcetto d'Alba"],
     "Italy", "Piedmont", "white"),

    # ── Italy – Lombardy ──────────────────────────────────────────────────────
    ("lombardy",            ["Franciacorta Brut", "Franciacorta Satèn",
                              "Valtellina Superiore", "Sforzato di Valtellina",
                              "Lugana Riserva", "Oltrepò Pavese Pinot Nero"],
     "Italy", "Lombardy", "sparkling"),

    # ── Italy – Lazio & Liguria ───────────────────────────────────────────────
    ("lazio-liguria",       ["Frascati Superiore", "Cesanese del Piglio",
                              "Rossese di Dolceacqua", "Cinque Terre Bianco",
                              "Vermentino Liguria"],
     "Italy", "Central Italy", "white"),

    # ── Italy – Calabria & Valle d'Aosta ─────────────────────────────────────
    ("calabria-aosta",      ["Cirò Rosso Classico", "Greco di Bianco",
                              "Donnas Valle d'Aosta", "Enfer d'Arvier"],
     "Italy", "Southern Italy", "red"),

    # ── Spain – Txakoli & Canary Islands ─────────────────────────────────────
    ("spain-basque-canary", ["Txakoli Getariako", "Txakoli Bizkaiko",
                              "Listán Negro Tenerife", "Malvasía Lanzarote",
                              "Marmajuelo Canary Islands"],
     "Spain", "Spain", "white"),

    # ── Spain – Valencia & Castilla ───────────────────────────────────────────
    ("spain-inland",        ["Valencia Bobal", "Utiel-Requena Bobal",
                              "La Mancha Tempranillo", "Valdepeñas Reserva",
                              "Ribera del Guadiana"],
     "Spain", "Spain", "red"),

    # ── Portugal – more ───────────────────────────────────────────────────────
    ("portugal-more",       ["Bairrada Baga", "Baga Bairrada",
                              "Dão Touriga Nacional", "Setúbal Moscatel",
                              "Lisboa Tejo", "Alentejo Aragonez"],
     "Portugal", "Portugal", "red"),

    # ── Madeira ───────────────────────────────────────────────────────────────
    ("madeira",             ["Madeira Sercial", "Madeira Verdelho",
                              "Madeira Bual", "Madeira Malmsey",
                              "Blandy's Madeira", "Henriques Henriques Madeira"],
     "Portugal", "Madeira", "fortified"),

    # ── Germany – Ahr & more ──────────────────────────────────────────────────
    ("germany-ahr",         ["Ahr Spätburgunder", "Ahr Pinot Noir",
                              "Mittelrhein Riesling", "Mosel Grosses Gewächs"],
     "Germany", "Germany", "red"),

    # ── Austria – more regions ────────────────────────────────────────────────
    ("austria-more",        ["Kamptal Riesling Lamm", "Kremstal Grüner Veltliner",
                              "Steiermark Sauvignon Blanc", "Wiener Gemischter Satz",
                              "Neusiedlersee Trockenbeerenauslese",
                              "Leithaberg Blaufränkisch"],
     "Austria", "Austria", "white"),

    # ── Switzerland ───────────────────────────────────────────────────────────
    ("switzerland",         ["Chasselas Lavaux", "Fendant Valais",
                              "Dôle Valais", "Pinot Noir Graubünden",
                              "Cornalin Valais", "Humagne Rouge"],
     "Switzerland", "Switzerland", "white"),

    # ── England ───────────────────────────────────────────────────────────────
    ("england",             ["Nyetimber Classic Cuvée", "Ridgeview Bloomsbury",
                              "Chapel Down Brut", "Camel Valley Brut",
                              "Hambledon Classic Cuvée"],
     "United Kingdom", "England", "sparkling"),

    # ── Uruguay ───────────────────────────────────────────────────────────────
    ("uruguay",             ["Tannat Uruguay", "Bouza Tannat",
                              "Pisano Tannat", "Carrau Tannat",
                              "Viña Varela Zarranz Tannat"],
     "Uruguay", "Uruguay", "red"),

    # ── Brazil ────────────────────────────────────────────────────────────────
    ("brazil",              ["Miolo Cuvée Giuseppe", "Casa Valduga Merlot",
                              "Pizzato Merlot Serra Gaúcha", "Don Guerino Syrah",
                              "Salton Talento"],
     "Brazil", "Brazil", "red"),

    # ── Mexico ────────────────────────────────────────────────────────────────
    ("mexico",              ["LA Cetto Nebbiolo Baja", "Monte Xanic Cabernet",
                              "Château Camou Baja", "Mogor Badan",
                              "Vena Cava Baja California"],
     "Mexico", "Baja California", "red"),

    # ── Turkey ────────────────────────────────────────────────────────────────
    ("turkey",              ["Kalecik Karası Ankara", "Öküzgözü Elazığ",
                              "Boğazkere Diyarbakır", "Kavaklidere Prestige",
                              "Doluca Özel Rezerv"],
     "Turkey", "Turkey", "red"),

    # ── Lebanon – more ────────────────────────────────────────────────────────
    ("lebanon-more",        ["Château Musar Rouge", "Château Musar Blanc",
                              "Massaya Classic", "Ksara Réserve du Couvent",
                              "Château Kefraya Comtes de M"],
     "Lebanon", "Lebanon", "red"),

    # ── China ─────────────────────────────────────────────────────────────────
    ("china",               ["Grace Vineyard Tasya's Reserve", "Château Changyu Cabernet",
                              "Silver Heights Ningxia", "Pernod Ricard Helan Mountain",
                              "Ao Yun Yunnan"],
     "China", "China", "red"),

    # ── India ─────────────────────────────────────────────────────────────────
    ("india",               ["Sula Rasa Shiraz", "Grover Zampa La Réserve",
                              "York Winery Cabernet", "Fratelli Sette",
                              "KRSMA Sangiovese"],
     "India", "India", "red"),

    # ── Romania & Bulgaria ────────────────────────────────────────────────────
    ("eastern-europe",      ["Fetească Neagră Dealu Mare", "Cramele Recaș Wines",
                              "Melnik 55 Damianitza", "Mavrud Asenovgrad",
                              "Bessa Valley Enira", "Chateau Copsa"],
     "Romania", "Eastern Europe", "red"),

    # ── Tasmania ──────────────────────────────────────────────────────────────
    ("tasmania",            ["Jansz Tasmania Sparkling", "Devil's Corner Pinot Noir",
                              "Domaine A Cabernet", "Josef Chromy Riesling",
                              "Freycinet Pinot Noir"],
     "Australia", "Tasmania", "sparkling"),

    # ── Argentina – more regions ──────────────────────────────────────────────
    ("argentina-regions",   ["Zuccardi Valle de Uco", "Catena Zapata Adrianna",
                              "Achaval Ferrer Malbec", "Clos de los Siete Malbec",
                              "Torrontés Cafayate Salta"],
     "Argentina", "Argentina", "red"),

    # ── Chile – more regions ──────────────────────────────────────────────────
    ("chile-regions",       ["Almaviva Puente Alto", "Seña Aconcagua",
                              "Don Melchor Cabernet", "Viñedo Chadwick",
                              "Concha y Toro Carmin de Peumo"],
     "Chile", "Chile", "red"),

    # ── US Boutique Producers – producer-name queries ─────────────────────────
    # These don't rank highly in broad appellation searches; targeting by
    # producer name surfaces their full range of wines directly.
    ("us-boutique-pinot-1", ["Hirsch Vineyards", "Littorai Wines",
                              "Occidental Wines", "Ceritas Wines",
                              "Failla Wines", "Freeman Vineyard"],
     "USA", "Sonoma Coast", "red"),
    ("us-boutique-pinot-2", ["Kutch Wines", "Brewer-Clifton", "Sandhi Wines",
                              "Alma Rosa Winery", "Dierberg Vineyard",
                              "Foxen Vineyard"],
     "USA", "California", "red"),
    ("us-boutique-pinot-3", ["Antica Terra Oregon", "Kelley Fox Wines",
                              "Beaux Frères Oregon", "Adelsheim Vineyard",
                              "Domaine Drouhin Oregon", "A to Z Wineworks"],
     "USA", "Oregon", "red"),
    ("us-boutique-chard-1", ["Peay Vineyards", "Varner Wine", "Mount Eden Vineyards",
                              "Ridge Vineyards", "Stony Hill Vineyard",
                              "Hanzell Vineyards"],
     "USA", "California", "white"),
    ("us-boutique-chard-2", ["DuMol Winery", "Kistler Vineyards", "Paul Hobbs Winery",
                              "Ramey Wine Cellars", "Lioco Wine", "Domaine Eden"],
     "USA", "California", "white"),
    ("us-boutique-cab-1",   ["Corison Winery", "Spottswoode Estate", "Stony Hill",
                              "Dunn Vineyards", "Philip Togni Vineyard",
                              "Araujo Estate"],
     "USA", "Napa Valley", "red"),
    ("us-boutique-cab-2",   ["Cain Vineyard", "Chappellet Vineyard", "Heitz Cellar",
                              "Mayacamas Vineyards", "Mount Veeder Winery",
                              "Viader Vineyard"],
     "USA", "Napa Valley", "red"),
    ("us-boutique-misc",    ["Sandlands Wines", "Bedrock Wine Co", "Jolie-Laide",
                              "Cruse Wine Co", "Populis Wine", "Scholium Project",
                              "Wind Gap Wines"],
     "USA", "California", "red"),
    ("us-sub-avs",          ["Fort Ross-Seaview Pinot Noir", "West Sonoma Coast Pinot Noir",
                              "Anderson Valley Pinot Noir", "Santa Cruz Mountains Pinot Noir",
                              "Sta. Rita Hills Pinot Noir", "Chehalem Mountains Pinot Noir",
                              "Ribbon Ridge Pinot Noir", "Eola-Amity Hills Pinot Noir"],
     "USA", "California/Oregon", "red"),
    ("us-natural-producers", ["Stolpman Vineyards", "Love and Terroir", "Hiyu Wine Farm",
                               "Iruai Wine", "Folk Machine Wines", "Scar of the Sea",
                               "Trail Marker Wine", "Tessier Winery"],
     "USA", "California", "red"),

    # ── Burgundy Boutique Domaines – producer-name queries ───────────────────
    ("burgundy-boutique-1", ["Bruno Clair Burgundy", "David Duband Burgundy",
                              "Domaine Michel Lafarge", "Domaine de Montille",
                              "Gabin et Felix Richoux", "Rodolphe Demougeot"],
     "France", "Burgundy", "red"),
    ("burgundy-boutique-2", ["Anthony Thevenet Beaujolais", "Jean-Louis Dutraive Fleurie",
                              "Domaine Chapelle Santenay", "Pierre-Yves Colin-Morey",
                              "Christophe et Fils Chablis", "Jean Collet Chablis"],
     "France", "Burgundy", "red"),
    ("burgundy-boutique-3", ["Domaine Drouhin Burgundy", "Taupenot-Merme",
                              "Rossignol-Trapet", "Heresztyn-Mazzini",
                              "Domaine Trapet Pere et Fils", "Faiveley Burgundy"],
     "France", "Burgundy", "red"),

    # ── Loire Boutique Domaines ────────────────────────────────────────────────
    ("loire-boutique",      ["Domaine du Collier Loire", "Thibaud Boudignon Anjou",
                              "Forteresse de Berrye", "Arnaud Lambert Saumur",
                              "Mark Angeli", "Nicolas Joly Savennières",
                              "Alexandre Bain Pouilly-Fumé"],
     "France", "Loire Valley", "white"),

    # ── Rhône Boutique Domaines ───────────────────────────────────────────────
    ("rhone-boutique",      ["Domaine Verset Cornas", "Domaine Jamet Cote-Rotie",
                              "Domaine Gonon Saint-Joseph", "Eric Texier Rhône",
                              "Domaine du Tunnel Cornas", "Yves Cuilleron Rhône"],
     "France", "Rhône", "red"),

    # ── Champagne Growers ─────────────────────────────────────────────────────
    ("champagne-growers",   ["André Clouet Champagne", "Eric Collinet Champagne",
                              "Clos Cazals Champagne", "Vilmart et Cie Champagne",
                              "Ultramarine Sparkling", "Pierre Gimonnet Champagne",
                              "Paltrinieri Lambrusco"],
     "France", "Champagne", "sparkling"),

    # ── Italy Boutique Producers ──────────────────────────────────────────────
    ("italy-boutique-1",    ["Gianni Brunelli Brunello", "Roccheviberti Barolo",
                              "Luigi Giordano Barbaresco", "San Fereolo Dolcetto",
                              "Angelo Negro Roero", "Fratelli Alessandria"],
     "Italy", "Italy", "red"),
    ("italy-boutique-2",    ["COS Sicily", "Calabretta Etna", "Tenuta delle Terre Nere",
                              "Fattoria La Rivolta", "Castello Romitorio",
                              "Paolo Bea Umbria"],
     "Italy", "Italy", "red"),
    ("italy-boutique-3",    ["G.D. Vajra Piedmont", "Fliederhof Alto Adige",
                              "La Miraja Piedmont", "Montenidoli Tuscany",
                              "Paltrinieri Lambrusco", "Vignalta Veneto"],
     "Italy", "Italy", "red"),

    # ── Spain / Austria Boutique ──────────────────────────────────────────────
    ("spain-boutique",      ["Alvaro Palacios Priorat", "La Rioja Alta",
                              "Manuel Moldes Bierzo", "Raul Perez Bierzo",
                              "Comando G Gredos", "Envinate Canary Islands"],
     "Spain", "Spain", "red"),
    ("austria-boutique",    ["Gut Oggau Burgenland", "Moric Blaufrankisch",
                              "Weszeli Kamptal", "Clemensbusch Mosel",
                              "Királyudvar Tokaji", "Judith Beck Burgenland"],
     "Austria", "Austria", "red"),

    # ── Beaujolais Natural / Cru Producers ────────────────────────────────────
    # Broad "Morgon" queries surface popular commercial wines; these cult natural
    # producers require name-level targeting to be discovered.
    ("beaujolais-natural",  ["Marcel Lapierre Morgon", "Jean Foillard Morgon",
                              "Jean-Paul Thévenet Morgon", "Guy Breton Morgon",
                              "Julien Sunier Fleurie", "Yvon Métras Fleurie",
                              "Jean-Louis Dutraive Fleurie", "Anthony Thevenet Beaujolais",
                              "Mathieu Lapierre Morgon", "Jean-Ernest Descombes Morgon"],
     "France", "Beaujolais", "red"),

    # ── Germany Boutique Estates ──────────────────────────────────────────────
    ("germany-boutique",    ["Clemensbusch Mosel", "Peter Lauer Saar",
                              "Van Volxem Saar", "Markus Molitor Mosel",
                              "Emrich-Schönleber Nahe", "Dönnhoff Nahe",
                              "Wittmann Rheinhessen", "Weingut Keller Rheinhessen",
                              "Schäfer-Fröhlich Nahe", "Kühling-Gillot Rheinhessen"],
     "Germany", "Germany", "white"),

    # ── Jura Boutique Domaines ────────────────────────────────────────────────
    ("jura-boutique",       ["Domaine de Montbourgeau Jura", "Domaine Rolet Arbois",
                              "Philippe Ganevat Jura", "Overnoy Houillon Jura",
                              "Stéphane Tissot Arbois", "Domaine de la Pinte Arbois",
                              "Berthet-Bondet Château-Chalon", "Les Pieds sur Terre Jura",
                              "Bénédicte et Stéphane Tissot", "Jacques Puffeney Arbois"],
     "France", "Jura", "white"),

    # ── Italy Skin-Contact & Natural Producers ────────────────────────────────
    ("italy-natural",       ["Paolo Bea Umbria", "Radikon Friuli",
                              "Josko Gravner Friuli", "Elisabetta Foradori Trentino",
                              "La Stoppa Emilia Romagna", "Frank Cornelissen Etna",
                              "Arianna Occhipinti Sicily", "Massa Vecchia Tuscany",
                              "I Vigneri Etna", "Cascina degli Ulivi Piedmont"],
     "Italy", "Italy", "white"),

    # ── Australia Small / Natural Producers ──────────────────────────────────
    ("australia-natural",   ["Brash Higgins McLaren Vale", "Jauma Wines",
                              "Lucy Margaux Wines", "Tom Shobbrook Barossa",
                              "BK Wines Adelaide Hills", "Patrick Sullivan Gippsland",
                              "Gentle Folk Adelaide Hills", "Ochota Barrels",
                              "Si Vintners Western Australia", "Commune of Buttons"],
     "Australia", "Australia", "red"),

    # ── Champagne Grower-Producers (RM) ───────────────────────────────────────
    ("champagne-rm-1",      ["Bereche et Fils Champagne", "Chartogne-Taillet Champagne",
                              "Pierre Peters Champagne", "Gaston Chiquet Champagne",
                              "Francis Boulard Champagne", "Laherte Frères Champagne",
                              "Benoit Lahaye Champagne", "Dehours et Fils Champagne"],
     "France", "Champagne", "sparkling"),
    ("champagne-rm-2",      ["Fleury Père et Fils Champagne", "Franck Bonville Champagne",
                              "Varnier-Fannière Champagne", "De Sousa Champagne",
                              "Marie-Noëlle Ledru Champagne", "Pascal Doquet Champagne",
                              "Tarlant Champagne", "Larmandier-Bernier Champagne"],
     "France", "Champagne", "sparkling"),

    # ── New Zealand Boutique ──────────────────────────────────────────────────
    ("new-zealand-boutique", ["Pyramid Valley Vineyards", "Clos Henri Marlborough",
                               "Felton Road Central Otago", "Rippon Vineyard",
                               "Ata Rangi Martinborough", "Dry River Martinborough",
                               "Kusuda Wines Martinborough", "Te Mata Estate Hawke's Bay"],
     "New Zealand", "New Zealand", "red"),

    # ── South Africa Boutique ─────────────────────────────────────────────────
    ("south-africa-boutique", ["Sadie Family Wines", "David and Nadia Wines",
                                "Mullineux Wines Swartland", "Testalonga Swartland",
                                "Intellego Wines Swartland", "AA Badenhorst Swartland",
                                "Botanica Wines Stellenbosch", "Crystallum Wines"],
     "South Africa", "South Africa", "red"),

    # ── Portugal Boutique ─────────────────────────────────────────────────────
    ("portugal-boutique",   ["Niepoort Douro", "Quinta do Vale Meão Douro",
                              "Mouchão Alentejo", "Aphros Vinho Verde",
                              "Quinta da Pellada Dão", "Herdade do Esporão",
                              "Conceito Douro", "Dirk Niepoort"],
     "Portugal", "Portugal", "red"),

    # ─────────────────────────────────────────────────────────────────────────
    # NEW BLOCKS — gaps identified from French Laundry, Per Se, Quince lists
    # ─────────────────────────────────────────────────────────────────────────

    # ── Burgundy Micro-Domaines (top-list unmatched) ──────────────────────────
    ("burgundy-micro-1",    ["Lignier-Michelot Morey-Saint-Denis", "Hubert Lignier Burgundy",
                              "Domaine Taupenot-Merme Burgundy", "Domaine Rossignol-Trapet",
                              "Domaine de Villaine Bouzeron", "Anne et Hervé Sigaut Chambolle",
                              "Domaine du Collier Saumur", "Domaine Jamet Côte-Rôtie"],
     "France", "Burgundy", "red"),
    ("burgundy-micro-2",    ["Michel Niellon Chassagne-Montrachet", "Les Horées Burgundy",
                              "Domaine Pierrick Bouley Volnay", "Domaine Philippe Livera",
                              "Domaine de la Haute Olive Chinon", "Ruppert-Leroy Champagne",
                              "BiNaume Gamay", "Maison Stephan Côte-Rôtie"],
     "France", "Burgundy", "red"),

    # ── Germany Fine Estates (top-list unmatched) ─────────────────────────────
    ("germany-fine",        ["Zilliken Saarburger Rausch Mosel", "Karthäuserhof Mosel",
                              "Carl Loewen Mosel", "Alfred Merkelbach Mosel",
                              "Pichler-Krutzler Wachau", "Selbach-Oster Mosel",
                              "Robert Weil Riesling Rheingau", "Leitz Rüdesheim Rheingau"],
     "Germany", "Germany", "white"),

    # ── Austria Fine Estates ──────────────────────────────────────────────────
    ("austria-fine",        ["Veyder-Malberg Wachau", "Wieninger Wien",
                              "Pichler-Krutzler Wachau", "Hirsch Kamptal",
                              "Nikolaihof Wachau", "Alzinger Wachau",
                              "Tegernseerhof Wachau", "Knoll Wachau"],
     "Austria", "Austria", "white"),

    # ── Italy Fine Estates (Valtellina, Piedmont heritage) ───────────────────
    ("italy-fine",          ["Nino Negri Valgella Valtellina", "Burlotto Barolo Monvigliero",
                              "Cappellano Barolo", "Vallana Piedmont",
                              "Fontanafredda Barolo", "Giacomo Conterno Barolo",
                              "Lorenzo Accomasso Barolo", "Elvio Cogno Barolo"],
     "Italy", "Italy", "red"),

    # ── California Specialist Producers ──────────────────────────────────────
    ("california-specialists", ["Turley Wine Cellars Zinfandel", "Seven Apart Napa",
                                 "Turnbull Wine Cellars Napa", "El Molino Chardonnay",
                                 "Stony Hill Vineyard Chardonnay", "Paul Lato Wines",
                                 "PerChance Wines Napa", "Chev Wines Sonoma"],
     "USA", "California", "red"),

    # ── Corsica & Rare French Appellations ───────────────────────────────────
    ("france-rare",         ["Antoine Arena Patrimonio Corsica", "Clos Canarelli Corsica",
                              "Domaine Leccia Corsica", "Eric Texier Brézème",
                              "Domaine du Tunnel Cornas", "Chateau Rayas Chateauneuf",
                              "Pierre Overnoy Arbois", "Ganevat Jura"],
     "France", "France", "red"),

    # ── Bordeaux Heritage (classic châteaux for older vintages) ──────────────
    ("bordeaux-heritage",   ["Château Gruaud Larose Saint-Julien", "Château Giscours Margaux",
                              "Château Léoville-Poyferré Saint-Julien", "Château Lynch-Bages",
                              "Château Montrose Saint-Estèphe", "Château Calon-Ségur",
                              "Château Pichon Baron", "Château Ducru-Beaucaillou"],
     "France", "Bordeaux", "red"),

    # ── French Laundry / Per Se Specific Gaps ────────────────────────────────
    ("fl-perse-gaps",       ["Krug 27ème Édition Champagne", "Château Lafleur Les Pensées",
                              "Domaine Leroy Musigny", "DRC Cuvée Duvault-Blochet",
                              "Domaine de Villaine Aligoté Bouzeron",
                              "Sylvain Cathiard Aligoté", "Roland Lavantureux Chablis",
                              "Domaine Vacheron Sancerre"],
     "France", "France", "red"),

    # ══════════════════════════════════════════════════════════════════════════
    # MID-TIER / ACCESSIBLE PRODUCERS — needed for everyday restaurant menus
    # ══════════════════════════════════════════════════════════════════════════

    # ── Sonoma Pinot Noir & Chardonnay mid-tier ───────────────────────────────
    ("sonoma-mid-pinot",    ["Merry Edwards Pinot Noir Sonoma Coast",
                              "Merry Edwards Pinot Noir Russian River Valley",
                              "Kutch Pinot Noir Sonoma Coast",
                              "Kutch Pinot Noir McDougall Ranch",
                              "Hartford Court Pinot Noir Russian River Valley",
                              "Hartford Court Land's Edge Pinot Noir",
                              "Raeburn Pinot Noir Sonoma County",
                              "Wind Racer Pinot Noir Sonoma Coast",
                              "Flowers Pinot Noir Sonoma Coast",
                              "Siduri Pinot Noir Russian River Valley",
                              "Meiomi Pinot Noir California",
                              "La Crema Pinot Noir Sonoma Coast",
                              "MacMurray Pinot Noir Russian River Valley",
                              "Goldeneye Pinot Noir Anderson Valley",
                              "Coppola Director's Cut Pinot Noir",
                              "EnRoute Pinot Noir Russian River Valley"],
     "USA", "Sonoma County", "red"),

    ("sonoma-mid-chard",    ["Hartford Court Chardonnay Russian River Valley",
                              "Merry Edwards Chardonnay Russian River Valley",
                              "Gundlach Bundschu Chardonnay Sonoma Coast",
                              "Gundlach Bundschu Chardonnay Estate",
                              "DuMol Chardonnay Russian River Valley",
                              "Landmark Chardonnay Overlook",
                              "La Crema Chardonnay Russian River Valley",
                              "Rombauer Chardonnay Carneros",
                              "Chalk Hill Chardonnay Sonoma Coast",
                              "Sonoma-Cutrer Russian River Ranches Chardonnay",
                              "Flowers Chardonnay Sonoma Coast"],
     "USA", "Sonoma County", "white"),

    # ── Napa mid-tier Cabernet & Chardonnay ──────────────────────────────────
    ("napa-mid-cab",        ["Turnbull Cabernet Sauvignon Napa Valley",
                              "Clos du Val Cabernet Sauvignon Napa Valley",
                              "Darms Lane Cabernet Sauvignon Napa Valley",
                              "Frank Family Cabernet Sauvignon Napa Valley",
                              "Raymond Cabernet Sauvignon Reserve Napa Valley",
                              "Jordan Cabernet Sauvignon Alexander Valley",
                              "Stag's Leap Wine Cellars Artemis Cabernet",
                              "Stag's Leap Wine Cellars Cask 23",
                              "Stag's Leap Wine Cellars S.L.V.",
                              "Beringer Knights Valley Cabernet",
                              "Beringer Private Reserve Cabernet Napa",
                              "Cakebread Cabernet Sauvignon Napa Valley",
                              "Groth Cabernet Sauvignon Napa Valley",
                              "Freemark Abbey Cabernet Bosche",
                              "Charles Krug Cabernet Sauvignon Napa",
                              "Markham Cabernet Sauvignon Napa Valley",
                              "Pine Ridge Cabernet Sauvignon Stags Leap",
                              "Simi Cabernet Sauvignon Alexander Valley",
                              "Silver Oak Cabernet Sauvignon Alexander Valley",
                              "Silver Oak Cabernet Sauvignon Napa Valley",
                              "Caymus Cabernet Sauvignon Napa Valley",
                              "Caymus Special Selection Cabernet",
                              "Jordan Cabernet Sauvignon Sonoma County",
                              "Rodney Strong Symmetry Alexander Valley",
                              "Wild Horse Cabernet Sauvignon Paso Robles"],
     "USA", "Napa Valley", "red"),

    ("napa-mid-chard",      ["Frank Family Chardonnay Napa Valley",
                              "Stag's Leap Wine Cellars Karia Chardonnay",
                              "Cakebread Chardonnay Napa Valley",
                              "Rombauer Chardonnay Napa Valley",
                              "Pahlmeyer Chardonnay Napa Valley",
                              "Duckhorn Chardonnay Napa Valley",
                              "Groth Chardonnay Napa Valley",
                              "Newton Chardonnay Napa Valley",
                              "La Crema Chardonnay Monterey"],
     "USA", "Napa Valley", "white"),

    # ── Napa & Sonoma Sauvignon Blanc ─────────────────────────────────────────
    ("california-sauvignon-blanc", ["Duckhorn Sauvignon Blanc Napa Valley",
                              "Duckhorn Sauvignon Blanc North Coast",
                              "Merry Edwards Sauvignon Blanc Russian River Valley",
                              "Cakebread Sauvignon Blanc Napa Valley",
                              "Groth Sauvignon Blanc Napa Valley",
                              "Murphy-Goode Sauvignon Blanc Fumé Blanc",
                              "Benziger Sauvignon Blanc Sonoma County",
                              "Ferrari-Carano Fumé Blanc",
                              "Textbook Sauvignon Blanc Napa Valley",
                              "Emmolo Sauvignon Blanc",
                              "Honig Sauvignon Blanc Napa Valley"],
     "USA", "California", "white"),

    # ── Oregon mid-tier ───────────────────────────────────────────────────────
    ("oregon-mid",          ["Argyle Brut Willamette Valley",
                              "Argyle Pinot Noir Willamette Valley",
                              "Argyle Chardonnay Willamette Valley",
                              "A to Z Pinot Noir Oregon",
                              "King Estate Pinot Noir Oregon",
                              "King Estate Pinot Gris Oregon",
                              "Erath Pinot Noir Willamette Valley",
                              "Rex Hill Pinot Noir Willamette Valley",
                              "Willamette Valley Vineyards Pinot Noir",
                              "Ponzi Pinot Noir Willamette Valley",
                              "Sokol Blosser Pinot Noir Willamette Valley",
                              "Chehalem Pinot Noir Willamette Valley",
                              "Stoller Pinot Noir Dundee Hills",
                              "Anne Amie Pinot Noir Willamette Valley",
                              "Cristom Pinot Noir Willamette Valley",
                              "St. Innocent Pinot Noir Willamette Valley",
                              "Elk Cove Pinot Noir Willamette Valley",
                              "Penner-Ash Pinot Noir Willamette Valley",
                              "Evening Land Pinot Noir Willamette Valley"],
     "USA", "Oregon", "red"),

    # ── California other varietals (Zin, Syrah, Rosé, misc) ──────────────────
    ("california-misc",     ["Alexander Valley Vineyards Zinfandel",
                              "Ridge Lytton Springs Zinfandel",
                              "Ravenswood Zinfandel Sonoma",
                              "Seghesio Zinfandel Sonoma County",
                              "Dry Creek Vineyard Zinfandel",
                              "Michael David Zinfandel Lodi",
                              "Turley Zinfandel Napa Valley",
                              "Eden Rift Pinot Noir Central Coast",
                              "Chamisal Pinot Noir Edna Valley",
                              "Tolosa Pinot Noir San Luis Obispo",
                              "Qupé Syrah Central Coast",
                              "Tablas Creek Esprit de Tablas",
                              "Casino Mine Ranch Rose Amador County",
                              "J. Lohr Cabernet Sauvignon Seven Oaks",
                              "Stonestreet Cabernet Sauvignon Alexander Valley",
                              "Kenwood Cabernet Sauvignon Sonoma",
                              "Kendall-Jackson Cabernet Sauvignon Grand Reserve",
                              "La Tene Pinot Noir Pays d Oc",
                              "Bread & Butter Pinot Noir California",
                              "Meiomi Pinot Noir",
                              "The Prisoner Red Blend Napa Valley"],
     "USA", "California", "red"),

    # ── Sparkling / Prosecco mid-tier ─────────────────────────────────────────
    ("sparkling-mid",       ["Piper-Heidsieck Brut Champagne",
                              "Piper-Heidsieck Cuvée Sublime Demi-Sec",
                              "Nicolas Feuillatte Brut Champagne",
                              "Moët & Chandon Impérial Brut",
                              "Veuve Clicquot Yellow Label Brut",
                              "Chandon California Brut",
                              "Chandon Garden Spritz",
                              "La Marca Prosecco",
                              "Benvolio Prosecco",
                              "Mionetto Prosecco",
                              "Ruffino Prosecco",
                              "Santa Margherita Prosecco",
                              "Bisol Prosecco Crede",
                              "Martini & Rossi Asti",
                              "Freixenet Cava Brut",
                              "Segura Viudas Brut Cava",
                              "Codorníu Anna Blanc de Blancs Cava",
                              "Gruet Blanc de Blancs New Mexico",
                              "Domaine Carneros Brut Sparkling",
                              "Iron Horse Wedding Cuvée"],
     "USA", "California", "sparkling"),

    # ── Mid-tier Burgundy (village level, négociant) ─────────────────────────
    ("burgundy-mid",        ["Louis Jadot Macon-Villages",
                              "Louis Jadot Bourgogne Blanc",
                              "Louis Jadot Bourgogne Pinot Noir",
                              "Louis Jadot Gevrey-Chambertin",
                              "Louis Latour Bourgogne Chardonnay",
                              "Louis Latour Macon-Lugny",
                              "Joseph Drouhin Bourgogne Laforêt",
                              "Joseph Drouhin Macon-Villages",
                              "Bouchard Père Macon-Villages",
                              "Faiveley Bourgogne Pinot Noir",
                              "Antonin Rodet Mercurey",
                              "Domaine Leflaive Macon-Verzé",
                              "Albert Bichot Bourgogne",
                              "Olivier Leflaive Bourgogne Blanc",
                              "Olivier Leflaive Puligny-Montrachet",
                              "Maison Leroy Bourgogne Rouge",
                              "Patriarche Bourgogne"],
     "France", "Burgundy", "white"),

    # ── Mid-tier Loire & Rhône everyday ──────────────────────────────────────
    ("france-mid-everyday", ["Sancerre Henri Bourgeois",
                              "Sancerre Pascal Jolivet",
                              "Pouilly-Fumé de Ladoucette",
                              "Pouilly-Fumé Henri Bourgeois",
                              "Muscadet Sèvre-et-Maine Luneau-Papin",
                              "Vouvray Huet",
                              "Chinon Charles Joguet",
                              "Crozes-Hermitage Delas Frères",
                              "Crozes-Hermitage Cave de Tain",
                              "Côtes du Rhône Guigal",
                              "Côtes du Rhône Château Rayas",
                              "Gigondas Domaine Santa Duc",
                              "Vacqueyras Domaine Le Clos des Cazaux",
                              "Chateauneuf-du-Pape Château Beaucastel",
                              "Chateauneuf-du-Pape Château Mont-Redon",
                              "Bandol Domaine Tempier",
                              "Bandol Château Pradeaux",
                              "Pic Saint-Loup Mas Mortiès",
                              "Faugères Léon Barral"],
     "France", "France", "red"),

    # ── Mid-tier Italy everyday ───────────────────────────────────────────────
    ("italy-mid-everyday",  ["Scarpetta Pinot Grigio Friuli",
                              "Santa Margherita Pinot Grigio Alto Adige",
                              "Pighin Pinot Grigio Friuli",
                              "Maso Canali Pinot Grigio Trentino",
                              "Jermann Pinot Grigio Venezia Giulia",
                              "Tenuta di Arceno Chianti Classico",
                              "Ruffino Riserva Ducale Chianti Classico",
                              "Antinori Pèppoli Chianti Classico",
                              "Frescobaldi Nipozzano Chianti Rufina",
                              "Badia a Coltibuono Chianti Classico",
                              "Melini Chianti Classico",
                              "Dievole Chianti Classico",
                              "Lungarotti Rubesco Torgiano",
                              "Umani Ronchi Jorio Montepulciano d'Abruzzo",
                              "Illuminati Montepulciano d'Abruzzo",
                              "Pio Cesare Barbera d'Alba",
                              "Michele Chiarlo Barbera d'Asti",
                              "Allegrini Palazzo della Torre",
                              "Zenato Amarone della Valpolicella",
                              "Masi Costasera Amarone",
                              "Banfi Brunello di Montalcino",
                              "Col d'Orcia Brunello di Montalcino",
                              "Carpineto Vino Nobile di Montepulciano",
                              "Les Cadrans de Lassegue Saint-Emilion"],
     "Italy", "Italy", "red"),

    # ── Mid-tier Spain everyday ───────────────────────────────────────────────
    ("spain-mid-everyday",  ["Marqués de Riscal Rioja Reserva",
                              "Marqués de Cáceres Rioja Reserva",
                              "CVNE Cune Rioja Reserva",
                              "La Rioja Alta Viña Ardanza Reserva",
                              "Muga Rioja Reserva",
                              "Beronia Rioja Reserva",
                              "Bodegas Roda Roda I Rioja Reserva",
                              "Bodegas Roda Roda Rioja Reserva",
                              "Faustino Rioja Gran Reserva",
                              "Torres Gran Sangre de Toro",
                              "Torres Mas La Plana Penedès",
                              "Protos Ribera del Duero Reserva",
                              "Pesquera Ribera del Duero",
                              "Flor de Pingus Ribera del Duero",
                              "Clos Mogador Priorat",
                              "Álvaro Palacios Les Terrasses Priorat",
                              "Martín Códax Albariño Rías Baixas",
                              "Pazo de Señorans Albariño",
                              "Viña Esmeralda Torres Catalunya"],
     "Spain", "Spain", "red"),

    # ── New Zealand mid-tier (beyond Marlborough SB) ─────────────────────────
    ("new-zealand-mid",     ["Greywacke Sauvignon Blanc Marlborough",
                              "Cloudy Bay Sauvignon Blanc Marlborough",
                              "Kim Crawford Sauvignon Blanc Marlborough",
                              "Zephyr Sauvignon Blanc Marlborough",
                              "Brancott Estate Sauvignon Blanc Marlborough",
                              "Villa Maria Sauvignon Blanc Marlborough",
                              "Nautilus Sauvignon Blanc Marlborough",
                              "Spy Valley Sauvignon Blanc Marlborough",
                              "Cloudy Bay Pinot Noir Marlborough",
                              "Craggy Range Te Muna Pinot Noir",
                              "Craggy Range Gimblett Gravels Syrah",
                              "Te Mata Coleraine Hawke's Bay",
                              "Villa Maria Reserve Hawke's Bay Cabernet",
                              "Esk Valley Hawke's Bay Red Blend",
                              "Palliser Estate Pinot Noir Martinborough",
                              "Ata Rangi Pinot Noir Martinborough",
                              "Escarpment Pinot Noir Martinborough",
                              "Dry River Pinot Noir Martinborough",
                              "Mount Difficulty Pinot Noir Central Otago",
                              "Misha's Vineyard Pinot Noir Central Otago",
                              "Two Paddocks Pinot Noir Central Otago",
                              "Prophet's Rock Pinot Noir Central Otago",
                              "Pegasus Bay Pinot Noir Waipara"],
     "New Zealand", "New Zealand", "red"),

    # ── Australia mid-tier (beyond Penfolds/Henschke) ────────────────────────
    ("australia-mid",       ["Wolf Blass Black Label Cabernet Shiraz",
                              "Penfolds Bin 389 Cabernet Shiraz",
                              "Penfolds Bin 407 Cabernet Sauvignon",
                              "Penfolds Bin 28 Kalimna Shiraz",
                              "Tyrrell's Vat 1 Semillon Hunter Valley",
                              "Tyrrell's Vat 9 Shiraz Hunter Valley",
                              "d'Arenberg The Dead Arm Shiraz",
                              "d'Arenberg The Footbolt Shiraz",
                              "Torbreck RunRig Shiraz Barossa",
                              "Two Hands Bella's Garden Shiraz Barossa",
                              "Yalumba Octavius Shiraz Barossa",
                              "Wynns Coonawarra Estate Cabernet",
                              "Leeuwin Estate Art Series Chardonnay",
                              "Cape Mentelle Cabernet Sauvignon",
                              "Vasse Felix Heytesbury Chardonnay",
                              "Cullen Diana Madeline Cabernet",
                              "Giant Steps Pinot Noir Yarra Valley",
                              "Mount Langi Ghiran Grampians Shiraz",
                              "Rockford Basket Press Shiraz"],
     "Australia", "Australia", "red"),

    # ── Argentina mid-tier ────────────────────────────────────────────────────
    ("argentina-mid",       ["Achaval Ferrer Malbec Mendoza",
                              "Clos de los Siete Mendoza",
                              "Catena Zapata Adrianna Vineyard",
                              "Catena Zapata Adrianna White Bones",
                              "Bodega Clos de Chacras Malbec",
                              "Zuccardi Valle de Uco Malbec",
                              "Zuccardi Concreto Malbec",
                              "Clos de Tres Cantos Malbec",
                              "Alta Vista Premium Malbec",
                              "Cuvelier Los Andes Grand Malbec",
                              "Pulenta Estate Gran Malbec",
                              "Alamos Malbec Mendoza",
                              "Kaiken Malbec Mendoza",
                              "Trivento Golden Reserve Malbec",
                              "Achaval Ferrer Finca Bella Vista Malbec",
                              "Luigi Bosca Malbec Mendoza"],
     "Argentina", "Mendoza", "red"),

    # ── South America other / Chile mid-tier ─────────────────────────────────
    ("chile-mid",           ["Montes Alpha Cabernet Sauvignon Colchagua",
                              "Montes Folly Syrah",
                              "Casa Lapostolle Clos Apalta",
                              "Concha y Toro Don Melchor Cabernet",
                              "Almaviva Cabernet Sauvignon Puente Alto",
                              "Errazuriz Don Maximiano Founder's Reserve",
                              "Viña Seña Aconcagua",
                              "Viña Cobos Felino Malbec",
                              "Carménère MiS Wines",
                              "Santa Rita Medalla Real Cabernet",
                              "Lapostolle Grand Selection Carménère"],
     "Chile", "Chile", "red"),

    # ── South Africa mid-tier ─────────────────────────────────────────────────
    ("south-africa-mid",    ["Rustenberg John X Merriman",
                              "Meerlust Rubicon",
                              "Vergelegen GVB Red",
                              "Kanonkop Pinotage",
                              "Kanonkop Cabernet Sauvignon",
                              "Neil Ellis Groenekloof Syrah",
                              "Boekenhoutskloof Syrah Franschhoek",
                              "Boekenhoutskloof The Chocolate Block",
                              "Warwick Estate Trilogy",
                              "Kleine Zalze Vineyard Selection Chenin Blanc",
                              "Ken Forrester Chenin Blanc",
                              "AA Badenhorst Family White Blend",
                              "Mullineux Kloof Street Red",
                              "David & Nadia Chenin Blanc Swartland"],
     "South Africa", "South Africa", "red"),

    # ── Germany mid-tier Riesling ─────────────────────────────────────────────
    ("germany-mid",         ["Dr. Loosen Riesling Mosel",
                              "Dr. Loosen Dr. L Riesling",
                              "Peter Mertes Riesling Mosel",
                              "Georg Breuer Rüdesheim Riesling Rheingau",
                              "Joh. Jos. Prüm Riesling Spätlese Mosel",
                              "Selbach-Oster Riesling Mosel",
                              "Maximin Grünhaus Riesling Mosel",
                              "Schloss Johannisberg Riesling Rheingau",
                              "Reichsrat von Buhl Riesling Pfalz",
                              "Bürklin-Wolf Riesling Pfalz",
                              "Weingut Gunderloch Riesling Rheinhessen",
                              "Pfalz Riesling Kabinett Weingut Müller-Catoir",
                              "Trimbach Riesling Alsace",
                              "Hugel Riesling Alsace",
                              "Zind-Humbrecht Riesling Alsace",
                              "Domaine Weinbach Riesling Alsace"],
     "Germany", "Germany", "white"),

    # ── Rosé mid-tier (Provence + California) ────────────────────────────────
    ("rose-mid",            ["Miraval Rosé Provence",
                              "Whispering Angel Rosé Provence",
                              "Château d'Esclans Garrus Rosé",
                              "Château d'Esclans Whispering Angel",
                              "Domaines Ott Château Romassan Rosé",
                              "Bandol Rosé Domaine Tempier",
                              "Château Minuty Rosé Provence",
                              "Peyrassol Rosé Provence",
                              "Fleur de Miraval Rosé",
                              "ONEHOPE Rosé California",
                              "Meiomi Rosé California",
                              "Simi Rosé Sonoma County",
                              "Jordan Rosé Sonoma County",
                              "Frank Family Rosé Napa Valley",
                              "Elk Cove Rosé Willamette Valley",
                              "Casino Mine Ranch Rosé Amador County"],
     "France", "Provence", "rosé"),

    # ── Pinot Grigio / Northern Italy whites everyday ─────────────────────────
    ("italy-whites-mid",    ["Santa Margherita Pinot Grigio",
                              "Scarpetta Pinot Grigio",
                              "Livio Felluga Pinot Grigio Friuli",
                              "Ecco Domani Pinot Grigio",
                              "Cavit Pinot Grigio Trentino",
                              "Alois Lageder Pinot Grigio",
                              "Zenato Pinot Grigio Garda",
                              "Tiefenbrunner Pinot Grigio",
                              "Terlan Pinot Grigio Alto Adige",
                              "Bottega Vinai Pinot Grigio",
                              "Kris Pinot Grigio Delle Venezie",
                              "Gavi La Scolca",
                              "Gavi di Gavi La Giustiniana",
                              "Soave Pieropan Classico",
                              "Soave Classico Inama",
                              "Vermentino Argiolas Costamolino Sardinia",
                              "Greco di Tufo Feudi di San Gregorio"],
     "Italy", "Northern Italy", "white"),

    # ── Mid-tier Bordeaux ─────────────────────────────────────────────────────
    ("bordeaux-mid",        ["Château Sociando-Mallet Haut-Médoc",
                              "Château Poujeaux Moulis",
                              "Château Chasse-Spleen Moulis",
                              "Château Cantemerle Haut-Médoc",
                              "Château de Pez Saint-Estèphe",
                              "Château Phélan Ségur Saint-Estèphe",
                              "Château Les Carmes Haut-Brion",
                              "Château Fombrauge Saint-Emilion",
                              "Château Franc Mayne Saint-Emilion",
                              "Château La Dominique Saint-Emilion",
                              "Les Cadrans de Lassegue Saint-Emilion",
                              "Château Bellefont-Belcier Saint-Emilion",
                              "Château Rouget Pomerol",
                              "Vieux Château Certan Pomerol",
                              "Clos René Pomerol",
                              "Château Bonnet Bordeaux",
                              "Dourthe Numero 1 Bordeaux",
                              "Château Greysac Médoc",
                              "Château Larose Trintaudon Haut-Médoc",
                              "Château de Sours Bordeaux Rosé"],
     "France", "Bordeaux", "red"),

    # ── Champagne mid-tier NV ─────────────────────────────────────────────────
    ("champagne-mid",       ["Piper-Heidsieck Brut NV",
                              "Piper-Heidsieck Essentiel Blanc de Blancs",
                              "Charles Heidsieck Brut Réserve NV",
                              "Charles Heidsieck Blanc de Millénaires",
                              "Mumm Cordon Rouge Brut NV",
                              "Mumm Grand Cordon Brut NV",
                              "Perrier-Jouët Grand Brut NV",
                              "Perrier-Jouët Belle Epoque",
                              "Lanson Black Label Brut NV",
                              "GH Martel Champagne Brut",
                              "Nicolas Feuillatte Brut NV",
                              "Deutz Brut Classic NV",
                              "Gosset Grande Réserve Brut",
                              "Henri Giraud Fût de Chêne",
                              "Billecart-Salmon Brut Rosé",
                              "Billecart-Salmon Blanc de Blancs",
                              "Taittinger Brut La Française NV",
                              "Taittinger Comtes de Champagne Blanc de Blancs",
                              "Moët & Chandon Imperial Brut NV",
                              "Veuve Clicquot Brut NV",
                              "Veuve Clicquot La Grande Dame"],
     "France", "Champagne", "sparkling"),

    # ── Burgundy Côte de Nuits — specific domaines (gap from deep wine-list analysis) ──
    ("burgundy-nuits-specific",
                            ["Domaine de Montille Volnay",
                             "Domaine de Montille Pommard",
                             "Domaine de Montille Nuits-Saint-Georges",
                             "Domaine de Montille Corton-Charlemagne",
                             "Domaine de Montille Puligny-Montrachet",
                             "Domaine Denis Mortet Gevrey-Chambertin",
                             "Domaine Denis Mortet Chambertin",
                             "Domaine Denis Mortet Clos-Vougeot",
                             "Domaine Denis Mortet Lavaux Saint-Jacques",
                             "Robert Groffier Chambertin Clos-de-Bèze",
                             "Robert Groffier Bonnes-Mares",
                             "Robert Groffier Les Amoureuses",
                             "Domaine Robert Chevillon Nuits-Saint-Georges",
                             "Domaine Robert Chevillon Les Saint Georges",
                             "Domaine Robert Chevillon Les Vaucrains",
                             "Confuron-Cotetidot Vosne-Romanée",
                             "Confuron-Cotetidot Echézeaux",
                             "Confuron-Cotetidot Gevrey-Chambertin",
                             "Domaine Hudelot-Noëllat Chambolle-Musigny",
                             "Domaine Hudelot-Noëllat Vosne-Romanée",
                             "Domaine Hudelot-Noëllat Richebourg",
                             "Mongeard-Mugneret Vosne-Romanée",
                             "Mongeard-Mugneret Echézeaux",
                             "Mongeard-Mugneret Grands-Echézeaux",
                             "Bruno Clair Gevrey-Chambertin",
                             "Bruno Clair Marsannay",
                             "Bruno Clair Bonnes-Mares",
                             "Louis Boillot Chambolle-Musigny",
                             "Louis Boillot Gevrey-Chambertin",
                             "Louis Boillot Volnay",
                             "Domaine Perrot-Minot Charmes-Chambertin",
                             "Domaine Perrot-Minot Morey-Saint-Denis",
                             "Christophe Roumier Charmes-Chambertin",
                             "Christophe Roumier Bonnes-Mares",
                             "Claude Dugat Griotte-Chambertin",
                             "Claude Dugat Charmes-Chambertin",
                             "Claude Dugat Gevrey-Chambertin",
                             "Sylvie Esmonin Gevrey-Chambertin",
                             "Clos de Tart Mommessin",
                             "Domaine Ponsot Clos de la Roche",
                             "Domaine Ponsot Morey-Saint-Denis",
                             "Pierre Labet Clos de Vougeot",
                             "Pierre Labet Beaune"],
     "France", "Burgundy", "red"),

    # ── Burgundy Côte de Beaune — white-specific domaines ─────────────────────
    ("burgundy-beaune-white-specific",
                            ["Jean-Philippe Fichet Meursault",
                             "Jean-Philippe Fichet Meursault Premier Cru",
                             "Jean-Philippe Fichet Puligny-Montrachet",
                             "Jean-Philippe Fichet Chassagne-Montrachet",
                             "Ballot-Millot Meursault",
                             "Ballot-Millot Meursault Perrieres",
                             "Ballot-Millot Meursault Charmes",
                             "Ballot-Millot Chassagne-Montrachet",
                             "Domaine Paul Pillot Chassagne-Montrachet",
                             "Domaine Paul Pillot Chassagne-Montrachet Premier Cru",
                             "Domaine Paul Pillot Saint-Aubin",
                             "Domaine Michel Niellon Chassagne-Montrachet",
                             "Domaine Michel Niellon Chassagne-Montrachet Premier Cru",
                             "Caroline Morey Chassagne-Montrachet",
                             "Caroline Morey Santenay",
                             "François Carillon Puligny-Montrachet",
                             "François Carillon Chassagne-Montrachet",
                             "François Carillon Puligny-Montrachet Premier Cru",
                             "Domaine Jean-Marc Pillot Chassagne-Montrachet",
                             "Domaine Blain-Gagnard Chassagne-Montrachet",
                             "Domaine Blain-Gagnard Criots-Bâtard-Montrachet",
                             "Domaine Fontaine-Gagnard Chassagne-Montrachet",
                             "Domaine Fontaine-Gagnard Bâtard-Montrachet",
                             "Etienne Sauzet Puligny-Montrachet",
                             "Etienne Sauzet Puligny-Montrachet Premier Cru",
                             "Etienne Sauzet Bâtard-Montrachet",
                             "Domaine Berthelemot Meursault",
                             "Albert Grivault Meursault Clos des Perrieres",
                             "Antoine Jobard Meursault",
                             "Domaine Latour-Girard Meursault Premier Cru",
                             "Jean-Louis Chavy Puligny-Montrachet",
                             "Domaine J.M. Boillot Puligny-Montrachet",
                             "Remoissenet Père et Fils Puligny-Montrachet",
                             "Moreau-Naudet Chablis Premier Cru",
                             "Samuel Billaud Chablis Premier Cru",
                             "Laurent Tribut Chablis",
                             "Vincent Dauvissat Chablis",
                             "Vincent Dauvissat Les Clos Grand Cru"],
     "France", "Burgundy", "white"),

    # ── Chablis — specific domaines ────────────────────────────────────────────
    ("chablis-specific",    ["Louis Michel Chablis",
                             "Louis Michel Chablis Premier Cru Montée de Tonnerre",
                             "Louis Michel Vaudesir Grand Cru",
                             "Louis Michel Les Clos Grand Cru",
                             "Louis Michel Butteaux",
                             "Louis Michel Forêts",
                             "François Raveneau Chablis",
                             "François Raveneau Chablis Premier Cru",
                             "François Raveneau Butteaux",
                             "François Raveneau Chapelot",
                             "François Raveneau Montée de Tonnerre",
                             "François Raveneau Valmur Grand Cru",
                             "Domaine Billaud-Simon Chablis Premier Cru",
                             "Domaine Billaud-Simon Valmur Grand Cru",
                             "Domaine Vocoret Chablis Premier Cru",
                             "Domaine Vocoret Valmur",
                             "Guy Robin Chablis Grand Cru",
                             "Jean-Marc Brocard Chablis Premier Cru"],
     "France", "Chablis", "white"),

    # ── Burgundy — Domaine Dujac & other Grand Cru specialists ─────────────────
    ("burgundy-grand-cru-special",
                            ["Domaine Dujac Clos de la Roche",
                             "Domaine Dujac Charmes-Chambertin",
                             "Domaine Dujac Bonnes-Mares",
                             "Domaine Dujac Aux Malconsorts",
                             "Domaine Dujac Gevrey-Chambertin",
                             "Domaine Dujac Chambolle-Musigny",
                             "Domaine Dujac Echézeaux",
                             "Clos de Tart Morey-Saint-Denis Grand Cru",
                             "Domaine Arnoux-Lachaux Vosne-Romanée",
                             "Domaine Arnoux-Lachaux Nuits-Saint-Georges",
                             "Domaine Arnoux-Lachaux Romanée-Saint-Vivant",
                             "Domaine Michel Gros Vosne-Romanée",
                             "Domaine Michel Gros Nuits-Saint-Georges Les Chaliots",
                             "Domaine Michel Gros Richebourg",
                             "Domaine Michel Gros Clos Vougeot",
                             "Jean-Marc Millot Echézeaux",
                             "Sylvain Cathiard Vosne-Romanée",
                             "Domaine Régis Forey Vosne-Romanée",
                             "J.-F. Coche-Dury Meursault",
                             "J.-F. Coche-Dury Corton-Charlemagne",
                             "Jean-Marc Roulot Meursault",
                             "Jean-Marc Roulot Meursault Premier Cru"],
     "France", "Burgundy", "red"),

    # ── California — boutique Pinot Noir & Chardonnay ─────────────────────────
    ("california-boutique-pinot",
                            ["Ceritas Pinot Noir Sonoma Coast",
                             "Ceritas Charles Heintz Vineyard Chardonnay",
                             "Ceritas Trout Gulch Vineyard Chardonnay",
                             "Ceritas Peter Martin Ray Vineyard",
                             "Ceritas Porter-Bass Vineyard",
                             "Littorai Pinot Noir Sonoma Coast",
                             "Littorai B.A. Theriot Vineyard",
                             "Littorai Mays Canyon Pinot Noir",
                             "Littorai Haven Vineyard Chenin Blanc",
                             "Copain Pinot Noir Anderson Valley",
                             "Copain Monument Tree Vineyard",
                             "Copain Wendling Vineyard",
                             "Copain Chardonnay Monterey",
                             "Arnot-Roberts Pinot Noir",
                             "Arnot-Roberts Watson Ranch Chardonnay",
                             "Arnot-Roberts Trout Gulch Chardonnay",
                             "Peay Vineyards Pinot Noir Sonoma Coast",
                             "Peay Pomarium Estate Pinot Noir",
                             "Peay Ama Pinot Noir",
                             "Peay Les Titans Syrah",
                             "Peay Estate Chardonnay",
                             "ROAR Pinot Noir Santa Lucia Highlands",
                             "ROAR Sierra Mar Vineyard Chardonnay",
                             "Lucia Pinot Noir Santa Lucia Highlands",
                             "Lucia Chardonnay Santa Lucia Highlands",
                             "Rhys Pinot Noir San Mateo County",
                             "Rhys Family Farm Vineyard",
                             "Rhys Horseshoe Vineyard",
                             "Rhys Alesia Chardonnay",
                             "Failla Pinot Noir Sonoma Coast",
                             "Failla Haynes Vineyard Chardonnay",
                             "Freeman Pinot Noir Sonoma Coast",
                             "Williams Selyem Pinot Noir Russian River Valley",
                             "Williams Selyem Rochioli River Block",
                             "Williams Selyem Precious Mountain",
                             "Emeritus Halberg Ranch Pinot Noir",
                             "Anthill Farms Pinot Noir",
                             "Siduri Pinot Noir Russian River Valley",
                             "Alfaro Family Vineyards Pinot Noir",
                             "Tyler Pinot Noir Santa Barbara",
                             "Sandhi Pinot Noir Sta. Rita Hills",
                             "Chanin Pinot Noir Santa Barbara"],
     "USA", "California", "red"),

    # ── California — cult Chardonnay (Aubert, DuMOL, Kistler, Kongsgaard) ─────
    ("california-cult-chard",
                            ["Aubert Chardonnay Sonoma Coast",
                             "Aubert UV-SL Vineyard Chardonnay",
                             "Aubert Eastside Chardonnay",
                             "Aubert Hyde Vineyard Chardonnay",
                             "DuMOL Wester Reach Chardonnay",
                             "DuMOL Chardonnay Russian River Valley",
                             "Kistler Les Noisetiers Chardonnay",
                             "Kistler Vine Hill Vineyard Chardonnay",
                             "Kistler McCrea Vineyard Chardonnay",
                             "Kongsgaard Chardonnay Napa Valley",
                             "Kongsgaard The Judge Chardonnay",
                             "Peter Michael Belle Côte Chardonnay",
                             "Peter Michael La Carrière Chardonnay",
                             "Peter Michael Ma Belle-Fille Chardonnay",
                             "Paul Hobbs Richard Dinner Vineyard Chardonnay",
                             "Kosta Browne One Sixteen Chardonnay",
                             "Mount Eden Estate Chardonnay Santa Cruz",
                             "Ridge Vineyards Estate Chardonnay Santa Cruz Mountains",
                             "Stony Hill Chardonnay Napa Valley",
                             "Hanzell Estate Chardonnay Sonoma",
                             "Chateau Montelena Chardonnay Napa Valley",
                             "Rochioli Chardonnay Russian River Valley",
                             "Lynmar Quail Hill Chardonnay",
                             "Pisoni Estate Chardonnay Santa Lucia Highlands"],
     "USA", "California", "white"),

    # ── California — cult Cabernet & red Bordeaux-style ───────────────────────
    ("california-cult-cab",
                            ["Bryant Family Vineyards Pritchard Hill",
                             "Bond St. Eden Oakville",
                             "Bond Quella Napa Valley",
                             "Bond Melbury Napa Valley",
                             "Bond Vecina Napa Valley",
                             "Sine Qua Non The Duel",
                             "Sine Qua Non Atlantis",
                             "Sine Qua Non Syrah",
                             "Marcassin Estate Vineyard Pinot Noir",
                             "Marcassin Chardonnay Sonoma",
                             "Anakota Helena Montana Vineyard Knights Valley",
                             "Corison Kronos Vineyard St. Helena",
                             "Corison Cabernet Sauvignon Napa Valley",
                             "Kelly Fleming Calistoga Cabernet",
                             "La Jota Howell Mountain Cabernet",
                             "Inglenook Cask Rutherford",
                             "Paradigm Oakville Cabernet",
                             "Spring Mountain Estate Cabernet",
                             "Mt. Brave Mt Veeder Cabernet",
                             "Blackbird Vineyards Arise Merlot Napa",
                             "Turley Wine Cellars Zinfandel",
                             "A. Rafanelli Zinfandel Dry Creek Valley",
                             "A. Rafanelli Cabernet Sauvignon",
                             "Bedrock Wine Co. Zinfandel Sonoma Valley",
                             "Stagecoach Vineyard Cabernet",
                             "Chappellet Signature Cabernet Napa"],
     "USA", "California", "red"),

    # ── Oregon — specific producers ────────────────────────────────────────────
    ("oregon-specific",     ["Beaux Frères Pinot Noir Ribbon Ridge",
                             "Beaux Frères Upper Terrace Vineyard",
                             "Beaux Frères The Belles Soeurs",
                             "Eyrie Vineyards Pinot Noir Dundee Hills",
                             "Eyrie Original Vines Reserve Pinot Noir",
                             "Eyrie Pinot Gris Willamette Valley",
                             "Cristom Eileen Vineyard Pinot Noir",
                             "Cristom Mt. Jefferson Cuvée",
                             "Cristom Marjorie Vineyard",
                             "Ken Wright Cellars Pinot Noir Eola-Amity",
                             "Ken Wright Carter Vineyard Pinot Noir",
                             "Ken Wright Guadalupe Vineyard Pinot Noir",
                             "Domaine Serene Evanstead Reserve Pinot Noir",
                             "Evening Land Seven Springs Vineyard La Source",
                             "Gran Moraine Yamhill-Carlton Pinot Noir",
                             "Cameron Winery Clos Electrique Chardonnay",
                             "Penner-Ash Pinot Noir Willamette Valley",
                             "Résonance Pinot Noir Willamette Valley",
                             "Adelsheim Pinot Noir Willamette Valley"],
     "USA", "Oregon", "red"),

    # ── Washington State — specific producers ─────────────────────────────────
    ("washington-specific",  ["Reynvaan Family Vineyards Walla Walla",
                              "Reynvaan In The Rocks Syrah",
                              "Reynvaan Stonessence Syrah",
                              "Andrew Will Champoux Vineyard",
                              "Quilceda Creek Cabernet Sauvignon",
                              "DeLille Cellars Chaleur Estate",
                              "Cayuse Vineyards Bionic Frog Syrah",
                              "Gramercy Cellars Syrah Walla Walla",
                              "K Vintners Syrah Washington"],
     "USA", "Washington", "red"),

    # ── Germany — specific estates (gap from deep wine-list analysis) ──────────
    ("germany-specific",    ["Dönnhoff Riesling Nahe",
                             "Dönnhoff Niederhäuser Hermannshöhle Spätlese",
                             "Dönnhoff Niederhäuser Hermannshöhle Auslese",
                             "Dönnhoff Niederhäuser Hermannshöhle GG",
                             "Dönnhoff Oberhäuser Leistenberg Kabinett",
                             "Keller G-Max Riesling Rheinhessen",
                             "Keller RR Riesling Rheinhessen",
                             "Keller Dalsheimer Hübacker Auslese",
                             "Keller Westhofer Abts E Auslese",
                             "Keller Niersteiner Hipping Spätlese",
                             "Fritz Haag Brauneberger Juffer-Sonnenuhr Spätlese",
                             "Fritz Haag Mosel Riesling Auslese",
                             "Egon Müller Scharzhofberger Riesling Spätlese",
                             "Egon Müller Scharzhofberger Auslese",
                             "Von Simmern Riesling Rheingau",
                             "Selbach-Oster Riesling Mosel",
                             "Prüm J.J. Wehlener Sonnenuhr Auslese"],
     "Germany", "Mosel / Nahe / Rheinhessen", "white"),

    # ── Austria — specific estates ─────────────────────────────────────────────
    ("austria-specific",    ["F.X. Pichler Riesling Smaragd Wachau",
                             "F.X. Pichler Kellerberg Smaragd",
                             "F.X. Pichler Loibner Berg Smaragd",
                             "F.X. Pichler Unendlich Smaragd",
                             "Knoll Ried Kellerberg Smaragd Wachau",
                             "Knoll Loibner Vinothek Smaragd",
                             "Prager Riesling Smaragd Wachau",
                             "Prager Steinriegl Federspiel",
                             "Prager Achleiten Smaragd",
                             "Nigl Riesling Privat Kremstal",
                             "Nigl Senftenberger Piri Riesling",
                             "Brundlmayer Grüner Veltliner Kamptal",
                             "Brundlmayer Heiligenstein Riesling",
                             "Hirsch Kammern Lamm Grüner Veltliner",
                             "Hirsch Heiligenstein Riesling Kamptal",
                             "Gobelsberg Steinsetz Grüner Veltliner"],
     "Austria", "Wachau / Kamptal / Kremstal", "white"),

    # ── Grower Champagne — specific producers (gap from deep wine-list) ────────
    ("champagne-grower-specific",
                            ["Agrapart Terroirs Blanc de Blancs",
                             "Agrapart Mineral Blanc de Blancs",
                             "Agrapart Venus Blanc de Blancs",
                             "Agrapart Complantée",
                             "Jacques Selosse Initial",
                             "Jacques Selosse Sous Le Mont",
                             "Jacques Selosse Substance",
                             "Vilmart Grand Cellier Premier Cru",
                             "Vilmart Grand Cellier d'Or",
                             "Vilmart Coeur de Cuvée",
                             "Cédric Bouchard Roses de Jeanne Blanc de Blancs",
                             "Cédric Bouchard Val Vilaine",
                             "Georges Laval Les Chênes Blanc de Blancs",
                             "Georges Laval Cumières Premier Cru",
                             "J. Lassalle Cuvée Spéciale Premier Cru",
                             "J. Lassalle Special Club",
                             "Henri Goutorbe Special Club Aÿ Grand Cru",
                             "Marc Hebrart Special Club",
                             "Robert Moncuit Blanc de Blancs Le Mesnil",
                             "Pierre Moncuit Blanc de Blancs",
                             "Moussé Fils Terres d'Illite",
                             "Vouette & Sorbée Fidèle",
                             "Vouette & Sorbée Cuvée d'Argile",
                             "David Léclapart L'Artiste",
                             "Francis Boulard Petraea",
                             "Forest Marié Blanc de Noirs",
                             "Rene Geoffroy Cuvée Expression",
                             "Paul Bara Bouzy Grand Cru",
                             "Paul Bara Special Club",
                             "Jean Vesselle Rosé de Saignée",
                             "R.H. Coutier Ambonnay Grand Cru",
                             "Alfred Gratien Épernay vintage",
                             "Alfred Gratien Cuvée Paradis",
                             "Henri Giraud Esprit Nature",
                             "A.R. Lenoble Blanc de Blancs",
                             "Jacquesson Cuvée 733",
                             "Jacquesson Champ Cain Avize",
                             "Tarlant Zero Brut Nature",
                             "Ruinart Dom Ruinart Blanc de Blancs",
                             "Canard-Duchêne Champagne Brut",
                             "Gosset Celebris Extra Brut"],
     "France", "Champagne", "sparkling"),

    # ── Italy — specific estates (gaps from deep wine-list analysis) ───────────
    ("italy-specific",      ["Biondi-Santi Brunello di Montalcino",
                             "Biondi-Santi Tenuta Il Greppo Riserva",
                             "Soldera Case Basse Brunello",
                             "Soldera Riserva Brunello di Montalcino",
                             "Giacomo Conterno Barolo Cascina Francia",
                             "Giacomo Conterno Barolo Monfortino",
                             "Giacomo Conterno Barbera Cascina Francia",
                             "Mastroberardino Taurasi Riserva Radici",
                             "Mastroberardino Naturalis Historia Taurasi",
                             "Giuseppe Quintarelli Amarone",
                             "Giuseppe Quintarelli Valpolicella Classico",
                             "Montevertine Rosso di Toscana",
                             "Montevertine Le Pergole Torte",
                             "Moris Farms Avvoltore Maremma",
                             "Ciacci Piccolomini Brunello di Montalcino",
                             "Altesino Brunello di Montalcino",
                             "Altesino Montosoli",
                             "Camigliano Brunello di Montalcino",
                             "Gaja Barbaresco",
                             "Gaja Sori San Lorenzo",
                             "Gaja Sori Tildin",
                             "Marchesi di Grésy Barbaresco Martinenga",
                             "Michele Chiarlo Barolo Tortoniano",
                             "Oddero Rocche di Castiglione Barolo",
                             "Brovia Barolo Rocche dei Brovia",
                             "Alain Voge Cornas Saint-Péray",
                             "Alain Voge Les Vieilles Vignes Cornas",
                             "Domaine du Pegaü Châteauneuf-du-Pape",
                             "Domaine du Pegaü Cuvée da Capo",
                             "Domaine du Pegaü Cuvée Réservée"],
     "Italy", "Piedmont / Tuscany", "red"),

    # ── Rhône Valley — specific estates ───────────────────────────────────────
    ("rhone-specific",      ["Château Rayas Châteauneuf-du-Pape",
                             "Château Rayas Pignan",
                             "Château de Fonsalette Côtes du Rhône",
                             "Auguste Clape Cornas",
                             "Auguste Clape Saint-Péray",
                             "Domaine Jean-Louis Chave Hermitage",
                             "Domaine Jean-Louis Chave Mon Coeur",
                             "Domaine Jean-Louis Chave Saint-Joseph",
                             "Château Beaucastel Hommage à Jacques Perrin",
                             "Château Beaucastel Châteauneuf-du-Pape Blanc",
                             "Vieux Télégraphe La Crau",
                             "Domaine Charvin Châteauneuf-du-Pape",
                             "Domaine Roger Sabon Le Secret des Sabon",
                             "Domaine Charvin Côtes du Rhône",
                             "Château Grillet Viognier",
                             "Yves Cuilleron La Petite Côte Condrieu",
                             "Yves Cuilleron Cavanos Saint-Joseph",
                             "Clos Mont Olivet Châteauneuf-du-Pape",
                             "Domaine du Gour de Chaulé Gigondas"],
     "France", "Rhône Valley", "red"),

    # ── Bordeaux — rare & heritage (gaps from deep wine-list analysis) ─────────
    ("bordeaux-rare",       ["Château Gilette Crème de Tête Sauternes",
                             "Château d'Yquem Sauternes",
                             "Château de Fargues Lur-Saluces Sauternes",
                             "Château Rieussec Premier Cru Sauternes",
                             "Château Guiraud Premier Cru Sauternes",
                             "Château La Tour Blanche Bommes",
                             "Château Coutet Premier Cru Barsac",
                             "Château Trotanoy Pomerol",
                             "Château L'Évangile Pomerol",
                             "Château Certan de May Pomerol",
                             "Château La Conseillante Pomerol",
                             "Château Canon Saint-Émilion Grand Cru Classé",
                             "Château Larcis-Ducasse Saint-Émilion",
                             "Château Cos d'Estournel Saint-Estèphe",
                             "Château Calon-Ségur Saint-Estèphe",
                             "Château Léoville-Poyferré Saint-Julien",
                             "Château Beychevelle Saint-Julien",
                             "Château Gruaud Larose Saint-Julien",
                             "Château Prieuré-Lichine Margaux",
                             "Château Rauzan-Ségla Margaux",
                             "Château Kirwan Margaux",
                             "Château Haut-Bailly Pessac-Léognan",
                             "Château Carbonnieux Pessac-Léognan",
                             "Château de Fieuzal Pessac-Léognan",
                             "Château Malartic-Lagravière Pessac-Léognan",
                             "Y d'Yquem Bordeaux Sec"],
     "France", "Bordeaux", "red"),

    # ── Loire Valley — specific estates ───────────────────────────────────────
    ("loire-specific",      ["Domaine Huet Vouvray Clos du Bourg",
                             "Domaine Huet Vouvray Le Haut-Lieu",
                             "Domaine Huet Vouvray Le Mont",
                             "Domaine Huet Cuvée Constance",
                             "François Cotat Les Monts Damnés Sancerre",
                             "François Cotat La Grande Côte Sancerre",
                             "Pascal Cotat Sancerre",
                             "Domaine Vacheron Sancerre",
                             "Domaine Vacheron Les Romains",
                             "Lucien Crochet Le Chêne Marchand Sancerre",
                             "Domaine Didier Dagueneau Silex Pouilly-Fumé",
                             "Domaine Didier Dagueneau Pur Sang",
                             "Serge Dagueneau et Filles Pouilly-Fumé",
                             "Domaine Delaporte Sancerre",
                             "Domaine Laporte Le Rochoy Sancerre",
                             "Henri Bourgeois La Côte des Mont Damnés",
                             "Henri Bourgeois La Demoiselle",
                             "Domaine du Collier Saumur",
                             "Foreau Domaine Clos Naudin Vouvray",
                             "Moulin Touchais Coteaux du Layon"],
     "France", "Loire Valley", "white"),

    # ── Alsace — specific estates ──────────────────────────────────────────────
    ("alsace-specific",     ["Domaine Weinbach Riesling Schlossberg Grand Cru",
                             "Domaine Weinbach Cuvée Théo",
                             "Domaine Weinbach Pinot Gris Altenbourg",
                             "Domaine Weinbach Gewurztraminer Furstentum",
                             "Trimbach Cuvée Frédéric Emile Riesling",
                             "Trimbach Clos Sainte-Hune Riesling",
                             "Trimbach Gewurztraminer Seigneurs de Ribeaupierre",
                             "Zind-Humbrecht Clos Windsbuhl",
                             "Zind-Humbrecht Rangen de Thann Grand Cru",
                             "Meyer-Fonné Pinot Gris Grand Cru",
                             "Roland Schmitt Altenberg de Bergbieten",
                             "Domaine Marcel Deiss Mambourg Grand Cru",
                             "Hugel Alsace Riesling Jubilee",
                             "Ostertag Riesling Alsace"],
     "France", "Alsace", "white"),

    # ── Sauternes & Dessert — specific estates ─────────────────────────────────
    ("dessert-wine-specific",
                            ["Château d'Yquem Premier Cru Supérieur",
                             "Château Gilette Crème de Tête",
                             "Château Rieussec Premier Cru",
                             "Château Rabaud-Promis Premier Cru Sauternes",
                             "Château La Tour Blanche Premier Cru Bommes",
                             "Château Coutet Premier Cru Barsac",
                             "Château Guiraud Premier Cru Sauternes",
                             "Domaine Huet Vouvray Moelleux",
                             "Disznókő Tokaji Aszú 5 Puttonyos",
                             "Dönnhoff Auslese Goldkapsel",
                             "Keller Westhofer Abts E Auslese",
                             "Château de Fargues Sauternes",
                             "Y d'Yquem Dry Sauternes",
                             "Domaine Fontanel Rivesaltes Ambré",
                             "Didier Dagueneau Jardins de Babylone Jurançon"],
     "France", "Sauternes", "white"),

    # ── California sparkling & prestige bubbles (Ad Hoc / Napa list gaps) ─────
    ("california-sparkling-specific",
                            ["Schramsberg Blanc de Blancs North Coast",
                             "Schramsberg Brut Rosé Mirabelle",
                             "Schramsberg Reserve Brut North Coast",
                             "Schramsberg J. Schram",
                             "Domaine Carneros Le Rêve Blanc de Blancs",
                             "Domaine Carneros Brut Carneros",
                             "Roederer Estate L'Ermitage Anderson Valley",
                             "Argyle Brut Extended Tirage Willamette Valley",
                             "Iron Horse Wedding Cuvée",
                             "Gloria Ferrer Carneros Cuvée",
                             "Caraccioli Cellars Brut Santa Lucia",
                             "Modicum Blanc de Blancs North Coast"],
     "USA", "California", "sparkling"),

    # ── Napa Valley — specific mid-tier & boutique (gaps from Ad Hoc list) ────
    ("napa-boutique-specific",
                            ["Ghost Block Estate Cabernet Oakville",
                             "Ghost Block Sauvignon Blanc Yountville",
                             "Kenzo Estate Rindo Cabernet Napa Valley",
                             "Kenzo Estate Asatsuyu Sauvignon Blanc",
                             "Amuse Bouche Red Blend Rutherford",
                             "Nickel & Nickel Sullenger Vineyard Cabernet",
                             "Nickel & Nickel Quarry Vineyard Cabernet",
                             "The Mascot Napa Valley Cabernet",
                             "Sullivan Coeur de Vigne Napa",
                             "Larkin Cabernet Franc Napa Valley",
                             "Mayacamas Vineyards Merlot Mt Veeder",
                             "Mayacamas Cabernet Sauvignon Mt Veeder",
                             "Tres Sabores Zinfandel Rutherford",
                             "Tres Sabores Que Sueño Cabernet",
                             "Hestan Cabernet Sauvignon Napa Valley",
                             "Stag's Leap Wine Cellars Karia Chardonnay",
                             "Dominus Napanook Napa Valley",
                             "Kenneth & Raymond Hyde Vineyard Carneros",
                             "Heitz Cellar Cabernet Sauvignon Napa",
                             "Heitz Cellar Martha's Vineyard",
                             "Mt. Brave Cabernet Merlot Mt Veeder",
                             "Long Meadow Ranch Cabernet Napa",
                             "Long Shadows Feather Columbia Valley",
                             "Storybook Mountain Bottled Poetry Zinfandel",
                             "Storybook Mountain Mayacamas Range Zinfandel",
                             "Frog's Leap Merlot Rutherford Napa",
                             "Frog's Leap Cabernet Sauvignon Napa",
                             "Bedrock Wine Co Cabernet Sonoma",
                             "Bedrock Wine Co Old Vine Zinfandel Sonoma",
                             "Seghesio Sonoma Zinfandel",
                             "Seghesio Home Ranch Zinfandel",
                             "Hartford Court Old Vine Zinfandel",
                             "Salty Goats Fort Ross-Seaview Pinot Noir"],
     "USA", "California", "red"),

    # ── Sonoma Coast & Santa Cruz — boutique Pinot gaps ───────────────────────
    ("sonoma-santa-cruz-pinot",
                            ["Scribe Winery Pinot Noir Carneros",
                             "Scribe Estate Pinot Noir Sonoma",
                             "Domaine Eden Pinot Noir Santa Cruz Mountains",
                             "Olivia Brion Pinot Noir Santa Cruz Mountains",
                             "Ceritas Pinot Noir Fort Ross-Seaview",
                             "Salty Goats Pinot Noir Fort Ross-Seaview",
                             "Hanzell Pinot Noir Sonoma Valley",
                             "Hanzell Sebella Chardonnay",
                             "Hanzell Estate Chardonnay Sonoma",
                             "Kerr Cellars Chardonnay Sonoma Coast",
                             "Paul Hobbs Lindsay Estate Pinot Noir",
                             "Paul Hobbs Russian River Valley Pinot Noir",
                             "Richard G. Peterson Santa Lucia Highlands",
                             "Cep Hopkins Ranch Rosé Russian River",
                             "Cep Syrah Sonoma Coast",
                             "Ramey Syrah Sonoma Coast",
                             "Ramey Cabernet Sauvignon Napa Valley",
                             "Ramey Hyde Vineyard Chardonnay"],
     "USA", "California", "red"),

    # ── Burgundy négociants & village specialists (Ad Hoc list gaps) ──────────
    ("burgundy-negociant-specific",
                            ["Frédéric Magnien Bourgogne Rouge",
                             "Frédéric Magnien Gevrey-Chambertin",
                             "Frédéric Magnien Morey-Saint-Denis",
                             "Pierre Girardin Eclat de Calcaire Bourgogne",
                             "Pierre Girardin Meursault",
                             "Pierre Girardin Puligny-Montrachet",
                             "Domaine Nudant Jean-René Volnay Premier Cru",
                             "Domaine Nudant Aloxe-Corton",
                             "Domaine Nudant Corton-Charlemagne",
                             "Vincent Girardin Santenay Premier Cru",
                             "Vincent Girardin Meursault Vieilles Vignes",
                             "Vincent Girardin Puligny-Montrachet",
                             "Domaine Parigot Meursault",
                             "Domaine Parigot Volnay",
                             "Domaine Parigot Pommard",
                             "Chanson Père et Fils Beaune Premier Cru",
                             "Joseph Drouhin Beaune Clos des Mouches",
                             "Louis Jadot Gevrey-Chambertin",
                             "Maison Champy Beaune",
                             "Pascal Jolivet Sancerre"],
     "France", "Burgundy", "red"),

    # ── Bordeaux mid-tier & second wines (gaps from Ad Hoc list) ──────────────
    ("bordeaux-mid-specific",
                            ["Château Cantemerle Haut-Médoc Grand Cru Classé",
                             "Château du Taillan Haut-Médoc Cru Bourgeois",
                             "Château de Pez Saint-Estèphe",
                             "Château Lassègue Saint-Émilion Grand Cru Classé",
                             "Le Petit Ducru de Ducru-Beaucaillou Saint-Julien",
                             "Château Haut-Beauséjour Saint-Estèphe",
                             "Château Moulin de Tricot Haut-Médoc",
                             "Croix Canon Saint-Émilion",
                             "Château Haut Segottes Saint-Émilion Grand Cru",
                             "Château Larrivet Haut-Brion Pessac-Léognan",
                             "Château La Croix du Gay Pomerol",
                             "Château Beauregard Pomerol"],
     "France", "Bordeaux", "red"),

    # ── Italy mid-tier specific (gaps from Ad Hoc list) ───────────────────────
    ("italy-mid-specific",  ["Damilano Lecinquevigne Barolo",
                             "Damilano Barolo Cannubi",
                             "Produttori del Barbaresco Barbaresco",
                             "Produttori del Barbaresco Riserva",
                             "Il Poggione Brunello di Montalcino",
                             "Il Poggione Rosso di Montalcino",
                             "Tenuta di Arceno Chianti Classico Riserva",
                             "Tenuta di Arceno Arcanum",
                             "Lavau Châteauneuf du Pape",
                             "Domaine de Cristia Châteauneuf du Pape",
                             "Zenato Amarone della Valpolicella",
                             "Zenato Lugana Sergio Zenato Riserva",
                             "Cascinetta Vietti Moscato d'Asti",
                             "Vietti Barolo Castiglione",
                             "Oddero Barolo Villero"],
     "Italy", "Piedmont / Tuscany", "red"),

    # ── Spain mid-tier specific (gaps from Ad Hoc/Acquerello lists) ───────────
    ("spain-mid-specific",  ["Peter Sisseck PSI Ribera del Duero",
                             "Peter Sisseck Dominio de Pingus",
                             "Alvaro Palacios Les Terrasses Priorat",
                             "Alvaro Palacios L'Ermita Priorat",
                             "López de Heredia Viña Tondonia Reserva",
                             "López de Heredia Viña Bosconia Reserva",
                             "Numanthia Termes Toro",
                             "Numanthia Toro",
                             "Descendientes de J. Palacios Corullón Bierzo",
                             "Raúl Pérez Ultreia Bierzo Godello"],
     "Spain", "Rioja / Ribera / Priorat", "red"),

    # ── Champagne — additional grower & mid-tier gaps ─────────────────────────
    ("champagne-grower-extra",
                            ["Henri Billiot Fils Rosé Grand Cru Ambonnay",
                             "Henri Billiot Fils Cuvée Laetitia",
                             "Forget-Chemin Rosé Premier Cru Champagne",
                             "Forget-Chemin Extra Brut Premier Cru",
                             "Sanchez Le Guédard Mes Trois Terroirs",
                             "Pierre Peters Blanc de Blancs Le Mesnil",
                             "Pierre Peters Cuvée de Réserve",
                             "Bérêche et Fils Réserve Brut",
                             "Bérêche Reflet d'Antan Solera",
                             "Dehours et Fils Grande Réserve",
                             "Laherte Frères Blanc de Blancs",
                             "Gaston Chiquet Blanc de Blancs",
                             "Ruinart Blanc de Blancs Brut",
                             "Ruinart Brut Rosé",
                             "Alfred Gratien Brut Reserve"],
     "France", "Champagne", "sparkling"),

    # ── Fortified & dessert wines (Madeira, Port, Sauternes gaps) ─────────────
    ("fortified-specific",  ["Rare Wine Co Bual Boston Madeira",
                             "Rare Wine Co New York Malmsey Madeira",
                             "Rare Wine Co Charleston Sercial Madeira",
                             "Rare Wine Co Savannah Verdelho Madeira",
                             "Barbeito Ribeiro Real Madeira",
                             "D'Oliveiras Verdelho Madeira",
                             "Graham's Tawny Port 10 Year",
                             "Graham's LBV Port",
                             "Taylor Fladgate 20 Year Tawny",
                             "Niepoort Colheita Tawny Port",
                             "Château Le Tertre du Bosquet Sauternes",
                             "El Maestro Sierra Palo Cortado Jerez",
                             "Lustau Almacenista Oloroso"],
     "Portugal", "Douro / Madeira", "fortified"),
]


# ──────────────────────────────────────────────────────────────────────────────
# Parsing helpers
# ──────────────────────────────────────────────────────────────────────────────

def _slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def _parse_explore_page(html: str, region_label: str, country: str, wine_type: str) -> list[dict]:
    """
    Parse Vivino search results HTML and return a list of wine dicts.

    Vivino's SSR HTML (when Playwright renders it) includes:
      - JSON-LD ItemList / Product blocks
      - Inline data patterns in rendered text
    """
    import json as _json

    wines: list[dict] = []
    now = datetime.now(timezone.utc).isoformat()

    # --- JSON-LD ---
    ld_blocks = re.findall(
        r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>',
        html,
        re.DOTALL | re.IGNORECASE,
    )
    for block in ld_blocks:
        try:
            data = _json.loads(block)
        except Exception:
            continue

        items = []
        if isinstance(data, dict) and data.get("@type") == "ItemList":
            items = data.get("itemListElement", [])
        elif isinstance(data, dict) and data.get("@type") in ("Product", "Wine"):
            items = [data]
        elif isinstance(data, list):
            items = data

        for item in items:
            name = (item.get("name") or "").strip()
            url = item.get("url") or item.get("@id") or ""
            offers = item.get("offers") or {}
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            price = offers.get("price") or offers.get("lowPrice")
            rating_agg = item.get("aggregateRating") or {}
            rating = rating_agg.get("ratingValue")
            rating_count = rating_agg.get("reviewCount") or rating_agg.get("ratingCount")

            # Extract vivino wine ID from URL
            vivino_id = ""
            m = re.search(r"/wines/(\d+)", url)
            if m:
                vivino_id = m.group(1)

            # Extract vintage from name
            vintage_match = re.search(r"\b(19|20)\d{2}\b", name)
            vintage = int(vintage_match.group()) if vintage_match else None

            # Split producer from wine name (Vivino usually shows "Producer Name")
            producer = _extract_producer_heuristic(name, region_label)

            try:
                avg_price = float(price) if price else None
            except (ValueError, TypeError):
                avg_price = None

            try:
                rating_val = float(rating) if rating else None
                rating_cnt = int(rating_count) if rating_count else None
            except (ValueError, TypeError):
                rating_val = None
                rating_cnt = None

            if not name or not vivino_id:
                continue

            slug_id = _slugify(f"{producer} {name} {vivino_id}")

            wines.append({
                "id": slug_id,
                "name": name,
                "producer": producer,
                "region": region_label,
                "country": country,
                "appellation": region_label,
                "varietal": "",       # filled in by caller when possible
                "wine_type": wine_type,
                "avg_retail_price": avg_price or 0.0,
                "price_tier": _price_tier(avg_price or 0.0),
                "vivino_wine_id": vivino_id,
                "vivino_url": url,
                "vivino_rating": rating_val,
                "vivino_ratings_count": rating_cnt,
                "vintage": vintage,
                "discovered_at": now,
            })

    return wines


def _extract_producer_heuristic(full_name: str, region: str) -> str:
    """
    Best-effort: extract producer name from a full Vivino wine title.
    e.g. "Domaine de la Romanée-Conti La Tâche 2019" → "Domaine de la Romanée-Conti"
    """
    # Remove vintage
    clean = re.sub(r"\b(19|20)\d{2}\b", "", full_name).strip()
    # Take first 1-3 meaningful tokens (up to ~25 chars)
    words = clean.split()
    # If starts with common producer prefixes, take 3 words; otherwise 2
    prefixes = {"domaine", "château", "chateau", "maison", "cave", "weingut",
                "bodegas", "tenuta", "azienda", "estate", "winery", "vineyards"}
    n = 3 if (words and words[0].lower() in prefixes) else 2
    return " ".join(words[:min(n, len(words))]).strip()


def _price_tier(price: float) -> str:
    if price <= 25:
        return "budget"
    if price <= 75:
        return "mid"
    if price <= 200:
        return "premium"
    if price <= 600:
        return "luxury"
    return "ultra"


# ──────────────────────────────────────────────────────────────────────────────
# Main scraping loop
# ──────────────────────────────────────────────────────────────────────────────

# ---------------------------------------------------------------------------
# JavaScript injected into the rendered Vivino search page.
# Collects all wine card anchors — with OR without a price — so we get
# the full catalog metadata even when price info isn't shown.
# ---------------------------------------------------------------------------
_EXTRACT_CATALOG_JS = """
() => {
    const results = [];
    const seen = new Set();

    const links = Array.from(document.querySelectorAll('a[href*="/wines/"], a[href*="/w/"]'));
    for (const link of links) {
        const url = link.href;
        if (!url || seen.has(url)) continue;
        const text = link.innerText.trim();
        if (!text || text.length < 3) continue;
        seen.add(url);

        const lines = text.split('\\n').map(l => l.trim()).filter(Boolean);
        const name = lines[0] || '';
        if (!name) continue;

        // Vivino URL contains the numeric wine ID
        const idMatch = url.match(/\\/wines\\/(\\d+)|\\/w\\/(\\d+)/);
        const vivino_id = idMatch ? (idMatch[1] || idMatch[2]) : null;
        if (!vivino_id) continue;

        // Optional price — match any currency symbol ($, €, £, etc.)
        let price = null;
        for (const line of lines) {
            const pm = line.match(/^[\\$€£¥]([\\d,]+(?:\\.\\d{1,2})?)$/) ||
                       line.match(/^([\\d,]+(?:\\.\\d{1,2})?)\\s*[\\$€£¥]$/);
            if (pm) { price = parseFloat(pm[1].replace(/,/g, '')); break; }
        }
        if (!price) {
            const parent = link.closest('div, li, article') || link.parentElement;
            if (parent) {
                const pm = (parent.innerText || '').match(/[\\$€£¥]([\\d,]+(?:\\.\\d{1,2})?)/);
                if (pm) price = parseFloat(pm[1].replace(/,/g, ''));
            }
        }

        // Optional rating
        let rating = null;
        for (const line of lines) {
            const r = parseFloat(line);
            if (r >= 1.0 && r <= 5.0 && /^[1-4]\\.[0-9]$/.test(line.trim())) {
                rating = r; break;
            }
        }

        results.push({ name, url, vivino_id, price, rating });
    }
    return results;
}
"""


async def scrape_region(
    page,
    region_key: str,
    queries: list[str],
    country: str,
    region_label: str,
    wine_type: str,
    max_per_region: int,
    existing_ids: set[str],
) -> list[dict]:
    """Scrape Vivino for one region definition and return discovered wines."""
    now = datetime.now(timezone.utc).isoformat()
    wines: list[dict] = []
    seen_vivino_ids: set[str] = set()

    for query in queries:
        if len(wines) >= max_per_region:
            break

        # Paginate up to 4 pages per query (~25 results/page)
        for page_num in range(1, 5):
            if len(wines) >= max_per_region:
                break

            url = (
                f"https://www.vivino.com/search/wines"
                f"?q={query.replace(' ', '+')}"
                f"&page={page_num}"
            )
            log.info("  → %s  (page %d)", query[:60], page_num)

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                # Wait for JS to render the wine cards
                await page.wait_for_timeout(2500)

                cards = await page.evaluate(_EXTRACT_CATALOG_JS)
                if not cards:
                    log.info("    page %d: no cards found (JS rendered nothing)", page_num)
                    break

                new_batch: list[dict] = []
                for card in cards:
                    vid = card.get("vivino_id") or ""
                    if not vid or vid in seen_vivino_ids:
                        continue
                    avg_price = card.get("price") or 0.0
                    slug_id = _slugify(f"{card['name']} {vid}")
                    if slug_id in existing_ids:
                        continue
                    producer = _extract_producer_heuristic(card["name"], region_label)
                    seen_vivino_ids.add(vid)
                    new_batch.append({
                        "id": slug_id,
                        "name": card["name"],
                        "producer": producer,
                        "region": region_label,
                        "country": country,
                        "appellation": region_label,
                        "varietal": "",
                        "wine_type": wine_type,
                        "avg_retail_price": avg_price,
                        "price_tier": _price_tier(avg_price),
                        "vivino_wine_id": vid,
                        "vivino_url": card["url"],
                        "vivino_rating": card.get("rating"),
                        "vivino_ratings_count": None,
                        "vintage": None,
                        "discovered_at": now,
                    })

                wines.extend(new_batch)
                log.info(
                    "    page %d: +%d new / %d total for region",
                    page_num, len(new_batch), len(wines),
                )

                if not new_batch:
                    break  # no new results on this page → stop paginating

            except Exception as exc:
                log.warning("  Error on '%s' page %d: %s", query, page_num, exc)
                break

            await asyncio.sleep(random.uniform(MIN_DELAY, MAX_DELAY))

    return wines[:max_per_region]


async def main(args: argparse.Namespace) -> None:
    from playwright.async_api import async_playwright

    # Load existing extended catalog
    catalog: dict[str, dict] = {}
    if _OUTPUT_PATH.exists():
        try:
            catalog = json.loads(_OUTPUT_PATH.read_text())
            log.info("Loaded %d existing extended catalog entries", len(catalog))
        except Exception as exc:
            log.warning("Could not load existing catalog: %s", exc)

    # Existing IDs (both base catalog and extended catalog)
    existing_ids = set(WINE_CATALOG_BY_ID.keys()) | set(catalog.keys())

    # Filter regions if --regions specified
    regions_to_process = REGION_QUERIES
    if args.regions:
        wanted = set(args.regions)
        regions_to_process = [r for r in REGION_QUERIES if r[0] in wanted]
        if not regions_to_process:
            log.error("No matching regions found. Available: %s",
                      [r[0] for r in REGION_QUERIES])
            return

    log.info(
        "Building extended catalog: %d region definitions, max %d per region",
        len(regions_to_process), args.max,
    )

    start = time.monotonic()
    total_added = 0

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = await browser.new_context(
            user_agent=USER_AGENT,
            locale="en-US",
            timezone_id="America/Los_Angeles",
            viewport={"width": 1280, "height": 900},
        )
        page = await context.new_page()
        await page.route(
            "**/*.{png,jpg,gif,webp,svg,woff,woff2,ttf}",
            lambda r: r.abort(),
        )

        for region_key, queries, country, region_label, wine_type in regions_to_process:
            log.info(
                "\n[%s] Scraping %d queries...", region_key, len(queries),
            )

            if args.resume:
                region_existing = sum(
                    1 for v in catalog.values() if v.get("region") == region_label
                )
                if region_existing >= args.max:
                    log.info("  → already have %d wines, skipping", region_existing)
                    continue

            wines = await scrape_region(
                page, region_key, queries, country, region_label, wine_type,
                args.max, existing_ids,
            )

            for w in wines:
                catalog[w["id"]] = w
                existing_ids.add(w["id"])

            total_added += len(wines)
            log.info("  [%s] Added %d wines (catalog total: %d)", region_key, len(wines), len(catalog))

            # Save after every region in case of interruption
            _OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
            _OUTPUT_PATH.write_text(json.dumps(catalog, indent=2, sort_keys=True))

        await browser.close()

    elapsed = time.monotonic() - start
    log.info(
        "\n"
        "═══════════════════════════════════════\n"
        "  Catalog build complete\n"
        "  New wines added:  %d\n"
        "  Total in catalog: %d\n"
        "  Runtime:          %.1f min\n"
        "═══════════════════════════════════════",
        total_added, len(catalog), elapsed / 60,
    )
    log.info("Saved to %s", _OUTPUT_PATH)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Expand wine catalog by scraping Vivino by region"
    )
    parser.add_argument(
        "--max", type=int, default=300, metavar="N",
        help="Max wines to add per region definition (default 300)",
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Skip regions that already have enough entries in the catalog",
    )
    parser.add_argument(
        "--regions", nargs="+", metavar="REGION_KEY",
        help="Only scrape specific region keys (e.g. bordeaux-left-bank napa-cabernet)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(main(parse_args()))
