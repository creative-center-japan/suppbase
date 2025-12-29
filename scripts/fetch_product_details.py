
import os
import json
import time
import requests
from datetime import datetime, timezone

# ===============================
# 環境変数
# ===============================
KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
DOMAIN_ID = 5  # Amazon.co.jp

ASIN_FILE = "asins_protein.json"
OUT_FILE = "product_details.json"
KEEPA_URL = "https://api.keepa.com/product"

# ===============================
# ユーティリティ
# ===============================
def safe_int(v):
    return v if isinstance(v, int) and v > 0 else None

def extract_price(stats: dict | None):
    if not stats:
        return None
    return (
        stats.get("buyBoxPrice")
        or stats.get("buyBoxPriceAvg90")
        or stats.get("avg90")
        or stats.get("avg30")
    )

def extract_sales_rank(product: dict):
    stats = product.get("stats") or {}
    if stats.get("salesRank"):
        return stats.get("salesRank")

    sales_ranks = product.get("salesRanks") or {}
    for _, values in sales_ranks.items():
        if isinstance(values, list) and len(values) >= 2:
            return values[-1]
    return None

def extract_image(product: dict):
    csv = product.get("imagesCSV")
    if not csv:
        return None
    first = csv.split(",")[0]
    return f"https://images-na.ssl-images-amazon.com/images/I/{first}"

# ===============================
# Keepa API（429対応）
# ===============================
def fetch_batch(asins: list[str]):
    while True:
        r = requests.get(
            KEEPA_URL,
            params={
                "key": KEEPA_API_KEY,
                "domain": DOMAIN_ID,
                "asin": ",".join(asins),
                "stats": 1,
                "buybox": 1,
                "history": 0,
            },
            timeout=60,
        )

        if r.status_code == 429:
            refill_ms = r.json().get("refillIn", 60000)
            wait_sec = int(refill_ms / 1000) + 5
            print(f"[429] product API rate limited. sleep {wait_sec}s")
            time.sleep(wait_sec)
            continue

        r.raise_for_status()
        return r.json()

# ===============================
# main
# ===============================
def main():
    with open(ASIN_FILE, "r", encoding="utf-8") as f:
        asins = json.load(f)

    if not asins:
        print("[i] no ASINs. skip.")
        return

    rows = []

    for i in range(0, len(asins), 50):
        batch = asins[i : i + 50]
        print(f"[i] fetch protein batch {i // 50 + 1}")

        data = fetch_batch(batch)
        products = data.get("products", [])

        for p in products:
            stats = p.get("stats") or {}

            price_raw = extract_price(stats)
            sales_rank_raw = extract_sales_rank(p)

            rows.append({
                "asin": p.get("asin"),

                # price
                "buyboxprice": safe_int(price_raw),
                "buyboxfallback": safe_int(stats.get("avg90")),

                # ranking / review / rating（★修正点）
                "salesrank": safe_int(sales_rank_raw),
                "reviewcount": safe_int(stats.get("reviewCount")),
                "rating": stats.get("rating"),

                # misc
                "imageurl": extract_image(p),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })

        time.sleep(30)

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    print(f"[OK] protein fetched {len(rows)} rows")

if __name__ == "__main__":
    main()
