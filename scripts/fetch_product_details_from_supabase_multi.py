import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests
from supabase import Client, create_client


SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]
KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]

LOCALES = [x.strip().lower() for x in os.environ.get("LOCALES", "").split(",") if x.strip()]
BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "20"))
KEEPA_CHUNK_SIZE = int(os.environ.get("KEEPA_CHUNK_SIZE", "10"))
MAX_ITEMS = int(os.environ.get("MAX_ITEMS", "0"))
ONLY_ACTIVE = os.environ.get("ONLY_ACTIVE", "true").strip().lower() == "true"
ORDER_ASC = os.environ.get("ORDER_ASC", "true").strip().lower() == "true"
SLEEP_SEC = float(os.environ.get("SLEEP_SEC", "1"))

KEEPA_PRODUCT_API = "https://api.keepa.com/product"

DOMAIN_MAP = {
    "us": 1,
    "uk": 2,
    "jp": 5,
}

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_locale(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    v = str(value).strip().lower()
    return v if v else None


def chunked(items: List[Any], size: int) -> List[List[Any]]:
    return [items[i:i + size] for i in range(0, len(items), size)]


def detect_protein_type(title: str) -> Optional[str]:
    if not title:
        return None

    t = title.lower()

    if any(
        k in t
        for k in [
            "bcaa",
            "eaa",
            "creatine",
            "pre workout",
            "pre-workout",
            "vitamin",
            "omega",
            "fish oil",
            "collagen",
        ]
    ):
        return "supplement"

    if any(k in t for k in ["soy protein", "soy isolate", "soy"]):
        return "soy"

    if any(
        k in t
        for k in [
            "wpi",
            "isolate",
            "iso100",
            "iso-100",
            "hydrowhey",
            "hydro whey",
            "whey isolate",
        ]
    ):
        return "wpi"

    if "whey" in t:
        return "other"

    return None


def fetch_tracked_asins_for_locale(locale: str) -> List[Dict[str, Any]]:
    q = supabase.table("tracked_asins").select(
        "asin, locale, category, source, sub_category, display_category, rank, priority, refresh_group, is_active, last_fetched_at"
    )

    if ONLY_ACTIVE:
        q = q.eq("is_active", True)

    q = q.eq("locale", locale)
    q = q.order("last_fetched_at", desc=(not ORDER_ASC)).limit(BATCH_SIZE)

    res = q.execute()
    rows = res.data or []

    if MAX_ITEMS > 0:
        rows = rows[:MAX_ITEMS]

    return rows


def fetch_tracked_asins_grouped() -> Dict[str, List[Dict[str, Any]]]:
    target_locales = LOCALES or ["jp", "us", "uk"]
    grouped: Dict[str, List[Dict[str, Any]]] = {}

    for locale in target_locales:
        locale = normalize_locale(locale)
        if not locale:
            continue
        rows = fetch_tracked_asins_for_locale(locale)
        grouped[locale] = rows
        print(f"[INFO] locale={locale} tracked_rows={len(rows)}")

    return grouped


def call_keepa_products(asins: List[str], locale: str) -> List[Dict[str, Any]]:
    domain = DOMAIN_MAP.get(locale)
    if not domain:
        print(f"[SKIP] unsupported locale={locale}")
        return []

    params = {
        "key": KEEPA_API_KEY,
        "domain": domain,
        "asin": ",".join(asins),
        "stats": 30,
        "buybox": 1,
        "offers": 20,
        "history": 0,
        "rating": 1,
    }

    r = requests.get(KEEPA_PRODUCT_API, params=params, timeout=60)

    if r.status_code == 429:
        print(f"[429] rate limited locale={locale}")
        return []

    if r.status_code != 200:
        print(f"[ERROR] Keepa HTTP {r.status_code} locale={locale} body={r.text[:300]}")
        return []

    data = r.json()
    return data.get("products") or []


def build_image_url(images_csv: Optional[str]) -> Optional[str]:
    if not images_csv:
        return None
    first_image = images_csv.split(",")[0].strip()
    if not first_image:
        return None
    return f"https://images-na.ssl-images-amazon.com/images/I/{first_image}"


def build_product_row(tracked: Dict[str, Any], keepa_product: Dict[str, Any]) -> Dict[str, Any]:
    tracked_locale = normalize_locale(tracked.get("locale"))
    title = keepa_product.get("title") or ""
    stats = keepa_product.get("stats") or {}

    buy_box_price = None
    if isinstance(stats.get("buyBoxPrice"), (int, float)) and stats["buyBoxPrice"] > 0:
        buy_box_price = stats["buyBoxPrice"] / 100.0

    return {
        "asin": tracked["asin"],
        "locale": tracked_locale,
        "title": title,
        "brand": keepa_product.get("brand"),
        "manufacturer": keepa_product.get("manufacturer"),
        "image_url": build_image_url(keepa_product.get("imagesCSV")),
        "buyboxprice": buy_box_price,
        "review_count": stats.get("reviewCount"),
        "monthly_sold": stats.get("monthlySold"),
        "sales_rank_drops_30": stats.get("salesRankDrops30"),
        "salesrank": stats.get("salesRankReference"),
        "protein_type": detect_protein_type(title),
        "category": tracked.get("category"),
        "source": tracked.get("source"),
        "sub_category": tracked.get("sub_category"),
        "display_category": tracked.get("display_category"),
        "rank": tracked.get("rank"),
        "priority": tracked.get("priority"),
        "refresh_group": tracked.get("refresh_group"),
        "updated_at": now_iso(),
    }


def upsert_products(rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    supabase.table("products").upsert(rows).execute()


def touch_tracked_asins(rows: List[Dict[str, Any]]) -> None:
    ts = now_iso()
    for row in rows:
        supabase.table("tracked_asins").update(
            {
                "last_fetched_at": ts,
                "last_checked_at": ts,
            }
        ).eq("asin", row["asin"]).eq("locale", row["locale"]).execute()


def main() -> None:
    grouped = fetch_tracked_asins_grouped()

    total_saved = 0

    for locale, rows in grouped.items():
        if not rows:
            print(f"[SKIP] locale={locale} no tracked_asins rows")
            continue

        asin_map = {row["asin"]: row for row in rows}
        asin_list = list(asin_map.keys())

        print(f"[INFO] locale={locale} processing_asins={len(asin_list)}")

        for asin_chunk in chunked(asin_list, KEEPA_CHUNK_SIZE):
            keepa_products = call_keepa_products(asin_chunk, locale)
            if not keepa_products:
                time.sleep(SLEEP_SEC)
                continue

            save_rows: List[Dict[str, Any]] = []
            touched_rows: List[Dict[str, Any]] = []

            for kp in keepa_products:
                asin = kp.get("asin")
                if not asin:
                    continue

                tracked = asin_map.get(asin)
                if not tracked:
                    continue

                product_row = build_product_row(tracked, kp)

                print(
                    f"[SAVE] asin={asin} tracked_locale={tracked.get('locale')} "
                    f"product_locale={product_row['locale']} title={product_row.get('title')}"
                )

                save_rows.append(product_row)
                touched_rows.append(
                    {
                        "asin": asin,
                        "locale": normalize_locale(tracked.get("locale")),
                    }
                )

            if save_rows:
                upsert_products(save_rows)
                touch_tracked_asins(touched_rows)
                total_saved += len(save_rows)
                print(f"[OK] locale={locale} saved={len(save_rows)}")

            time.sleep(SLEEP_SEC)

    print(f"[DONE] fetch_product_details_from_supabase_multi finished total_saved={total_saved}")


if __name__ == "__main__":
    main()