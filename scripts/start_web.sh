#!/usr/bin/env bash
# Web service startup script
# Runs on Railway (and locally via docker run) to start the FastAPI app.
set -euo pipefail

DATA_DIR="/app/app/data"
SEED_DIR="/app/seed_data"

# ── Seed the data volume on first deploy ──────────────────────────────────────
# If the mounted volume is empty (or the key cache file is missing / tiny),
# copy the baked-in seed files so the app has baseline data immediately.
if [ -d "$SEED_DIR" ]; then
    for f in "$SEED_DIR"/*.json "$SEED_DIR"/*.py; do
        [ -f "$f" ] || continue
        fname=$(basename "$f")
        dest="$DATA_DIR/$fname"
        if [ ! -f "$dest" ] || [ "$(wc -c < "$dest")" -lt 50 ]; then
            echo "[init] Seeding $fname from seed_data…"
            cp "$f" "$dest"
        fi
    done
fi

echo "[web] Starting background pricing worker…"
bash scripts/start_worker.sh >> /tmp/worker.log 2>&1 &
echo "[web] Worker PID: $!"

echo "[web] Starting Gerbitrage API on port ${PORT:-8000}…"
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --workers 1 \
    --log-level info
