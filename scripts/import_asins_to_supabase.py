import os, json
from datetime import datetime
from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]

ASIN_FILE = os.environ["ASIN_FILE"]
CATEGORY = os.environ["CATEGORY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

if not os.path.exists(ASIN_FILE):
    print(f"[SKIP] {ASIN_FILE} not found")
    raise SystemExit(0)

asins = json.load(open(ASIN_FILE, "r", encoding="utf-8"))
if not asins:
    print("[SKIP] no ASINs to import")
    raise SystemExit(0)

now = datetime.utcnow().isoformat()
rows = []

for idx, asin in enumerate(asins[:200]):
    rows.append({
        "asin": asin,
        "category": CATEGORY,
        "source": "best_sellers",
        "rank": idx + 1,
        "last_seen_at": now,
    })

supabase.table("tracked_asins").upsert(rows).execute()
print(f"[OK] upserted {len(rows)} tracked_asins ({CATEGORY})")
