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
MAX_PER_RUN = int(os.environ.get("MAX_PER_RUN", 5))

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

KEEPA_PRODUCT_API = "https://api.keepa.com/product"
DOMAIN_JP = 5

# =====================
# Helper
# =====================
def fetch_keepa_product(asin: str) -> dict | None:
    """
    軽量取得（statsのみ）
    """
    params = {
        "key": KEEPA_API_KEY,
        "domain": DOMAIN_JP,
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


def fetch_keepa_product_with_offers(asin: str) -> dict | None:
    """
    重い取得（offers付き）
    """
    params = {
        "key": KEEPA_API_KEY,
        "domain": DOMAIN_JP,
        "asin": asin,
        "offers": 20,
        "buybox": 1,
        "update": 48,
        "history": 0,
    }

    r = requests.get(KEEPA_PRODUCT_API, params=params, timeout=60)

    if r.status_code == 429:
        print(f"[429] rate limited → skip offers {asin}")
        return None

    if r.status_code != 200:
        print(f"[ERROR] HTTP {r.status_code} offers {asin}")
        return None

    products = r.json().get("products")
    return products[0] if products else None


def extract_price_from_offers(product: dict) -> int | None:
    """
    offersCSV から最新価格を抽出
    """
    offers = product.get("offers") or []
    latest_ts = -1
    latest_price = None

    for offer in offers:
        csv = offer.get("offerCSV") or []
        for i in range(0, len(csv), 3):
            try:
                ts, price, _ = csv[i:i+3]
            except ValueError:
                continue
            if price > 0 and ts > latest_ts:
                latest_ts = ts
                latest_price = price

    return latest_price


def extract_image_url(product: dict) -> str | None:
    images_csv = product.get("imagesCSV")
    if not images_csv:
        return None
    return f"https://images-na.ssl-images-amazon.com/images/I/{images_csv.split(',')[0]}"


def safe_get_current(stats: dict, index: int):
    cur = stats.get("current")
    if not cur or len(cur) <= index:
        return None
    return cur[index]


def extract_latest_sales_rank(product: dict) -> int | None:
    sales_ranks = product.get("salesRanks")
    if not sales_ranks:
        return None
    last_category = list(sales_ranks.values())[-1]
    if not last_category or len(last_category) < 2:
        return None
    return last_category[-1]


# =====================
# Main
# =====================
def main():
    res = (
        supabase.table("products")
        .select("asin")
        .order("updated_at", desc=False)
        .limit(MAX_PER_RUN)
        .execute()
    )

    asins = [r["asin"] for r in res.data]
    if not asins:
        print("No ASINs to process")
        return

    upsert_products = []
    insert_snapshots = []

    for asin in asins:
        product = fetch_keepa_product(asin)
        if not product:
            continue

        now = datetime.now(timezone.utc).isoformat()

        title = product.get("title")
        if not title:
            continue

        image_url = extract_image_url(product)

        upsert_products.append(
            {
                "asin": asin,
                "title": title,
                "imageUrl": image_url,
                "updated_at": now,
            }
        )

        stats = product.get("stats", {})
        price = stats.get("buyBoxPrice")

        # ---- 価格が取れない場合のみ offers を使う ----
        if not isinstance(price, int) or price <= 0:
            heavy = fetch_keepa_product_with_offers(asin)
            if heavy:
                price = extract_price_from_offers(heavy)

        snapshot = {
            "asin": asin,
            "buybox_price": price,
            "rating": safe_get_current(stats, 2),
            "review_count": safe_get_current(stats, 11),
            "sales_rank_latest": extract_latest_sales_rank(product),
            "sales_rank_drops30": stats.get("salesRankDrops30"),
            "sales_rank_drops90": stats.get("salesRankDrops90"),
            "sales_rank_drops180": stats.get("salesRankDrops180"),
            "captured_at": now,
        }

        insert_snapshots.append(snapshot)
        time.sleep(1)

    if upsert_products:
        supabase.table("products").upsert(upsert_products).execute()
        print(f"[OK] upserted {len(upsert_products)} products")

    if insert_snapshots:
        supabase.table("product_snapshots").insert(insert_snapshots).execute()
        print(f"[OK] inserted {len(insert_snapshots)} snapshots")


if __name__ == "__main__":
    main()
