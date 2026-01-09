import os
import time
import random
import requests
from datetime import datetime, timezone
from supabase import create_client

# ===== ENV =====
KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]

# ===== Keepa 設定 =====
DOMAIN_ID = 5  # Amazon.co.jp
API_URL = "https://api.keepa.com/product"

BATCH_SIZE = 10
SLEEP_SEC = 30
MAX_ASINS_PER_RUN = 100

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def safe_sleep(sec):
    time.sleep(sec + random.uniform(0, 3))

# ===== 対象 ASIN 取得 =====
res = (
    supabase.table("tracked_asins")
    .select("asin")
    .eq("is_active", True)
    .order("last_seen_at", desc=True)
    .limit(MAX_ASINS_PER_RUN)
    .execute()
)

asins = [r["asin"] for r in (res.data or [])]

if not asins:
    print("[SKIP] no tracked asins")
    raise SystemExit(0)

now = datetime.now(timezone.utc).isoformat()
rows = []

# ===== Keepa fetch =====
for i in range(0, len(asins), BATCH_SIZE):
    batch = asins[i:i + BATCH_SIZE]

    r = requests.get(
        API_URL,
        params={
            "key": KEEPA_API_KEY,
            "domain": DOMAIN_ID,
            "asin": ",".join(batch),
            "stats": 180,
            "update": 1,
            "history": 0,
        },
        timeout=60,
    )

    if r.status_code == 429:
        print("[429] rate limited → wait 60s")
        safe_sleep(60)
        continue

    r.raise_for_status()
    products = r.json().get("products", [])

    for p in products:
        stats = p.get("stats") or {}

        rows.append({
            "asin": p.get("asin"),
            "buybox_price": stats.get("buyBoxPrice"),      # NULL OK
            "sales_rank": p.get("salesRank")
                if isinstance(p.get("salesRank"), int) else None,
            "review_count": stats.get("reviewCount"),
            "rating": stats.get("rating"),
            "captured_at": now,
        })

    safe_sleep(SLEEP_SEC)

# ===== INSERT =====
if rows:
    supabase.table("product_snapshots").insert(rows).execute()
    print(f"[OK] inserted {len(rows)} snapshots")
else:
    print("[WARN] no snapshot rows generated")
