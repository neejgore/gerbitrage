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
updated = 0
for k, v in seed.items():
    if k not in vol:
        vol[k] = v
    else:
        seed_p = v.get("avg_price", 0) if isinstance(v, dict) else 0
        vol_p  = vol[k].get("avg_price", 0) if isinstance(vol[k], dict) else 0
        if seed_p and vol_p and abs(seed_p - vol_p) / max(vol_p, 1) > 0.01:
            vol[k] = v
            updated += 1
added = len(vol) - before
if added or updated:
    open(dest_path, "w").write(json.dumps(vol, indent=2, ensure_ascii=False))
    print(f"  merged +{added} new, {updated} updated from seed (total {len(vol)})")
else:
    print(f"  no changes from seed ({len(vol)} existing)")
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

# ── Catalog builder loop (runs independently in background) ──────────────────
# Continuously expands extended_catalog.json with new wines from Vivino.
# Runs its own loop so it doesn't wait for vintage pricing to finish.
catalog_loop() {
    while true; do
        echo "[catalog] Running catalog builder (target: 500/region)…"
        python scripts/vivino_catalog_builder.py --max 500 --resume
        echo "[catalog] Catalog cycle done. Sleeping 30 min…"
        sleep 1800
    done
}
catalog_loop &

# ── Vintage pricing loop (main loop) ─────────────────────────────────────────
# Cycle A (every run): price anything uncached — new wines from catalog builder
# Cycle B (every 30 days): refresh fine wine prices (mid-tier and above)
# Cycle C (every 14 days): refresh ultra/luxury cult wine prices
CYCLE=0
while true; do
    CYCLE=$((CYCLE + 1))
    echo "[worker] === Pricing cycle $CYCLE ==="

    # Always: price anything not yet cached
    echo "[worker] Cycle $CYCLE-A: pricing new/uncached entries…"
    python scripts/vivino_price_all.py --vintages all --skip-known

    # Every 3rd cycle (~3 hours apart = ~every 9 hours): refresh entries > 30 days
    if [ $((CYCLE % 3)) -eq 0 ]; then
        echo "[worker] Cycle $CYCLE-B: refreshing entries older than 30 days…"
        python scripts/vivino_price_all.py --vintages all --max-age-days 30
    fi

    # Every 7th cycle (~every 21 hours): also refresh ultra-luxury entries > 14 days
    if [ $((CYCLE % 7)) -eq 0 ]; then
        echo "[worker] Cycle $CYCLE-C: refreshing ultra/luxury entries older than 14 days…"
        python scripts/vivino_price_all.py \
            --ids $(python3 -c "
import sys; sys.path.insert(0,'.')
from app.data.wine_catalog import WINE_CATALOG
ids = [w.id for w in WINE_CATALOG if w.price_tier in ('ultra','luxury')]
print(' '.join(ids))
") --max-age-days 14
    fi

    echo "[worker] Pricing cycle $CYCLE done. Sleeping 1 hour…"
    sleep 3600
done
