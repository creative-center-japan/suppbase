import os
import json
import time
import requests

KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
DOMAIN_ID = 5  # Amazon.co.jp
ASIN_FILE = "asins_protein.json"
OUT_FILE = "product_details.json"

KEEPA_PRODUCT_API = "https://api.keepa.com/product"

def chunk(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]

def fetch_products(asins):
    params = {
        "key": KEEPA_API_KEY,
        "domain": DOMAIN_ID,
        "asin": ",".join(asins),
        "stats": 180,   # stats を必ず有効化
        "history": 0
    }
    r = requests.get(KEEPA_PRODUCT_API, params=params, timeout=60)
    if r.status_code == 429:
        print("[429] rate limited, sleep 60s")
        time.sleep(60)
        return None
    r.raise_for_status()
    return r.json()

def extract_product(p):
    """
    Keepa product 1件 → DB用 dict
    """
    asin = p.get("asin")
    title = p.get("title")

    # title が無い商品は products 更新できないので捨てる
    if not asin or not title:
        return None

    # ---- レビュー ----
    reviewcount = p.get("reviewCount")
    rating = p.get("rating")

    # ---- 売れ筋ランク ----
    salesrank = None
    stats = p.get("stats") or {}
    sr = stats.get("salesRank")
    if isinstance(sr, dict):
        # categoryId は無視して最小値を使う
        try:
            salesrank = min(v for v in sr.values() if v is not None)
        except ValueError:
            salesrank = None

    # ---- 価格 ----
    price = None
    stats_current = stats.get("current") or {}
    buybox = stats_current.get("buyBoxPrice")
    if isinstance(buybox, list) and len(buybox) > 0:
        # Keepa は「円 × 100」
        price = buybox[0]

    return {
        "asin": asin,
        "title": title,
        "salesrank": salesrank,
        "reviewcount": reviewcount,
        "rating": rating,
        "price": price
    }

def main():
    if not os.path.exists(ASIN_FILE):
        print(f"[ERROR] {ASIN_FILE} not found")
        return

    with open(ASIN_FILE, "r", encoding="utf-8") as f:
        asins = json.load(f)

    if not asins:
        print("[SKIP] no ASINs")
        return

    results = []

    for batch_no, asin_batch in enumerate(chunk(asins, 10), start=1):
        print(f"[i] fetch protein batch {batch_no}")
        data = fetch_products(asin_batch)
        if not data:
            continue

        products = data.get("products") or []
        for p in products:
            row = extract_product(p)
            if row:
                results.append(row)

        time.sleep(1)  # 軽い間隔（429対策）

    if not results:
        print("[SKIP] no valid product rows")
        return

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False)

    print(f"[OK] protein fetched {len(results)} rows")

if __name__ == "__main__":
    main()
