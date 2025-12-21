# scripts/register_asins_from_deal.py
import os
import json
from datetime import datetime, timezone
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]

ASIN_FILE = os.environ.get("ASIN_FILE")
CATEGORY = os.environ.get("ASIN_CATEGORY", "unknown")
SOURCE = "deal"

supa = create_client(SUPABASE_URL, SUPABASE_KEY)
now = datetime.now(timezone.utc).isoformat()

with open(ASIN_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

# ★ list / dict 両対応
if isinstance(data, list):
    asins = data
elif isinstance(data, dict):
    asins = data.get("asins", [])
else:
    asins = []

if not asins:
    print("⚠ No ASINs found in ASIN_FILE (skip registration)")
    raise SystemExit(0)

rows = [{
    "asin": asin,
    "category": CATEGORY,
    "source": SOURCE,
    "first_seen_at": now,
    "last_seen_at": now,
    "is_active": True,
} for asin in asins]

supa.table("tracked_asins").upsert(
    rows,
    on_conflict="asin",
    returning="minimal"
).execute()

print(f"✓ registered {len(rows)} ASINs into tracked_asins")
