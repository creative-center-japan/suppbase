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
DOMAIN_US = 1


def fetch_keepa_product(asin: str):
    params = {
        "key": KEEPA_API_KEY,
        "domain": DOMAIN_US,
        "asin": asin,
        "stats": 180,
        "history": 0,
    }

    try:
        r = requests.get(KEEPA_PRODUCT_API, params=params, timeout=30)
    except Exception as e:
        print(f"[ERROR][US] request failed for {asin}: {e}")
        return None

    if r.status_code == 429:
        print(f"[429][US] rate limited -> skip {asin}")
        return None

    if r.status_code != 200:
        print(f"[ERROR][US] HTTP {r.status_code} for {asin}")
        return None

    products = r.json().get("products")
    return products[0] if products else None


def extract_image_url(product):
    images = product.get("imagesCSV")
    if not images:
        return None
    return f"https://images-na.ssl-images-amazon.com/images/I/{images.split(',')[0]}"


def extract_sales_rank(product):
    ranks = product.get("salesRanks")
    if not ranks:
        return None
    try:
        last = list(ranks.values())[-1]
        return last[-1]
    except:
        return None


def infer_protein_type(title):
    if not title:
        return None

    t = title.lower()

    if "soy" in t:
        return "soy"
    if "isolate" in t or "wpi" in t:
        return "wpi"
    if "whey" in t:
        return "wpi"

    return None


def select_asins():
    res = (
        supabase.table("v_asin_priority_us")
        .select("asin")
        .limit(MAX_PER_RUN)
        .execute()
    )

    return [r["asin"] for r in res.data or []]


def main():
    asins = select_asins()

    if not asins:
        print("[US] no ASINs selected")
        return

    now = datetime.now(timezone.utc).isoformat()

    products = []
    snapshots = []

    for asin in asins:
        print(f"[US] processing {asin}")

        p = fetch_keepa_product(asin)
        if not p:
            continue

        title = p.get("title")
        if not title:
            continue

        stats = p.get("stats", {}) or {}

        product_row = {
            "asin": asin,
            "locale": "us",
            "title": title,
            "brand": p.get("brand"),
            "imageUrl": extract_image_url(p),
            "protein_type": infer_protein_type(title),
            "updated_at": now,
        }

        snapshot_row = {
            "asin": asin,
            "locale": "us",
            "buybox_price": stats.get("buyBoxPrice"),
            "sales_rank_latest": extract_sales_rank(p),
            "monthly_sold": p.get("monthlySold"),
            "captured_at": now,
        }

        products.append(product_row)
        snapshots.append(snapshot_row)

        time.sleep(1)

    # ★ここが最重要修正
    if products:
        supabase.table("products").upsert(
            products,
            on_conflict="asin,locale"
        ).execute()

        print(f"[OK] upsert products: {len(products)}")

    if snapshots:
        supabase.table("product_snapshots").insert(snapshots).execute()
        print(f"[OK] insert snapshots: {len(snapshots)}")


if __name__ == "__main__":
    main()