import os
import requests
from supabase import create_client

# ========= 環境変数 =========
KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]
MAX_PRODUCTS = int(os.environ.get("MAX_PRODUCTS", "20"))

DOMAIN_ID = 5
PRODUCT_API = "https://api.keepa.com/product"

# ========= Supabase =========
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ========= 画像URL正規化（ここが肝） =========
def build_image_url(images_value: str | None) -> str | None:
    """
    Keepa の images / imagesCSV から
    正しい Amazon CDN の1枚目URLを返す
    """
    if not images_value:
        return None

    # Keepa は「;」区切り
    parts = [p.strip() for p in images_value.split(";") if p.strip()]
    if not parts:
        return None

    first = parts[0]

    # すでに完全URL
    if first.startswith("http"):
        return first

    # 相対パス対応
    if first.startswith("/images/"):
        return f"https://m.media-amazon.com{first}"
    if first.startswith("images/"):
        return f"https://m.media-amazon.com/{first}"

    return None


# ========= tracked_asins から ASIN 取得 =========
res = (
    supabase.table("tracked_asins")
    .select("asin")
    .order("rank")
    .limit(MAX_PRODUCTS)
    .execute()
)

asins = [r["asin"] for r in (res.data or [])]
if not asins:
    print("[SKIP] no tracked asins")
    raise SystemExit(0)

# ========= Keepa Product API =========
r = requests.get(
    PRODUCT_API,
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
    raise SystemExit(0)

r.raise_for_status()
products = r.json().get("products", [])

# ========= DBに入れる =========
rows = []
for p in products:
    stats = p.get("stats") or {}
    price_raw = stats.get("buyBoxPrice")

    rows.append({
        "asin": p.get("asin"),
        "title": p.get("title"),
        "brand": p.get("brand"),
        # ★ ここで正規化した1枚目だけ入れる
        "imageurl": build_image_url(
            p.get("imagesCSV") or p.get("images")
        ),
        "price": price_raw // 100 if isinstance(price_raw, int) else None,
        "rating": p.get("rating"),
        "reviewcount": p.get("reviewCount"),
        # 仮スコア（確認用）
        "score": int(
            (p.get("rating") or 0) * 20
            + min(p.get("reviewCount") or 0, 500)
        ),
    })

if rows:
    supabase.table("products").upsert(rows).execute()
    print(f"[OK] updated {len(rows)} products")
else:
    print("[SKIP] no products to update")
