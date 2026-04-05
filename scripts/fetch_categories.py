import json
import os
import sys
from typing import Any, Dict, List

import requests

KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]

SEARCH_API = "https://api.keepa.com/search"

DOMAIN_MAP = {
    "us": 1,
    "uk": 2,
    "jp": 5,
}

CATEGORY_TERM = os.environ.get("CATEGORY_TERM", "protein").strip()
CATEGORY_LOCALE = os.environ.get("CATEGORY_LOCALE", "jp").strip().lower()
TIMEOUT_SEC = int(os.environ.get("TIMEOUT_SEC", "60"))
MAX_RESULTS = int(os.environ.get("MAX_RESULTS", "50"))


def get_domain_id(locale: str) -> int:
    domain_id = DOMAIN_MAP.get(locale)
    if domain_id is None:
        print(f"[ERROR] unsupported CATEGORY_LOCALE={locale}")
        sys.exit(1)
    return domain_id


def normalize_candidates(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    candidates = data.get("categories") or data.get("categoryList") or []
    out: List[Dict[str, Any]] = []

    for c in candidates[:MAX_RESULTS]:
        if not isinstance(c, dict):
            continue

        cat_id = c.get("catId") or c.get("categoryId") or c.get("id")
        name = c.get("name") or c.get("categoryName")
        parent = c.get("parent") or c.get("parentId")
        product_count = c.get("productCount")

        if cat_id and name:
            out.append(
                {
                    "catId": str(cat_id),
                    "name": str(name),
                    "parent": parent,
                    "productCount": product_count,
                }
            )

    return out


def main() -> None:
    domain_id = get_domain_id(CATEGORY_LOCALE)

    params = {
        "key": KEEPA_API_KEY,
        "domain": domain_id,
        "type": "category",
        "term": CATEGORY_TERM,
    }

    print(
        f"[INFO] search categories locale={CATEGORY_LOCALE} "
        f"domain={domain_id} term={CATEGORY_TERM}"
    )

    try:
        r = requests.get(SEARCH_API, params=params, timeout=TIMEOUT_SEC)
    except requests.RequestException as exc:
        print(f"[ERROR] category search request failed: {exc}")
        sys.exit(1)

    print(f"[INFO] status={r.status_code}")
    print(f"[DEBUG] request_url={r.url.replace(KEEPA_API_KEY, '***')}")

    if r.status_code == 429:
        print("[429] rate limited on category search")
        sys.exit(2)

    if r.status_code != 200:
        print(f"[ERROR] category search failed: {r.status_code} {r.text[:1000]}")
        sys.exit(1)

    data = r.json()
    out = normalize_candidates(data)

    print(f"[OK] category candidates: {len(out)}")
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()