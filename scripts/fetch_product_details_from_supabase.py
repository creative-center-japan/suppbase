# scripts/fetch_product_details_from_supabase.py

import os
import time
import requests
from supabase import create_client

# ===== ENV =====
KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]
MAX_PRODUCTS = int(os.environ.get("MAX_PRODUCTS", "40"))

# ===== CONST =====
DOMAIN_ID = 5  # Amazon.co.jp
API_URL = "https://api.keepa.com/product"
IMG_HOST = "https://images-na.ssl-images-amazon.com"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ===== image URL 正規化 =====
def normalize_image_url(images_csv):
    if not images_csv:
        return None

    first = images_csv.split(",")[0].strip()
    if not first:
        return None

    if first.startswith("http://") or first.startswith("https://"):
        return first

    if first.startswith("/images/"):
        return f"{IMG_HOST}{first}"

    return f"{IMG_HOST}/images/I/{first}"

# ===== ASIN 取得（recent-first）=====
res = (
    supabase.table("tracked_asins")
    .select("asin")
    .order("last_seen_at", desc=True)  # ★重要
    .limit(MAX_PRODUCTS)
    .execute()
)

asins = [r["asin"] for r in (res.data or [])]

if not asins:
    print("[SKIP] no tracked asins")
    raise SystemExit(0)

rows = []

# ===== Keepa fetch =====
for i in range(0, len(asins), 20):
    batch = asins[i:i + 20]

    r = requests.get(
        API_URL,
        params={
            "key": KEEPA_API_KEY,
            "domain": DOMAIN_ID,
            "asin": ",".join(batch),
            "stats": 180,
            "update": -1,
            "history": 0,
        },
        timeout=60,
    )

    if r.status_code == 429:
        print("[429] rate limited → skip batch")
        continue

    r.raise_for_status()
    products = r.json().get("products", [])

    for p in products:
        stats = p.get("stats") or {}
        price = stats.get("buyBoxPrice")

        rows.append({
            "asin": p.get("asin"),
            "title": p.get("title"),
            "brand": p.get("brand"),
            "imageurl": normalize_image_url(p.get("imagesCSV")),
            "buyboxprice": price,
            "rating": p.get("rating"),
            "reviewcount": p.get("reviewCount"),
        })

    time.sleep(2)

if not rows:
    print("[SKIP] no product rows")
    raise SystemExit(0)

supabase.table("products").upsert(rows).execute()
print(f"[OK] upserted {len(rows)} products")
