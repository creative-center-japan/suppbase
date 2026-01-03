# scripts/fetch_product_details.py

import json
import os
import time
import requests

KEEPA_API_KEY = os.environ.get("KEEPA_API_KEY")
DOMAIN_ID = 5  # Amazon.co.jp
ASIN_FILE = "asins_protein.json"
OUT_FILE = "product_details.json"

# ★ 安定優先：10以下
BATCH_SIZE = 10

API_URL = "https://api.keepa.com/product"

def fetch_batch(asins):
    while True:
        params = {
            "key": KEEPA_API_KEY,
            "domain": DOMAIN_ID,
            "asin": ",".join(asins),
            "stats": 180,
            "rating": 1,
            "buybox": 1,
            "update": 48,
            "history": 0
        }

        r = requests.get(API_URL, params=params, timeout=60)

        if r.status_code == 429:
            # ★ 即終了しない。待って再試行
            print("[429] rate limited. sleep 60s and retry")
            time.sleep(60)
            continue

        r.raise_for_status()
        return r.json()


def main():
    if not os.path.exists(ASIN_FILE):
        print(f"[SKIP] {ASIN_FILE} not found")
        return

    with open(ASIN_FILE, "r", encoding="utf-8") as f:
        asins = json.load(f)

    if not asins:
        print("[SKIP] no ASINs")
        return

    all_rows = []
    batch_no = 0

    for i in range(0, len(asins), BATCH_SIZE):
        batch_no += 1
        batch = asins[i:i + BATCH_SIZE]
        print(f"[i] fetch protein batch {batch_no} ({len(batch)} ASINs)")

        data = fetch_batch(batch)
        products = data.get("products", [])

        for p in products:
            stats = p.get("stats", {})
            bb = stats.get("buyBoxPrice")

            row = {
                "asin": p.get("asin"),
                "title": p.get("title"),
                "brand": p.get("brand"),
                "imageurl": p.get("imagesCSV", "").split(",")[0] if p.get("imagesCSV") else None,
                "price": bb // 100 if isinstance(bb, int) else None,
                "salesrank": p.get("salesRanks", {}).get(str(DOMAIN_ID)),
                "rating": p.get("rating"),
                "reviewcount": p.get("reviewCount"),
            }

            # title が無いものは除外（事実）
            if row["asin"] and row["title"]:
                all_rows.append(row)

        # ★ token回復を待つ
        time.sleep(5)

    if not all_rows:
        print("[SKIP] no product rows fetched")
        return

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_rows, f, ensure_ascii=False, indent=2)

    print(f"[OK] protein fetched {len(all_rows)} rows")
    print(f"      output -> {OUT_FILE}")


if __name__ == "__main__":
    main()
