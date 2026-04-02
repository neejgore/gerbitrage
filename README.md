# Gerbitrage – Wine Pricing Intelligence API

Identify wines from menu text, benchmark retail pricing across multiple sources, estimate wholesale cost, and evaluate whether a restaurant's markup is fair.

---

## Architecture

```
gerbitrage/
├── app/
│   ├── main.py                  FastAPI application factory
│   ├── config.py                Settings (pydantic-settings, .env)
│   ├── database.py              Async SQLAlchemy engine + session
│   │
│   ├── models/
│   │   ├── wine.py              ORM: wines table
│   │   └── pricing.py           ORM: wine_pricing + analysis_log tables
│   │
│   ├── schemas/
│   │   ├── wine.py              Pydantic: WineBase, WineDetail, WineSearchResult
│   │   ├── pricing.py           Pydantic: PricingBreakdown, WinePricingResponse
│   │   └── analysis.py          Pydantic: AnalyzeRequest/Response, MarkupAnalysis
│   │
│   ├── data/
│   │   └── wine_catalog.py      In-memory catalog: 120+ wines, prices, aliases
│   │
│   ├── services/
│   │   ├── text_parser.py       NLP/regex: extract vintage, producer, region, varietal
│   │   ├── wine_identifier.py   Fuzzy-match engine (RapidFuzz multi-factor scoring)
│   │   ├── pricing_aggregator.py Fan-out to all providers, merge + cache results
│   │   ├── markup_analyzer.py   Fairness scoring, verdicts, flags, insight text
│   │   └── cache.py             Redis async cache (graceful no-op when unavailable)
│   │
│   ├── integrations/
│   │   ├── base.py              BasePricingProvider ABC + mock utility
│   │   ├── wine_searcher.py     Wine-Searcher API (mock when key absent)
│   │   ├── total_wine.py        Total Wine (mock placeholder)
│   │   └── wine_com.py          Wine.com API (mock when key absent)
│   │
│   └── api/routes/
│       ├── analyze.py           POST /analyze, POST /analyze/batch
│       ├── search.py            GET /search
│       └── pricing.py           GET /wine/{id}/pricing
│
├── alembic/                     Database migrations
├── tests/                       pytest test suite
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

---

## Quick Start

### With Docker (recommended)

```bash
cp .env.example .env
docker compose up --build
```

The API is available at **http://localhost:8000**.  
Interactive docs: **http://localhost:8000/docs**

### Local development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

# Copy and edit the env file (database + redis can be local or skipped)
cp .env.example .env

# Run without a database (pricing + identification work out of the box)
USE_MOCK_PRICING=true uvicorn app.main:app --reload
```

### Run migrations

```bash
alembic upgrade head
```

---

## API Endpoints

### `POST /analyze`

Identify a wine from menu text and evaluate markup.

```json
// Request
{
  "menu_text": "2019 Chateau Margaux, Margaux",
  "menu_price": 450.00,
  "venue_id": "restaurant-abc"
}

// Response (abbreviated)
{
  "identification": {
    "matched": true,
    "confidence": 0.97,
    "confidence_level": "very_high",
    "wine_id": "chateau-margaux",
    "name": "Chateau Margaux",
    "vintage": 2019,
    "region": "Margaux, Bordeaux, France",
    "varietal": "Cabernet Sauvignon blend",
    "wine_type": "red",
    "avg_retail_price": 890.0,
    "price_tier": "ultra",
    "alternatives": [ … ],
    "parsed_components": { "vintage": 2019, "producer": "Chateau Margaux", … }
  },
  "pricing": {
    "avg_retail": 920.00,
    "min_retail": 780.00,
    "max_retail": 1100.00,
    "estimated_wholesale": 570.40,
    "sources": [ { "name": "Wine-Searcher", "avg_price": 915, … } ]
  },
  "markup_analysis": {
    "menu_price": 450.0,
    "avg_retail": 920.0,
    "estimated_wholesale": 570.40,
    "retail_multiple": 0.489,
    "wholesale_multiple": 0.789,
    "industry_standard_wholesale_range": [1.5, 2.5],
    "fairness_score": 100,
    "verdict": "exceptional_value",
    "verdict_label": "Exceptional Value",
    "flags": ["below_market", "below_retail"],
    "insight": "At $450, this wine is priced significantly below both its ~$570 estimated wholesale and ~$920 average retail. Extraordinary value."
  },
  "metadata": { "analyzed_at": "…", "processing_time_ms": 142 }
}
```

### `POST /analyze/batch`

Analyse up to 50 wine entries in one request (processed concurrently).

```json
{
  "items": [
    { "menu_text": "Dom Perignon 2013", "menu_price": 350 },
    { "menu_text": "Kim Crawford Sauvignon Blanc", "menu_price": 55 }
  ],
  "venue_id": "restaurant-abc"
}
```

### `GET /search?q=opus+one&limit=5`

Free-text search over the catalog with match scores.

