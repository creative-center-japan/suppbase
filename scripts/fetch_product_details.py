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

AMAZON_IMAGE_BASE = "https://images-na.ssl-images-amazon.com"


# -----------------------------
# ユーティリティ
# -----------------------------
def build_image_url(images_csv: str | None) -> str | None:
    """
    Keepa imagesCSV -> Amazon CDN 完全URL
    """
    if not images_csv:
        return None

    first = images_csv.split(",")[0]
    if first.startswith("http"):
        return first

    return f"{AMAZON_IMAGE_BASE}{first}"


def yen(price):
    """
    Keepaは最小通貨単位（円×100）
    """
    if isinstance(price, int) and price > 0:
        return price // 100
    return None


def calc_score(price, rating, reviewcount):
    """
    仮スコア（あとで調整前提）
    """
    score = 0

    if rating:
        score += rating * 20

    if reviewcount:
        score += min(reviewcount, 500)

    if price:
        score += max(0, 5000 - price) / 100

    return int(score)


def classify_sub_category(title: str) -> str:
    if not title:
        return "other"

    t = title.lower()

    if "bcaa" in t:
        return "bcaa"

    if "ソイ" in title or "soy" in t:
        return "soy"

    if "wpi" in t or "isolate" in t or "アイソレート" in title:
        return "wpi"

    if "ホエイ" in title or "whey" in t:
        return "whey"

    return "other"


# -----------------------------
# Keepa Product API
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

            price_yen = yen(stats.get("buyBoxPrice"))

            row = {
                "asin": p.get("asin"),
                "title": title,
                "brand": p.get("brand"),
                "imageurl": build_image_url(p.get("imagesCSV")),
                "price": price_yen,
                "rating": p.get("rating"),
                "reviewcount": p.get("reviewCount"),
                "sub_category": classify_sub_category(title),
                "score": calc_score(
                    price_yen,
                    p.get("rating"),
                    p.get("reviewCount"),
                ),
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
