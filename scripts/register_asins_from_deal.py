import os
import json
from datetime import datetime, timezone
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]

ASIN_FILE = os.environ.get("ASIN_FILE", "protein_asins_deals_filtered.json")
CATEGORY = os.environ.get("ASIN_CATEGORY", "protein")
SOURCE = "deal"

supa = create_client(SUPABASE_URL, SUPABASE_KEY)

now = datetime.now(timezone.utc).isoformat()

with open(ASIN_FILE, "r", encoding="utf-8") as f:
    asins = json.load(f)

if not isinstance(asins, list):
    raise RuntimeError("ASIN_FILE must be a list of ASINs")

rows = []
for asin in asins:
    rows.append({
        "asin": asin,
        "category": CATEGORY,
        "source": SOURCE,
        "first_seen_at": now,
        "last_seen_at": now,
        "is_active": True,
    })

# UPSERT（既存は last_seen_at だけ更新）
supa.table("tracked_asins").upsert(
    rows,
    on_conflict="asin",
    returning="minimal"
).execute()

print(f"✓ registered {len(rows)} ASINs into tracked_asins")
