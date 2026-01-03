import json
import os
import time
import requests

KEEPA_API_KEY = os.environ.get("KEEPA_API_KEY")
DOMAIN_ID = 5  # Amazon.co.jp
ASIN_FILE = "asins_protein.json"
OUT_FILE = "product_details.json"

BATCH_SIZE = 10
API_URL = "https://api.keepa.com/product"

MAX_429_RETRY = 5        # ★ 無限ループ防止
SLEEP_ON_429 = 60

def fetch_batch(asins):
    retry_429 = 0

    while True:
        r = requests.get(
            API_URL,
            params={
                "key": KEEPA_API_KEY,
                "domain": DOMAIN_ID,
                "asin": ",".join(asins),
                "stats": 180,
                "rating": 1,
                "buybox": 1,
                "update": 48,
                "history": 0
            },
            timeout=60
        )

        if r.status_code == 429:
            retry_429 += 1
            print(f"[429] rate limited ({retry_429}/{MAX_429_RETRY})")

            if retry_429 >= MAX_429_RETRY:
                print("[STOP] too many 429s. skip this batch")
                return None

            time.sleep(SLEEP_ON_429)
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

    for i in range(0, len(asins), BATCH_SIZE):
        batch = asins[i:i + BATCH_SIZE]
        print(f"[i] fetch protein batch {i//BATCH_SIZE + 1}")

        data = fetch_batch(batch)
        if not data:
            break

        for p in data.get("products", []):
            sales_ranks = p.get("salesRanks") or {}

            row = {
                "asin": p.get("asin"),
                "title": p.get("title"),
                "brand": p.get("brand"),
                "imageurl": p.get("imagesCSV", "").split(",")[0] if p.get("imagesCSV") else None,
                "price": p.get("stats", {}).get("buyBoxPrice"),
                "salesrank": sales_ranks.get(str(DOMAIN_ID)),
                "rating": p.get("rating"),
                "reviewcount": p.get("reviewCount"),
            }

            if row["asin"] and row["title"]:
                all_rows.append(row)

        time.sleep(5)

    if not all_rows:
        print("[SKIP] no product rows fetched")
        return

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_rows, f, ensure_ascii=False, indent=2)

    print(f"[OK] protein fetched {len(all_rows)} rows")


if __name__ == "__main__":
    main()
