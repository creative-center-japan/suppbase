import os
import time
from datetime import datetime, timezone

import requests
from supabase import create_client


KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]

# 必須ENV
LOCALE = os.environ.get("ASIN_LOCALE", "jp").strip().lower()
CATEGORY = os.environ.get("ASIN_CATEGORY", "protein").strip().lower()
CATEGORY_ID = os.environ.get("CATEGORY_ID", "").strip()

# 任意ENV
SOURCE = os.environ.get("ASIN_SOURCE", "bestseller").strip().lower()
TOP_N = int(os.environ.get("TOP_N", "100"))
MAX_INSERT = int(os.environ.get("MAX_INSERT", "100"))
SLEEP_SEC = float(os.environ.get("SLEEP_SEC", "1"))

DOMAIN_MAP = {
    "us": 1,
    "uk": 2,
    "jp": 5,
}

KEEPA_BESTSELLER_API = "https://api.keepa.com/bestsellers"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def validate():
    if LOCALE not in DOMAIN_MAP:
        raise ValueError(f"unsupported locale: {LOCALE}")

    if not CATEGORY_ID:
        raise ValueError("CATEGORY_ID is required")

    try:
        int(CATEGORY_ID)
    except Exception:
        raise ValueError(f"invalid CATEGORY_ID: {CATEGORY_ID}")


def fetch_bestseller_asins():
    domain = DOMAIN_MAP[LOCALE]

    params = {
        "key": KEEPA_API_KEY,
        "domain": domain,
        "category": CATEGORY_ID,
    }

    print(f"[INFO] request bestseller locale={LOCALE} category={CATEGORY} category_id={CATEGORY_ID}")

    r = requests.get(KEEPA_BESTSELLER_API, params=params, timeout=60)

    if r.status_code == 429:
        print("[429] rate limited on bestseller API")
        return []

    if r.status_code != 200:
        print(f"[ERROR] HTTP {r.status_code} body={r.text[:500]}")
        return []

    data = r.json()

    # Keepa返却差分吸収
    asins = (
        data.get("bestSellersList")
        or data.get("asinList")
        or data.get("asins")
        or []
    )

    cleaned = []
    seen = set()

    for asin in asins:
        if not isinstance(asin, str):
            continue

        a = asin.strip().upper()
        if not a:
            continue

        if a in seen:
            continue

        seen.add(a)
        cleaned.append(a)

    return cleaned[:TOP_N]


def build_rows(asins):
    now = datetime.now(timezone.utc).isoformat()
    rows = []

    for asin in asins[:MAX_INSERT]:
        rows.append({
            "asin": asin,
            "locale": LOCALE,
            "category": CATEGORY,
            "source": SOURCE,
            "first_seen_at": now,
            "last_seen_at": now,
            "is_active": True,
        })

    return rows, now


def upsert_tracked_asins(rows):
    if not rows:
        print("[SKIP] no rows to upsert")
        return

    try:
        resp = supabase.table("tracked_asins").upsert(
            rows,
            on_conflict="asin,locale",
            returning="representation"
        ).execute()

        count = len(resp.data or []) if hasattr(resp, "data") and resp.data else 0
        print(f"[OK] upsert tracked_asins rows={len(rows)} response_count={count}")

    except Exception as e:
        print(f"[ERROR] failed to upsert tracked_asins: {e}")
        raise


def main():
    validate()

    asins = fetch_bestseller_asins()

    print(f"[INFO] fetched_asins={len(asins)}")
    print(f"[INFO] sample_asins={asins[:20]}")

    if not asins:
        print("[SKIP] no bestseller asins fetched")
        return

    rows, now = build_rows(asins)
    upsert_tracked_asins(rows)

    print("[DONE] bestseller ASIN import finished")
    print(f"[DONE] locale={LOCALE} category={CATEGORY} category_id={CATEGORY_ID} captured_at={now}")

    time.sleep(SLEEP_SEC)


if __name__ == "__main__":
    main()