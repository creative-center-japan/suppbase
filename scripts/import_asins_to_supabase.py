import json
import os
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]

ASIN_FILE = os.environ.get("ASIN_FILE")
CATEGORY = os.environ.get("CATEGORY")

if not ASIN_FILE:
    print("[ERROR] ASIN_FILE not set")
    raise SystemExit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ===== JSON 読み込み =====
if not os.path.exists(ASIN_FILE):
    print(f"[ERROR] {ASIN_FILE} not found")
    raise SystemExit(1)

with open(ASIN_FILE, "r", encoding="utf-8") as f:
    asins = json.load(f)

if not asins:
    print("[SKIP] no asins")
    raise SystemExit(0)

# ===== tracked_asins に upsert =====
rows = []
for asin in asins:
    if not isinstance(asin, str):
        continue
    rows.append({
        "asin": asin,
        "category": CATEGORY,
    })

if not rows:
    print("[SKIP] no valid asins")
    raise SystemExit(0)

supabase.table("tracked_asins").upsert(
    rows,
    on_conflict="asin"
).execute()

print(f"[OK] imported {len(rows)} asins from {ASIN_FILE}")
