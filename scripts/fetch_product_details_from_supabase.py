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

# ===== Keepa / Plan20 設定 =====
DOMAIN_ID = 5
API_URL = "https://api.keepa.com/product"

BATCH_SIZE = 10          # 10 ASIN / request
SLEEP_SEC = 30           # 30秒 → 20 tokens / 分
MAX_ASINS_PER_RUN = 100  # 1回の実行上限

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

rows = []
now = datetime.now(timezone.utc).isoformat()

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
            "update": 1,   # ★ 強制更新（Plan20なので件数制限で安全）
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

        buyboxprice = stats.get("buyBoxPrice")
        rating = stats.get("rating") or p.get("rating")
        reviewcount = stats.get("reviewCount") or p.get("reviewCount")

        # BuyBox未確定は除外（ランキング母集団に入れない）
        if not buyboxprice or buyboxprice <= 0:
            continue

        score = int((rating or 0) * 20 + min(reviewcount or 0, 500))

        rows.append({
            "asin": p.get("asin"),
            "title": p.get("title"),
            "brand": p.get("brand"),
            "buyboxprice": buyboxprice,
            "rating": rating,
            "reviewcount": reviewcount,
            "score": score,
            "updated_at": now,
        })

    safe_sleep(SLEEP_SEC)

if rows:
    supabase.table("products").upsert(rows).execute()
    print(f"[OK] upserted {len(rows)} products")
else:
    print("[WARN] no valid BuyBox products")
