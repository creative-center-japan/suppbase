import os
import json
import time
import requests
from datetime import datetime, timezone

API_KEY = os.environ["KEEPA_API_KEY"]
DOMAIN_ID = 5  # JP

ASIN_FILE = "asins_protein.json"
OUT_FILE = "product_details.json"

KEEPA_URL = "https://api.keepa.com/product"

def safe_int(v):
    return v if isinstance(v, int) and v > 0 else None

def fetch_batch(asins):
    """
    Product API を安全に叩く（429完全対応）
    """
    while True:
        r = requests.get(
            KEEPA_URL,
            params={
                "key": API_KEY,
                "domain": DOMAIN_ID,
                "asin": ",".join(asins),
                "stats": 1,
                "buybox": 1,
                "history": 0,
            },
            timeout=60,
        )

        # ★ レート制限対応
        if r.status_code == 429:
            try:
                refill_ms = r.json().get("refillIn", 60000)
            except Exception:
                refill_ms = 60000

            wait_sec = int(refill_ms / 1000) + 5
            print(f"[429] product API rate limited. sleep {wait_sec}s")
            time.sleep(wait_sec)
            continue

        r.raise_for_status()
        return r.json()

def main():
    with open(ASIN_FILE, "r", encoding="utf-8") as f:
        asins = json.load(f)

    if not asins:
        print("[i] no protein ASINs. skip.")
        return

    rows = []

    for i in range(0, len(asins), 50):
        batch = asins[i:i+50]
        print(f"[i] fetch protein batch {i//50 + 1}")

        data = fetch_batch(batch)

        for p in data.get("products", []):
            stats = p.get("stats") or {}
            rows.append({
                "asin": p.get("asin"),
                "price": safe_int(stats.get("buyBoxPrice")) or safe_int(stats.get("avg90")),
                "sales_rank": safe_int(p.get("salesRank")),
                "rating": stats.get("rating"),
                "review_count": stats.get("reviewCount"),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })

        # ★ 通常時もゆっくり
        time.sleep(30)

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    print(f"[OK] protein fetched {len(rows)} rows")

if __name__ == "__main__":
    main()
