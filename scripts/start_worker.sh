#!/usr/bin/env bash
# Worker service startup script
# Runs as a separate Railway service to handle background scraping.
# Railway will restart this automatically if it exits.
set -euo pipefail

DATA_DIR="/app/app/data"
SEED_DIR="/app/seed_data"

# ── Seed / merge data ─────────────────────────────────────────────────────────
if [ -d "$SEED_DIR" ]; then
    for f in "$SEED_DIR"/*.json "$SEED_DIR"/*.py; do
        [ -f "$f" ] || continue
        fname=$(basename "$f")
        dest="$DATA_DIR/$fname"
        if [[ "$fname" == *.json ]]; then
            if [ ! -f "$dest" ] || [ "$(wc -c < "$dest")" -lt 50 ]; then
                echo "[init] Seeding $fname (volume empty)…"
                cp "$f" "$dest"
            else
                echo "[init] Merging $fname (seed → volume)…"
                python3 - "$f" "$dest" <<'PYEOF'
import json, sys
seed_path, dest_path = sys.argv[1], sys.argv[2]
try:
    seed = json.loads(open(seed_path).read())
    vol  = json.loads(open(dest_path).read())
except Exception as e:
    print(f"  merge skipped ({e})")
    sys.exit(0)
before = len(vol)
vol.update({k: v for k, v in seed.items() if k not in vol})
added = len(vol) - before
if added:
    open(dest_path, "w").write(json.dumps(vol, indent=2, ensure_ascii=False))
    print(f"  merged +{added} entries from seed (total {len(vol)})")
else:
    print(f"  no new entries from seed ({len(vol)} existing)")
PYEOF
            fi
        else
            if [ ! -f "$dest" ] || [ "$(wc -c < "$dest")" -lt 50 ]; then
                echo "[init] Seeding $fname from seed_data…"
                cp "$f" "$dest"
            fi
        fi
    done
fi

echo "[worker] Starting Vivino pricing worker…"

# Run the full vintage matrix first (skips already-cached entries).
# When that finishes (or on restart), loop back and pick up any new wines
# added by the catalog builder.
while true; do
    echo "[worker] Running vintage matrix (skip-known)…"
    python scripts/vivino_price_all.py --vintages all --skip-known

    echo "[worker] Running catalog builder…"
    python scripts/vivino_catalog_builder.py --max 300 --resume

    echo "[worker] Cycle complete. Sleeping 1 hour before next refresh…"
    sleep 3600
done
