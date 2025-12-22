import os
import sys
import json
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]

CATEGORY = sys.argv[1]          # protein / supplement
LIMIT = int(sys.argv[2])        # 30 など

supa = create_client(SUPABASE_URL, SUPABASE_KEY)

res = (
    supa.table("tracked_asins")
    .select("asin")
    .eq("category", CATEGORY)
    .eq("is_active", True)
    .order("last_fetched_at", desc=False, nullsfirst=True)
    .limit(LIMIT)
    .execute()
)

asins = [r["asin"] for r in (res.data or [])]

outfile = f"asins_{CATEGORY}.json"
with open(outfile, "w", encoding="utf-8") as f:
    json.dump(asins, f, ensure_ascii=False)

print(f"[OK] exported {len(asins)} ASINs for {CATEGORY}")
