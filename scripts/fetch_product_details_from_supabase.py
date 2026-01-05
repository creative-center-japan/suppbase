import os
import requests
from supabase import create_client

# ===== ENV =====
KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]
MAX_PRODUCTS = int(os.environ.get("MAX_PRODUCTS", "20"))

# ===== CONST =====
DOMAIN_ID = 5
API_URL = "https://api.keepa.com/product"
IMG_BASE = "https://images-na.ssl-images-amazon.com"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ===== ASIN 取得（rank 不使用）=====
res = (
    supabase.table("tracked_asins")
    .select("asin")
    .order("asin")
    .limit(MAX_PRODUCTS)
    .execute()
)

asins = [r["asin"] for r in (res.data or [])]

if not asins:
    print("[SKIP] no tracked asins")
    raise SystemExit(0)

# ===== Keepa API =====
r = requests.get(
    API_URL,
    params={
        "key": KEEPA_API_KEY,
        "domain": DOMAIN_ID,
        "asin": ",".join(asins),
        "stats": 180,
        "update": -1,
        "history": 0,
    },
    timeout=60,
)

if r.status_code == 429:
    print("[429] rate limited")
    raise SystemExit(2)

r.raise_for_status()

products = r.json().get("products", [])
if not products:
    print("[SKIP] no products from keepa")
    raise SystemExit(0)

rows = []

for p in products:
    stats = p.get("stats") or {}
    price = stats.get("buyBoxPrice")

    # ===== image 判定 =====
    image_url = None
    img_csv = p.get("imagesCSV")

    if img_csv:
        first = img_csv.split(",")[0]
        if first and not any(
            k in first.lower()
            for k in ["noimage", "no-image", "placeholder"]
        ):
            image_url = f"{IMG_BASE}{first}"

    rows.append({
        "asin": p.get("asin"),
        "title": p.get("title"),
        "brand": p.get("brand"),
        "imageurl": image_url,
        "price": price // 100 if isinstance(price, int) else None,
        "rating": p.get("rating"),
        "reviewcount": p.get("reviewCount"),
        "score": int(
            (p.get("rating") or 0) * 20
            + min(p.get("reviewCount") or 0, 500)
        ),
    })

supabase.table("products").upsert(rows).execute()

print(f"[OK] updated {len(rows)} products")
