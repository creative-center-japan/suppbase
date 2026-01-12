import os
import time
import requests
from datetime import datetime, timezone
from supabase import create_client

# =====================
# ENV
# =====================
KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]

DOMAIN_ID = 1  # US (amazon.com)
MAX_PER_RUN = int(os.environ.get("MAX_PER_RUN", "40"))

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
KEEPA_PRODUCT_API = "https://api.keepa.com/product"

# =====================
# Helper
# =====================
def fetch_keepa_product(asin: str):
    r = requests.get(
        KEEPA_PRODUCT_API,
        params={
            "key": KEEPA_API_KEY,
            "domain": DOMAIN_ID,
            "asin": asin,
            "stats": 180,
            "history": 0,
        },
        timeout=60,
    )

    if r.status_code == 429:
        print(f"[429] rate limited → skip {asin}")
        return None

    if r.status_code != 200:
        print(f"[ERROR] HTTP {r.status_code} {asin}")
        return None

    products = r.json().get("products")
    return products[0] if products else None


def extract_image_url(product: dict):
    images = product.get("images")
    if not images:
        return None
    return f"https://images-na.ssl-images-amazon.com/images/I/{images[0]['l']}"


def safe_current(stats: dict, idx: int):
    cur = stats.get("current")
    if not cur or len(cur) <= idx:
        return None
    val = cur[idx]
    return val if isinstance(val, int) and val >= 0 else None


# =====================
# Main
# =====================
def main():
    res = (
        supabase.table("tracked_asins")
        .select("asin")
        .eq("locale", "us")
        .limit(MAX_PER_RUN)
        .execute()
    )

    asins = [r["asin"] for r in res.data]
    if not asins:
        print("No US ASINs to process")
        return

    now = datetime.now(timezone.utc).isoformat()

    upsert_products = []
    insert_snapshots = []

    for asin in asins:
        product = fetch_keepa_product(asin)
        if not product:
            continue

        title = product.get("title")
        if not title:
            continue

        upsert_products.append(
            {
                "asin": asin,
                "title": title,
                "brand": product.get("brand"),
                "imageUrl": extract_image_url(product),
                "locale": "us",
                "updated_at": now,
            }
        )

        stats = product.get("stats", {})

        insert_snapshots.append(
            {
                "asin": asin,
                "locale": "us",
                "buybox_price": safe_current(stats, 0),
                "rating": safe_current(stats, 2),
                "review_count": safe_current(stats, 11),
                "sales_rank_latest": safe_current(stats, 3),
                "sales_rank_drops30": stats.get("salesRankDrops30"),
                "sales_rank_drops90": stats.get("salesRankDrops90"),
                "sales_rank_drops180": stats.get("salesRankDrops180"),
                "captured_at": now,
            }
        )

        time.sleep(1)

    if upsert_products:
        supabase.table("products").upsert(
            upsert_products,
            on_conflict="asin,locale"
        ).execute()
        print(f"[OK] upserted {len(upsert_products)} US products")

    if insert_snapshots:
        supabase.table("product_snapshots").insert(insert_snapshots).execute()
        print(f"[OK] inserted {len(insert_snapshots)} US snapshots")


if __name__ == "__main__":
    main()
