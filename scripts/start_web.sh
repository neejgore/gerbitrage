#!/usr/bin/env bash
# Web service startup script
# Runs on Railway (and locally via docker run) to start the FastAPI app.
set -euo pipefail

DATA_DIR="/app/app/data"
SEED_DIR="/app/seed_data"

# ── Seed / merge data on every deploy ────────────────────────────────────────
# JSON cache files: merge seed into volume so we never lose worker-written
# entries, but the volume always has at least everything in the seed.
# Non-JSON files (wine_catalog.py): copy only if missing or tiny.
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
                # Merge: seed entries that are missing from the volume file
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
        # Update if seed has a corrected price (avg_price differs by >1%)
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

echo "[web] Starting background pricing worker…"
bash scripts/start_worker.sh 2>&1 | sed 's/^/[worker] /' &
echo "[web] Worker PID: $!"

echo "[web] Starting Gerbitrage API on port ${PORT:-8000}…"
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT:-8000}" \
    --workers 1 \
    --log-level info
