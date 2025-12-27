import os
import sys
import json
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]

# python export_asins.py protein 30
CATEGORY = sys.argv[1]
LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else 30

supa = create_client(SUPABASE_URL, SUPABASE_KEY)

res = (
    supa.table("tracked_asins")
    .select("asin")
    .eq("is_active", True)
    .eq("category", CATEGORY)
    .order("last_fetched_at", desc=False, nullsfirst=True)
    .limit(LIMIT)
    .execute()
)

asins = [r["asin"] for r in (res.data or [])]

outfile = f"asins_{CATEGORY}.json"
with open(outfile, "w", encoding="utf-8") as f:
    json.dump(asins, f, ensure_ascii=False, indent=2)

print(f"[OK] exported {len(asins)} ASINs -> {outfile}")
