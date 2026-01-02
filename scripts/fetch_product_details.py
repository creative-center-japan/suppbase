# scripts/fetch_product_details.py

import json
import os
import time
import requests

KEEPA_API_KEY = os.environ.get("KEEPA_API_KEY")
DOMAIN_ID = 5  # Amazon.co.jp
ASIN_FILE = "asins_protein.json"
OUT_FILE = "product_details.json"

BATCH_SIZE = 20  # ←重要：一気に叩かない

API_URL = "https://api.keepa.com/product"

def fetch_batch(asins):
    params = {
        "key": KEEPA_API_KEY,
        "domain": DOMAIN_ID,
        "asin": ",".join(asins),
        "stats": 180,
        "rating": 1,
        "buybox": 1,
        "update": 48,     # ← 即時更新しない
        "history": 0
    }
    r = requests.get(API_URL, params=params, timeout=60)

    if r.status_code == 429:
        print("[429] rate limited. stop this run.")
        return None

    r.raise_for_status()
    return r.json()

def main():
    if not os.path.exists(ASIN_FILE):
        print(f"[SKIP] {ASIN_FILE} not found")
        return

    with open(ASIN_FILE, "r", encoding="utf-8") as f:
        asins = json.load(f)

    all_rows = []
    batch_no = 0

    for i in range(0, len(asins), BATCH_SIZE):
        batch_no += 1
        batch = asins[i:i + BATCH_SIZE]
        print(f"[i] fetch protein batch {batch_no}")

        data = fetch_batch(batch)
        if data is None:
            break  # ← sleepせず終了

        products = data.get("products", [])
        for p in products:
            stats = p.get("stats", {})
            bb = stats.get("buyBoxPrice")

            row = {
                "asin": p.get("asin"),
                "title": p.get("title"),
                "brand": p.get("brand"),
                "imageUrl": p.get("imagesCSV", "").split(",")[0] if p.get("imagesCSV") else None,
                "price": bb // 100 if isinstance(bb, int) else None,
                "salesrank": p.get("salesRanks", {}).get(str(DOMAIN_ID)),
                "rating": p.get("rating"),
                "reviewcount": p.get("reviewCount"),
            }
            all_rows.append(row)

        # 軽い間隔だけ入れる（token回復待ちではない）
        time.sleep(2)

    if not all_rows:
        print("[SKIP] no product rows fetched")
        return

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_rows, f, ensure_ascii=False, indent=2)

    print(f"[OK] protein fetched {len(all_rows)} rows")

if __name__ == "__main__":
    main()
