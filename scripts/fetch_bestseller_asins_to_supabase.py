import os
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests
from supabase import Client, create_client

KEEPA_DOMAIN_MAP = {
    "jp": 5,
    "us": 1,
    "uk": 2,
}

BESTSELLER_API = "https://api.keepa.com/bestSeller"

DEFAULT_TIMEOUT = 60
DEFAULT_TOP_N = 100
DEFAULT_MAX_INSERT = 100
DEFAULT_SLEEP_SEC = 1
DEFAULT_RETRY_COUNT = 2
DEFAULT_RETRY_WAIT_SEC = 70


def getenv_required(name: str) -> str:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        print(f"[ERROR] missing required env: {name}")
        sys.exit(1)
    return value.strip()


def getenv_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    try:
        return int(value.strip())
    except ValueError:
        print(f"[WARN] invalid int env {name}={value!r}; fallback={default}")
        return default


def getenv_str(name: str, default: Optional[str] = None) -> Optional[str]:
    value = os.getenv(name)
    if value is None:
        return default
    value = value.strip()
    return value if value != "" else default


def getenv_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def create_supabase_client() -> Client:
    supabase_url = getenv_required("SUPABASE_URL")
    supabase_key = getenv_required("SUPABASE_SERVICE_ROLE")
    return create_client(supabase_url, supabase_key)


def get_domain_id(locale: str) -> int:
    domain = KEEPA_DOMAIN_MAP.get(locale.lower())
    if domain is None:
        print(f"[ERROR] unsupported locale: {locale}")
        sys.exit(1)
    return domain


def request_bestseller_with_retry(
    locale: str,
    category: str,
    category_id: str,
    keepa_api_key: str,
    retry_count: int,
    retry_wait_sec: int,
) -> Dict[str, Any]:
    domain = get_domain_id(locale)

    params = {
        "key": keepa_api_key,
        "domain": domain,
        "category": category_id,
    }

    for attempt in range(1, retry_count + 2):
        print(
            f"[INFO] request bestseller locale={locale} "
            f"category={category} category_id={category_id} "
            f"domain={domain} attempt={attempt}"
        )

        try:
            response = requests.get(BESTSELLER_API, params=params, timeout=DEFAULT_TIMEOUT)
        except requests.RequestException as exc:
            print(f"[ERROR] request failed: {exc}")
            if attempt <= retry_count:
                print(f"[INFO] retry after {retry_wait_sec}s")
                time.sleep(retry_wait_sec)
                continue
            sys.exit(1)

        safe_url = response.url.replace(keepa_api_key, "***")
        print(f"[DEBUG] request_url={safe_url}")

        if response.status_code == 200:
            try:
                data = response.json()
            except ValueError:
                print("[ERROR] failed to parse JSON response")
                sys.exit(1)

            keys = list(data.keys()) if isinstance(data, dict) else []
            print(f"[DEBUG] bestseller response keys={keys}")

            if isinstance(data, dict):
                print(f"[INFO] tokensLeft={data.get('tokensLeft')}")
                print(f"[INFO] refillIn={data.get('refillIn')}")
                print(f"[INFO] refillRate={data.get('refillRate')}")
                print(f"[INFO] tokenFlowReduction={data.get('tokenFlowReduction')}")

            return data

        if response.status_code == 429:
            print("[429] rate limited on bestseller API")
            if attempt <= retry_count:
                print(f"[INFO] retry after {retry_wait_sec}s")
                time.sleep(retry_wait_sec)
                continue
            sys.exit(2)

        if response.status_code == 404:
            print(
                "[ERROR] keepa bestseller returned 404. "
                "Most likely invalid category_id for this locale/domain."
            )
            print(f"[ERROR] response_body={response.text[:1000]}")
            sys.exit(1)

        print(f"[ERROR] keepa api status={response.status_code} body={response.text[:1000]}")
        sys.exit(1)

    sys.exit(1)


def extract_asins(data: Dict[str, Any], top_n: int) -> List[str]:
    raw_list = data.get("bestSellersList", []) if isinstance(data, dict) else []
    if not isinstance(raw_list, list):
        return []

    cleaned: List[str] = []
    seen = set()

    for asin in raw_list:
        if not isinstance(asin, str):
            continue
        asin = asin.strip().upper()
        if not asin:
            continue
        if asin in seen:
            continue
        seen.add(asin)
        cleaned.append(asin)
        if len(cleaned) >= top_n:
            break

    return cleaned


