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

    try:
        products = r.json().get("products")
    except Exception as e:
        print(f"[ERROR][US] invalid json for {asin}: {e}")
        return None

    return products[0] if products else None


def extract_image_url(product: dict):
    images_csv = product.get("imagesCSV")
    if not images_csv:
        return None
    first_image = images_csv.split(",")[0].strip()
    if not first_image:
        return None
    return f"https://images-na.ssl-images-amazon.com/images/I/{first_image}"


def extract_latest_sales_rank(product: dict):
    ranks = product.get("salesRanks")
    if not ranks:
        return None

    try:
        last_cat = list(ranks.values())[-1]
        if not last_cat or len(last_cat) < 2:
            return None
        return last_cat[-1]
    except Exception:
        return None


def normalize_int(value, default=None):
    if value is None:
        return default
    try:
        return int(value)
    except Exception:
        return default


def infer_protein_type(title: str) -> str | None:
    if not title:
        return None

    t = title.lower()

    # soy
    if "soy" in t or "soy protein" in t:
        return "soy"

    # WPI / isolate
    if "isolate" in t or "wpi" in t:
        return "wpi"

    # US向け商品では "whey" だけのタイトルが多いので、
    # ひとまず公開画面に載るよう wpi 側へ寄せる
    if "whey" in t or "whey protein" in t:
        return "wpi"

    return None


def select_asins():
    try:
        res = (
            supabase.table("v_asin_priority_us")
            .select("asin,priority_bucket,snapshot_count")
            .limit(MAX_PER_RUN)
            .execute()
        )
    except Exception as e:
        print(f"[ERROR][US] failed to query v_asin_priority_us: {e}")
        return []

    rows = res.data or []
    asins = [r["asin"] for r in rows if r.get("asin")]

    bucket_summary = {}
    for r in rows:
        b = r.get("priority_bucket")
        bucket_summary[b] = bucket_summary.get(b, 0) + 1

    print(f"[INFO][US] selected rows: {len(rows)}")
    print(f"[INFO][US] selected asins: {len(asins)}")
    print(f"[INFO][US] priority mix: {bucket_summary}")

    return asins


def main():
    asins = select_asins()
    if not asins:
        print("[US] no ASINs selected")
        return

    now = datetime.now(timezone.utc).isoformat()

    upsert_products = []
    snapshots = []

    success_count = 0
    skipped_no_product = 0
    skipped_no_title = 0
    type_none_count = 0

    for idx, asin in enumerate(asins, start=1):
        print(f"[INFO][US] processing {idx}/{len(asins)}: {asin}")

        product = fetch_keepa_product(asin)
        if not product:
            skipped_no_product += 1
            continue

        title = product.get("title")
        if not title:
            print(f"[SKIP][US] no title: {asin}")
            skipped_no_title += 1
            continue

        brand = product.get("brand") or ""
        stats = product.get("stats", {}) or {}
        image_url = extract_image_url(product)

        monthly_sold = normalize_int(product.get("monthlySold"), 0)
        sales_rank_latest = extract_latest_sales_rank(product)
        sales_rank_drops30 = normalize_int(stats.get("salesRankDrops30"), 0)
        sales_rank_drops90 = normalize_int(stats.get("salesRankDrops90"), 0)
        sales_rank_drops180 = normalize_int(stats.get("salesRankDrops180"), 0)

        price = stats.get("buyBoxPrice")
        if not isinstance(price, int) or price <= 0:
            price = None

        protein_type = infer_protein_type(title)
        if protein_type is None:
            type_none_count += 1

        upsert_products.append(
            {
                "asin": asin,
                "title": title,
                "brand": brand,
                "imageUrl": image_url,
                "locale": "us",
                "protein_type": protein_type,
                "updated_at": now,
            }
        )

        snapshots.append(
            {
                "asin": asin,
                "locale": "us",
                "buybox_price": price,
                "rating": None,
                "review_count": None,
                "monthly_sold": monthly_sold,
                "sales_rank_latest": sales_rank_latest,
                "sales_rank_drops30": sales_rank_drops30,
                "sales_rank_drops90": sales_rank_drops90,
                "sales_rank_drops180": sales_rank_drops180,
                "captured_at": now,
            }
        )

        print(
            f"[US] {asin} | type={protein_type} | monthly_sold={monthly_sold} "
            f"| sales_rank_latest={sales_rank_latest} | drops30={sales_rank_drops30} | price={price}"
        )

        success_count += 1
        time.sleep(1)

    print("[INFO][US] collection summary:")
    print(f"  selected_asins    : {len(asins)}")
    print(f"  fetched_products  : {success_count}")
    print(f"  skipped_no_product: {skipped_no_product}")
    print(f"  skipped_no_title  : {skipped_no_title}")
    print(f"  type_none_count   : {type_none_count}")
    print(f"  upsert_count      : {len(upsert_products)}")
    print(f"  snapshot_count    : {len(snapshots)}")

    if upsert_products:
        try:
            result = (
                supabase.table("products")
                .upsert(upsert_products, on_conflict="asin")
                .execute()
            )
            print(f"[OK][US] upserted {len(upsert_products)} products")
            print(
                f"[DEBUG][US] products response count: "
                f"{len(result.data) if getattr(result, 'data', None) else 0}"
            )
        except Exception as e:
            print(f"[ERROR][US] products upsert failed: {e}")

    if snapshots:
        try:
            result = supabase.table("product_snapshots").insert(snapshots).execute()
            print(f"[OK][US] inserted {len(snapshots)} snapshots")
            print(
                f"[DEBUG][US] snapshots response count: "
                f"{len(result.data) if getattr(result, 'data', None) else 0}"
            )
        except Exception as e:
            print(f"[ERROR][US] snapshot insert failed: {e}")


if __name__ == "__main__":
    main()