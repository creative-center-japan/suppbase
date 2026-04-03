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
ONLY_ACTIVE = os.environ.get("ONLY_ACTIVE", "true").lower() == "true"
ORDER_ASC = os.environ.get("ORDER_ASC", "true").lower() == "true"
SLEEP_SEC = float(os.environ.get("SLEEP_SEC", "1"))

KEEPA_API = "https://api.keepa.com/product"

DOMAIN_MAP = {
    "us": 1,
    "uk": 2,
    "jp": 5,
}

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_locale(v: Optional[str]) -> Optional[str]:
    return str(v).strip().lower() if v else None


def chunk(lst: List[Any], size: int) -> List[List[Any]]:
    return [lst[i:i + size] for i in range(0, len(lst), size)]


def detect_type(title: str) -> Optional[str]:
    if not title:
        return None

    t = title.lower()

    if any(k in t for k in ["bcaa", "eaa", "creatine"]):
        return "supplement"

    if "soy" in t:
        return "soy"

    if any(k in t for k in ["isolate", "wpi", "iso100", "iso-100", "whey isolate", "hydro whey", "hydrowhey"]):
        return "wpi"

    if "whey" in t:
        return "other"

    return None


def fetch_tracked(locale: str) -> List[Dict[str, Any]]:
    q = supabase.table("tracked_asins").select(
        "asin, locale, sub_category, is_active, last_fetched_at"
    )

    if ONLY_ACTIVE:
        q = q.eq("is_active", True)

    q = q.eq("locale", locale)
    q = q.order("last_fetched_at", desc=(not ORDER_ASC)).limit(BATCH_SIZE)

    return q.execute().data or []


def call_keepa(asins: List[str], locale: str) -> List[Dict[str, Any]]:
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
    }

    r = requests.get(KEEPA_API, params=params, timeout=60)

    if r.status_code == 429:
        print(f"[429] locale={locale}")
        return []

    if r.status_code != 200:
        print(f"[ERROR] locale={locale} status={r.status_code} body={r.text[:300]}")
        return []

    return r.json().get("products", [])


def img_url(csv: Optional[str]) -> Optional[str]:
    if not csv:
        return None
    first = csv.split(",")[0].strip()
    if not first:
        return None
    return f"https://images-na.ssl-images-amazon.com/images/I/{first}"


def to_int_or_none(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    try:
        s = str(value).strip()
        if not s:
            return None
        return int(float(s))
    except Exception:
        return None


def build(tracked: Dict[str, Any], kp: Dict[str, Any]) -> Dict[str, Any]:
    stats = kp.get("stats") or {}

    buy_box_price = to_int_or_none(stats.get("buyBoxPrice"))
    review_count = to_int_or_none(stats.get("reviewCount"))
    sales_rank = to_int_or_none(stats.get("salesRankReference"))

    return {
        "asin": tracked["asin"],
        "locale": normalize_locale(tracked["locale"]),
        "title": kp.get("title"),
        "brand": kp.get("brand"),
        "imageUrl": img_url(kp.get("imagesCSV")),
        "buyBoxPrice": buy_box_price,
        "reviewCount": review_count,
        "salesRank": sales_rank,
        "sub_category": tracked.get("sub_category"),
        "protein_type": detect_type(kp.get("title") or ""),
        "updated_at": now(),
    }


def touch_tracked(rows: List[Dict[str, Any]]) -> None:
    ts = now()
    for row in rows:
        supabase.table("tracked_asins").update(
            {
                "last_fetched_at": ts,
                "last_checked_at": ts,
            }
        ).eq("asin", row["asin"]).eq("locale", row["locale"]).execute()


def main() -> None:
    targets = LOCALES or ["jp", "us", "uk"]
    total = 0

    for locale in targets:
        rows = fetch_tracked(locale)
        print(f"[INFO] locale={locale} rows={len(rows)}")

        if not rows:
            continue

        asin_map = {r["asin"]: r for r in rows}

        for group in chunk(list(asin_map.keys()), KEEPA_CHUNK_SIZE):
            products = call_keepa(group, locale)
            save_rows: List[Dict[str, Any]] = []
            touched_rows: List[Dict[str, Any]] = []

            for kp in products:
                asin = kp.get("asin")
                tracked = asin_map.get(asin)
                if not asin or not tracked:
                    continue

                row = build(tracked, kp)
                print(
                    f"[SAVE] asin={asin} locale={row['locale']} "
                    f"buyBoxPrice={row['buyBoxPrice']} reviewCount={row['reviewCount']} salesRank={row['salesRank']}"
                )
                save_rows.append(row)
                touched_rows.append(
                    {
                        "asin": asin,
                        "locale": normalize_locale(tracked["locale"]),
                    }
                )

            if save_rows:
                supabase.table("products").upsert(save_rows).execute()
                touch_tracked(touched_rows)
                total += len(save_rows)
                print(f"[OK] locale={locale} saved={len(save_rows)}")

            time.sleep(SLEEP_SEC)

    print(f"[DONE] total_saved={total}")


if __name__ == "__main__":
    main()