import os
import time
import requests
from datetime import datetime, timezone
from supabase import create_client

KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]
MAX_PER_RUN = int(os.environ.get("MAX_PER_RUN", "40"))

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

KEEPA_PRODUCT_API = "https://api.keepa.com/product"
DOMAIN_US = 1  # US

def fetch_keepa_product(asin: str):
    params = {
        "key": KEEPA_API_KEY,
        "domain": DOMAIN_US,
        "asin": asin,
        "stats": 180,
        "history": 0,
    }
    r = requests.get(KEEPA_PRODUCT_API, params=params, timeout=30)
    if r.status_code == 429:
        print(f"[429] rate limited → skip stats {asin}")
        return None
    if r.status_code != 200:
        print(f"[ERROR] HTTP {r.status_code} stats {asin}")
        return None
    products = r.json().get("products")
    return products[0] if products else None

def extract_image_url(product: dict):
    images_csv = product.get("imagesCSV")
    if not images_csv:
        return None
    return f"https://images-na.ssl-images-amazon.com/images/I/{images_csv.split(',')[0]}"

def extract_latest_sales_rank(product: dict):
    ranks = product.get("salesRanks")
    if not ranks:
        return None
    last_cat = list(ranks.values())[-1]
    if not last_cat or len(last_cat) < 2:
        return None
    return last_cat[-1]

def normalize_int(value, default=None):
    if value is None:
        return default
    try:
        value = int(value)
        return value
    except Exception:
        return default

def select_asins():
    res = (
        supabase.table("v_asin_priority_us")
        .select("asin,priority_bucket,snapshot_count")
        .limit(MAX_PER_RUN)
        .execute()
    )
    rows = res.data or []
    return [r["asin"] for r in rows if r.get("asin")]

def main():
    asins = select_asins()
    if not asins:
        print("[US] no ASINs")
        return

    now = datetime.now(timezone.utc).isoformat()

    upsert_products = []
    snapshots = []

    for asin in asins:
        product = fetch_keepa_product(asin)
        if not product:
            continue

        title = product.get("title")
        if not title:
            continue

        stats = product.get("stats", {})
        monthly_sold = normalize_int(product.get("monthlySold"), 0)

        price = stats.get("buyBoxPrice")
        if not isinstance(price, int) or price <= 0:
            price = None

        upsert_products.append({
            "asin": asin,
            "title": title,
            "imageUrl": extract_image_url(product),
            "locale": "us",
            "updated_at": now,
        })

        snapshots.append({
            "asin": asin,
            "locale": "us",
            "buybox_price": price,
            "rating": None,
            "review_count": None,
            "monthly_sold": monthly_sold,
            "sales_rank_latest": extract_latest_sales_rank(product),
            "sales_rank_drops30": normalize_int(stats.get("salesRankDrops30"), 0),
            "sales_rank_drops90": normalize_int(stats.get("salesRankDrops90"), 0),
            "sales_rank_drops180": normalize_int(stats.get("salesRankDrops180"), 0),
            "captured_at": now,
        })

        print(
            f"[US] {asin} | monthly_sold={monthly_sold} "
            f"| drops30={stats.get('salesRankDrops30')} | price={price}"
        )

        time.sleep(1)

    if upsert_products:
        supabase.table("products").upsert(
            upsert_products,
            on_conflict="asin"
        ).execute()
        print(f"[OK] upserted {len(upsert_products)} US products")

    if snapshots:
        supabase.table("product_snapshots").insert(snapshots).execute()
        print(f"[OK] inserted {len(snapshots)} US snapshots")

if __name__ == "__main__":
    main()