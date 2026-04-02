# ── Base: official Playwright image with Chromium pre-installed ──────────────
# This saves ~10 min of dep installation vs python:slim + manual Chromium setup.
FROM mcr.microsoft.com/playwright/python:v1.49.0-jammy

WORKDIR /app

# System deps (libpq for asyncpg in case Postgres is later enabled)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Chromium for Playwright (drivers already in base image)
RUN playwright install chromium

# ── Seed data ─────────────────────────────────────────────────────────────────
# Baked-in JSON caches used to seed the Railway volume on first deploy.
# The startup script copies these to /app/app/data only if that directory
# is empty (i.e. fresh volume mount).
RUN mkdir -p /app/seed_data
COPY app/data/wine_catalog.py         /app/seed_data/
COPY app/data/vivino_prices_cache.json /app/seed_data/
COPY app/data/extended_catalog.json   /app/seed_data/
COPY app/data/ct_wine_id_map.json     /app/seed_data/
COPY app/data/ct_prices_cache.json    /app/seed_data/

# ── Application code ──────────────────────────────────────────────────────────
COPY . .

EXPOSE 8000

CMD ["bash", "scripts/start_web.sh"]
