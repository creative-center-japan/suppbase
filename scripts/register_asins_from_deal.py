import os
import json
from datetime import datetime, timezone
from supabase import create_client


SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE"]

ASIN_FILE = os.environ.get("ASIN_FILE")
CATEGORY = os.environ.get("ASIN_CATEGORY", "unknown").strip().lower()
LOCALE = os.environ.get("ASIN_LOCALE", "jp").strip().lower()
SOURCE = os.environ.get("ASIN_SOURCE", "deal").strip().lower()

VALID_LOCALES = {"jp", "us", "uk"}
VALID_CATEGORIES = {"protein", "supplement", "unknown"}

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
now = datetime.now(timezone.utc).isoformat()


def load_asins(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        raw_asins = data
    elif isinstance(data, dict):
        raw_asins = data.get("asins", [])
    else:
        raw_asins = []

    cleaned = []
    seen = set()

    for asin in raw_asins:
        if not isinstance(asin, str):
            continue

        a = asin.strip().upper()
        if not a:
            continue

        if a in seen:
            continue

        seen.add(a)
        cleaned.append(a)

    return cleaned


def validate_inputs():
    if not ASIN_FILE:
        raise ValueError("ASIN_FILE is not set")

    if not os.path.exists(ASIN_FILE):
        raise FileNotFoundError(f"ASIN_FILE not found: {ASIN_FILE}")

    if LOCALE not in VALID_LOCALES:
        raise ValueError(f"invalid ASIN_LOCALE: {LOCALE}")

    if CATEGORY not in VALID_CATEGORIES:
        raise ValueError(f"invalid ASIN_CATEGORY: {CATEGORY}")


def build_rows(asins: list[str]):
    rows = []

    for asin in asins:
        rows.append({
            "asin": asin,
            "locale": LOCALE,
            "category": CATEGORY,
            "source": SOURCE,
            "first_seen_at": now,
            "last_seen_at": now,
            "is_active": True,
        })

    return rows


def main():
    validate_inputs()

    asins = load_asins(ASIN_FILE)

    print(f"[INFO] ASIN_FILE={ASIN_FILE}")
    print(f"[INFO] ASIN_LOCALE={LOCALE}")
    print(f"[INFO] ASIN_CATEGORY={CATEGORY}")
    print(f"[INFO] ASIN_SOURCE={SOURCE}")
    print(f"[INFO] loaded_asins={len(asins)}")
    print(f"[INFO] sample_asins={asins[:10]}")

    if not asins:
        print("[SKIP] no asins in ASIN_FILE")
        raise SystemExit(0)

    rows = build_rows(asins)

    try:
        resp = supabase.table("tracked_asins").upsert(
            rows,
            on_conflict="asin,locale",
            returning="representation"
        ).execute()

        count = len(resp.data or []) if hasattr(resp, "data") and resp.data else 0
        print(f"[OK] registered {len(rows)} rows / response_count={count}")

    except Exception as e:
        print(f"[ERROR] failed to upsert tracked_asins: {e}")
        raise


if __name__ == "__main__":
    main()