# scripts/fetch_product_details.py

import json
import os
import time
import requests

KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
DOMAIN_ID = 5  # Amazon.co.jp
BATCH_SIZE = 20
SLEEP_SEC = 60

ASIN_FILE = "asins_protein.json"
OUT_FILE = "product_details.json"

API_URL = "https://api.keepa.com/product"

def fetch_batch(asins):
    params = {
        "key": KEEPA_API_KEY,
        "domain": DOMAIN_ID,
        "asin": ",".join(asins),
        "stats": 180,
        "rating": 1,
        "buybox": 1,
        "update": 0,
    }
    r = requests.get(API_URL, params=params, timeout=60)
    r.raise_for_status()
    return r.json().get("products", [])

def main():
    if not os.path.exists(ASIN_FILE):
        print("[SKIP] asins_protein.json not found")
        return

    with open(ASIN_FILE, "r", encoding="utf-8") as f:
        asins = json.load(f)

    all_products = []
    for i in range(0, len(asins), BATCH_SIZE):
        batch = asins[i:i+BATCH_SIZE]
        print(f"[i] fetch protein batch {i//BATCH_SIZE + 1}")
        try:
            products = fetch_batch(batch)
            all_products.extend(products)
        except Exception as e:
            print("[ERROR]", e)
            print("[WAIT] sleep", SLEEP_SEC)
            time.sleep(SLEEP_SEC)
            continue
        time.sleep(SLEEP_SEC)

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_products, f, ensure_ascii=False)

    print(f"[OK] protein fetched {len(all_products)} rows")

if __name__ == "__main__":
    main()
