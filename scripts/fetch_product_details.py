import os
import json
import time
import requests

KEEPA_API_KEY = os.environ["KEEPA_API_KEY"]
DOMAIN_ID = 5  # Amazon.co.jp

ASIN_FILE = os.environ.get("ASIN_FILE", "asins_protein.json")
OUT_FILE = os.environ.get("OUT_FILE", "product_details.json")

API_URL = "https://api.keepa.com/product"
BATCH_SIZE = 20
SLEEP_SEC = 2


# -----------------------------
# 分類ロジック
# -----------------------------
def classify_sub_category(title: str) -> str:
    if not title:
        return "other"

    t = title.lower()

    # BCAA
    if "bcaa" in t:
        return "bcaa"

    # ソイ
    if "ソイ" in title or "soy" in t:
        return "soy"

    # WPI（アイソレート）
    if "wpi" in t or "isolate" in t or "アイソレート" in title:
        return "wpi"

    # ホエイ
    if "ホエイ" in title or "whey" in t:
        return "whey"

    return "other"


# -----------------------------
# Product API
# -----------------------------
def fetch_products(asins):
    r = requests.get(
        API_URL,
        params={
            "key": KEEPA_API_KEY,
            "domain": DOMAIN_ID,
            "asin": ",".join(asins),
            "stats": 180,
            "update": -1,
            "history": 0,
        },
        timeout=60,
    )

    if r.status_code == 429:
        print("[429] rate limited -> skip batch")
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

    for i in range(0, len(asins), BATCH_SIZE):
        batch = asins[i:i + BATCH_SIZE]
        print(f"[i] fetch products {i + 1} - {i + len(batch)}")

        products = fetch_products(batch)

        for p in products:
            title = p.get("title")
            stats = p.get("stats") or {}

            row = {
                "asin": p.get("asin"),
                "title": title,
                "brand": p.get("brand"),
                "imageurl": (
                    p.get("imagesCSV", "").split(",")[0]
                    if p.get("imagesCSV")
                    else None
                ),
                "price": stats.get("buyBoxPrice"),
                "rating": p.get("rating"),
                "reviewcount": p.get("reviewCount"),
                "sub_category": classify_sub_category(title),
            }

            if row["asin"] and row["title"]:
                rows.append(row)

        time.sleep(SLEEP_SEC)

    if not rows:
        print("[SKIP] no product rows fetched")
        return

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    print(f"[OK] fetched {len(rows)} products -> {OUT_FILE}")


if __name__ == "__main__":
    main()
