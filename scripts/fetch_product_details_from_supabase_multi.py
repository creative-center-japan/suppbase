import os
import time
import requests
from datetime import datetime, timezone
from supabase import create_client


KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]

MAX_PER_RUN = int(os.environ.get("MAX_PER_RUN", "4"))
MAX_JP_PROTEIN = int(os.environ.get("MAX_JP_PROTEIN", "1"))
MAX_JP_SUPPLEMENT = int(os.environ.get("MAX_JP_SUPPLEMENT", "1"))
MAX_US_PROTEIN = int(os.environ.get("MAX_US_PROTEIN", "1"))
MAX_UK_PROTEIN = int(os.environ.get("MAX_UK_PROTEIN", "1"))

# Keepa domain mapping
# US = 1, UK = 2, JP = 5
DOMAIN_MAP = {
    "us": 1,
    "uk": 2,
    "jp": 5,
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
        print(f"[429] rate limited -> skip stats {locale}:{asin}")
        return None

    if r.status_code != 200:
        print(f"[ERROR] HTTP {r.status_code} for stats {locale}:{asin} / body={r.text[:500]}")
        return None

    try:
        data = r.json()
    except Exception as e:
        print(f"[ERROR] invalid json for stats {locale}:{asin}: {e}")
        return None

    products = data.get("products")
    if not products:
        print(f"[SKIP] no products returned for stats {locale}:{asin}")
        return None

    return products[0]


def fetch_keepa_product_with_offers(asin: str, locale: str):
    domain = DOMAIN_MAP.get(locale)
    if not domain:
        print(f"[SKIP] unsupported locale for offers: {locale} / {asin}")
        return None

    params = {
        "key": KEEPA_API_KEY,
        "domain": domain,
        "asin": asin,
        "offers": 20,
        "buybox": 1,
        "update": 48,
        "history": 0,
    }

    try:
        r = requests.get(KEEPA_PRODUCT_API, params=params, timeout=60)
    except Exception as e:
        print(f"[ERROR] request failed for offers {locale}:{asin}: {e}")
        return None

    if r.status_code == 429:
        print(f"[429] rate limited -> skip offers {locale}:{asin}")
        return None

    if r.status_code != 200:
        print(f"[ERROR] HTTP {r.status_code} for offers {locale}:{asin} / body={r.text[:500]}")
        return None

    try:
        data = r.json()
    except Exception as e:
        print(f"[ERROR] invalid json for offers {locale}:{asin}: {e}")
        return None

    products = data.get("products")
    if not products:
        print(f"[SKIP] no products returned for offers {locale}:{asin}")
        return None

    return products[0]


def extract_price_from_offers(product: dict):
    offers = product.get("offers") or []
    latest_ts = -1
    latest_price = None

    for offer in offers:
        csv = offer.get("offerCSV") or []
        for i in range(0, len(csv), 3):
            try:
                ts, price, _ = csv[i:i + 3]
            except ValueError:
                continue

            if isinstance(price, int) and price > 0 and ts > latest_ts:
                latest_ts = ts
                latest_price = price

    return latest_price


def extract_image_url(product: dict):
    images = product.get("imagesCSV")
    if not images:
        return None

    first_image = images.split(",")[0].strip()
    if not first_image:
        return None

    return f"https://images-na.ssl-images-amazon.com/images/I/{first_image}"


def extract_sales_rank(product: dict):
    ranks = product.get("salesRanks")
    if not ranks:
        return None

    try:
        # KeepaのsalesRanksはカテゴリIDごとの配列
        # 最後のカテゴリ配列の最後の値を採用
        last_rank_series = list(ranks.values())[-1]
        if not last_rank_series:
            return None
        return last_rank_series[-1]
    except Exception:
        return None


def infer_protein_type(title: str | None, category: str | None):
    if category == "supplement":
        return None

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
    try:
        v = int(value)
        return v if v > 0 else None
    except Exception:
        return None


def normalize_monthly_sold(value):
    if value in (None, -1):
        return None
    try:
        return int(value)
    except Exception:
        return None


def normalize_int(value, default=0):
    if value is None:
        return default
    try:
        return int(value)
    except Exception:
        return default


def build_score(product, stats):
    drops30 = normalize_int(stats.get("salesRankDrops30"), 0)
    drops90 = normalize_int(stats.get("salesRankDrops90"), 0)
    reviews = normalize_int(product.get("reviewsCount"), 0)
    monthly_sold = normalize_int(product.get("monthlySold"), 0)

    return int(drops30 * 100 + drops90 * 50 + reviews * 2 + monthly_sold * 3)


def dedupe_rows(rows):
    seen = set()
    out = []

    for r in rows:
        asin = (r.get("asin") or "").strip().upper()
        locale = (r.get("locale") or "").strip().lower()

        if not asin or not locale:
            continue

        key = (asin, locale)
        if key in seen:
            continue

        seen.add(key)
        r["asin"] = asin
        r["locale"] = locale
        out.append(r)

    return out


def select_targets():
    try:
        res = (
            supabase.table("v_asin_priority_multi")
            .select("asin, locale, category, priority, locale_rank")
            .execute()
        )
    except Exception as e:
        print(f"[ERROR] failed to read v_asin_priority_multi: {e}")
        raise

    rows = res.data or []
    print(f"[INFO] rows from v_asin_priority_multi: {len(rows)}")

    rows = dedupe_rows(rows)

    jp_protein = [
        r for r in rows
        if r.get("locale") == "jp" and r.get("category") == "protein"
    ][:MAX_JP_PROTEIN]

    jp_supplement = [
        r for r in rows
        if r.get("locale") == "jp" and r.get("category") == "supplement"
    ][:MAX_JP_SUPPLEMENT]

    us_protein = [
        r for r in rows
        if r.get("locale") == "us" and r.get("category") == "protein"
    ][:MAX_US_PROTEIN]

    uk_protein = [
        r for r in rows
        if r.get("locale") == "uk" and r.get("category") == "protein"
    ][:MAX_UK_PROTEIN]

    targets = (jp_protein + jp_supplement + us_protein + uk_protein)[:MAX_PER_RUN]

    print("[INFO] selected targets summary:")
    for r in targets:
        print(
            f"  - locale={r.get('locale')} "
            f"category={r.get('category')} "
            f"asin={r.get('asin')} "
            f"priority={r.get('priority')} "
            f"locale_rank={r.get('locale_rank')}"
        )

    if not targets:
        print("[WARN] no targets selected. check v_asin_priority_multi contents.")

    return targets


def upsert_products(rows):
    if not rows:
        print("[SKIP] no product rows")
        return

    try:
        resp = supabase.table("products").upsert(
            rows,
            on_conflict="asin,locale",
        ).execute()
        print(f"[OK] upsert products: {len(rows)} / response_count={len(resp.data or []) if hasattr(resp, 'data') else 'n/a'}")
    except Exception as e:
        print(f"[ERROR] upsert products failed: {e}")
        raise


def insert_snapshots(rows):
    if not rows:
        print("[SKIP] no snapshot rows")
        return

    try:
        resp = supabase.table("product_snapshots").insert(rows).execute()
        print(f"[OK] insert snapshots: {len(rows)} / response_count={len(resp.data or []) if hasattr(resp, 'data') else 'n/a'}")
    except Exception as e:
        print(f"[ERROR] insert snapshots failed: {e}")
        raise


def update_last_checked(asins_by_locale, checked_at):
    for locale, asin_list in asins_by_locale.items():
        if not asin_list:
            print(f"[SKIP] no checked asins for {locale}")
            continue

        try:
            resp = (
                supabase.table("tracked_asins")
                .update({"last_checked_at": checked_at})
                .eq("locale", locale)
                .in_("asin", asin_list)
                .execute()
            )
            print(
                f"[OK] updated last_checked_at: locale={locale} "
                f"count={len(asin_list)} "
                f"response_count={len(resp.data or []) if hasattr(resp, 'data') else 'n/a'}"
            )
        except Exception as e:
            print(f"[ERROR] update_last_checked failed: locale={locale} / {e}")
            raise


def main():
    targets = select_targets()

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
        category = (row.get("category") or "").strip().lower()

        if not asin or not locale:
            print(f"[SKIP] invalid row: {row}")
            continue

        print(f"[PROCESS] locale={locale} category={category} asin={asin}")

        p = fetch_keepa_product(asin, locale)
        if not p:
            print(f"[SKIP] no product detail for {locale}:{asin}")
            continue

        title = p.get("title")
        if not title:
            print(f"[SKIP] no title for {locale}:{asin}")
            continue

        stats = p.get("stats", {}) or {}
        sales_rank = extract_sales_rank(p)
        buybox_price = normalize_buybox_price(stats.get("buyBoxPrice"))

        if buybox_price is None:
            heavy = fetch_keepa_product_with_offers(asin, locale)
            if heavy:
                buybox_price = extract_price_from_offers(heavy)
                buybox_price = normalize_buybox_price(buybox_price)

        monthly_sold = normalize_monthly_sold(p.get("monthlySold"))
        suppbase_score = build_score(p, stats)

        product_row = {
            "asin": asin,
            "locale": locale,
            "title": title,
            "brand": p.get("brand"),
            "imageUrl": extract_image_url(p),
            "reviewCount": normalize_int(p.get("reviewsCount"), None),
            "salesRank": sales_rank,
            "buyBoxPrice": buybox_price,
            "protein_type": infer_protein_type(title, category),
            "suppbase_score": suppbase_score,
            "updated_at": now,
        }

        snapshot_row = {
            "asin": asin,
            "locale": locale,
            "buybox_price": buybox_price,
            "rating": None,
            "review_count": normalize_int(p.get("reviewsCount"), None),
            "monthly_sold": monthly_sold,
            "sales_rank_latest": sales_rank,
            "sales_rank_drops30": normalize_int(stats.get("salesRankDrops30"), 0),
            "sales_rank_drops90": normalize_int(stats.get("salesRankDrops90"), 0),
            "sales_rank_drops180": normalize_int(stats.get("salesRankDrops180"), 0),
            "captured_at": now,
        }

        products.append(product_row)
        snapshots.append(snapshot_row)
        checked.setdefault(locale, []).append(asin)

        print(
            f"[OK] locale={locale} category={category} asin={asin} "
            f"title={title[:80]} "
            f"price={buybox_price} monthly_sold={monthly_sold} sales_rank={sales_rank}"
        )

        time.sleep(1)

    upsert_products(products)
    insert_snapshots(snapshots)
    update_last_checked(checked, now)

    print("[DONE] multi collection finished")
    print(f"[DONE] products={len(products)} snapshots={len(snapshots)}")
    print(f"[DONE] checked={checked}")


if __name__ == "__main__":
    main()