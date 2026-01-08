import os
import json
from datetime import datetime, timezone
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]

ASIN_FILE = os.environ.get("ASIN_FILE")
CATEGORY = os.environ.get("ASIN_CATEGORY", "unknown")
SOURCE = "deal"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

now = datetime.now(timezone.utc).isoformat()

with open(ASIN_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

if isinstance(data, list):
    asins = data
elif isinstance(data, dict):
    asins = data.get("asins", [])
else:
    asins = []

if not asins:
    print("[SKIP] no asins in ASIN_FILE")
    raise SystemExit(0)

rows = []
for asin in asins:
    if not isinstance(asin, str):
        continue

    rows.append({
        "asin": asin,
        "category": CATEGORY,
        "source": SOURCE,
        "first_seen_at": now,
        "last_seen_at": now,
        "is_active": True,
    })

supabase.table("tracked_asins").upsert(
    rows,
    on_conflict="asin",
    returning="minimal"
).execute()

print(f"[OK] registered {len(rows)} asins with timestamp")
