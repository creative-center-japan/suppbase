# scripts/fetch_product_details.py
import os
import json
import time
import requests
from datetime import datetime, timezone
from typing import List, Dict, Any

API_KEY = os.environ["KEEPA_API_KEY"]
DOMAIN_ID = 5  # Amazon JP

ASIN_LIST_FILE = os.environ.get("ASIN_LIST_FILE", "asins.json")
OUT_PRODUCT = os.environ.get("OUT_PRODUCT", "product_details.json")

KEEPA_PRODUCT_URL = "https://api.keepa.com/product"


def chunk(lst: List[str], size: int):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


def safe_int(v):
    if isinstance(v, int) and v > 0:
        return v
    return None


def map_product(p: Dict[str, Any]) -> Dict[str, Any]:
    stats = p.get("stats") or {}

    # 価格は「buyBox → avg90」のみ使用（最安値系は使わない）
    price = (
        safe_int(stats.get("buyBoxPrice"))
        or safe_int(stats.get("avg90"))
    )

    # salesRank は履歴があれば末尾、それ以外は直値
    sales_rank = safe_int(p.get("salesRank"))
    if sales_rank is None:
        ranks = (p.get("salesRanks") or {}).get("0")
        if isinstance(ranks, list) and ranks:
            sales_rank = safe_int(ranks[-1])

    return {
        "asin": p.get("asin"),
        "price": price,
        "sales_rank": sales_rank,
        "rating": stats.get("rating"),
        "review_count": stats.get("reviewCount"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def fetch_products(asins: List[str]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []

    for group in chunk(asins, 50):
        r = requests.get(
            KEEPA_PRODUCT_URL,
            params={
                "key": API_KEY,
                "domain": DOMAIN_ID,
                "asin": ",".join(group),
                "stats": 1,
                "buybox": 1,
                "history": 0,
            },
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()

        for p in data.get("products", []):
            row = map_product(p)
            if row.get("asin"):
                results.append(row)

        time.sleep(1.2)

    return results


def main():
    if not os.path.exists(ASIN_LIST_FILE):
        raise RuntimeError("ASIN list file not found")

    with open(ASIN_LIST_FILE, "r", encoding="utf-8") as f:
        asins = json.load(f)

    if not isinstance(asins, list):
        raise RuntimeError("ASIN list must be a list")

    products = fetch_products(asins)

    with open(OUT_PRODUCT, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)

    print(f"✓ fetched {len(products)} records")


if __name__ == "__main__":
    main()
