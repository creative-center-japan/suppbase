import os
import time
import requests
from datetime import datetime, timezone
from supabase import create_client

KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]
MAX_PER_RUN = int(os.environ.get("MAX_PER_RUN", "10"))

# localeごとの取得件数上限
MAX_JP = int(os.environ.get("MAX_JP", "6"))
MAX_US = int(os.environ.get("MAX_US", "4"))
MAX_UK = int(os.environ.get("MAX_UK", "0"))

DOMAIN_MAP = {
    "jp": 1,
    "us": 2,
    "uk": 3,
}

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
KEEPA_PRODUCT_API = "https://api.keepa.com/product"


def fetch_keepa_product(asin: str, locale: str):
    domain = DOMAIN_MAP.get(locale)
    if not domain:
        print(f"[SKIP] unsupported locale: {locale} / {asin}")
        return None

    params = {
        "key": KEEPA_API_KEY,
        "domain": domain,
        "asin": asin,
        "stats": 180,
        "history": 0,
    }

    try:
        r = requests.get(KEEPA_PRODUCT_API, params=params, timeout=30)
    except Exception as e:
        print(f"[ERROR] request failed for {locale}:{asin}: {e}")
        return None

    if r.status_code == 429:
        print(f"[429] rate limited -> skip {locale}:{asin}")
        return None

    if r.status_code != 200:
        print(f"[ERROR] HTTP {r.status_code} for {locale}:{asin}")
        return None

    products = r.json().get("products")
    return products[0] if products else None


def extract_image_url(product):
    images = product.get("imagesCSV")
    if not images:
        return None
    first_image = images.split(",")[0].strip()
    if not first_image:
        return None
    return f"https://images-na.ssl-images-amazon.com/images/I/{first_image}"


def extract_sales_rank(product):
    ranks = product.get("salesRanks")
    if not ranks:
        return None
    try:
        last_rank_series = list(ranks.values())[-1]
        if not last_rank_series:
            return None
        return last_rank_series[-1]
    except Exception:
        return None


def infer_protein_type(title: str | None):
    if not title:
        return None

    t = title.lower()

    if "soy" in t:
        return "soy"
    if "isolate" in t or "wpi" in t:
        return "wpi"
    if "whey" in t:
        return "whey"
    if "protein" in t:
        return "protein"

    return None


def normalize_buybox_price(value):
    if value in (None, -1):
        return None
    return value


def normalize_monthly_sold(value):
    if value in (None, -1):
        return None
    return value


def build_score(product, stats):
    drops30 = stats.get("salesRankDrops30") or 0
    drops90 = stats.get("salesRankDrops90") or 0
    reviews = product.get("reviewsCount") or 0
    return int(drops30 * 100 + drops90 * 50 + reviews * 2)


def select_asins():
    query = """
    select asin, locale, category, priority, locale_rank
    from v_asin_priority_multi
    where
      (locale = 'jp' and locale_rank <= {max_jp})
      or
      (locale = 'us' and locale_rank <= {max_us})
      or
      (locale = 'uk' and locale_rank <= {max_uk})
    order by
      case locale
        when 'jp' then 1
        when 'us' then 2
        when 'uk' then 3
        else 9
      end,
      locale_rank
    limit {max_per_run}
    """.format(
        max_jp=MAX_JP,
        max_us=MAX_US,
        max_uk=MAX_UK,
        max_per_run=MAX_PER_RUN,
    )

    res = supabase.rpc("run_sql", {"query": query}).execute()
    return res.data or []


def upsert_products(rows):
    if not rows:
        return
    supabase.table("products").upsert(
        rows,
        on_conflict="asin,locale",
    ).execute()
    print(f"[OK] upsert products: {len(rows)}")


def insert_snapshots(rows):
    if not rows:
        return
    supabase.table("product_snapshots").insert(rows).execute()
    print(f"[OK] insert snapshots: {len(rows)}")


def update_last_checked(asins_by_locale, checked_at):
    for locale, asin_list in asins_by_locale.items():
        if not asin_list:
            continue

        supabase.table("tracked_asins").update(
            {"last_checked_at": checked_at}
        ).eq("locale", locale).in_("asin", asin_list).execute()

        print(f"[OK] updated last_checked_at: {locale} / {len(asin_list)}")


def main():
    targets = select_asins()

    if not targets:
        print("[INFO] no ASINs selected")
        return

    now = datetime.now(timezone.utc).isoformat()

    products = []
    snapshots = []
    checked = {"jp": [], "us": [], "uk": []}

    print(f"[INFO] selected {len(targets)} targets")

    for row in targets:
        asin = (row.get("asin") or "").strip().upper()
        locale = (row.get("locale") or "").strip().lower()

        if not asin or not locale:
            continue

        print(f"[PROCESS] {locale}:{asin}")

        p = fetch_keepa_product(asin, locale)
        if not p:
            continue

        title = p.get("title")
        if not title:
            continue

        stats = p.get("stats", {}) or {}
        suppbase_score = build_score(p, stats)

        product_row = {
            "asin": asin,
            "locale": locale,
            "title": title,
            "brand": p.get("brand"),
            "imageUrl": extract_image_url(p),
            "protein_type": infer_protein_type(title),
            "suppbase_score": suppbase_score,
            "updated_at": now,
        }

        snapshot_row = {
            "asin": asin,
            "locale": locale,
            "buybox_price": normalize_buybox_price(stats.get("buyBoxPrice")),
            "sales_rank_latest": extract_sales_rank(p),
            "monthly_sold": normalize_monthly_sold(p.get("monthlySold")),
            "captured_at": now,
        }

        products.append(product_row)
        snapshots.append(snapshot_row)
        checked.setdefault(locale, []).append(asin)

        time.sleep(1)

    upsert_products(products)
    insert_snapshots(snapshots)
    update_last_checked(checked, now)


if __name__ == "__main__":
    main()