| Parameter   | Type    | Default | Description                         |
|-------------|---------|---------|-------------------------------------|
| `q`         | string  | —       | Search query (≥ 2 chars)            |
| `limit`     | integer | 10      | Max results (1–50)                  |
| `wine_type` | string  | —       | red / white / rose / sparkling etc. |
| `country`   | string  | —       | Filter by country                   |

### `GET /wine/{id}/pricing?vintage=2019`

Fetch current market pricing and wholesale estimate for a catalog wine.

---

## Wine Identification

The identification engine runs a multi-stage pipeline:

1. **Text parsing** (`text_parser.py`)
   - Strip prices, volume annotations
   - Extract vintage via regex (`1950–2030`)
   - Detect NV (non-vintage) for Champagne
   - Expand abbreviations: `Ch.` → `chateau`, `DRC` → `domaine de la romanee conti`
   - Detect region, varietal, wine type from keyword dictionaries
   - Strip diacritics and normalise

2. **Token pre-filter** (`wine_identifier.py`)
   - Build a set of significant tokens (≥ 3 chars, not stop words) from the query
   - Skip catalog entries with zero overlapping tokens (fast O(n) pass)

3. **Multi-factor fuzzy scoring** (RapidFuzz)
   - `token_sort_ratio` — 30% weight (handles word-order differences)
   - `token_set_ratio` — 25% weight (handles subset matches)
   - `partial_ratio` — 20% weight (handles abbreviated names)
   - `WRatio` — 15% weight (adaptive scorer)
   - `JaroWinkler` — 10% weight (good for short strings / typos)
   - Best alias score applied across all known alternative names
   - Structural bonuses: vintage plausibility (+4%), region match (+6%), varietal match (+3%), wine type match (+2%)

4. **Confidence levels**

| Score | Level      |
|-------|------------|
| ≥ 0.90 | very_high |
| ≥ 0.85 | high      |
| ≥ 0.65 | medium    |
| ≥ 0.45 | low       |
| < 0.45 | none      |

---

## Markup Fairness Scoring

### Wholesale estimation

| Price tier  | Retail range   | Wholesale ratio |
|-------------|----------------|-----------------|
| budget      | < $25          | 50%             |
| mid         | $25–$75        | 52%             |
| premium     | $75–$200       | 55%             |
| luxury      | $200–$600      | 58%             |
| ultra       | > $600         | 62%             |

### Industry standard markup ranges (wholesale → menu price)

| Tier    | Fair low | Fair high | Excessive |
|---------|----------|-----------|-----------|
| budget  | 2.8×     | 4.5×      | 5.5×      |
| mid     | 2.5×     | 4.0×      | 5.0×      |
| premium | 2.25×    | 3.5×      | 4.5×      |
| luxury  | 1.8×     | 3.0×      | 4.0×      |
| ultra   | 1.5×     | 2.5×      | 3.5×      |

### Fairness score (0–100) → Verdict

| Score | Verdict              |
|-------|----------------------|
| 90–100 | Exceptional Value  |
| 75–89  | Fair               |
| 55–74  | Moderate Markup    |
| 35–54  | High Markup        |
| 15–34  | Excessive Markup   |
| 0–14   | Price Gouging      |

---

## Connecting Real Pricing APIs

Set the relevant key in `.env` and set `USE_MOCK_PRICING=false`:

```env
WINE_SEARCHER_API_KEY=your_key_here
USE_MOCK_PRICING=false
```

See each integration file in `app/integrations/` for implementation notes.

---

## Testing

```bash
pip install -r requirements-dev.txt
pytest
```

No database or Redis is needed to run the test suite — the app works with mocked pricing and in-memory catalog data.

---

## Environment Variables

| Variable                     | Default                                          | Description                          |
|------------------------------|--------------------------------------------------|--------------------------------------|
| `DATABASE_URL`               | `postgresql+asyncpg://…/gerbitrage`              | Async PostgreSQL connection string   |
| `REDIS_URL`                  | `redis://localhost:6379/0`                       | Redis connection string              |
| `CACHE_TTL_SECONDS`          | `3600`                                           | Pricing cache TTL                    |
| `USE_MOCK_PRICING`           | `true`                                           | Use mock data instead of real APIs   |
| `WINE_SEARCHER_API_KEY`      | _(empty)_                                        | Wine-Searcher API key                |
| `WINE_COM_API_KEY`           | _(empty)_                                        | Wine.com API key                     |
| `HIGH_CONFIDENCE_THRESHOLD`  | `0.85`                                           | Score threshold for "high" confidence |
| `MEDIUM_CONFIDENCE_THRESHOLD`| `0.65`                                           | Score threshold for "medium"         |
| `MIN_MATCH_THRESHOLD`        | `0.45`                                           | Minimum score to return any match    |
| `MAX_BATCH_SIZE`             | `50`                                             | Max wines per batch request          |
| `DEBUG`                      | `false`                                          | Enable SQLAlchemy query logging      |
