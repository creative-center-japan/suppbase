import os
import time
import requests
from supabase import create_client

KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]

DOMAIN_ID = 5
API_URL = "https://api.keepa.com/product"
MAX_PRODUCTS = 200  # ← 一時的に増やす（重要）

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# 直近ASINを取得
res = (
    supabase.table("tracked_asins")
    .select("asin")
    .eq("is_active", True)
    .order("last_seen_at", desc=True)
    .limit(MAX_PRODUCTS)
    .execute()
)

asins = [r["asin"] for r in (res.data or [])]

if not asins:
    print("[SKIP] no tracked asins")
    raise SystemExit(0)

rows = []

for i in range(0, len(asins), 20):
    batch = asins[i:i + 20]

    r = requests.get(
        API_URL,
        params={
            "key": KEEPA_API_KEY,
            "domain": DOMAIN_ID,
            "asin": ",".join(batch),
            "stats": 180,
            "update": 1,   # ★ ここが最重要
            "history": 0,
        },
        timeout=60,
    )

    r.raise_for_status()
    products = r.json().get("products", [])

    for p in products:
        stats = p.get("stats") or {}

        buyboxprice = stats.get("buyBoxPrice")
        rating = stats.get("rating") or p.get("rating")
        reviewcount = stats.get("reviewCount") or p.get("reviewCount")

        # BuyBoxが無い商品は除外（ランキング母集団にしない）
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
        })

    time.sleep(2)

if not rows:
    print("[WARN] no valid BuyBox products")
    raise SystemExit(0)

supabase.table("products").upsert(rows).execute()
print(f"[OK] upserted {len(rows)} products with BuyBox")
