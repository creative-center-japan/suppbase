import json
import os
import time
import requests

KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
DOMAIN_ID = 5  # Amazon.co.jp

ASIN_FILE = "asins_protein.json"
OUT_FILE = "product_details.json"

BATCH_SIZE = 20          # ← 仕様上 OK（最大100）
MAX_BATCH_PER_RUN = 5    # ← GitHub Actions向け制限
SLEEP_BETWEEN_BATCH = 2

API_URL = "https://api.keepa.com/product"


def fetch_products(asins):
    r = requests.get(
        API_URL,
        params={
            "key": KEEPA_API_KEY,
            "domain": DOMAIN_ID,
            "asin": ",".join(asins),
            "stats": 180,     # token消費なし
            "update": -1,     # ★ 最重要：更新しない
            "history": 0,     # ★ 最重要：履歴削除
        },
        timeout=60,
    )

    if r.status_code == 429:
        print("[429] rate limited → skip this batch")
        return []

    r.raise_for_status()
    return r.json().get("products", [])


def main():
    if not os.path.exists(ASIN_FILE):
        print(f"[SKIP] {ASIN_FILE} not found")
        return

    with open(ASIN_FILE, "r", encoding="utf-8") as f:
        asins = json.load(f)

    if not asins:
        print("[SKIP] no ASINs")
        return

    rows = []

    for batch_index, i in enumerate(range(0, len(asins), BATCH_SIZE)):
        if batch_index >= MAX_BATCH_PER_RUN:
            print("[STOP] reached max batch per run")
            break

        batch = asins[i:i + BATCH_SIZE]
        print(f"[i] fetch batch {batch_index + 1} ({len(batch)} ASINs)")

        products = fetch_products(batch)
        if not products:
            continue

        for p in products:
            stats = p.get("stats") or {}

            row = {
                "asin": p.get("asin"),
                "title": p.get("title"),
                "brand": p.get("brand"),
                "imageurl": (
                    p.get("imagesCSV", "").split(",")[0]
                    if p.get("imagesCSV")
                    else None
                ),
                "price": stats.get("buyBoxPrice"),
                "salesrank": None,  # history=0 なので来ない
                "rating": p.get("rating"),
                "reviewcount": p.get("reviewCount"),
            }

            if row["asin"] and row["title"]:
                rows.append(row)

        time.sleep(SLEEP_BETWEEN_BATCH)

    if not rows:
        print("[SKIP] no product rows fetched")
        return

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    print(f"[OK] fetched {len(rows)} products")
    print(f"     output -> {OUT_FILE}")


if __name__ == "__main__":
    main()
