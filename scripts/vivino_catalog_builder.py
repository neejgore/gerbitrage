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