def build_upsert_rows(
    asins: List[str],
    locale: str,
    category: str,
    source: str,
    captured_at: str,
    max_insert: int,
    sub_category: Optional[str] = None,
    display_category: Optional[str] = None,
    priority: Optional[int] = None,
    refresh_group: Optional[str] = None,
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    for rank, asin in enumerate(asins[:max_insert], start=1):
        row: Dict[str, Any] = {
            "asin": asin,
            "locale": locale,
            "category": category,
            "source": source,
            "rank": rank,
            "last_rank": rank,
            "display_category": display_category or category,
            "last_seen_at": captured_at,
            "last_rank_at": captured_at,
            "last_active_at": captured_at,
            "last_checked_at": captured_at,
            "last_fetched_at": captured_at,
            "is_active": True,
        }

        if sub_category:
            row["sub_category"] = sub_category

        if priority is not None:
            row["priority"] = priority

        if refresh_group:
            row["refresh_group"] = refresh_group

        rows.append(row)

    return rows


def upsert_tracked_asins(supabase: Client, rows: List[Dict[str, Any]]) -> int:
    if not rows:
        return 0

    try:
        response = (
            supabase.table("tracked_asins")
            .upsert(rows, on_conflict="asin,locale")
            .execute()
        )
    except Exception as exc:
        print(f"[ERROR] upsert failed: {exc}")
        sys.exit(1)

    data = getattr(response, "data", None)
    response_count = len(data) if isinstance(data, list) else 0
    print(f"[OK] upsert tracked_asins rows={len(rows)} response_count={response_count}")
    return response_count


def main() -> None:
    supabase = create_supabase_client()

    keepa_api_key = getenv_required("KEEPA_API_KEY")
    locale = getenv_required("ASIN_LOCALE").lower()
    category = getenv_required("ASIN_CATEGORY").lower()
    category_id = getenv_required("CATEGORY_ID")
    source = getenv_str("ASIN_SOURCE", "bestseller") or "bestseller"

    top_n = getenv_int("TOP_N", DEFAULT_TOP_N)
    max_insert = getenv_int("MAX_INSERT", DEFAULT_MAX_INSERT)
    sleep_sec = getenv_int("SLEEP_SEC", DEFAULT_SLEEP_SEC)
    retry_count = getenv_int("RETRY_COUNT", DEFAULT_RETRY_COUNT)
    retry_wait_sec = getenv_int("RETRY_WAIT_SEC", DEFAULT_RETRY_WAIT_SEC)

    sub_category = getenv_str("SUB_CATEGORY")
    display_category = getenv_str("DISPLAY_CATEGORY", category)
    refresh_group = getenv_str("REFRESH_GROUP")
    priority_env = getenv_str("PRIORITY")
    priority = int(priority_env) if priority_env is not None and priority_env.isdigit() else None
    dry_run = getenv_bool("DRY_RUN", False)

    captured_at = utc_now_iso()

    data = request_bestseller_with_retry(
        locale=locale,
        category=category,
        category_id=category_id,
        keepa_api_key=keepa_api_key,
        retry_count=retry_count,
        retry_wait_sec=retry_wait_sec,
    )

    asins = extract_asins(data, top_n=top_n)

    print(f"[INFO] fetched_asins={len(asins)}")
    print(f"[INFO] sample_asins={asins[:20]}")

    if not asins:
        print("[ERROR] no bestseller asins fetched")
        sys.exit(1)

    rows = build_upsert_rows(
        asins=asins,
        locale=locale,
        category=category,
        source=source,
        captured_at=captured_at,
        max_insert=max_insert,
        sub_category=sub_category,
        display_category=display_category,
        priority=priority,
        refresh_group=refresh_group,
    )

    if dry_run:
        print("[DRY_RUN] skip upsert")
        print(f"[DRY_RUN] rows_preview={rows[:5]}")
        sys.exit(0)

    upsert_tracked_asins(supabase, rows)

    if sleep_sec > 0:
        time.sleep(sleep_sec)

    print("[DONE] bestseller ASIN import finished")
    print(
        f"[DONE] locale={locale} category={category} "
        f"sub_category={sub_category} category_id={category_id} "
        f"captured_at={captured_at}"
    )


if __name__ == "__main__":
    main()