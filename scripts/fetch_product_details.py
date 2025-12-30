import os
import json
import time
import requests
from datetime import datetime, timezone

API_KEY = os.environ["KEEPA_API_KEY"]
DOMAIN_ID = 5  # Amazon.co.jp

ASIN_FILE = "asins_protein.json"
OUT_FILE = "product_details.json"
KEEPA_PRODUCT_API = "https://api.keepa.com/product"


def safe_int(v):
    return v if isinstance(v, int) and v > 0 else None


def extract_salesrank(stats):
    """
    stats.salesRank は dict（カテゴリ別）なので最小値を採用
    """
    sr = stats.get("salesRank")
    if isinstance(sr, dict):
        try:
            return min(v for v in sr.values() if isinstance(v, int))
        except ValueError:
            return None
    return None


def extract_price(stats):
    """
    Keepa の stats.current は dict / list 両方来るので両対応
    """
    current = stats.get("current")

    # パターン1: dict
    if isinstance(current, dict):
        bb = current.get("buyBoxPrice")
        if isinstance(bb, list) and len(bb) > 0:
            return bb[0]

    # パターン2: list（Keepa の raw 配列）
    if isinstance(current, list):
        try:
            price = current[2]  # buyBoxPrice が入ることが多い
            if isinstance(price, int) and price > 0:
                return price
        except (IndexError, TypeError):
            pass

    return None


def fetch(asins):
    rows = []

    for i in range(0, len(asins), 10):
        batch = asins[i:i + 10]
        print(f"[i] fetch protein batch {i//10 + 1}")

        while True:
            r = requests.get(
                KEEPA_PRODUCT_API,
                params={
                    "key": API_KEY,
                    "domain": DOMAIN_ID,
                    "asin": ",".join(batch),
                    "stats": 180,
                    "history": 0,
                },
                timeout=60,
            )

            if r.status_code == 429:
                refill_ms = r.json().get("refillIn", 60000)
                wait_sec = int(refill_ms / 1000) + 5
                print(f"[429] rate limited, sleep {wait_sec}s")
                time.sleep(wait_sec)
                continue

            r.raise_for_status()
            break

        data = r.json()

        for p in data.get("products", []):
            stats = p.get("stats") or {}

            asin = p.get("asin")
            title = p.get("title")

            # title が無いと products を更新できない
            if not asin or not title:
                continue

            row = {
                "asin": asin,
                "title": title,

                # ★ products 用
                "salesrank": extract_salesrank(stats),
                "reviewcount": safe_int(p.get("reviewCount")),
                "rating": p.get("rating"),

                # ★ price_history 用
                "price": extract_price(stats),

                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }

            rows.append(row)

        time.sleep(30)  # API負荷軽減

    return rows


def main():
    if not os.path.exists(ASIN_FILE):
        print(f"[ERROR] {ASIN_FILE} not found")
        return

    with open(ASIN_FILE, "r", encoding="utf-8") as f:
        asins = json.load(f)

    if not asins:
        print("[SKIP] no protein ASINs")
        return

    rows = fetch(asins)

    if not rows:
        print("[SKIP] no valid protein product rows")
        return

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    print(f"[OK] protein fetched {len(rows)} rows")


if __name__ == "__main__":
    main()
