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


def now():
    return datetime.now(timezone.utc).isoformat()


def normalize_locale(v):
    return str(v).strip().lower() if v else None


def chunk(lst, size):
    return [lst[i:i + size] for i in range(0, len(lst), size)]


def detect_type(title: str):
    if not title:
        return None

    t = title.lower()

    if any(k in t for k in ["bcaa", "eaa", "creatine"]):
        return "supplement"

    if "soy" in t:
        return "soy"

    if any(k in t for k in ["isolate", "wpi", "iso100"]):
        return "wpi"

    if "whey" in t:
        return "other"

    return None


def fetch_tracked(locale):
    q = supabase.table("tracked_asins").select(
        "asin, locale, category, source, sub_category, display_category, rank, priority, refresh_group, is_active, last_fetched_at"
    )

    if ONLY_ACTIVE:
        q = q.eq("is_active", True)

    q = q.eq("locale", locale)
    q = q.order("last_fetched_at", desc=(not ORDER_ASC)).limit(BATCH_SIZE)

    return q.execute().data or []


def call_keepa(asins, locale):
    domain = DOMAIN_MAP.get(locale)

    params = {
        "key": KEEPA_API_KEY,
        "domain": domain,
        "asin": ",".join(asins),
        "stats": 30,
        "buybox": 1,
    }

    r = requests.get(KEEPA_API, params=params)

    if r.status_code != 200:
        print("[ERROR]", r.text)
        return []

    return r.json().get("products", [])


def img_url(csv):
    if not csv:
        return None
    return f"https://images-na.ssl-images-amazon.com/images/I/{csv.split(',')[0]}"


def build(tracked, kp):
    stats = kp.get("stats") or {}

    price = stats.get("buyBoxPrice")
    price = price / 100 if price else None

    return {
        "asin": tracked["asin"],
        "locale": normalize_locale(tracked["locale"]),
        "title": kp.get("title"),
        "brand": kp.get("brand"),
        "manufacturer": kp.get("manufacturer"),
        "imageUrl": img_url(kp.get("imagesCSV")),
        "buyBoxPrice": price,
        "reviewCount": stats.get("reviewCount"),
        "monthly_sold": stats.get("monthlySold"),
        "salesRank": stats.get("salesRankReference"),
        "sales_rank_drops_30": stats.get("salesRankDrops30"),
        "protein_type": detect_type(kp.get("title")),
        "category": tracked.get("category"),
        "source": tracked.get("source"),
        "sub_category": tracked.get("sub_category"),
        "display_category": tracked.get("display_category"),
        "rank": tracked.get("rank"),
        "priority": tracked.get("priority"),
        "refresh_group": tracked.get("refresh_group"),
        "updated_at": now(),
    }


def main():
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

            save = []

            for kp in products:
                asin = kp.get("asin")
                tracked = asin_map.get(asin)

                if not tracked:
                    continue

                row = build(tracked, kp)

                print(f"[SAVE] {asin} locale={row['locale']}")

                save.append(row)

            if save:
                supabase.table("products").upsert(save).execute()
                total += len(save)

            time.sleep(SLEEP_SEC)

    print("[DONE]", total)


if __name__ == "__main__":
    main()