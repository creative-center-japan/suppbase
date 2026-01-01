# scripts/fetch_product_details.py
import os
import json
import time
import requests

KEEPA_KEY = os.environ["KEEPA_API_KEY"]
DOMAIN = 5  # co.jp
ASIN_FILE = "asins_protein.json"
OUT_FILE = "product_details.json"

BASE_URL = "https://api.keepa.com/product"

def fetch_products(asins):
    params = {
        "key": KEEPA_KEY,
        "domain": DOMAIN,
        "asin": ",".join(asins),
        "stats": 180,
        "rating": 1,
        "buybox": 1,
        "offers": 20,
        "update": 48,
        "history": 0,
    }
    r = requests.get(BASE_URL, params=params, timeout=60)
    r.raise_for_status()
    return r.json().get("products", [])

def main():
    with open(ASIN_FILE, "r", encoding="utf-8") as f:
        asins = json.load(f)

    all_rows = []
    BATCH = 10  # ← トークン節約

    for i in range(0, len(asins), BATCH):
        batch = asins[i:i+BATCH]
        print(f"[FETCH] batch {i//BATCH + 1}")
        try:
            products = fetch_products(batch)
            for p in products:
                stats = p.get("stats", {})
                all_rows.append({
                    "asin": p.get("asin"),
                    "title": p.get("title"),
                    "brand": p.get("brand"),
                    "salesrank": p.get("salesRanks", {}).get("SALES", {}).get("last"),
                    "reviewcount": stats.get("reviewCount"),
                    "rating": stats.get("rating"),
                    "buyboxprice": stats.get("buyBoxPrice"),
                    "imageurl": p.get("imagesCSV", "").split(",")[0] if p.get("imagesCSV") else None,
                })
        except Exception as e:
            print("ERROR:", e)

        time.sleep(65)  # ← 429回避

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_rows, f, ensure_ascii=False, indent=2)

    print(f"[OK] fetched {len(all_rows)} products")

if __name__ == "__main__":
    main()
